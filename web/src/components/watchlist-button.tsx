"use client";

import { useEffect, useState } from "react";

const KEY = "egx:watchlist";

export function readWatchlist(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as string[]) : [];
  } catch {
    return [];
  }
}

function writeWatchlist(items: string[]) {
  window.localStorage.setItem(KEY, JSON.stringify(items));
  window.dispatchEvent(new Event("watchlist:change"));
}

export function WatchlistButton({ symbol }: { symbol: string }) {
  const [on, setOn] = useState(false);
  useEffect(() => {
    setOn(readWatchlist().includes(symbol));
  }, [symbol]);

  const toggle = () => {
    const items = readWatchlist();
    const next = items.includes(symbol)
      ? items.filter((s) => s !== symbol)
      : [...items, symbol];
    writeWatchlist(next);
    setOn(next.includes(symbol));
  };

  return (
    <button onClick={toggle} className={on ? "btn-primary" : "btn"}>
      {on ? "★ مُتابَع" : "☆ تابعنى"}
    </button>
  );
}
