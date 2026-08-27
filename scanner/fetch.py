"""EGX daily OHLCV from Yahoo Finance, cached as JSON in the repo.

Why Yahoo: it lists every EGX name we track under the ``.CA`` suffix with ~5
years of daily bars, updated the same day, and it is reachable from GitHub
Actions runners (investing.com was not). We call the public chart endpoint
directly — no API key, no crumb dance.

Caching: every run refetches the full 5y window (42 cheap requests) and merges
it over ``web/public/data/prices/{SYM}.json``. Fresh data wins on overlapping
dates (keeps split/dividend back-adjustments current); cache-only history is
kept; a failed fetch falls back to the cache and is reported as ``stale``.

Adjusted vs raw: ``close`` is the raw traded price (what the user sees on
Thndr) and is what the live scanner uses. ``adjclose`` is Yahoo's
split/dividend-adjusted close and is what the backtester scales OHLC by so a
stock split does not look like a crash.
"""

from __future__ import annotations

import time
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import requests

from series import repair_splits
from store_json import PRICE_COLUMNS, read_prices, write_prices
from tickers import yahoo_for

CAIRO = ZoneInfo("Africa/Cairo")
EGX_CLOSE_HOUR = 15  # session ends 14:30; treat the bar as final from 15:00

YF_HOSTS = ("query1", "query2")
YF_CHART = "https://{host}.finance.yahoo.com/v8/finance/chart/{ysym}"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}
TIMEOUT = 15
MAX_ATTEMPTS = 4


class FetchResult:
    __slots__ = ("df", "source")

    def __init__(self, df: pd.DataFrame | None, source: str):
        self.df = df          # None when nothing is available at all
        self.source = source  # "yahoo" | "cache" | "none"


# ---------- Yahoo ----------

def _parse_chart(payload: dict) -> pd.DataFrame | None:
    chart = payload.get("chart") or {}
    if chart.get("error"):
        return None
    results = chart.get("result") or []
    if not results:
        return None
    res = results[0]
    ts = res.get("timestamp") or []
    ind = res.get("indicators") or {}
    quote = (ind.get("quote") or [{}])[0]
    adj_list = ind.get("adjclose") or [{}]
    adj = adj_list[0].get("adjclose") if adj_list else None
    if not ts or not quote.get("close"):
        return None

    df = pd.DataFrame(
        {
            "open": quote.get("open"),
            "high": quote.get("high"),
            "low": quote.get("low"),
            "close": quote.get("close"),
            "volume": quote.get("volume"),
            "adjclose": adj if adj and len(adj) == len(ts) else quote.get("close"),
        }
    )
    # Bar timestamps are session opens; convert to the Cairo calendar date.
    df["date"] = (
        pd.to_datetime(ts, unit="s", utc=True)
        .tz_convert(CAIRO)
        .normalize()
        .tz_localize(None)
    )
    df = (
        df.dropna(subset=["open", "high", "low", "close"])
        .drop_duplicates("date", keep="last")
        .set_index("date")
        .sort_index()
    )
    if df.empty:
        return None
    df["adjclose"] = pd.to_numeric(df["adjclose"], errors="coerce").fillna(df["close"])
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0).astype("int64")
    return df[PRICE_COLUMNS].astype({c: float for c in PRICE_COLUMNS if c != "volume"})


def fetch_yahoo(yahoo_symbol: str, rng: str = "5y") -> pd.DataFrame | None:
    params = {"range": rng, "interval": "1d", "includeAdjustedClose": "true"}
    last_err = "?"
    for attempt in range(MAX_ATTEMPTS):
        host = YF_HOSTS[attempt % len(YF_HOSTS)]
        url = YF_CHART.format(host=host, ysym=yahoo_symbol)
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
        except requests.exceptions.RequestException as e:
            last_err = f"conn: {str(e)[:80]}"
            time.sleep(1.5 * (attempt + 1))
            continue

        if r.status_code == 404:
            last_err = "404 (symbol unknown to Yahoo)"
            break
        if r.status_code == 429:
            last_err = "429 rate-limited"
            time.sleep(5 * (attempt + 1))
            continue
        if r.status_code != 200:
            last_err = f"http {r.status_code}"
            time.sleep(1.5 * (attempt + 1))
            continue

        try:
            payload = r.json()
        except ValueError:
            last_err = "non-json body"
            continue

        df = _parse_chart(payload)
        if df is not None and not df.empty:
            return df
        err = (payload.get("chart") or {}).get("error") or {}
        last_err = f"empty payload {err.get('code', '')} {err.get('description', '')}".strip()
        break

    print(f"  ⚠ Yahoo {yahoo_symbol}: {last_err}")
    return None


def _drop_partial_today(df: pd.DataFrame) -> pd.DataFrame:
    """During the session Yahoo returns today's bar half-formed; drop it."""
    if df.empty:
        return df
    now = datetime.now(CAIRO)
    if df.index[-1].date() == now.date() and now.hour < EGX_CLOSE_HOUR:
        return df.iloc[:-1]
    return df


# ---------- Public entry ----------

def update_cache(symbol: str, *, fetch: bool = True, write: bool = True) -> FetchResult:
    """Fetch → merge over cache → (optionally) write. Never loses good data."""
    cached = read_prices(symbol)

    if not fetch:
        return FetchResult(cached, "cache" if cached is not None else "none")

    fresh = fetch_yahoo(yahoo_for(symbol))
    if fresh is None or fresh.empty:
        return FetchResult(cached, "cache" if cached is not None else "none")

    fresh = _drop_partial_today(fresh)
    fresh, split_log = repair_splits(fresh)
    if split_log:
        print(f"  ↺ {symbol}: adjusted {len(split_log)} corporate action(s) "
              + ", ".join(f"{e['date']}×{e['factor']:.3f}" for e in split_log) + " ", end="")
    if cached is not None and not cached.empty:
        # Fresh (repaired) data wins on overlapping dates; older cache-only bars
        # are kept. A repair factor changes the whole history, so re-run the
        # repair over the merged frame to keep any cache-only tail consistent.
        merged = pd.concat([cached[~cached.index.isin(fresh.index)], fresh]).sort_index()
        merged, _ = repair_splits(merged)
    else:
        merged = fresh

    if write:
        write_prices(symbol, merged, yahoo_for(symbol))
    return FetchResult(merged, "yahoo")


def fetch_history(symbol: str) -> pd.DataFrame | None:
    """Convenience for one-off use: fresh data if possible, else cache."""
    return update_cache(symbol, write=False).df
