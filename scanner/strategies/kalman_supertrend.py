"""Port of "Hytham Sherif Pro Scalper v2.2" (Pine Script) to pandas.

Pipeline (mirrors recommended-scripts.txt lines 69–114):
  kalmanHL2   = kalman((high+low)/2, gain=0.7, momentum=0.3)
  atr10       = rma(true_range, 10)                  (Pine ta.rma == Wilder EMA)
  atrFiltered = kalman(atr10, gain=0.35, momentum=0.3)
  upper/lower = kalmanHL2 ± 3.0 * atrFiltered
  finalUpper  = upper if close[1] > finalUpper[1] else min(upper, finalUpper[1])
  finalLower  = lower if close[1] < finalLower[1] else max(lower, finalLower[1])
  trend       = +1 if close > finalUpper[1], -1 if close < finalLower[1], else carry
  BUY         = trend flips -1 → +1 ;  SELL = +1 → -1
  stop        = finalLower on the entry bar ; TP1/2/3 = entry + risk × {0.5, 1.0, 1.5}

The OB/OS zones (VWMA ± range × 1.5) are computed for display only.

Applied to closed daily bars with next-open fills — no intrabar repainting.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from indicators import atr, enrich, sma
from signals import (
    MIN_ADV_EGP,
    SignalRow,
    assemble_signal,
)
from strategies.base import Strategy

# Pine defaults
KALMAN_GAIN = 0.7
KALMAN_MOMENTUM = 0.3
ATR_PERIOD = 10
ATR_MULT = 3.0
VWMA_LEN = 20
BAND_LOOKBACK = 20
OB_MULT = 1.5
OS_MULT = 1.5
TP_RR = (0.5, 1.0, 1.5)


def kalman_filter(src: np.ndarray, gain: float, momentum: float) -> np.ndarray:
    """Pine f_kalmanFilter: constant-velocity predictor with proportional gain."""
    out = np.full(len(src), np.nan)
    est = np.nan
    vel = 0.0
    for i, x in enumerate(src):
        if np.isnan(x):
            out[i] = est
            continue
        if np.isnan(est):
            est, vel = x, 0.0
        else:
            pred = est + vel
            err = x - pred
            est = pred + gain * err
            vel = vel * momentum + gain * err
        out[i] = est
    return out


def supertrend_bands(
    close: np.ndarray, upper: np.ndarray, lower: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Recursive final bands + trend exactly as the Pine script does it."""
    n = len(close)
    f_up = np.full(n, np.nan)
    f_lo = np.full(n, np.nan)
    trend = np.ones(n, dtype=int)  # Pine: var int trend = 1
    for i in range(n):
        if np.isnan(upper[i]) or np.isnan(lower[i]):
            trend[i] = trend[i - 1] if i else 1
            continue
        if i == 0 or np.isnan(f_up[i - 1]):
            f_up[i] = upper[i]
        else:
            f_up[i] = upper[i] if close[i - 1] > f_up[i - 1] else min(upper[i], f_up[i - 1])
        if i == 0 or np.isnan(f_lo[i - 1]):
            f_lo[i] = lower[i]
        else:
            f_lo[i] = lower[i] if close[i - 1] < f_lo[i - 1] else max(lower[i], f_lo[i - 1])

        prev_t = trend[i - 1] if i else 1
        if i and not np.isnan(f_up[i - 1]) and close[i] > f_up[i - 1]:
            trend[i] = 1
        elif i and not np.isnan(f_lo[i - 1]) and close[i] < f_lo[i - 1]:
            trend[i] = -1
        else:
            trend[i] = prev_t
    return f_up, f_lo, trend


def vwma(close: pd.Series, volume: pd.Series, length: int) -> pd.Series:
    pv = (close * volume).rolling(length, min_periods=length).sum()
    v = volume.rolling(length, min_periods=length).sum()
    return pv / v.replace(0, np.nan)


class KalmanSupertrend(Strategy):
    """The Pine script as published. Two principled variants are exposed via
    the constructor (see ``KalmanMA200`` / ``KalmanRide``) so the backtest can
    compare them side by side without any parameter fitting."""

    name = "kalman_supertrend"
    label_ar = "كالمان سوبرترند (هيثم شريف)"
    tp_fractions = (1 / 3, 1 / 3, 1 / 3)
    breakeven_after_tp1 = False
    max_hold = None  # Pine has no time stop; the trend flip is the exit

    def __init__(self, *, trend_filter: bool = False, use_tps: bool = True):
        self.trend_filter = trend_filter  # only buy flips above the 200-day MA
        self.use_tps = use_tps            # False → no ladder, ride until flip/stop
        if not use_tps:
            self.tp_fractions = ()

    def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        out = enrich(df)  # ma20/50/200, rsi, macd, atr14, vol_z, adv20 — for the expert layer
        high = out["high"].to_numpy(float)
        low = out["low"].to_numpy(float)
        close = out["close"].to_numpy(float)

        k_hl2 = kalman_filter((high + low) / 2.0, KALMAN_GAIN, KALMAN_MOMENTUM)
        atr10 = atr(out["high"], out["low"], out["close"], ATR_PERIOD).to_numpy(float)
        atr_f = kalman_filter(atr10, KALMAN_GAIN * 0.5, KALMAN_MOMENTUM)
        upper = k_hl2 + ATR_MULT * atr_f
        lower = k_hl2 - ATR_MULT * atr_f
        f_up, f_lo, trend = supertrend_bands(close, upper, lower)

        out["kalman_hl2"] = k_hl2
        out["atr_filtered"] = atr_f
        out["st_upper"] = f_up
        out["st_lower"] = f_lo
        out["trend"] = trend
        out["supertrend"] = np.where(trend == 1, f_lo, f_up)

        prev_trend = np.roll(trend, 1)
        prev_trend[0] = 1
        flip_up = (trend == 1) & (prev_trend == -1)
        flip_dn = (trend == -1) & (prev_trend == 1)
        # Ignore flips inside the warm-up where bands are still NaN
        valid = ~np.isnan(f_lo) & ~np.isnan(f_up)
        entry = flip_up & valid
        if self.trend_filter:
            ma200 = out["ma200"].to_numpy(float)
            entry = entry & ~np.isnan(ma200) & (close > ma200)
        out["long_entry"] = entry
        out["long_exit"] = flip_dn & valid

        stop = np.where(out["long_entry"], f_lo, np.nan)
        risk = close - stop
        out["stop"] = stop
        for k, rr in enumerate(TP_RR, start=1):
            if self.use_tps:
                out[f"tp{k}"] = np.where(out["long_entry"], close + risk * rr, np.nan)
            else:
                out[f"tp{k}"] = np.nan

        # OB / OS zones (display)
        vw = vwma(out["close"], out["volume"].astype(float), VWMA_LEN)
        hh = out["high"].rolling(BAND_LOOKBACK, min_periods=BAND_LOOKBACK).max()
        ll = out["low"].rolling(BAND_LOOKBACK, min_periods=BAND_LOOKBACK).min()
        out["vwma20"] = vw
        out["ob_zone"] = vw + (hh - vw) * OB_MULT
        out["os_zone"] = vw - (vw - ll) * OS_MULT

        out["reason_ar"] = np.where(
            out["long_entry"],
            "انقلاب اتجاه السوبرترند لصاعد (فلتر كالمان)",
            np.where(out["long_exit"], "انقلاب اتجاه السوبرترند لهابط", ""),
        )
        self.validate(out)
        return out

    # ---- live ----

    def signal_from_prepared(self, prep: pd.DataFrame, **kwargs) -> SignalRow | None:
        if prep is None or len(prep) < 60:
            return None
        last = prep.iloc[-1]
        if not bool(last["long_entry"]):
            return None
        if pd.isna(last["stop"]) or last["stop"] >= last["close"]:
            return None
        adv = float(last["adv20"]) if not pd.isna(last["adv20"]) else 0.0
        if adv < MIN_ADV_EGP:
            return None

        setups, score, rationale = _kalman_context(last)
        if self.trend_filter:
            setups.append("above_ma200")
        entry = float(last["close"])
        risk = entry - float(last["stop"])
        if self.use_tps:
            targets = [float(last["tp1"]), float(last["tp2"]), float(last["tp3"])]
            lead = (
                "انقلب اتجاه السوبرترند (بفلتر كالمان) من هابط لصاعد — "
                "الدخول عند الإغلاق والوقف على خط السوبرترند نفسه، وجنى الأرباح على ثلاث مراحل."
            )
        else:
            # No ladder: show reference levels (1R / 2R / 3R) but the real exit is the flip.
            targets = [entry + risk * 1.0, entry + risk * 2.0, entry + risk * 3.0]
            lead = (
                "انقلب اتجاه السوبرترند (بفلتر كالمان) من هابط لصاعد — "
                "الدخول عند الإغلاق، الوقف على خط السوبرترند، ومفيش أهداف ثابتة: "
                "نركب الاتجاه ونخرج لما السوبرترند ينقلب لهابط."
            )
        return assemble_signal(
            symbol=kwargs.get("symbol", ""),
            last=last,
            strategy=self.name,
            setups=setups,
            score=score,
            rationale=rationale,
            lead_ar=lead,
            entry=entry,
            stop=float(last["stop"]),
            targets=targets,
            max_hold=None,
        )


class KalmanMA200(KalmanSupertrend):
    """Same flips, but only above the 200-day average (classic trend filter)."""

    name = "kalman_ma200"
    label_ar = "كالمان سوبرترند + فلتر متوسط 200"

    def __init__(self):
        super().__init__(trend_filter=True, use_tps=True)


class KalmanRide(KalmanSupertrend):
    """Same flips, no take-profit ladder — hold until the trend flips back."""

    name = "kalman_ride"
    label_ar = "كالمان سوبرترند — ركوب الاتجاه بدون أهداف"

    def __init__(self):
        super().__init__(trend_filter=False, use_tps=False)


def _kalman_context(last: pd.Series) -> tuple[list[str], int, list[str]]:
    """Descriptive chips + a 0-100 'score' for ranking (the rule itself is the flip)."""
    setups = ["kalman_flip"]
    score = 50
    rationale = ["انقلاب سوبرترند صاعد"]
    if not pd.isna(last.get("ma50")) and last["close"] > last["ma50"]:
        setups.append("above_ma50")
        score += 15
        rationale.append("فوق متوسط 50 جلسة")
    if not pd.isna(last.get("ma200")) and last["close"] > last["ma200"]:
        score += 10
        rationale.append("فوق متوسط 200 جلسة")
    if not pd.isna(last.get("vol_z20")) and last["vol_z20"] > 1.0:
        setups.append("volume_confirm")
        score += 15
        rationale.append("حجم تداول فوق المتوسط")
    if not pd.isna(last.get("macd_hist")) and last["macd_hist"] > 0:
        setups.append("macd_positive")
        score += 10
        rationale.append("زخم MACD إيجابى")
    return setups, min(score, 100), rationale


__all__ = ["KalmanSupertrend", "KalmanMA200", "KalmanRide", "kalman_filter", "supertrend_bands", "vwma", "sma"]
