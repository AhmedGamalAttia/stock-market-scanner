import Link from "next/link";
import { getAllStocks } from "@/lib/data";
import { shariaBadge } from "@/lib/utils";

export default async function StocksPage() {
  const stocks = await getAllStocks();

  const halal = stocks.filter((s) => s.sharia_status === "halal").length;
  const haram = stocks.filter((s) => s.sharia_status === "haram").length;
  const mixed = stocks.filter((s) => s.sharia_status === "mixed").length;

  return (
    <div className="space-y-4">
      <header className="panel p-5">
        <h1 className="text-2xl font-bold">كل الأسهم</h1>
        <p className="text-muted text-sm mt-1">
          {stocks.length} سهم متابع • ⭐ حلال: {halal} • ⚠ مختلط: {mixed} • ✕ محل خلاف: {haram}
        </p>
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
            {stocks.map((s) => {
              const sh = shariaBadge(s.sharia_status);
              return (
                <tr key={s.symbol} className="border-t border-border hover:bg-panel2/50">
                  <td className="px-4 py-3 font-mono text-brand">{s.symbol}</td>
                  <td className="px-4 py-3">{s.name_ar ?? s.name_en ?? "—"}</td>
                  <td className="px-4 py-3 text-muted">{s.sector ?? "—"}</td>
                  <td className="px-4 py-3">
                    <span className={`chip ${sh.cls}`}>{sh.emoji} {sh.short}</span>
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
        ⚠️ التصنيف الشرعى اجتهادى مبدئى بناءً على النشاط الأساسى. يُفضّل المراجعة مع
        هيئة شرعية موثوقة قبل اتخاذ قرار تداول حقيقى.
      </p>
    </div>
  );
}
