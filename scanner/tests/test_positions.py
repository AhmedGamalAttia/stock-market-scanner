"""Lifecycle test for the paper position book: signal → pending → fill →
TP ladder → close, plus stop-hit and trend-flip paths, using a fake strategy.

Run:  python -m tests.test_positions
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from positions import archive_closed, build_actions, evaluate, open_new
from signals import SignalRow
from strategies.base import Strategy


class FakeStrategy(Strategy):
    name = "fake"
    label_ar = "اختبار"
    tp_fractions = (1 / 3, 1 / 3, 1 / 3)
    breakeven_after_tp1 = False

    def prepare(self, df):
        return df

    def signal_from_prepared(self, prep, **kw):
        return None


def _sig(symbol="TST", date="2026-01-01", entry=100.0, stop=90.0) -> SignalRow:
    return SignalRow(
        symbol=symbol, signal_date=date, strategy="fake", score=50, confidence=60, risk_class="متوسط",
        setups=["x"], trend="صاعد", rsi=None, macd_hist=None, ma20=None, ma50=None, volume_z=None,
        atr=2.0, atr_pct=0.02, adv_20=1e6, entry=entry, stop_loss=stop,
        target_1=105.0, target_2=110.0, target_3=115.0, rr_t1=0.5, rr_t2=1.0, blended_rr=1.0,
        expected_days=8, max_hold=None, suggested_shares_20k=40, suggested_value_20k=4000.0,
        max_loss_20k=400.0, rationale_ar="", strategy_ar="", warnings_ar=[], close=entry,
    )


def _bars(rows: list[tuple[str, float, float, float, float, bool]]) -> pd.DataFrame:
    df = pd.DataFrame(
        [{"open": o, "high": h, "low": l, "close": c, "long_exit": x} for (_, o, h, l, c, x) in rows],
        index=pd.to_datetime([r[0] for r in rows]),
    )
    return df


def test_full_ladder_closes_at_tp3():
    book = {"updated": None, "positions": []}
    added = open_new([_sig()], book, {"TST": "اختبار"})
    assert len(added) == 1 and added[0]["status"] == "pending"

    prep = _bars([
        ("2026-01-02", 101.0, 104.0, 100.0, 103.0, False),   # fill at 101, nothing hit
        ("2026-01-03", 103.0, 106.0, 102.0, 105.5, False),   # tp1 (105) hit
        ("2026-01-04", 106.0, 116.0, 105.0, 115.0, False),   # tp2 + tp3 hit → closed
    ])
    closed = evaluate(book, {"TST": prep}, FakeStrategy())
    assert len(closed) == 1
    p = closed[0]
    assert p["status"] == "closed" and p["reason"] == "tp_final"
    assert p["entry"] == 101.0 and p["entry_date"] == "2026-01-02"
    assert p["tp_hit"] == [True, True, True]
    assert p["shares_open"] == 0
    assert p["realized_pnl"] > 0 and p["realized_r"] > 0
    assert len(p["exits"]) == 3


def test_stop_hit_after_partial_tp():
    book = {"updated": None, "positions": []}
    open_new([_sig()], book, {})
    prep = _bars([
        ("2026-01-02", 101.0, 103.0, 100.0, 102.0, False),
        ("2026-01-03", 102.0, 105.5, 101.0, 105.0, False),   # tp1
        ("2026-01-04", 100.0, 101.0, 89.0, 89.5, False),     # gap → stop at 90 hit, fill at min(open, stop)=90
    ])
    closed = evaluate(book, {"TST": prep}, FakeStrategy())
    p = closed[0]
    assert p["reason"] == "stop_hit"
    assert p["tp_hit"] == [True, False, False]
    assert p["exits"][-1]["price"] == 90.0
    assert p["realized_r"] < 0


def test_trend_flip_exits_next_open_and_is_idempotent():
    book = {"updated": None, "positions": []}
    open_new([_sig()], book, {})
    day1 = _bars([
        ("2026-01-02", 101.0, 102.0, 100.0, 101.5, False),
        ("2026-01-03", 101.0, 102.0, 100.5, 101.0, True),    # flip on close → exit tomorrow
    ])
    closed = evaluate(book, {"TST": day1}, FakeStrategy())
    assert closed == []
    p = book["positions"][0]
    assert p["status"] == "open" and p["pending_exit"] == "trend_flip"
    # re-running on the same data must not change anything
    closed = evaluate(book, {"TST": day1}, FakeStrategy())
    assert closed == [] and p["bars_held"] == 2

    day2 = pd.concat([day1, _bars([("2026-01-04", 100.0, 100.5, 99.0, 99.5, False)])])
    closed = evaluate(book, {"TST": day2}, FakeStrategy())
    assert len(closed) == 1 and closed[0]["reason"] == "trend_flip"
    assert closed[0]["exit_price"] == 100.0

    archived = archive_closed(book)
    assert len(archived) == 1 and book["positions"] == []
    holds, exits = build_actions(book, "2026-01-04", archived)
    assert holds == [] and len(exits) == 1 and exits[0]["reason_ar"]


def test_duplicate_symbol_not_reopened_and_invalid_fill():
    book = {"updated": None, "positions": []}
    open_new([_sig()], book, {})
    assert open_new([_sig(date="2026-01-02")], book, {}) == []      # already held
    prep = _bars([("2026-01-02", 85.0, 86.0, 84.0, 85.0, False)])    # opens below the stop
    closed = evaluate(book, {"TST": prep}, FakeStrategy())
    assert closed and closed[0]["reason"] == "invalid"


if __name__ == "__main__":
    import inspect
    import sys

    failed = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and inspect.isfunction(fn):
            try:
                fn()
                print(f"ok    {name}")
            except AssertionError as e:
                failed += 1
                print(f"FAIL  {name}: {e}")
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"ERROR {name}: {type(e).__name__}: {e}")
    sys.exit(1 if failed else 0)
