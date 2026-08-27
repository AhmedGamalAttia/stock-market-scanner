"""Price-series hygiene: repair corporate actions Yahoo did not adjust.

EGX companies frequently do bonus-share issues / splits and Yahoo often leaves
the raw close series with a one-day cliff (e.g. OCDI 61 → 16). The exchange's
daily price limit is ±20 %, so any overnight gap beyond ±30 % is a corporate
action (or a data glitch), never a real trade — either way the history before
it must be scaled so indicators (ATR, MAs, Supertrend) stay continuous.

We back-adjust the bars BEFORE the event; the latest bars keep their real
traded prices, so entries/stops shown to the user are always in today's terms.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

GAP_THRESHOLD = 0.30  # |gap| beyond this can't be a normal EGX session


def detect_splits(df: pd.DataFrame) -> list[tuple[pd.Timestamp, float]]:
    """Return [(date, factor)] where bars before ``date`` must be multiplied by
    ``factor`` to line up with the bars from ``date`` on."""
    if df is None or len(df) < 2:
        return []
    close = df["close"].to_numpy(float)
    open_ = df["open"].to_numpy(float)
    events: list[tuple[pd.Timestamp, float]] = []
    for i in range(1, len(df)):
        prev = close[i - 1]
        if not prev or np.isnan(prev):
            continue
        ref = open_[i] if open_[i] and not np.isnan(open_[i]) else close[i]
        if not ref or np.isnan(ref):
            continue
        ratio = ref / prev
        if abs(ratio - 1.0) > GAP_THRESHOLD:
            events.append((df.index[i], float(ratio)))
    return events


def repair_splits(df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """Back-adjust OHLC (and volume) across detected corporate actions.

    Returns (repaired_df, log) where log lists the events applied.
    """
    events = detect_splits(df)
    if not events:
        return df, []
    out = df.copy()
    log: list[dict] = []
    price_cols = [c for c in ("open", "high", "low", "close") if c in out.columns]
    has_adj = "adjclose" in out.columns
    # Apply from the most recent event backwards so factors compound correctly.
    for date, factor in sorted(events, key=lambda e: e[0], reverse=True):
        before = out.index < date
        out.loc[before, price_cols] = out.loc[before, price_cols] * factor
        if "volume" in out.columns:
            out.loc[before, "volume"] = (out.loc[before, "volume"] / factor).round().astype("int64")
        if has_adj:
            # Only scale adjclose if Yahoo left the same cliff in it.
            pos = out.index.get_loc(date)
            a_prev, a_now = out["adjclose"].iloc[pos - 1], out["adjclose"].iloc[pos]
            if a_prev and not np.isnan(a_prev) and abs(a_now / a_prev - 1.0) > GAP_THRESHOLD:
                out.loc[before, "adjclose"] = out.loc[before, "adjclose"] * factor
        log.append({"date": date.date().isoformat(), "factor": round(factor, 6)})
    return out, log
