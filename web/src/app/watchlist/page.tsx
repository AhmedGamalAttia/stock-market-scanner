"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { readWatchlist } from "@/components/watchlist-button";

export default function WatchlistPage() {
  const [items, setItems] = useState<string[]>([]);

  useEffect(() => {
    const refresh = () => setItems(readWatchlist());
    refresh();
    window.addEventListener("watchlist:change", refresh);
    return () => window.removeEventListener("watchlist:change", refresh);
  }, []);

  return (
    <div className="space-y-4">
      <header className="panel p-5">
        <h1 className="text-2xl font-bold">قائمة متابعتى</h1>
        <p className="text-muted text-sm mt-1">
          الأسهم اللى ضفتها لمتابعتها. القائمة محفوظة محلياً على المتصفح.
        </p>
      </header>

      {items.length === 0 ? (
        <div className="panel p-10 text-center text-muted">
          لا توجد أسهم فى قائمتك. اضغط ★ من صفحة أى سهم لإضافته.
        </div>
      ) : (
        <ul className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {items.map((sym) => (
            <li key={sym}>
              <Link
                href={`/stock/${encodeURIComponent(sym)}`}
                className="panel p-4 flex items-center justify-between hover:border-brand/40"
              >
                <span className="font-semibold">{sym}</span>
                <span className="text-xs text-brand">عرض ←</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
