"""Sanity tests for the Kalman-Supertrend port and the backtest engine.

Run:  python -m tests.test_kalman        (from the scanner/ folder)
Also collectable by pytest.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from backtest.engine import BacktestConfig, run_symbol
from strategies.kalman_supertrend import KalmanSupertrend, kalman_filter, supertrend_bands


def _frame(closes: np.ndarray, start="2024-01-01") -> pd.DataFrame:
    idx = pd.bdate_range(start, periods=len(closes))
    o = np.roll(closes, 1)
    o[0] = closes[0]
    h = np.maximum(o, closes) * 1.01
    l = np.minimum(o, closes) * 0.99
    return pd.DataFrame(
        {"open": o, "high": h, "low": l, "close": closes, "adjclose": closes, "volume": 100_000},
        index=idx,
    )


def test_kalman_tracks_constant():
    x = np.full(50, 10.0)
    out = kalman_filter(x, 0.7, 0.3)
    assert np.allclose(out, 10.0)


def test_kalman_follows_ramp():
    x = np.linspace(10, 60, 200)
    out = kalman_filter(x, 0.7, 0.3)
    # after warm-up the filter should lag the ramp by less than one step
    assert abs(out[-1] - x[-1]) < (x[1] - x[0])


def test_ramp_has_no_flips():
    closes = np.linspace(10, 30, 300)
    df = _frame(closes)
    prep = KalmanSupertrend().prepare(df)
    valid = prep.dropna(subset=["st_lower"])
    assert (valid["trend"] == 1).all()
    assert not valid["long_entry"].any()
    assert not valid["long_exit"].any()


def test_v_shape_flips_down_then_up():
    down = np.linspace(30, 10, 150)
    up = np.linspace(10, 40, 150)
    closes = np.concatenate([down, up[1:]])
    df = _frame(closes)
    prep = KalmanSupertrend().prepare(df)
    flips_dn = prep.index[prep["long_exit"]]
    flips_up = prep.index[prep["long_entry"]]
    assert len(flips_dn) >= 1, "expected a bearish flip in the decline"
    assert len(flips_up) >= 1, "expected a bullish flip in the recovery"
    assert flips_up[-1] > flips_dn[0]
    # stop is the lower band on the entry bar and sits below the close
    row = prep.loc[flips_up[-1]]
    assert row["stop"] < row["close"]
    assert row["tp1"] < row["tp2"] < row["tp3"]


def test_bands_are_monotone_inside_a_trend():
    closes = np.linspace(10, 30, 300)
    prep = KalmanSupertrend().prepare(_frame(closes))
    lower = prep["st_lower"].dropna().to_numpy()
    assert (np.diff(lower) >= -1e-9).all(), "lower band must only ratchet up in an uptrend"


def test_supertrend_bands_default_trend_is_one():
    close = np.array([10.0, 10.0, 10.0])
    up = np.array([11.0, 11.0, 11.0])
    lo = np.array([9.0, 9.0, 9.0])
    _, _, trend = supertrend_bands(close, up, lo)
    assert list(trend) == [1, 1, 1]


def test_engine_fills_next_open_and_charges_costs():
    down = np.linspace(30, 10, 150)
    up = np.linspace(10, 40, 200)
    closes = np.concatenate([down, up[1:]])
    df = _frame(closes)
    trades = run_symbol("TEST", df, KalmanSupertrend(), BacktestConfig())
    assert trades, "the V-shape must produce at least one trade"
    t = trades[-1]
    prep = KalmanSupertrend().prepare(df)
    sig_dates = prep.index[prep["long_entry"]]
    # entry date is the bar AFTER a signal bar
    sig_pos = {d.date().isoformat() for d in sig_dates}
    entry_idx = list(prep.index).index(pd.Timestamp(t.entry_date))
    assert prep.index[entry_idx - 1].date().isoformat() in sig_pos
    # the linear ramp keeps rising, so all three TPs must have been hit
    assert all(t.tp_hits), t.tp_hits
    assert t.reason == "tp_final"
    assert t.pnl_net > 0
    assert 0 < t.r_multiple < 1.5  # ladder average (0.5+1+1.5)/3 minus costs


def test_repair_splits_removes_cliff():
    from series import repair_splits

    closes = np.concatenate([np.full(50, 60.0), np.full(50, 15.0)])  # 4:1 bonus, unadjusted
    df = _frame(closes)
    df.loc[df.index[50], "open"] = 15.0
    fixed, log = repair_splits(df)
    assert len(log) == 1 and abs(log[0]["factor"] - 0.25) < 1e-6
    assert abs(fixed["close"].iloc[0] - 15.0) < 1e-9, "history must be scaled down"
    assert fixed["close"].iloc[-1] == 15.0, "latest bars must keep real prices"
    assert fixed["volume"].iloc[0] == 400_000, "volume scaled the other way"
    # no cliff left: all day-over-day moves are tiny
    assert (fixed["close"].pct_change().abs().fillna(0) < 0.05).all()


def test_repair_splits_ignores_normal_moves():
    from series import repair_splits

    closes = np.linspace(10, 12, 100)  # gentle drift, no event
    _, log = repair_splits(_frame(closes))
    assert log == []


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
