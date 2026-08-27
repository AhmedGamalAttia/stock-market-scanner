"""EGX scanner entry point — daily post-close run.

Usage:
  python main.py                 # fetch → signals → write web/public/data/*.json
  python main.py --dry-run       # fetch + print only, write nothing
  python main.py --no-fetch      # use cached prices only (fast local iteration)
  python main.py --limit 10      # only scan first 10 tickers (debug)
  python main.py --min-score 20  # looser signal threshold

Everything the site shows comes from the JSON files this script writes; the
GitHub Actions workflow commits them and Vercel redeploys.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone

# Force UTF-8 stdout so Arabic text doesn't crash Windows cp1252 console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
from tabulate import tabulate

from fetch import update_cache
from notify import format_daily_message, send_telegram
from paths import BACKTEST_DIR, DATA_DIR
from positions import archive_closed, bootstrap, build_actions, evaluate, open_new
from store_json import (
    append_trades_live,
    read_json,
    read_meta,
    read_positions,
    read_trades_live,
    write_latest,
    write_meta,
    write_positions,
    write_stocks,
)
from strategies import DEFAULT_STRATEGY, get_strategy
from tickers import list_symbols, metadata_rows, stock_info

SLEEP_PER_CALL = 0.4  # be polite to Yahoo


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="Print only, write nothing")
    p.add_argument("--no-fetch", action="store_true", help="Use cached prices, skip Yahoo")
    p.add_argument("--limit", type=int, default=0, help="Limit number of tickers (0 = all)")
    p.add_argument("--min-score", type=int, default=30, help="(current_scoring only)")
    p.add_argument(
        "--strategy",
        default=None,
        help="Override the live strategy (default: LIVE_STRATEGY env, else the backtest winner)",
    )
    p.add_argument("--notify", action="store_true", help="Send Telegram even if the data date did not advance")
    p.add_argument(
        "--bootstrap",
        action="store_true",
        help="If the position book is empty, seed it with the strategy's currently-open trades",
    )
    return p.parse_args()


def resolve_strategy_name(cli_value: str | None) -> tuple[str, str]:
    """CLI flag → env var → backtest/index.json 'recommended' → default."""
    if cli_value:
        return cli_value, "cli"
    env = os.environ.get("LIVE_STRATEGY")
    if env:
        return env, "env"
    idx = read_json(BACKTEST_DIR / "index.json")
    if idx and idx.get("recommended"):
        return idx["recommended"], "backtest"
    return DEFAULT_STRATEGY, "default"


def _signal_payload(sig) -> dict:
    d = asdict(sig)
    info = stock_info(sig.symbol) or {}
    d["stock"] = {
        "symbol": sig.symbol,
        "name_ar": info.get("name_ar"),
        "name_en": info.get("name_en"),
        "sector": info.get("sector"),
        "sharia_status": info.get("sharia_status"),
    }
    return d


def main() -> int:
    load_dotenv()
    args = parse_args()
    write = not args.dry_run

    symbols = list_symbols()
    if args.limit:
        symbols = symbols[: args.limit]

    strat_name, strat_source = resolve_strategy_name(args.strategy)
    strategy = get_strategy(strat_name)

    print(f"=== EGX Scanner ===  {len(symbols)} tickers  →  {DATA_DIR}")
    print(f"strategy: {strategy.name} ({strat_source})")
    if args.dry_run:
        print("(dry-run — nothing will be written)")
    if args.no_fetch:
        print("(no-fetch — using cached prices)")

    failures = 0
    stale = 0
    signals = []
    last_dates: list[str] = []
    prepared: dict = {}

    for i, sym in enumerate(symbols, 1):
        print(f"[{i:>3}/{len(symbols)}] {sym:<6} ", end="", flush=True)
        res = update_cache(sym, fetch=not args.no_fetch, write=write)
        df = res.df
        if df is None or df.empty:
            print("no data")
            failures += 1
            if not args.no_fetch:
                time.sleep(SLEEP_PER_CALL)
            continue
        if res.source == "cache" and not args.no_fetch:
            stale += 1

        last_dates.append(df.index[-1].date().isoformat())
        prep = strategy.prepare(df)
        prepared[sym] = prep
        sig = strategy.signal_from_prepared(prep, symbol=sym, min_score=args.min_score)
        last_close = float(df["close"].iloc[-1])
        tag = "" if res.source == "yahoo" else f" [{res.source}]"
        if sig:
            signals.append(sig)
            print(
                f"{len(df):>5} bars  close={last_close:>8.2f}  "
                f"score={sig.score:<3} conf={sig.confidence:<3} {sig.risk_class:<6} "
                f"{','.join(sig.setups)}{tag}"
            )
        else:
            print(f"{len(df):>5} bars  close={last_close:>8.2f}  —{tag}")
        if not args.no_fetch:
            time.sleep(SLEEP_PER_CALL)

    # Sort by confidence (expert layer's verdict), then by raw technical score
    signals.sort(key=lambda s: (s.confidence, s.score), reverse=True)

    print("\n--- Top opportunities ---")
    if not signals:
        print("(no signals today)")
    else:
        rows = [
            [
                s.symbol, s.confidence, s.score, s.risk_class,
                ", ".join(s.setups)[:30],
                s.entry, s.stop_loss, s.target_1, s.target_2,
                s.blended_rr, s.suggested_shares_20k, s.expected_days,
            ]
            for s in signals[:25]
        ]
        print(
            tabulate(
                rows,
                headers=["symbol", "conf", "score", "risk", "setups", "entry", "stop",
                         "T1", "T2", "R:R", "@20k", "days"],
                tablefmt="github",
            )
        )

    data_date = max(last_dates) if last_dates else None
    ran_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    ok = failures < len(symbols)
    prev_meta = read_meta() or {}

    # ---- paper positions: replay new bars, then add today's signals
    names = {r["symbol"]: r["name_ar"] for r in metadata_rows()}
    book = read_positions()
    if args.bootstrap and not book["positions"]:
        seeded = bootstrap(book, prepared, strategy, names)
        print(f"\nbootstrap: seeded {len(seeded)} open position(s) from the strategy's current state")
    closed_now = evaluate(book, prepared, strategy)
    open_new(signals, book, names)
    closed_all = archive_closed(book)
    history = read_trades_live() + closed_all
    holds, exits = build_actions(book, data_date, history)
    if closed_now:
        print("\n--- Exits ---")
        for p in closed_now:
            print(f"  {p['symbol']:<6} {p.get('reason_ar')}  {p.get('realized_r', 0):+.2f}R  {p.get('realized_pnl', 0):+,.0f} EGP")
    if holds:
        print(f"\n--- Open positions: {len(holds)} ---")
        for h in holds:
            chg = h.get("change_pct")
            print(f"  {h['symbol']:<6} {h['status']:<8} entry={h['entry']} last={h['last_close']} "
                  f"{'' if chg is None else f'{chg:+.1f}%'}  {h['note_ar']}")

    latest = {
        "date": data_date,
        "generated_at": ran_at,
        "strategy": strategy.name,
        "strategy_label_ar": strategy.label_ar,
        "buys": [_signal_payload(s) for s in signals],
        "holds": holds,
        "exits": exits,
    }

    if write:
        write_stocks(metadata_rows())
        write_positions(book)
        append_trades_live(closed_all)
        write_latest(latest)
        write_meta(
            {
                "ran_at": ran_at,
                "ok": ok,
                "data_date": data_date,
                "symbols_total": len(symbols),
                "symbols_failed": failures,
                "symbols_stale": stale,
                "signals_emitted": len(signals),
                "strategy": strategy.name,
                "notes": f"strategy={strategy.name} ({strat_source})",
            }
        )
        print(
            f"\nWrote {len(signals)} signals, {len(holds)} open, {len(exits)} exits for {data_date} "
            f"({failures} failed, {stale} stale) → {DATA_DIR}"
        )
        advanced = data_date and data_date != prev_meta.get("data_date")
        if advanced or args.notify:
            send_telegram(format_daily_message(latest))
        else:
            print("(telegram: data date unchanged — no message)")
    elif args.notify:
        print("\n--- Telegram preview ---\n" + format_daily_message(latest))

    if failures == len(symbols):
        print("!! ALL fetches failed and no cache available.")
        return 3
    return 0


if __name__ == "__main__":
    import traceback

    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\ninterrupted")
        sys.exit(130)
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        sys.exit(1)
