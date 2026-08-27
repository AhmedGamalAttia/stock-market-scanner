"""Performance statistics over a list of Trades."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from statistics import mean

from strategies.base import Trade


def closed(trades: list[Trade]) -> list[Trade]:
    return [t for t in trades if t.reason != "end_of_data"]


def _max_drawdown(pnls_in_order: list[float], capital: float) -> float:
    """Max peak-to-trough drawdown of cumulative PnL, as a fraction of capital."""
    eq = capital
    peak = capital
    worst = 0.0
    for p in pnls_in_order:
        eq += p
        peak = max(peak, eq)
        dd = (peak - eq) / peak if peak > 0 else 0.0
        worst = max(worst, dd)
    return round(worst, 4)


def summarize(trades: list[Trade], capital: float, *, account_level: bool = False) -> dict:
    """Per-trade quality stats. ``account_level`` adds drawdown / return, which
    only make sense for a sequence a single account could actually hold (see
    ``portfolio_sim``) — never for the pooled list of all tickers."""
    ts = sorted(closed(trades), key=lambda t: (t.exit_date, t.entry_date))
    n = len(ts)
    if n == 0:
        return {"n_trades": 0}
    rs = [t.r_multiple for t in ts]
    pnls = [t.pnl_net for t in ts]
    wins = [t for t in ts if t.pnl_net > 0]
    losses = [t for t in ts if t.pnl_net <= 0]
    gross_win = sum(t.pnl_net for t in wins)
    gross_loss = -sum(t.pnl_net for t in losses)
    pf = round(gross_win / gross_loss, 2) if gross_loss > 0 else None
    out = {
        "n_trades": n,
        "win_rate": round(len(wins) / n, 4),
        "avg_r": round(mean(rs), 3),
        "avg_win_r": round(mean(t.r_multiple for t in wins), 3) if wins else 0.0,
        "avg_loss_r": round(mean(t.r_multiple for t in losses), 3) if losses else 0.0,
        "profit_factor": pf,
        "expectancy_egp": round(mean(pnls), 2),
        "total_pnl": round(sum(pnls), 2),
        "avg_hold_bars": round(mean(t.bars_held for t in ts), 1),
        "best_r": round(max(rs), 2),
        "worst_r": round(min(rs), 2),
        "exit_reasons": dict(Counter(t.reason for t in ts)),
        "tp1_hit_rate": round(sum(1 for t in ts if t.tp_hits and t.tp_hits[0]) / n, 4),
    }
    if account_level:
        out["total_return_pct"] = round(sum(pnls) / capital, 4)
        out["max_drawdown_pct"] = _max_drawdown(pnls, capital)
        first = ts[0].entry_date
        last = ts[-1].exit_date
        years = max((_days(first, last)) / 365.25, 0.1)
        out["years"] = round(years, 2)
        out["cagr_pct"] = round(((capital + sum(pnls)) / capital) ** (1 / years) - 1, 4)
    return out


def _days(a: str, b: str) -> int:
    from datetime import date

    return (date.fromisoformat(b) - date.fromisoformat(a)).days


def equity_curve(trades: list[Trade], capital: float) -> list[dict]:
    ts = sorted(closed(trades), key=lambda t: (t.exit_date, t.entry_date))
    eq = capital
    curve: list[dict] = []
    if ts:
        curve.append({"date": ts[0].entry_date, "equity": round(capital, 2)})
    for t in ts:
        eq += t.pnl_net
        curve.append({"date": t.exit_date, "equity": round(eq, 2)})
    return curve


def portfolio_sim(trades: list[Trade], capital: float, max_concurrent: int = 4) -> dict:
    """What actually happens if you follow every signal with ONE 20k account:
    at most ``max_concurrent`` open trades; extra signals are skipped."""
    ts = sorted(closed(trades), key=lambda t: (t.entry_date, t.symbol))
    open_until: list[str] = []
    taken: list[Trade] = []
    skipped = 0
    for t in ts:
        open_until = [d for d in open_until if d >= t.entry_date]
        if len(open_until) >= max_concurrent:
            skipped += 1
            continue
        open_until.append(t.exit_date)
        taken.append(t)
    stats = summarize(taken, capital, account_level=True)
    stats["skipped_signals"] = skipped
    stats["max_concurrent"] = max_concurrent
    return {"stats": stats, "equity_curve": equity_curve(taken, capital)}


def trade_to_dict(t: Trade) -> dict:
    d = asdict(t)
    return d
