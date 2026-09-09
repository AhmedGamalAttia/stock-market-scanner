"use client";

import Link from "next/link";
import { useMemo } from "react";
import type { Stock } from "@/lib/types";
import { isHalal, shariaBadge } from "@/lib/utils";
import { HiddenBanner, useHalalOnly } from "./halal-context";

export function StocksTable({ stocks }: { stocks: Stock[] }) {
  const { halalOnly } = useHalalOnly();

  const halal = stocks.filter((s) => s.sharia_status === "halal").length;
  const haram = stocks.filter((s) => s.sharia_status === "haram").length;
  const mixed = stocks.filter((s) => s.sharia_status === "mixed").length;

  const visible = useMemo(
    () => (halalOnly ? stocks.filter((s) => isHalal(s.sharia_status)) : stocks),
    [stocks, halalOnly],
  );
  const hidden = stocks.length - visible.length;

  return (
    <div className="space-y-4">
      <header className="panel p-5">
        <h1 className="text-2xl font-bold">
          {halalOnly ? "الأسهم المتوافقة مع الشريعة" : "كل الأسهم"}
        </h1>
        <p className="text-muted text-sm mt-1">
          {visible.length} سهم معروض
          {halalOnly ? "" : ` من ${stocks.length}`} • ⭐ حلال: {halal} • ⚠ مختلط: {mixed} • ✕ محل خلاف:{" "}
          {haram}
        </p>
        <div className="mt-2">
          <HiddenBanner count={hidden} />
        </div>
      </header>

      <div className="panel overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-panel2 text-muted text-xs uppercase">
            <tr>
              <th className="px-4 py-3 text-right">الكود</th>
              <th className="px-4 py-3 text-right">الاسم</th>
              <th className="px-4 py-3 text-right">القطاع</th>
              <th className="px-4 py-3 text-right">الحالة الشرعية</th>
              <th className="px-4 py-3 text-right"></th>
            </tr>
          </thead>
          <tbody>
            {visible.map((s) => {
              const sh = shariaBadge(s.sharia_status);
              return (
                <tr key={s.symbol} className="border-t border-border hover:bg-panel2/50">
                  <td className="px-4 py-3 font-mono text-brand">{s.symbol}</td>
                  <td className="px-4 py-3">{s.name_ar ?? s.name_en ?? "—"}</td>
                  <td className="px-4 py-3 text-muted">{s.sector ?? "—"}</td>
                  <td className="px-4 py-3">
                    <span className={`chip ${sh.cls}`}>
                      {sh.emoji} {sh.short}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-left">
                    <Link
                      href={`/stock/${encodeURIComponent(s.symbol)}`}
                      className="text-brand hover:underline"
                    >
                      عرض ←
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-muted px-2">
        ⚠️ التصنيف الشرعى اجتهادى مبدئى بناءً على النشاط الأساسى للشركة (مش على النسب المالية). يُفضّل
        المراجعة مع هيئة شرعية موثوقة قبل اتخاذ قرار تداول حقيقى.
      </p>
    </div>
  );
}
