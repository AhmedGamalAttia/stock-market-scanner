"""Supabase persistence layer."""

from __future__ import annotations

import os
from dataclasses import asdict
from typing import Iterable

from supabase import Client, create_client

from signals import SignalRow


def get_client() -> Client | None:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)


def upsert_stocks(client: Client, rows: list[dict]) -> None:
    if not rows:
        return
    client.table("stocks").upsert(rows, on_conflict="symbol").execute()


def upsert_daily_prices(client: Client, rows: list[dict]) -> None:
    if not rows:
        return
    # Chunk for safety
    CHUNK = 500
    for i in range(0, len(rows), CHUNK):
        client.table("daily_prices").upsert(
            rows[i : i + CHUNK], on_conflict="symbol,date"
        ).execute()


def replace_signals_for_date(client: Client, signals: Iterable[SignalRow], signal_date: str) -> int:
    rows = []
    for s in signals:
        d = asdict(s)
        d.pop("close", None)
        rows.append(d)
    # Delete existing rows for this date so we don't get stale ones lingering
    client.table("signals").delete().eq("signal_date", signal_date).execute()
    if rows:
        # Chunk inserts to keep payloads small
        CHUNK = 50
        for i in range(0, len(rows), CHUNK):
            client.table("signals").insert(rows[i : i + CHUNK]).execute()
    return len(rows)


def log_run(
    client: Client,
    ok: bool,
    symbols_total: int,
    symbols_failed: int,
    signals_emitted: int,
    notes: str = "",
) -> None:
    client.table("run_meta").insert(
        {
            "ok": ok,
            "symbols_total": symbols_total,
            "symbols_failed": symbols_failed,
            "signals_emitted": signals_emitted,
            "notes": notes,
        }
    ).execute()
