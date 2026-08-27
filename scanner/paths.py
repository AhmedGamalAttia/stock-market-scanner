"""Filesystem layout shared by the scanner, the backtester and the web app.

All published data lives under ``web/public/data`` so that:
  * Next.js can read it with ``fs`` at build time (server components), and
  * the browser can fetch the very same files at ``/data/...`` (charts).

Override the root with ``EGX_DATA_DIR`` for tests / scratch runs.
"""

from __future__ import annotations

import os
from pathlib import Path

SCANNER_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCANNER_DIR.parent

DATA_DIR = Path(os.environ.get("EGX_DATA_DIR") or REPO_ROOT / "web" / "public" / "data")
PRICES_DIR = DATA_DIR / "prices"
BACKTEST_DIR = DATA_DIR / "backtest"

STOCKS_FILE = DATA_DIR / "stocks.json"
LATEST_FILE = DATA_DIR / "latest.json"
META_FILE = DATA_DIR / "meta.json"
POSITIONS_FILE = DATA_DIR / "positions.json"
TRADES_LIVE_FILE = DATA_DIR / "trades_live.json"

# Heavy per-trade backtest logs the browser never loads.
BACKTEST_DETAIL_DIR = REPO_ROOT / "data" / "backtest_detail"


def price_file(symbol: str) -> Path:
    return PRICES_DIR / f"{symbol}.json"
