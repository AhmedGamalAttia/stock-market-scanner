"""Strategy interface shared by the live scanner and the backtester.

A strategy's ``prepare(df)`` must return the frame with these columns added:

  long_entry  bool   decision taken on this bar's close → filled at NEXT open
  long_exit   bool   hard exit taken on this bar's close → filled at NEXT open
  stop        float  stop-loss level if entering on this bar (NaN = no entry)
  tp1..tp3    float  take-profit ladder (NaN = unused level)
  trend       int    +1 / -1 (display + exit logic)
  reason_ar   str    one-line Arabic rationale for this bar (may be "")
  max_hold    int    optional per-bar time stop; falls back to Strategy.max_hold

Everything acts on CLOSED daily bars, so there is no repainting: what the
backtester sees on bar i is exactly what the live run sees at the end of the
day.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import pandas as pd

from signals import SignalRow

REQUIRED_COLUMNS = ("long_entry", "long_exit", "stop", "tp1", "tp2", "tp3", "trend", "reason_ar")


@dataclass
class Exit:
    date: str
    price: float
    shares: int
    reason: str


@dataclass
class Trade:
    symbol: str
    strategy: str
    entry_date: str
    entry_price: float
    shares: int
    initial_stop: float
    tp_levels: list[float | None]
    exits: list[Exit] = field(default_factory=list)
    tp_hits: list[bool] = field(default_factory=list)
    pnl_net: float = 0.0
    r_multiple: float = 0.0
    bars_held: int = 0
    reason: str = ""          # final exit reason
    exit_date: str = ""
    mfe_r: float = 0.0        # max favourable excursion (in R)
    mae_r: float = 0.0        # max adverse excursion (in R)


class Strategy(ABC):
    name: str = "base"
    label_ar: str = "استراتيجية"
    #: fraction of the position sold at each TP level (must sum to ≤ 1;
    #: any remainder rides until stop / flip / time stop)
    tp_fractions: tuple[float, ...] = (1 / 3, 1 / 3, 1 / 3)
    #: move stop to entry once TP1 is hit
    breakeven_after_tp1: bool = False
    #: default time stop in bars (None = none)
    max_hold: int | None = None

    @abstractmethod
    def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add indicator + rule columns (see module docstring)."""

    @abstractmethod
    def signal_from_prepared(self, prep: pd.DataFrame, **kwargs) -> SignalRow | None:
        """Build the publishable SignalRow for the LAST bar of a prepared frame."""

    def live_signal(self, df: pd.DataFrame, **kwargs) -> SignalRow | None:
        if df is None or len(df) < 60:
            return None
        return self.signal_from_prepared(self.prepare(df), **kwargs)

    def validate(self, prepared: pd.DataFrame) -> None:
        missing = [c for c in REQUIRED_COLUMNS if c not in prepared.columns]
        if missing:
            raise ValueError(f"{self.name}.prepare() missing columns: {missing}")
