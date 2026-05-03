"""Pure-pandas technical indicators. No third-party TA library needed."""

from __future__ import annotations

import numpy as np
import pandas as pd


def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period, min_periods=period).mean()


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False, min_periods=period).mean()


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    roll_up = up.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    roll_down = down.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = roll_up / roll_down.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = ema(macd_line, signal)
    hist = macd_line - signal_line
    return pd.DataFrame({"macd": macd_line, "signal": signal_line, "hist": hist})


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def volume_zscore(volume: pd.Series, lookback: int = 20) -> pd.Series:
    rolling_mean = volume.rolling(lookback, min_periods=lookback).mean()
    rolling_std = volume.rolling(lookback, min_periods=lookback).std()
    return (volume - rolling_mean) / rolling_std.replace(0, np.nan)


def rolling_high(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(period, min_periods=period).max()


def rolling_low(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(period, min_periods=period).min()


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Adds all indicator columns to an OHLCV dataframe."""
    out = df.copy()
    out["ma20"] = sma(out["close"], 20)
    out["ma50"] = sma(out["close"], 50)
    out["ma200"] = sma(out["close"], 200)
    out["rsi14"] = rsi(out["close"], 14)
    macd_df = macd(out["close"])
    out["macd"] = macd_df["macd"]
    out["macd_signal"] = macd_df["signal"]
    out["macd_hist"] = macd_df["hist"]
    out["atr14"] = atr(out["high"], out["low"], out["close"], 14)
    out["vol_z20"] = volume_zscore(out["volume"], 20)
    out["high20"] = rolling_high(out["high"], 20)
    out["high55"] = rolling_high(out["high"], 55)
    out["low20"] = rolling_low(out["low"], 20)
    # Average Daily Value in EGP (close × volume) over 20 days — liquidity gate
    out["adv20"] = (out["close"] * out["volume"]).rolling(20, min_periods=20).mean()
    return out
