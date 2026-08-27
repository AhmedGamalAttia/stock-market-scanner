"""Bar-by-bar simulation of one strategy on one symbol.

Realism rules (all pessimistic on purpose):
  * A signal on bar i's close is filled at bar i+1's OPEN (+ slippage).
  * Each bar: the stop is checked BEFORE take-profits. A gap through the stop
    fills at the open, not at the stop.
  * TP fills at the TP price (limit), or at the open if it gapped above it.
  * Commission is charged on both legs (Thndr ≈ 0.4% per side).
  * Sizing = fixed-fractional on the *starting* capital (no compounding) so a
    trade's R-multiple means the same thing in 2021 and in 2026.
  * One position per symbol; a new signal while in a trade is ignored.
  * Backtests run on split/dividend-ADJUSTED prices (adjclose/close factor).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from signals import DEFAULT_CAPITAL, DEFAULT_RISK_PCT, _position_size
from strategies.base import Exit, Strategy, Trade


@dataclass
class BacktestConfig:
    capital: float = float(DEFAULT_CAPITAL)
    risk_pct: float = DEFAULT_RISK_PCT
    commission_pct: float = 0.004  # per side → 0.8% round trip
    slippage_pct: float = 0.001    # per side
    use_adjusted: bool = True

    def as_dict(self) -> dict:
        return {
            "capital": self.capital,
            "risk_pct": self.risk_pct,
            "commission_pct_per_side": self.commission_pct,
            "slippage_pct_per_side": self.slippage_pct,
            "use_adjusted": self.use_adjusted,
        }


def adjust_ohlc(df: pd.DataFrame) -> pd.DataFrame:
    """Scale OHLC by adjclose/close so splits don't look like crashes; also
    repair the odd Yahoo row where high < open etc."""
    out = df.copy()
    if "adjclose" in out.columns:
        factor = (out["adjclose"] / out["close"]).replace([np.inf, -np.inf], np.nan).fillna(1.0)
        for c in ("open", "high", "low", "close"):
            out[c] = out[c] * factor
    out["high"] = out[["open", "high", "low", "close"]].max(axis=1)
    out["low"] = out[["open", "high", "low", "close"]].min(axis=1)
    return out


class _Position:
    __slots__ = (
        "entry_date", "entry_px", "shares_total", "shares_open", "stop", "initial_stop",
        "tps", "tp_hits", "bars_held", "exits", "costs", "mfe", "mae", "max_hold",
    )

    def __init__(self, entry_date: str, entry_px: float, shares: int, stop: float,
                 tps: list[float | None], max_hold: int | None, entry_cost: float):
        self.entry_date = entry_date
        self.entry_px = entry_px
        self.shares_total = shares
        self.shares_open = shares
        self.stop = stop
        self.initial_stop = stop
        self.tps = tps
        self.tp_hits = [False] * len(tps)
        self.bars_held = 0
        self.exits: list[Exit] = []
        self.costs = entry_cost
        self.mfe = 0.0
        self.mae = 0.0
        self.max_hold = max_hold


def _nan_to_none(x) -> float | None:
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else float(x)


def run_symbol(symbol: str, df: pd.DataFrame, strategy: Strategy, cfg: BacktestConfig) -> list[Trade]:
    if df is None or len(df) < 80:
        return []
    data = adjust_ohlc(df) if cfg.use_adjusted else df
    prep = strategy.prepare(data)

    o = prep["open"].to_numpy(float)
    h = prep["high"].to_numpy(float)
    l = prep["low"].to_numpy(float)
    c = prep["close"].to_numpy(float)
    entry_sig = prep["long_entry"].to_numpy(bool)
    exit_sig = prep["long_exit"].to_numpy(bool)
    stop_lvl = prep["stop"].to_numpy(float)
    tp_cols = [prep[f"tp{k}"].to_numpy(float) for k in (1, 2, 3)]
    if "max_hold" in prep.columns:
        max_hold_col = prep["max_hold"].to_numpy(float)
    else:
        max_hold_col = np.full(len(prep), np.nan)
    dates = [d.date().isoformat() for d in prep.index]
    fracs = list(strategy.tp_fractions)

    comm = cfg.commission_pct
    slip = cfg.slippage_pct
    n = len(prep)

    trades: list[Trade] = []
    pos: _Position | None = None
    pending_entry: dict | None = None
    pending_exit: str | None = None

    def finalize(p: _Position, i: int, reason: str) -> None:
        proceeds = sum(e.shares * e.price for e in p.exits)
        pnl = proceeds - p.shares_total * p.entry_px - p.costs
        risk_total = p.shares_total * (p.entry_px - p.initial_stop)
        trades.append(
            Trade(
                symbol=symbol,
                strategy=strategy.name,
                entry_date=p.entry_date,
                entry_price=round(p.entry_px, 4),
                shares=p.shares_total,
                initial_stop=round(p.initial_stop, 4),
                tp_levels=[_nan_to_none(t) for t in p.tps],
                exits=p.exits,
                tp_hits=p.tp_hits,
                pnl_net=round(pnl, 2),
                r_multiple=round(pnl / risk_total, 3) if risk_total > 0 else 0.0,
                bars_held=p.bars_held,
                reason=reason,
                exit_date=dates[i],
                mfe_r=round(p.mfe, 2),
                mae_r=round(p.mae, 2),
            )
        )

    def sell(p: _Position, i: int, qty: int, px: float, reason: str) -> None:
        qty = min(qty, p.shares_open)
        if qty <= 0:
            return
        p.exits.append(Exit(date=dates[i], price=round(px, 4), shares=qty, reason=reason))
        p.costs += qty * px * comm
        p.shares_open -= qty

    for i in range(n):
        # ---- A) fills at today's open (decisions taken on yesterday's close)
        if pos is not None and pending_exit is not None:
            px = o[i] * (1 - slip)
            sell(pos, i, pos.shares_open, px, pending_exit)
            finalize(pos, i, pending_exit)
            pos, pending_exit = None, None

        if pos is None and pending_entry is not None:
            px = o[i] * (1 + slip)
            stop = pending_entry["stop"]
            if not np.isnan(px) and stop < px:
                shares, _, _ = _position_size(px, stop, cfg.capital, cfg.risk_pct)
                if shares > 0:
                    pos = _Position(
                        entry_date=dates[i], entry_px=px, shares=shares, stop=stop,
                        tps=pending_entry["tps"], max_hold=pending_entry["max_hold"],
                        entry_cost=shares * px * comm,
                    )
            pending_entry = None

        # ---- B) manage the open position through today's bar
        if pos is not None:
            pos.bars_held += 1
            r = pos.entry_px - pos.initial_stop
            if r > 0:
                pos.mfe = max(pos.mfe, (h[i] - pos.entry_px) / r)
                pos.mae = min(pos.mae, (l[i] - pos.entry_px) / r)

            if l[i] <= pos.stop:  # stop first — pessimistic
                px = min(o[i], pos.stop) * (1 - slip)
                reason = "stop_hit" if pos.stop == pos.initial_stop else "breakeven_stop"
                sell(pos, i, pos.shares_open, px, reason)
                finalize(pos, i, reason)
                pos = None
            else:
                last_tp_idx = max((k for k, t in enumerate(pos.tps) if t is not None and not np.isnan(t)), default=-1)
                for k, tp in enumerate(pos.tps):
                    if tp is None or np.isnan(tp) or pos.tp_hits[k] or pos.shares_open <= 0:
                        continue
                    if h[i] >= tp:
                        px = max(o[i], tp) * (1 - slip)
                        if k >= last_tp_idx or k >= len(fracs) - 1:
                            qty = pos.shares_open
                        else:
                            qty = int(round(pos.shares_total * fracs[k]))
                        sell(pos, i, qty, px, f"tp{k + 1}")
                        pos.tp_hits[k] = True
                        if k == 0 and strategy.breakeven_after_tp1:
                            pos.stop = max(pos.stop, pos.entry_px)
                if pos.shares_open <= 0:
                    finalize(pos, i, "tp_final")
                    pos = None

            if pos is not None:
                if exit_sig[i]:
                    pending_exit = "trend_flip"
                else:
                    mh = pos.max_hold
                    if mh is not None and not np.isnan(mh) and pos.bars_held >= int(mh):
                        pending_exit = "time_stop"
                if i == n - 1:  # end of data: mark to market
                    sell(pos, i, pos.shares_open, c[i], "end_of_data")
                    finalize(pos, i, "end_of_data")
                    pos, pending_exit = None, None

        # ---- C) new signal on today's close → fill tomorrow
        if pos is None and pending_exit is None and entry_sig[i] and i < n - 1:
            st = stop_lvl[i]
            if not np.isnan(st) and st < c[i]:
                pending_entry = {
                    "stop": float(st),
                    "tps": [float(col[i]) if not np.isnan(col[i]) else None for col in tp_cols],
                    "max_hold": (
                        int(max_hold_col[i]) if not np.isnan(max_hold_col[i]) else strategy.max_hold
                    ),
                }

    return trades
