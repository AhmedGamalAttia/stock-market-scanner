"""EGX historical OHLCV via investing.com.

Two endpoints with automatic fallback. Both are public; the second sometimes
survives Cloudflare blocks of the first (different subdomain rules).
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests

from tickers import id_for

API_PRIMARY = "https://api.investing.com/api/financialdata/{iid}/historical/chart/?interval=P1D&pointscount={n}"
API_TVC = "https://tvc6.investing.com/4f9f4b3e0a5d5ebf3aa1f8c3eea9e34d/0/0/0/0/history?symbol={iid}&resolution=D&from={frm}&to={to}"

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

TIMEOUT = 8  # short — fail fast, don't hang the whole run
_ALLOWED_POINTS = (60, 70, 90, 110, 120, 140, 160)


def _is_blocked(text: str) -> bool:
    head = text[:200].lower()
    return "<!doctype html" in head or "just a moment" in head or "cloudflare" in head


def _try_primary(iid: int, points: int) -> pd.DataFrame | None:
    url = API_PRIMARY.format(iid=iid, n=points)
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return None
    if _is_blocked(r.text):
        return None
    payload = r.json()
    rows = payload.get("data") or []
    if not rows:
        return None
    df = pd.DataFrame(
        rows, columns=["ts_ms", "open", "high", "low", "close", "volume", "_x"]
    )
    df["date"] = pd.to_datetime(df["ts_ms"], unit="ms").dt.normalize()
    return (
        df.drop(columns=["ts_ms", "_x"])
        .set_index("date")
        .sort_index()
        .astype({"open": float, "high": float, "low": float, "close": float})
    )


def _try_tvc(iid: int, points: int) -> pd.DataFrame | None:
    now = datetime.now(timezone.utc)
    frm = int((now - timedelta(days=int(points * 1.6))).timestamp())
    to = int(now.timestamp())
    url = API_TVC.format(iid=iid, frm=frm, to=to)
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200 or _is_blocked(r.text):
        return None
    j = r.json()
    if j.get("s") != "ok" or not j.get("t"):
        return None
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(j["t"], unit="s").normalize(),
            "open": j.get("o", []),
            "high": j.get("h", []),
            "low": j.get("l", []),
            "close": j.get("c", []),
            "volume": j.get("v", [0] * len(j["t"])),
        }
    )
    return df.set_index("date").sort_index().astype({"open": float, "high": float, "low": float, "close": float})


def fetch_history(symbol: str, points: int = 160) -> pd.DataFrame | None:
    iid = id_for(symbol)
    if iid is None:
        return None
    if points not in _ALLOWED_POINTS:
        points = next((p for p in _ALLOWED_POINTS if p >= points), 160)

    for endpoint, fn in (("primary", _try_primary), ("tvc", _try_tvc)):
        try:
            df = fn(iid, points)
            if df is not None and not df.empty:
                df["volume"] = df["volume"].fillna(0).astype("int64")
                return df[["open", "high", "low", "close", "volume"]]
        except requests.exceptions.RequestException:
            continue
        except Exception as e:  # noqa: BLE001
            print(f"  ! {symbol} {endpoint} parse err: {str(e)[:80]}")
            continue

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
