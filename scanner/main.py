"""EGX scanner entry point.

Usage:
  python main.py                # full run, writes to Supabase if env is set
  python main.py --dry-run      # local only, prints top opportunities
  python main.py --limit 10     # only scan first 10 tickers (debug)
"""

from __future__ import annotations

import argparse
import sys
import time

# Force UTF-8 stdout so Arabic text doesn't crash Windows cp1252 console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
from tabulate import tabulate

from fetch import fetch_history, to_price_rows
from indicators import enrich
from signals import build_signal
from store import (
    get_client,
    log_run,
    replace_signals_for_date,
    upsert_daily_prices,
    upsert_stocks,
)
from tickers import EGX_TICKERS, list_symbols, metadata_rows


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="Don't write to Supabase")
    p.add_argument("--limit", type=int, default=0, help="Limit number of tickers (0 = all)")
    p.add_argument("--min-score", type=int, default=30)
    return p.parse_args()


def main() -> int:
    load_dotenv()
    args = parse_args()

    symbols = list_symbols()
    if args.limit:
        symbols = symbols[: args.limit]

    print(f"=== EGX Scanner ===  scanning {len(symbols)} tickers")

    client = None if args.dry_run else get_client()
    if args.dry_run:
        print("(dry-run mode — no Supabase writes)")
    elif client is None:
        print("!! SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY missing — failing fast.")
        print("   Add them in GitHub: Settings → Secrets and variables → Actions.")
        return 2

    if client is not None:
        try:
            upsert_stocks(client, metadata_rows())
            print(f"Supabase OK — upserted {len(metadata_rows())} stocks metadata")
        except Exception as e:  # noqa: BLE001
            print(f"!! Supabase upsert_stocks FAILED: {type(e).__name__}: {e}")
            print("   Most likely cause: you used the ANON key instead of the SERVICE_ROLE key,")
            print("   or the schema.sql wasn't run in Supabase yet.")
            raise

    failures = 0
    signals = []
    all_price_rows: list[dict] = []
    last_signal_date: str | None = None

    for i, sym in enumerate(symbols, 1):
        print(f"[{i:>3}/{len(symbols)}] {sym} ... ", end="", flush=True)
        df = fetch_history(sym)
        if df is None or df.empty:
            print("no data")
            failures += 1
            continue

        enriched = enrich(df)
        sig = build_signal(sym, enriched, min_score=args.min_score)
        last_close = float(enriched["close"].iloc[-1])
        if sig:
            signals.append(sig)
            last_signal_date = sig.signal_date
            print(
                f"score={sig.score} conf={sig.confidence} {sig.risk_class:6} "
                f"setups={','.join(sig.setups)}  close={last_close:.2f}"
            )
        else:
            print(f"close={last_close:.2f}  no signal")

        all_price_rows.extend(to_price_rows(sym, df, last_n=120))
        time.sleep(0.25)  # be polite to data source

    # Sort by confidence (expert layer's verdict), then by raw technical score
    signals.sort(key=lambda s: (s.confidence, s.score), reverse=True)

    print("\n--- Top opportunities ---")
    if not signals:
        print("(no signals today)")
    else:
        rows = [
            [
                s.symbol,
                s.confidence,
                s.score,
                s.risk_class,
                ", ".join(s.setups)[:30],
                s.entry,
                s.stop_loss,
                s.target_1,
                s.target_2,
                s.blended_rr,
                s.suggested_shares_20k,
                s.expected_days,
            ]
            for s in signals[:25]
        ]
        print(
            tabulate(
                rows,
                headers=[
                    "symbol",
                    "conf",
                    "score",
                    "risk",
                    "setups",
                    "entry",
                    "stop",
                    "T1",
                    "T2",
                    "R:R",
                    "@20k",
                    "days",
                ],
                tablefmt="github",
            )
        )

    emitted = 0
    if client is not None:
        if all_price_rows:
            upsert_daily_prices(client, all_price_rows)
        if last_signal_date and signals:
            emitted = replace_signals_for_date(client, signals, last_signal_date)
        log_run(
            client,
            ok=failures < len(symbols),  # only "ok" if at least one fetch worked
            symbols_total=len(symbols),
            symbols_failed=failures,
            signals_emitted=emitted,
            notes=f"min_score={args.min_score}",
        )
        print(
            f"\nSupabase: wrote {len(all_price_rows)} prices, {emitted} signals "
            f"({failures}/{len(symbols)} fetch failures)"
        )

    if failures == len(symbols):
        print("!! ALL fetches failed. Likely the data source is blocking GitHub IPs.")
        return 3
    return 0


if __name__ == "__main__":
    import traceback

    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\ninterrupted")
        sys.exit(130)
    except Exception as e:  # noqa: BLE001
        print("\n========= UNCAUGHT EXCEPTION =========")
        print(f"{type(e).__name__}: {e}")
        traceback.print_exc()
        print("======================================")
        sys.exit(1)
