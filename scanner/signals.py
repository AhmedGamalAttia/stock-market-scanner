"""Signal detection + scoring.

Each setup contributes points to a 0-100 score. We don't predict the future —
we identify configurations that historically precede meaningful moves.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class SignalRow:
    symbol: str
    signal_date: str
    score: int
    setups: list[str]
    trend: str
    rsi: float
    macd_hist: float
    ma20: float
    ma50: float
    volume_z: float
    atr: float
    entry: float
    stop_loss: float
    target_1: float
    target_2: float
    expected_days: int
    rationale_ar: str
    close: float


def _trend(row: pd.Series) -> str:
    if pd.isna(row.get("ma50")):
        return "غير محدد"
    if row["close"] > row["ma50"] and (pd.isna(row.get("ma200")) or row["close"] > row["ma200"]):
        return "صاعد"
    if row["close"] < row["ma50"]:
        return "هابط"
    return "محايد"


def _detect(df: pd.DataFrame) -> tuple[list[str], int, list[str]]:
    """Returns (setups, score, rationale_parts) for the latest row."""
    if len(df) < 60:
        return [], 0, []

    last = df.iloc[-1]
    prev = df.iloc[-2]

    setups: list[str] = []
    rationale: list[str] = []
    score = 0

    # 1) 20-day breakout with volume
    prior_high20 = df["high20"].iloc[-2]
    if (
        not pd.isna(prior_high20)
        and last["close"] > prior_high20
        and not pd.isna(last["vol_z20"])
        and last["vol_z20"] > 1.0
    ):
        setups.append("breakout_20d")
        score += 30
        rationale.append("اختراق أعلى 20 جلسة بحجم تداول قوى")

    # 2) MACD bullish cross
    if (
        not pd.isna(prev["macd_hist"])
        and not pd.isna(last["macd_hist"])
        and prev["macd_hist"] <= 0
        and last["macd_hist"] > 0
    ):
        setups.append("macd_cross_up")
        score += 20
        rationale.append("تقاطع MACD صاعد")

    # 3) Golden cross MA20 > MA50 (recent)
    cross_window = df.iloc[-5:]
    if (
        not cross_window["ma20"].isna().any()
        and not cross_window["ma50"].isna().any()
        and (cross_window["ma20"].iloc[0] <= cross_window["ma50"].iloc[0])
        and (cross_window["ma20"].iloc[-1] > cross_window["ma50"].iloc[-1])
    ):
        setups.append("golden_cross_20_50")
        score += 15
        rationale.append("تقاطع ذهبى للمتوسطات (20 فوق 50)")

    # 4) Pullback bounce in uptrend (RSI bounces from oversold while above MA50)
    if (
        not pd.isna(last["ma50"])
        and last["close"] > last["ma50"]
        and not pd.isna(prev["rsi14"])
        and not pd.isna(last["rsi14"])
        and prev["rsi14"] < 40
        and last["rsi14"] > 45
    ):
        setups.append("pullback_bounce")
        score += 15
        rationale.append("ارتداد من تشبع البيع داخل اتجاه صاعد")

    # 5) Trend strength bonus
    if (
        not pd.isna(last["ma20"])
        and not pd.isna(last["ma50"])
        and last["close"] > last["ma20"] > last["ma50"]
    ):
        score += 10
        if "اتجاه فنى متماسك" not in rationale:
            rationale.append("اتجاه فنى متماسك")

    # 6) Volume confirmation bonus
    if not pd.isna(last["vol_z20"]) and last["vol_z20"] > 1.5:
        score += 10
        rationale.append("حجم تداول استثنائى (+1.5σ)")

    return setups, min(score, 100), rationale


def _expected_days(atr_pct: float) -> int:
    """Rough heuristic: more volatile -> shorter expected hold to T1."""
    if atr_pct >= 0.04:
        return 5
    if atr_pct >= 0.025:
        return 8
    if atr_pct >= 0.015:
        return 12
    return 18


def build_signal(symbol: str, df: pd.DataFrame) -> SignalRow | None:
    if df is None or df.empty or len(df) < 60:
        return None

    setups, score, rationale = _detect(df)
    if score < 30 or not setups:
        return None

    last = df.iloc[-1]
    if pd.isna(last["atr14"]) or last["atr14"] <= 0:
        return None

    entry = float(last["close"])
    atr_v = float(last["atr14"])
    stop = round(entry - 1.5 * atr_v, 2)
    t1 = round(entry + 2.0 * atr_v, 2)
    t2 = round(entry + 3.5 * atr_v, 2)
    atr_pct = atr_v / entry if entry else 0
    days = _expected_days(atr_pct)
    trend = _trend(last)

    return SignalRow(
        symbol=symbol,
        signal_date=str(last.name.date() if hasattr(last.name, "date") else last.name),
        score=int(score),
        setups=setups,
        trend=trend,
        rsi=float(last["rsi14"]) if not pd.isna(last["rsi14"]) else None,
        macd_hist=float(last["macd_hist"]) if not pd.isna(last["macd_hist"]) else None,
        ma20=float(last["ma20"]) if not pd.isna(last["ma20"]) else None,
        ma50=float(last["ma50"]) if not pd.isna(last["ma50"]) else None,
        volume_z=float(last["vol_z20"]) if not pd.isna(last["vol_z20"]) else None,
        atr=round(atr_v, 4),
        entry=round(entry, 2),
        stop_loss=stop,
        target_1=t1,
        target_2=t2,
        expected_days=days,
        rationale_ar=" • ".join(rationale) if rationale else "إشارة فنية",
        close=round(entry, 2),
    )
