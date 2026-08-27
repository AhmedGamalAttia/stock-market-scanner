"""Paper position book — turns "buy signals" into a daily BUY / HOLD / EXIT list.

Every live signal becomes a tracked paper position, managed with EXACTLY the
rules the backtester uses (next-open fill, stop before TP, TP ladder, trend
flip → exit at next open, time stop). Each day the scanner replays the newest
bar over every open position and tells the user what to do.

Idempotent: each position remembers ``last_evaluated`` so re-running the
scanner on the same data does nothing twice.

Costs use the same 0.4 %/side assumption as the backtest so realised P&L on
the site matches what the backtest promised.
"""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd

from signals import DEFAULT_CAPITAL, DEFAULT_RISK_PCT, SignalRow, _position_size
from strategies.base import Strategy

COMMISSION_PER_SIDE = 0.004

EXIT_REASONS_AR = {
    "stop_hit": "ضرب وقف الخسارة",
    "breakeven_stop": "خرج على سعر الدخول (الوقف المتحرك)",
    "tp_final": "تحقق الهدف الأخير ✅",
    "trend_flip": "انقلب الاتجاه لهابط",
    "time_stop": "انتهت المدة بدون تحرك",
    "invalid": "أُلغيت — الافتتاح تحت الوقف",
}


def _f(x, nd=2):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), nd)


def new_position(sig: SignalRow, name_ar: str | None) -> dict:
    return {
        "id": f"{sig.symbol}-{sig.signal_date}",
        "symbol": sig.symbol,
        "name_ar": name_ar,
        "strategy": sig.strategy,
        "signal_date": sig.signal_date,
        "status": "pending",          # pending → open → closed
        "entry_ref": sig.entry,       # signal close (what the card shows)
        "entry": None,                # actual paper fill (next open)
        "entry_date": None,
        "stop": sig.stop_loss,
        "initial_stop": sig.stop_loss,
        "tps": [sig.target_1, sig.target_2, sig.target_3],
        "tp_hit": [False, False, False],
        "shares": sig.suggested_shares_20k,
        "shares_open": sig.suggested_shares_20k,
        "risk_egp": None,
        "max_hold": sig.max_hold,
        "bars_held": 0,
        "high_water": None,
        "exits": [],
        "pending_exit": None,
        "last_evaluated": sig.signal_date,
        "last_close": sig.close,
        "unrealized_pnl": 0.0,
        "unrealized_r": 0.0,
        "note_ar": "فى انتظار الافتتاح لتنفيذ الدخول",
    }


def open_new(signals: list[SignalRow], book: dict, names: dict[str, str | None]) -> list[dict]:
    """Add today's signals as pending positions (skip symbols already held)."""
    held = {p["symbol"] for p in book["positions"] if p["status"] in ("pending", "open")}
    added = []
    for s in signals:
        if s.symbol in held:
            continue
        p = new_position(s, names.get(s.symbol))
        book["positions"].append(p)
        held.add(s.symbol)
        added.append(p)
    return added


def _sell(p: dict, date: str, qty: int, price: float, reason: str) -> None:
    qty = min(qty, p["shares_open"])
    if qty <= 0:
        return
    p["exits"].append({"date": date, "price": round(price, 4), "shares": qty, "reason": reason})
    p["shares_open"] -= qty


def _realized(p: dict) -> tuple[float, float]:
    """(pnl_net, r_multiple) over the exits so far."""
    if not p.get("entry"):
        return 0.0, 0.0
    proceeds = sum(e["shares"] * e["price"] for e in p["exits"])
    sold = sum(e["shares"] for e in p["exits"])
    cost_basis = sold * p["entry"]
    fees = cost_basis * COMMISSION_PER_SIDE + proceeds * COMMISSION_PER_SIDE
    pnl = proceeds - cost_basis - fees
    risk_total = p["shares"] * (p["entry"] - p["initial_stop"]) if p["shares"] else 0
    return round(pnl, 2), (round(pnl / risk_total, 3) if risk_total > 0 else 0.0)


def _close(p: dict, date: str, reason: str) -> None:
    p["status"] = "closed"
    p["closed_date"] = date
    p["reason"] = reason
    p["reason_ar"] = EXIT_REASONS_AR.get(reason, reason)
    p["pending_exit"] = None
    pnl, r = _realized(p)
    p["realized_pnl"] = pnl
    p["realized_r"] = r
    p["exit_price"] = round(p["exits"][-1]["price"], 4) if p["exits"] else None
    p["note_ar"] = p["reason_ar"]


def evaluate(book: dict, prepared: dict[str, pd.DataFrame], strategy: Strategy) -> list[dict]:
    """Replay every new bar over each pending/open position. Returns the
    positions that closed during this evaluation."""
    closed_now: list[dict] = []
    fracs = list(strategy.tp_fractions)

    for p in book["positions"]:
        if p["status"] == "closed":
            continue
        prep = prepared.get(p["symbol"])
        if prep is None or prep.empty:
            continue
        new_bars = prep[prep.index > pd.Timestamp(p["last_evaluated"])]
        for ts, bar in new_bars.iterrows():
            date = ts.date().isoformat()
            o, h, l, c = float(bar["open"]), float(bar["high"]), float(bar["low"]), float(bar["close"])
            p["last_evaluated"] = date
            p["last_close"] = round(c, 4)

            # ---- fill a pending entry at this bar's open
            if p["status"] == "pending":
                if p["stop"] >= o:
                    p["status"] = "closed"
                    p["closed_date"] = date
                    p["reason"] = "invalid"
                    p["reason_ar"] = EXIT_REASONS_AR["invalid"]
                    p["realized_pnl"] = 0.0
                    p["realized_r"] = 0.0
                    p["note_ar"] = p["reason_ar"]
                    closed_now.append(p)
                    break
                shares, _, risk = _position_size(o, p["stop"], DEFAULT_CAPITAL, DEFAULT_RISK_PCT)
                p["entry"] = round(o, 4)
                p["entry_date"] = date
                p["shares"] = shares
                p["shares_open"] = shares
                p["risk_egp"] = risk
                p["status"] = "open"
                p["high_water"] = o
                p["note_ar"] = "مركز مفتوح"

            # ---- exits flagged yesterday fill at today's open
            if p["pending_exit"]:
                _sell(p, date, p["shares_open"], o, p["pending_exit"])
                _close(p, date, p["pending_exit"])
                closed_now.append(p)
                break

            p["bars_held"] += 1
            p["high_water"] = max(p["high_water"] or o, h)

            # ---- stop first (pessimistic)
            if l <= p["stop"]:
                reason = "stop_hit" if p["stop"] == p["initial_stop"] else "breakeven_stop"
                _sell(p, date, p["shares_open"], min(o, p["stop"]), reason)
                _close(p, date, reason)
                closed_now.append(p)
                break

            # ---- take-profit ladder
            tps = p["tps"]
            last_idx = max((k for k, t in enumerate(tps) if t is not None), default=-1)
            for k, tp in enumerate(tps):
                if tp is None or p["tp_hit"][k] or p["shares_open"] <= 0:
                    continue
                if h >= tp:
                    px = max(o, tp)
                    if k >= last_idx or k >= len(fracs) - 1:
                        qty = p["shares_open"]
                    else:
                        qty = int(round(p["shares"] * fracs[k]))
                    _sell(p, date, qty, px, f"tp{k + 1}")
                    p["tp_hit"][k] = True
                    if k == 0 and strategy.breakeven_after_tp1:
                        p["stop"] = max(p["stop"], p["entry"])
                        p["note_ar"] = "تحقق الهدف الأول — الوقف اتحرك لسعر الدخول"
                    else:
                        p["note_ar"] = f"تحقق الهدف {k + 1} — بيع جزء من المركز"
            if p["shares_open"] <= 0:
                _close(p, date, "tp_final")
                closed_now.append(p)
                break

            # ---- signals that exit at the NEXT open
            if bool(bar.get("long_exit", False)):
                p["pending_exit"] = "trend_flip"
                p["note_ar"] = "⚠️ انقلب الاتجاه — اخرج غداً عند الافتتاح"
            elif p["max_hold"] and p["bars_held"] >= int(p["max_hold"]):
                p["pending_exit"] = "time_stop"
                p["note_ar"] = "⏱ انتهت المدة — اخرج غداً عند الافتتاح"

        # unrealised mark-to-market on the remainder
        if p["status"] == "open" and p.get("entry"):
            open_val = p["shares_open"] * (p["last_close"] - p["entry"])
            realized, _ = _realized(p)
            pnl = round(realized + open_val - p["shares_open"] * p["last_close"] * COMMISSION_PER_SIDE, 2)
            risk_total = p["shares"] * (p["entry"] - p["initial_stop"]) if p["shares"] else 0
            p["unrealized_pnl"] = pnl
            p["unrealized_r"] = round(pnl / risk_total, 2) if risk_total > 0 else 0.0

    return closed_now


def build_actions(book: dict, data_date: str | None, closed_history: list[dict]) -> tuple[list[dict], list[dict]]:
    """(holds, exits_today) in the shape latest.json publishes."""
    holds = []
    for p in book["positions"]:
        if p["status"] not in ("pending", "open"):
            continue
        entry = p["entry"] or p["entry_ref"]
        last = p["last_close"] or entry
        holds.append(
            {
                "id": p["id"],
                "symbol": p["symbol"],
                "name_ar": p["name_ar"],
                "status": p["status"],
                "signal_date": p["signal_date"],
                "entry_date": p["entry_date"],
                "entry": _f(entry),
                "stop": _f(p["stop"]),
                "tps": [_f(t) for t in p["tps"]],
                "tp_hit": p["tp_hit"],
                "shares": p["shares"],
                "shares_open": p["shares_open"],
                "last_close": _f(last),
                "change_pct": _f((last - entry) / entry * 100, 2) if entry else None,
                "stop_distance_pct": _f((last - p["stop"]) / last * 100, 2) if last else None,
                "unrealized_pnl": p["unrealized_pnl"],
                "unrealized_r": p["unrealized_r"],
                "bars_held": p["bars_held"],
                "pending_exit": p["pending_exit"],
                "note_ar": p["note_ar"],
            }
        )
    exits = [
        {
            "id": t["id"],
            "symbol": t["symbol"],
            "name_ar": t.get("name_ar"),
            "entry_date": t.get("entry_date"),
            "entry": _f(t.get("entry")),
            "exit_date": t.get("closed_date"),
            "exit_price": _f(t.get("exit_price")),
            "reason": t.get("reason"),
            "reason_ar": t.get("reason_ar"),
            "realized_pnl": t.get("realized_pnl"),
            "realized_r": t.get("realized_r"),
            "bars_held": t.get("bars_held"),
            "tp_hit": t.get("tp_hit"),
        }
        for t in closed_history
        if t.get("closed_date") == data_date
    ]
    holds.sort(key=lambda h: (h["status"] != "pending", h["symbol"]))
    exits.sort(key=lambda e: e["symbol"])
    return holds, exits


def bootstrap(book: dict, prepared: dict[str, pd.DataFrame], strategy: Strategy,
              names: dict[str, str | None], lookback: int = 120) -> list[dict]:
    """Seed an EMPTY book with the positions the strategy would currently be
    holding, so the user gets HOLD/EXIT guidance from day one instead of
    waiting weeks for fresh flips. Replays each candidate through ``evaluate``
    with the exact live rules; only positions still open survive. They are
    flagged ``bootstrap`` — informational, not an invitation to buy now."""
    if book["positions"]:
        return []
    seeded: list[dict] = []
    for sym, prep in prepared.items():
        if prep is None or len(prep) < lookback + 2:
            continue
        tail = prep.iloc[-lookback:]
        entries = tail.index[tail["long_entry"].to_numpy(bool)]
        if len(entries) == 0:
            continue
        sig_ts = entries[-1]
        after = prep[prep.index > sig_ts]
        if after.empty or bool(after["long_exit"].any()):
            continue  # the trend already flipped back — no open position
        sig_row = prep.loc[sig_ts]
        sig = strategy.signal_from_prepared(prep.loc[:sig_ts], symbol=sym)
        if sig is None:
            continue
        p = new_position(sig, names.get(sym))
        p["bootstrap"] = True
        book["positions"].append(p)
        seeded.append(p)
    # replay everything since each signal with the real rules
    evaluate(book, prepared, strategy)
    survivors = [p for p in book["positions"] if p["status"] == "open"]
    book["positions"] = survivors
    for p in survivors:
        p["note_ar"] = f"دخول سابق بتاريخ {p['entry_date']} — للمتابعة فقط، مش دخول جديد"
    return survivors


def archive_closed(book: dict) -> list[dict]:
    """Move closed positions out of the book; return them for trades_live."""
    closed = [p for p in book["positions"] if p["status"] == "closed"]
    book["positions"] = [p for p in book["positions"] if p["status"] != "closed"]
    book["updated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return closed
