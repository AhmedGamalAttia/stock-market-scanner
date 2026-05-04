"""EGX historical OHLCV — multi-source with automatic fallback.

Source priority:
  1. Cloudflare Worker proxy (CLOUDFLARE_PROXY_URL + CLOUDFLARE_PROXY_TOKEN set)
       → fastest, works from cloud IPs (proxies through Cloudflare's own network)
  2. TwelveData (TWELVEDATA_API_KEY set) — free 800 req/day, slow (8 req/min limit)
  3. investing.com direct — works locally, blocked from most cloud IPs
  4. investing.com TVC — sometimes survives blocks
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


def has_cf_proxy() -> bool:
    return bool(os.environ.get("CLOUDFLARE_PROXY_URL") and os.environ.get("CLOUDFLARE_PROXY_TOKEN"))


# -------- Shared parsers --------

def _parse_inv_primary(payload: dict) -> pd.DataFrame | None:
    rows = payload.get("data") or []
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


def _parse_inv_tvc(payload: dict) -> pd.DataFrame | None:
    if payload.get("s") != "ok" or not payload.get("t"):
        return None
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(payload["t"], unit="s").normalize(),
            "open": payload.get("o", []),
            "high": payload.get("h", []),
            "low": payload.get("l", []),
            "close": payload.get("c", []),
            "volume": payload.get("v", [0] * len(payload["t"])),
        }
    )
    return df.set_index("date").sort_index().astype({"open": float, "high": float, "low": float, "close": float})


# -------- Cloudflare Worker proxy (best for cloud IPs) --------

_cf_warnings_shown: set[str] = set()


def _try_cf_proxy(iid: int, points: int) -> pd.DataFrame | None:
    base = os.environ.get("CLOUDFLARE_PROXY_URL", "").rstrip("/")
    token = os.environ.get("CLOUDFLARE_PROXY_TOKEN")
    if not base or not token:
        return None

    headers = {"X-Proxy-Token": token, "Accept": "application/json"}

    # Try primary route first
    try:
        r = requests.get(f"{base}/?iid={iid}&points={points}", headers=headers, timeout=TIMEOUT)
        if r.status_code == 200:
            try:
                df = _parse_inv_primary(r.json())
                if df is not None and not df.empty:
                    return df
            except (ValueError, KeyError):
                pass
        elif r.status_code == 401:
            if "auth" not in _cf_warnings_shown:
                _cf_warnings_shown.add("auth")
                print(f"  ⚠ CF proxy: 401 unauthorized — token mismatch with Worker secret")
            return None
        elif r.status_code >= 500:
            if str(iid) not in _cf_warnings_shown and len(_cf_warnings_shown) < 3:
                _cf_warnings_shown.add(str(iid))
                print(f"  ⚠ CF proxy upstream {r.status_code}: {r.text[:140]}")
    except requests.exceptions.RequestException as e:
        if "conn" not in _cf_warnings_shown:
            _cf_warnings_shown.add("conn")
            print(f"  ⚠ CF proxy connection failed: {str(e)[:120]}")
        return None

    # Try TVC fallback through proxy
    try:
        r = requests.get(f"{base}/tvc?iid={iid}&points={points}", headers=headers, timeout=TIMEOUT)
        if r.status_code == 200:
            try:
                df = _parse_inv_tvc(r.json())
                if df is not None and not df.empty:
                    return df
            except (ValueError, KeyError):
                pass
    except requests.exceptions.RequestException:
        pass

    return None


# -------- TwelveData --------

_td_warnings_shown: set[str] = set()


def _try_twelvedata(symbol: str, points: int) -> pd.DataFrame | None:
    key = os.environ.get("TWELVEDATA_API_KEY")
    if not key:
        return None

    last_err_msg: str | None = None
    for sym_fmt in (f"{symbol}:EGX", symbol, f"{symbol}.EG"):
        try:
            r = requests.get(
                API_TD,
                params={
                    "symbol": sym_fmt,
                    "interval": "1day",
                    "outputsize": points,
                    "apikey": key,
                    "exchange": "EGX",
                    "format": "JSON",
                },
                timeout=TIMEOUT,
            )
            if r.status_code != 200:
                last_err_msg = f"http {r.status_code}: {r.text[:160]}"
                continue
            try:
                j = r.json()
            except ValueError:
                last_err_msg = f"non-json response: {r.text[:160]}"
                continue
            if j.get("status") == "error":
                last_err_msg = f"{sym_fmt}: {j.get('code', '?')} — {j.get('message', '?')}"
                continue
            if not j.get("values"):
                last_err_msg = f"{sym_fmt}: no values"
                continue
            df = pd.DataFrame(j["values"])
            df["date"] = pd.to_datetime(df["datetime"]).dt.normalize()
            df = df.set_index("date").sort_index()
            for c in ["open", "high", "low", "close"]:
                df[c] = pd.to_numeric(df[c], errors="coerce")
            df["volume"] = pd.to_numeric(df.get("volume", 0), errors="coerce").fillna(0).astype("int64")
            df = df.dropna(subset=["close"])
            if not df.empty:
                return df[["open", "high", "low", "close", "volume"]]
        except requests.exceptions.RequestException as e:
            last_err_msg = f"request err: {str(e)[:160]}"
            continue

    if last_err_msg and len(_td_warnings_shown) < 3:
        _td_warnings_shown.add(symbol)
        print(f"  ⚠ TwelveData rejected {symbol} → {last_err_msg}")
    return None


# -------- Investing.com direct --------

def _try_investing_primary(iid: int, points: int) -> pd.DataFrame | None:
    url = API_INV_PRIMARY.format(iid=iid, n=points)
    try:
        r = requests.get(url, headers=INV_HEADERS, timeout=TIMEOUT)
    except requests.exceptions.RequestException:
        return None
    if r.status_code != 200 or _is_blocked(r.text):
        return None
    try:
        return _parse_inv_primary(r.json())
    except ValueError:
        return None


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
        return _parse_inv_tvc(r.json())
    except ValueError:
        return None


# -------- Public entry --------

def fetch_history(symbol: str, points: int = 160) -> pd.DataFrame | None:
    iid = id_for(symbol)
    if points not in _ALLOWED_POINTS:
        points = next((p for p in _ALLOWED_POINTS if p >= points), 160)

    chain: list[tuple[str, callable]] = []

    # Best for cloud IPs — try first if configured
    if has_cf_proxy() and iid is not None:
        chain.append(("cf-proxy", lambda: _try_cf_proxy(iid, points)))

    # Local-friendly — try direct after proxy
    if iid is not None:
        chain.append(("investing", lambda: _try_investing_primary(iid, points)))
        chain.append(("investing-tvc", lambda: _try_investing_tvc(iid, points)))

    # Last-resort fallback
    if has_twelvedata():
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
