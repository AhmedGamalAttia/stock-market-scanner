"""EGX historical OHLCV — multi-source with automatic fallback.

Source priority:
  1. TwelveData (if TWELVEDATA_API_KEY env is set) — works from any IP, free 800 req/day
  2. investing.com financialdata API — works locally but Cloudflare blocks cloud IPs
  3. investing.com TVC (different subdomain) — sometimes survives blocks

This way: locally you don't need a TwelveData key (investing.com works fine),
but on GitHub Actions you set the key and it Just Works.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests

from tickers import id_for

API_INV_PRIMARY = "https://api.investing.com/api/financialdata/{iid}/historical/chart/?interval=P1D&pointscount={n}"
API_INV_TVC = "https://tvc6.investing.com/4f9f4b3e0a5d5ebf3aa1f8c3eea9e34d/0/0/0/0/history?symbol={iid}&resolution=D&from={frm}&to={to}"
API_TD = "https://api.twelvedata.com/time_series"

INV_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
    "Referer": "https://www.investing.com/",
    "Origin": "https://www.investing.com",
}

TIMEOUT = 12
_ALLOWED_POINTS = (60, 70, 90, 110, 120, 140, 160)


def _is_blocked(text: str) -> bool:
    head = text[:200].lower()
    return "<!doctype html" in head or "just a moment" in head or "cloudflare" in head


def has_twelvedata() -> bool:
    return bool(os.environ.get("TWELVEDATA_API_KEY"))


# -------- TwelveData --------

def _try_twelvedata(symbol: str, points: int) -> pd.DataFrame | None:
    key = os.environ.get("TWELVEDATA_API_KEY")
    if not key:
        return None

    # TwelveData accepts several symbol formats for EGX — try them in order
    for sym_fmt in (f"{symbol}:EGX", symbol, f"{symbol}.EG"):
        try:
            r = requests.get(
                API_TD,
                params={
                    "symbol": sym_fmt,
                    "interval": "1day",
                    "outputsize": points,
                    "apikey": key,
                    "format": "JSON",
                },
                timeout=TIMEOUT,
            )
            if r.status_code != 200:
                continue
            j = r.json()
            # TwelveData returns {"status":"error",...} on errors, {"values":[...]} on success
            if j.get("status") == "error" or not j.get("values"):
                continue
            values = j["values"]
            df = pd.DataFrame(values)
            df["date"] = pd.to_datetime(df["datetime"]).dt.normalize()
            df = df.set_index("date").sort_index()
            for c in ["open", "high", "low", "close"]:
                df[c] = pd.to_numeric(df[c], errors="coerce")
            df["volume"] = pd.to_numeric(df.get("volume", 0), errors="coerce").fillna(0).astype("int64")
            df = df.dropna(subset=["close"])
            if not df.empty:
                return df[["open", "high", "low", "close", "volume"]]
        except requests.exceptions.RequestException:
            continue
        except Exception:  # noqa: BLE001
            continue

    return None


# -------- Investing.com primary --------

def _try_investing_primary(iid: int, points: int) -> pd.DataFrame | None:
    url = API_INV_PRIMARY.format(iid=iid, n=points)
    try:
        r = requests.get(url, headers=INV_HEADERS, timeout=TIMEOUT)
    except requests.exceptions.RequestException:
        return None
    if r.status_code != 200 or _is_blocked(r.text):
        return None
    try:
        rows = r.json().get("data") or []
    except ValueError:
        return None
    if not rows:
        return None
    df = pd.DataFrame(rows, columns=["ts_ms", "open", "high", "low", "close", "volume", "_x"])
    df["date"] = pd.to_datetime(df["ts_ms"], unit="ms").dt.normalize()
    return (
        df.drop(columns=["ts_ms", "_x"])
        .set_index("date")
        .sort_index()
        .astype({"open": float, "high": float, "low": float, "close": float})
    )


def _try_investing_tvc(iid: int, points: int) -> pd.DataFrame | None:
    now = datetime.now(timezone.utc)
    frm = int((now - timedelta(days=int(points * 1.6))).timestamp())
    to = int(now.timestamp())
    url = API_INV_TVC.format(iid=iid, frm=frm, to=to)
    try:
        r = requests.get(url, headers=INV_HEADERS, timeout=TIMEOUT)
    except requests.exceptions.RequestException:
        return None
    if r.status_code != 200 or _is_blocked(r.text):
        return None
    try:
        j = r.json()
    except ValueError:
        return None
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


# -------- Public entry --------

def fetch_history(symbol: str, points: int = 160) -> pd.DataFrame | None:
    iid = id_for(symbol)
    if points not in _ALLOWED_POINTS:
        points = next((p for p in _ALLOWED_POINTS if p >= points), 160)

    chain = []
    if has_twelvedata():
        # If we have a TwelveData key, use it FIRST — it works from any IP
        chain.append(("twelvedata", lambda: _try_twelvedata(symbol, points)))
    if iid is not None:
        chain.append(("investing", lambda: _try_investing_primary(iid, points)))
        chain.append(("investing-tvc", lambda: _try_investing_tvc(iid, points)))
    if not has_twelvedata():
        # No key locally? Still try TwelveData last (returns None silently if no key)
        chain.append(("twelvedata", lambda: _try_twelvedata(symbol, points)))

    for name, fn in chain:
        try:
            df = fn()
            if df is not None and not df.empty:
                df["volume"] = df["volume"].fillna(0).astype("int64")
                return df[["open", "high", "low", "close", "volume"]]
        except Exception as e:  # noqa: BLE001
            print(f"  ! {symbol} {name} unexpected err: {str(e)[:80]}")
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
