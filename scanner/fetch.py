"""EGX historical OHLCV via investing.com financialdata API.

Yahoo Finance dropped EGX coverage; Stooq now requires a paid key.
This endpoint is public, returns the same data investing.com's charts use,
and works with browser-like headers from a low-volume scheduled job.
"""

from __future__ import annotations

import time

import pandas as pd
import requests

from tickers import id_for

API = "https://api.investing.com/api/financialdata/{iid}/historical/chart/?interval=P1D&pointscount={n}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
    "Referer": "https://www.investing.com/",
    "Origin": "https://www.investing.com",
}


_ALLOWED_POINTS = (60, 70, 90, 110, 120, 140, 160)


def fetch_history(symbol: str, points: int = 160, retries: int = 2) -> pd.DataFrame | None:
    if points not in _ALLOWED_POINTS:
        # snap up to the nearest allowed value
        points = next((p for p in _ALLOWED_POINTS if p >= points), 160)
    iid = id_for(symbol)
    if iid is None:
        return None

    url = API.format(iid=iid, n=points)
    last_err: Exception | None = None

    for attempt in range(retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                payload = r.json()
                rows = payload.get("data") or []
                if not rows:
                    return None
                df = pd.DataFrame(
                    rows, columns=["ts_ms", "open", "high", "low", "close", "volume", "_x"]
                )
                df["date"] = pd.to_datetime(df["ts_ms"], unit="ms").dt.normalize()
                df = (
                    df.drop(columns=["ts_ms", "_x"])
                    .set_index("date")
                    .sort_index()
                    .astype({"open": float, "high": float, "low": float, "close": float})
                )
                df["volume"] = df["volume"].fillna(0).astype("int64")
                return df[["open", "high", "low", "close", "volume"]]
            if r.status_code in (403, 429, 503):
                # Cloudflare / rate limit — back off
                time.sleep(3 * (attempt + 1))
                continue
            print(f"  ! {symbol} http {r.status_code}")
            return None
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(2 * (attempt + 1))

    if last_err:
        print(f"  ! {symbol} fetch err: {last_err}")
    return None


def to_price_rows(symbol: str, df: pd.DataFrame, last_n: int = 90) -> list[dict]:
    tail = df.tail(last_n)
    rows = []
    for ts, r in tail.iterrows():
        rows.append(
            {
                "symbol": symbol,
                "date": ts.date().isoformat(),
                "open": _safe(r["open"]),
                "high": _safe(r["high"]),
                "low": _safe(r["low"]),
                "close": _safe(r["close"]),
                "volume": int(r["volume"]) if pd.notna(r["volume"]) else None,
            }
        )
    return rows


def _safe(x) -> float | None:
    try:
        return float(x) if pd.notna(x) else None
    except Exception:  # noqa: BLE001
        return None
