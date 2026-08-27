"""JSON persistence — the whole "database" is a folder of files in the repo.

Design rules:
  * Atomic writes (temp file + ``os.replace``) so a crashed run never leaves a
    half-written file behind for the site to read.
  * Deterministic output (sorted keys / sorted bars, fixed precision, one bar
    per line for price files) so the daily git commit is a one-line diff per
    ticker instead of a full-file rewrite.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pandas as pd

from paths import (
    LATEST_FILE,
    META_FILE,
    POSITIONS_FILE,
    STOCKS_FILE,
    TRADES_LIVE_FILE,
    price_file,
)

PRICE_COLUMNS = ["open", "high", "low", "close", "adjclose", "volume"]
# Short keys keep 42 × ~1200 bars around 4 MB total.
_BAR_KEYS = {"open": "o", "high": "h", "low": "l", "close": "c", "adjclose": "a", "volume": "v"}


# ---------- generic ----------

def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def write_json(path: Path, obj: Any, indent: int | None = 2) -> None:
    text = json.dumps(obj, ensure_ascii=False, indent=indent, sort_keys=False, default=_default)
    _atomic_write_text(path, text + "\n")


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return default


def _default(o: Any) -> Any:
    if isinstance(o, (pd.Timestamp,)):
        return o.date().isoformat()
    if hasattr(o, "item"):  # numpy scalars
        return o.item()
    raise TypeError(f"not JSON serializable: {type(o).__name__}")


# ---------- prices ----------

def df_to_bars(df: pd.DataFrame) -> list[dict]:
    """DataFrame (DatetimeIndex, PRICE_COLUMNS) -> list of compact bar dicts."""
    bars: list[dict] = []
    for ts, r in df.iterrows():
        bar = {"d": ts.date().isoformat()}
        for col, key in _BAR_KEYS.items():
            v = r.get(col)
            if col == "volume":
                bar[key] = int(v) if pd.notna(v) else 0
            else:
                bar[key] = round(float(v), 4) if pd.notna(v) else None
        bars.append(bar)
    return bars


def bars_to_df(bars: list[dict]) -> pd.DataFrame:
    if not bars:
        return pd.DataFrame(columns=PRICE_COLUMNS)
    df = pd.DataFrame(bars).rename(columns={v: k for k, v in _BAR_KEYS.items()} | {"d": "date"})
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    df = df[~df.index.duplicated(keep="last")]
    for c in ("open", "high", "low", "close", "adjclose"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["adjclose"] = df["adjclose"].fillna(df["close"])
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0).astype("int64")
    return df[PRICE_COLUMNS]


def write_prices(symbol: str, df: pd.DataFrame, yahoo_symbol: str | None = None) -> Path:
    """One bar per line so daily commits diff to a single appended line."""
    bars = df_to_bars(df)
    lines = [json.dumps(b, separators=(",", ":")) for b in bars]
    head = {
        "symbol": symbol,
        "yahoo": yahoo_symbol,
        "updated": bars[-1]["d"] if bars else None,
        "count": len(bars),
    }
    text = (
        "{"
        + ",".join(f"\n  {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in head.items())
        + ',\n  "bars": [\n    '
        + ",\n    ".join(lines)
        + "\n  ]\n}\n"
    )
    path = price_file(symbol)
    _atomic_write_text(path, text)
    return path


def read_prices(symbol: str) -> pd.DataFrame | None:
    obj = read_json(price_file(symbol))
    if not obj or not obj.get("bars"):
        return None
    df = bars_to_df(obj["bars"])
    return df if not df.empty else None


# ---------- published files ----------

def write_stocks(rows: list[dict]) -> None:
    write_json(STOCKS_FILE, sorted(rows, key=lambda r: r["symbol"]))


def read_stocks() -> list[dict]:
    return read_json(STOCKS_FILE, default=[]) or []


def write_latest(payload: dict) -> None:
    write_json(LATEST_FILE, payload)


def read_latest() -> dict | None:
    return read_json(LATEST_FILE)


def write_meta(meta: dict) -> None:
    write_json(META_FILE, meta)


def read_meta() -> dict | None:
    return read_json(META_FILE)


def read_positions() -> dict:
    return read_json(POSITIONS_FILE, default={"updated": None, "positions": []}) or {
        "updated": None,
        "positions": [],
    }


def write_positions(book: dict) -> None:
    write_json(POSITIONS_FILE, book)


def read_trades_live() -> list[dict]:
    return read_json(TRADES_LIVE_FILE, default=[]) or []


def append_trades_live(trades: list[dict]) -> None:
    if not trades:
        return
    existing = read_trades_live()
    existing.extend(trades)
    write_json(TRADES_LIVE_FILE, existing)
