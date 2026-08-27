"""Signal detection + expert recommendation layer.

We don't predict the future. We identify configurations that historically
precede meaningful moves, gate them by liquidity & risk/reward, classify
risk, and translate into a complete trade plan in plain Arabic.

``assemble_signal`` is the shared "expert layer": any strategy that can name
an entry, a stop and a target ladder gets the same risk class, confidence,
position sizing and Arabic narrative.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

# Risk management constants (well-documented retail trading defaults)
STOP_ATR_MULT = 1.5
TARGET_1_ATR_MULT = 2.0   # 50% exit, R:R = 1.33
TARGET_2_ATR_MULT = 4.0   # final exit,  R:R = 2.67  →  blended R:R = 2.0

# Default capital assumption for sizing (EGP). User can override in calculator.
DEFAULT_CAPITAL = 20_000
DEFAULT_RISK_PCT = 0.02   # 2% max loss per trade
MAX_POSITION_PCT = 0.40   # never put more than 40% of capital in one stock

# Liquidity gate — minimum average daily traded value in EGP
MIN_ADV_EGP = 50_000


@dataclass
class SignalRow:
    symbol: str
    signal_date: str
    strategy: str
    score: int
    confidence: int
    risk_class: str
    setups: list[str]
    trend: str
    rsi: float | None
    macd_hist: float | None
    ma20: float | None
    ma50: float | None
    volume_z: float | None
    atr: float
    atr_pct: float
    adv_20: float
    entry: float
    stop_loss: float
    target_1: float
    target_2: float
    target_3: float | None
    rr_t1: float
    rr_t2: float
    blended_rr: float
    expected_days: int
    max_hold: int | None
    suggested_shares_20k: int
    suggested_value_20k: float
    max_loss_20k: float
    rationale_ar: str
    strategy_ar: str
    warnings_ar: list[str]
    close: float


def _trend(row: pd.Series) -> str:
    if pd.isna(row.get("ma50")):
        return "غير محدد"
    if row["close"] > row["ma50"] and (pd.isna(row.get("ma200")) or row["close"] > row["ma200"]):
        return "صاعد"
    if row["close"] < row["ma50"]:
        return "هابط"
    return "محايد"


def _detect_setups(df: pd.DataFrame) -> tuple[list[str], int, list[str]]:
    """Returns (setups, technical_score, rationale_parts) for the latest row."""
    if len(df) < 60:
        return [], 0, []

    last = df.iloc[-1]
    prev = df.iloc[-2]

    setups: list[str] = []
    rationale: list[str] = []
    score = 0

    # 1) 20-day breakout with volume confirmation
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

    # 2) MACD bullish histogram cross
    if (
        not pd.isna(prev["macd_hist"])
        and not pd.isna(last["macd_hist"])
        and prev["macd_hist"] <= 0
        and last["macd_hist"] > 0
    ):
        setups.append("macd_cross_up")
        score += 20
        rationale.append("تقاطع MACD صاعد")

    # 3) Golden cross MA20 > MA50 (within last 5 sessions)
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

    # 4) Pullback bounce: RSI bounces from oversold while above MA50
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

    # 5) Stacked uptrend bonus
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
    if atr_pct >= 0.04:
        return 5
    if atr_pct >= 0.025:
        return 8
    if atr_pct >= 0.015:
        return 12
    return 18


def _risk_class(atr_pct: float, adv: float, score: int, trend: str) -> str:
    """🟢 محافظ / 🟡 متوسط / 🔴 جرىء"""
    # Aggressive triggers (any one is enough)
    if atr_pct > 0.05 or adv < 200_000:
        return "جرىء"
    # Conservative requires all of: low vol, high liquidity, strong score, uptrend
    if atr_pct < 0.025 and adv > 500_000 and score >= 50 and trend == "صاعد":
        return "محافظ"
    return "متوسط"


def _confidence(score: int, n_setups: int, trend: str, adv: float) -> int:
    """Confidence 0-100 — combines technical strength, confirmation, context."""
    base = score * 0.55
    setup_bonus = min(n_setups * 8, 24)
    trend_bonus = 12 if trend == "صاعد" else (-8 if trend == "هابط" else 0)
    if adv > 1_000_000:
        liq_bonus = 12
    elif adv > 500_000:
        liq_bonus = 8
    elif adv > 200_000:
        liq_bonus = 4
    else:
        liq_bonus = 0
    raw = base + setup_bonus + trend_bonus + liq_bonus
    return int(max(0, min(100, round(raw))))


def _position_size(entry: float, stop: float, capital: float, risk_pct: float) -> tuple[int, float, float]:
    """Returns (shares, position_value, max_loss)."""
    risk_per_share = entry - stop
    if risk_per_share <= 0:
        return 0, 0.0, 0.0
    max_loss_egp = capital * risk_pct
    shares_by_risk = int(max_loss_egp // risk_per_share)
    shares_by_capital = int((capital * MAX_POSITION_PCT) // entry)
    shares = max(0, min(shares_by_risk, shares_by_capital))
    position_value = round(shares * entry, 2)
    actual_loss = round(shares * risk_per_share, 2)
    return shares, position_value, actual_loss


def _lead_for_setups(setups: list[str], vol_z: float | None) -> str:
    if "breakout_20d" in setups:
        vol_text = f"بحجم تداول يفوق المتوسط بـ {vol_z:.1f} انحراف معيارى" if vol_z else "بحجم قوى"
        return f"السهم اخترق أعلى 20 جلسة {vol_text}، وهو نمط فنى يسبق غالباً موجة صعود قصيرة."
    if "macd_cross_up" in setups:
        return "MACD تحوّل لإشارة شراء بعد فترة من الضعف، ما يدل على تحسن الزخم الإيجابى."
    if "golden_cross_20_50" in setups:
        return "المتوسط المتحرك القصير (20) قطع المتوسط المتوسط (50) صعوداً — إشارة كلاسيكية لبداية اتجاه صاعد."
    if "pullback_bounce" in setups:
        return "السهم ارتد من منطقة تشبع البيع داخل اتجاه صاعد قائم — فرصة دخول بسعر أفضل من القمم."
    return "إشارة فنية."


def _strategy_narrative(
    lead_ar: str,
    trend: str,
    adv: float,
    atr_pct: float,
    rr_t1: float,
    rr_t2: float,
    risk_class: str,
    expected_days: int,
    confidence: int,
) -> str:
    """Plain-Arabic explanation a coach would give."""
    parts: list[str] = [lead_ar]

    # Trend context
    if trend == "صاعد":
        parts.append("الاتجاه العام للسهم صاعد فوق متوسط الـ 50 جلسة، ما يدعم الإشارة.")
    elif trend == "هابط":
        parts.append("⚠️ تحذير: الاتجاه العام لايزال هابطاً، ما يجعل هذه الإشارة محل شك أعلى.")

    # Liquidity color
    if adv > 1_000_000:
        parts.append("سيولة السهم ممتازة، يسهل الدخول والخروج بأى حجم تقريباً.")
    elif adv > 500_000:
        parts.append("سيولة السهم جيدة لرأس مال صغير-متوسط.")
    elif adv > 200_000:
        parts.append("سيولة السهم مقبولة لكنها محدودة — تجنب الأحجام الكبيرة.")
    else:
        parts.append("⚠️ سيولة السهم ضعيفة — قد يصعب الخروج بسعر مناسب.")

    # Volatility note
    if atr_pct > 0.04:
        parts.append(f"السهم متذبذب (±{atr_pct*100:.1f}% يومى)، الحركة قد تكون سريعة فى الاتجاهين.")
    elif atr_pct < 0.015:
        parts.append("السهم منخفض التذبذب، الحركة عادةً تدريجية.")

    # Risk/Reward summary
    parts.append(
        f"خطة الخروج تعطى نسبة عائد/مخاطرة {rr_t1:.2f}:1 على الهدف الأول و{rr_t2:.2f}:1 على الثانى — "
        f"إجمالى متوسط مرجّح ≈ {(rr_t1 + rr_t2) / 2:.1f}:1."
    )

    # Time horizon
    parts.append(f"المدة المتوقعة: {expected_days} جلسة. تجاوزها بدون تحرك يعنى أن الإشارة فقدت زخمها.")

    # Closing recommendation strength
    if risk_class == "محافظ":
        parts.append(f"التصنيف: 🟢 محافظ — هذه إحدى أنظف الإشارات اليوم بمستوى ثقة {confidence}%.")
    elif risk_class == "متوسط":
        parts.append(f"التصنيف: 🟡 متوسط — إشارة جيدة بمستوى ثقة {confidence}%، التزم بإدارة المخاطرة.")
    else:
        parts.append(f"التصنيف: 🔴 جرىء — مخاطرة عالية، خصص لها رأس مال أصغر. ثقة {confidence}%.")

    return " ".join(parts)


def _warnings(adv: float, atr_pct: float, trend: str, rr_t1: float) -> list[str]:
    w: list[str] = []
    if adv < 200_000:
        w.append("سيولة منخفضة جداً — قد يصعب تنفيذ كميات كبيرة بسعر مناسب.")
    if atr_pct > 0.06:
        w.append("تذبذب مرتفع جداً — احتمال ضرب وقف الخسارة بالـ noise اليومى وارد.")
    if trend == "هابط":
        w.append("الاتجاه العام للسهم هابط — تداول ضد التيار الكبير.")
    if rr_t1 < 1.0:
        w.append("الهدف الأول قريب (أقل من 1R) — بعد عمولة ثاندر (~0.8%) ربحه محدود، الهدفان التاليان هما اللى بيصنعوا الفرق.")
    return w


def _f(x) -> float | None:
    return float(x) if x is not None and not pd.isna(x) else None


def assemble_signal(
    *,
    symbol: str,
    last: pd.Series,
    strategy: str,
    setups: list[str],
    score: int,
    rationale: list[str],
    lead_ar: str,
    entry: float,
    stop: float,
    targets: list[float | None],
    max_hold: int | None,
) -> SignalRow | None:
    """Shared expert layer: risk class, confidence, sizing, narrative."""
    if pd.isna(last.get("atr14")) or last["atr14"] <= 0 or stop >= entry:
        return None
    adv = float(last["adv20"]) if not pd.isna(last.get("adv20")) else 0.0
    atr_v = float(last["atr14"])
    atr_pct = atr_v / entry if entry else 0.0

    targets = [t for t in targets if t is not None and not pd.isna(t)]
    while len(targets) < 2:  # UI always shows two targets
        targets.append(targets[-1] if targets else entry)
    t1, t2 = round(targets[0], 2), round(targets[1], 2)
    t3 = round(targets[2], 2) if len(targets) > 2 else None
    stop = round(stop, 2)
    risk_per_share = entry - stop
    rr_t1 = round((t1 - entry) / risk_per_share, 2) if risk_per_share > 0 else 0.0
    rr_t2 = round((t2 - entry) / risk_per_share, 2) if risk_per_share > 0 else 0.0
    rr_all = [(t - entry) / risk_per_share for t in targets] if risk_per_share > 0 else [0.0]
    blended_rr = round(sum(rr_all) / len(rr_all), 2)

    days = _expected_days(atr_pct)
    trend = _trend(last)
    risk_class = _risk_class(atr_pct, adv, score, trend)
    confidence = _confidence(score, len(setups), trend, adv)
    shares, pos_val, max_loss = _position_size(entry, stop, DEFAULT_CAPITAL, DEFAULT_RISK_PCT)

    strategy_ar = _strategy_narrative(
        lead_ar, trend, adv, atr_pct, rr_t1, rr_t2, risk_class, days, confidence
    )
    return SignalRow(
        symbol=symbol,
        signal_date=str(last.name.date() if hasattr(last.name, "date") else last.name),
        strategy=strategy,
        score=int(score),
        confidence=confidence,
        risk_class=risk_class,
        setups=setups,
        trend=trend,
        rsi=_f(last.get("rsi14")),
        macd_hist=_f(last.get("macd_hist")),
        ma20=_f(last.get("ma20")),
        ma50=_f(last.get("ma50")),
        volume_z=_f(last.get("vol_z20")),
        atr=round(atr_v, 4),
        atr_pct=round(atr_pct, 4),
        adv_20=round(adv, 2),
        entry=round(entry, 2),
        stop_loss=stop,
        target_1=t1,
        target_2=t2,
        target_3=t3,
        rr_t1=rr_t1,
        rr_t2=rr_t2,
        blended_rr=blended_rr,
        expected_days=days,
        max_hold=max_hold,
        suggested_shares_20k=shares,
        suggested_value_20k=pos_val,
        max_loss_20k=max_loss,
        rationale_ar=" • ".join(rationale) if rationale else "إشارة فنية",
        strategy_ar=strategy_ar,
        warnings_ar=_warnings(adv, atr_pct, trend, rr_t1),
        close=round(float(last["close"]), 2),
    )


def build_signal(symbol: str, df: pd.DataFrame, min_score: int = 30) -> SignalRow | None:
    """The original scoring strategy's live signal (kept for compatibility)."""
    if df is None or df.empty or len(df) < 60:
        return None

    setups, score, rationale = _detect_setups(df)
    if score < min_score or not setups:
        return None

    last = df.iloc[-1]
    if pd.isna(last["atr14"]) or last["atr14"] <= 0:
        return None
    adv = float(last["adv20"]) if not pd.isna(last["adv20"]) else 0.0
    if adv < MIN_ADV_EGP:
        return None  # too thin to trade

    entry = float(last["close"])
    atr_v = float(last["atr14"])
    atr_pct = atr_v / entry if entry else 0.0
    return assemble_signal(
        symbol=symbol,
        last=last,
        strategy="current_scoring",
        setups=setups,
        score=score,
        rationale=rationale,
        lead_ar=_lead_for_setups(setups, _f(last.get("vol_z20"))),
        entry=entry,
        stop=entry - STOP_ATR_MULT * atr_v,
        targets=[entry + TARGET_1_ATR_MULT * atr_v, entry + TARGET_2_ATR_MULT * atr_v],
        max_hold=2 * _expected_days(atr_pct),
    )
