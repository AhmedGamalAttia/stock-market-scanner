"""Run every strategy over every cached ticker and publish the report.

  python -m backtest.run                         # all strategies
  python -m backtest.run --strategies kalman     # one
  python -m backtest.run --split 0.7             # in-sample = first 70% of dates

Outputs
  web/public/data/backtest/{strategy}.json   aggregate + per-ticker + curves
  web/public/data/backtest/index.json        comparison + recommended strategy
  data/backtest_detail/{strategy}_trades.json  every trade (not shipped to browser)

Selection rule (anti-overfitting): the recommended live strategy is the one
with the best OUT-OF-SAMPLE expectancy (avg R) with at least MIN_OOS_TRADES.
No parameters are tuned here — both strategies run with their published
defaults, so the out-of-sample numbers are an honest estimate.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from backtest.engine import BacktestConfig, run_symbol
from backtest.metrics import equity_curve, portfolio_sim, summarize, trade_to_dict
from paths import BACKTEST_DETAIL_DIR, BACKTEST_DIR
from store_json import read_prices, write_json
from strategies import ALL_STRATEGIES, get_strategy
from tickers import list_symbols

MIN_OOS_TRADES = 30


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--strategies", default=",".join(ALL_STRATEGIES))
    p.add_argument("--split", type=float, default=0.7, help="in-sample fraction of the date range")
    p.add_argument("--max-concurrent", type=int, default=4)
    p.add_argument("--min-score", type=int, default=30)
    return p.parse_args()


def _split_date(frames: list, frac: float) -> str:
    dates = sorted({d for df in frames for d in df.index})
    if not dates:
        return "1970-01-01"
    idx = min(len(dates) - 1, max(0, int(len(dates) * frac)))
    return dates[idx].date().isoformat()


def main() -> int:
    args = parse_args()
    cfg = BacktestConfig()
    names = [s.strip() for s in args.strategies.split(",") if s.strip()]

    symbols = list_symbols()
    frames = {s: read_prices(s) for s in symbols}
    frames = {s: df for s, df in frames.items() if df is not None and len(df) >= 80}
    if not frames:
        print("!! no cached prices — run main.py first")
        return 2
    split_date = _split_date(list(frames.values()), args.split)
    first = min(df.index[0] for df in frames.values()).date().isoformat()
    last = max(df.index[-1] for df in frames.values()).date().isoformat()
    print(f"=== Backtest ===  {len(frames)} tickers  {first} → {last}   in-sample ends {split_date}")

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    index: list[dict] = []

    for name in names:
        strat = get_strategy(name)
        if hasattr(strat, "min_score"):
            strat.min_score = args.min_score
        all_trades = []
        per_ticker = []
        for sym, df in frames.items():
            trades = run_symbol(sym, df, strat, cfg)
            all_trades.extend(trades)
            full = summarize(trades, cfg.capital)
            oos = summarize([t for t in trades if t.entry_date >= split_date], cfg.capital)
            per_ticker.append({"symbol": sym, "full": full, "out_of_sample": oos})

        is_trades = [t for t in all_trades if t.entry_date < split_date]
        oos_trades = [t for t in all_trades if t.entry_date >= split_date]
        agg = {
            "full": summarize(all_trades, cfg.capital),
            "in_sample": summarize(is_trades, cfg.capital),
            "out_of_sample": summarize(oos_trades, cfg.capital),
        }
        port_full = portfolio_sim(all_trades, cfg.capital, args.max_concurrent)
        port_oos = portfolio_sim(oos_trades, cfg.capital, args.max_concurrent)

        report = {
            "strategy": strat.name,
            "label_ar": strat.label_ar,
            "generated_at": generated_at,
            "config": cfg.as_dict()
            | {
                "tp_fractions": list(strat.tp_fractions),
                "breakeven_after_tp1": strat.breakeven_after_tp1,
                "max_concurrent": args.max_concurrent,
                "min_score": getattr(strat, "min_score", None),
            },
            "period": {"from": first, "to": last, "in_sample_until": split_date},
            "aggregate": agg,
            "portfolio": {
                "full": port_full,
                "out_of_sample": port_oos,
            },
            "pooled_equity_curve": equity_curve(all_trades, cfg.capital),
            "per_ticker": sorted(per_ticker, key=lambda r: -(r["full"].get("total_pnl") or 0)),
        }
        BACKTEST_DIR.mkdir(parents=True, exist_ok=True)
        write_json(BACKTEST_DIR / f"{strat.name}.json", report)
        BACKTEST_DETAIL_DIR.mkdir(parents=True, exist_ok=True)
        write_json(
            BACKTEST_DETAIL_DIR / f"{strat.name}_trades.json",
            [trade_to_dict(t) for t in all_trades],
            indent=None,
        )

        f, o = agg["full"], agg["out_of_sample"]
        pf_, po_ = port_full["stats"], port_oos["stats"]
        print(
            f"\n{strat.name:<22} trades: n={f.get('n_trades',0):<4} win={f.get('win_rate',0):.0%} "
            f"avgR={f.get('avg_r',0):+.2f} PF={f.get('profit_factor')} | "
            f"OOS: n={o.get('n_trades',0):<4} win={o.get('win_rate',0):.0%} avgR={o.get('avg_r',0):+.2f} "
            f"PF={o.get('profit_factor')} | 20k account (max 4 open): "
            f"{pf_.get('total_pnl',0):+,.0f} EGP  CAGR={pf_.get('cagr_pct',0):.1%}  DD={pf_.get('max_drawdown_pct',0):.0%}"
        )
        keys = ("n_trades", "win_rate", "avg_r", "profit_factor", "total_pnl")
        index.append(
            {
                "strategy": strat.name,
                "label_ar": strat.label_ar,
                "full": {k: f.get(k) for k in keys},
                "out_of_sample": {k: o.get(k) for k in keys},
                "portfolio_full": {k: pf_.get(k) for k in ("total_pnl", "cagr_pct", "max_drawdown_pct", "n_trades", "skipped_signals")},
                "portfolio_oos": {k: po_.get(k) for k in ("total_pnl", "cagr_pct", "max_drawdown_pct", "n_trades", "skipped_signals")},
            }
        )

    # Selection: what a single 20k account would have earned OUT OF SAMPLE,
    # per unit of drawdown suffered (Calmar-style). Per-trade avg R ignores
    # trade frequency and slot usage, so it is shown but not used.
    def calmar(r: dict) -> float:
        p = r["portfolio_oos"]
        cagr = p.get("cagr_pct") or 0.0
        dd = max(p.get("max_drawdown_pct") or 0.0, 0.02)
        return cagr / dd

    eligible = [r for r in index if (r["out_of_sample"].get("n_trades") or 0) >= MIN_OOS_TRADES]
    pool = eligible or index
    for r in index:
        r["oos_calmar"] = round(calmar(r), 2)
    best = max(pool, key=calmar) if pool else None
    write_json(
        BACKTEST_DIR / "index.json",
        {
            "generated_at": generated_at,
            "period": {"from": first, "to": last, "in_sample_until": split_date},
            "selection_rule": (
                f"أعلى نسبة عائد/تراجع خارج العينة على حساب 20 ألف (بحد أقصى {args.max_concurrent} مراكز)"
                f" مع ≥{MIN_OOS_TRADES} صفقة"
            ),
            "recommended": best["strategy"] if best else None,
            "strategies": index,
        },
    )
    print("\nOOS on a 20k account: " + " | ".join(
        f"{r['strategy']}: {r['portfolio_oos'].get('total_pnl',0):+,.0f} EGP "
        f"CAGR={r['portfolio_oos'].get('cagr_pct',0):.1%} DD={r['portfolio_oos'].get('max_drawdown_pct',0):.0%} "
        f"calmar={r['oos_calmar']}"
        for r in index
    ))
    if best:
        print(f"\nRecommended live strategy (OOS return/drawdown): {best['strategy']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
