"""The original scoring strategy, expressed as vectorised rules so it can be
backtested bar-by-bar with exactly the same logic the live scanner uses.

Scoring (per bar):
  breakout_20d        +30   close > prior 20-day high  AND volume z > 1.0
  macd_cross_up       +20   MACD histogram crosses from ≤0 to >0
  golden_cross_20_50  +15   MA20 ≤ MA50 four bars ago AND MA20 > MA50 now
  pullback_bounce     +15   close > MA50 AND RSI(14) went from <40 to >45
  stacked uptrend     +10   close > MA20 > MA50            (bonus, no label)
  volume bonus        +10   volume z > 1.5                 (bonus, no label)
Entry when score ≥ min_score AND at least one labelled setup AND ADV ≥ gate.
Stop = close − 1.5·ATR14 ; TP1 = +2·ATR ; TP2 = +4·ATR ; break-even after TP1 ;
time stop = 2 × expected_days(atr%).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from indicators import enrich
from signals import (
    MIN_ADV_EGP,
    STOP_ATR_MULT,
    TARGET_1_ATR_MULT,
    TARGET_2_ATR_MULT,
    SignalRow,
    build_signal,
)
from strategies.base import Strategy


def score_frame(e: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Vectorised twin of signals._detect_setups → (score, has_labelled_setup)."""
    breakout = (e["close"] > e["high20"].shift(1)) & (e["vol_z20"] > 1.0)
    macd_x = (e["macd_hist"].shift(1) <= 0) & (e["macd_hist"] > 0)
    golden = (e["ma20"].shift(4) <= e["ma50"].shift(4)) & (e["ma20"] > e["ma50"])
    pullback = (e["close"] > e["ma50"]) & (e["rsi14"].shift(1) < 40) & (e["rsi14"] > 45)
    stacked = (e["close"] > e["ma20"]) & (e["ma20"] > e["ma50"])
    vol_bonus = e["vol_z20"] > 1.5

    score = (
        30 * breakout.astype(int)
        + 20 * macd_x.astype(int)
        + 15 * golden.astype(int)
        + 15 * pullback.astype(int)
        + 10 * stacked.astype(int)
        + 10 * vol_bonus.astype(int)
    ).clip(upper=100)
    has_setup = breakout | macd_x | golden | pullback
    return score, has_setup


def _expected_days_vec(atr_pct: pd.Series) -> pd.Series:
    return pd.Series(
        np.select(
            [atr_pct >= 0.04, atr_pct >= 0.025, atr_pct >= 0.015],
            [5, 8, 12],
            default=18,
        ),
        index=atr_pct.index,
    )


class CurrentScoring(Strategy):
    name = "current_scoring"
    label_ar = "نظام النقاط (اختراق + MACD + تقاطع ذهبى)"
    tp_fractions = (0.5, 0.5)
    breakeven_after_tp1 = True
    max_hold = None  # per-bar column below

    def __init__(self, min_score: int = 30):
        self.min_score = min_score

    def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        out = enrich(df)
        score, has_setup = score_frame(out)
        out["score"] = score
        atr_ok = out["atr14"] > 0
        liquid = out["adv20"] >= MIN_ADV_EGP
        out["long_entry"] = has_setup & (score >= self.min_score) & atr_ok & liquid
        out["long_exit"] = False
        out["stop"] = np.where(out["long_entry"], out["close"] - STOP_ATR_MULT * out["atr14"], np.nan)
        out["tp1"] = np.where(out["long_entry"], out["close"] + TARGET_1_ATR_MULT * out["atr14"], np.nan)
        out["tp2"] = np.where(out["long_entry"], out["close"] + TARGET_2_ATR_MULT * out["atr14"], np.nan)
        out["tp3"] = np.nan
        out["trend"] = np.where(out["close"] > out["ma50"], 1, -1)
        atr_pct = (out["atr14"] / out["close"]).fillna(0)
        out["max_hold"] = 2 * _expected_days_vec(atr_pct)
        out["reason_ar"] = np.where(out["long_entry"], "إشارة نقاط فنية", "")
        self.validate(out)
        return out

    def signal_from_prepared(self, prep: pd.DataFrame, **kwargs) -> SignalRow | None:
        # prepare() already ran enrich(); build_signal only needs those columns.
        return build_signal(kwargs.get("symbol", ""), prep, min_score=kwargs.get("min_score", self.min_score))
