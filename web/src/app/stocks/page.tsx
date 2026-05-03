import Link from "next/link";
import { getAllStocks } from "@/lib/queries";
import { supabaseConfigured } from "@/lib/supabase";

export const revalidate = 3600;

export default async function StocksPage() {
  if (!supabaseConfigured) {
    return <div className="panel p-6 text-muted">Supabase غير مهيّأ.</div>;
  }
  const stocks = await getAllStocks();

  return (
    <div className="space-y-4">
      <header className="panel p-5">
        <h1 className="text-2xl font-bold">كل الأسهم</h1>
        <p className="text-muted text-sm mt-1">{stocks.length} سهم متابع</p>
      </header>

      <div className="panel overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-panel2 text-muted text-xs uppercase">
            <tr>
              <th className="px-4 py-3 text-right">الكود</th>
              <th className="px-4 py-3 text-right">الاسم</th>
              <th className="px-4 py-3 text-right">القطاع</th>
              <th className="px-4 py-3 text-right"></th>
            </tr>
          </thead>
          <tbody>
            {stocks.map((s) => (
              <tr key={s.symbol} className="border-t border-border hover:bg-panel2/50">
                <td className="px-4 py-3 font-mono text-brand">{s.symbol}</td>
                <td className="px-4 py-3">{s.name_ar ?? s.name_en ?? "—"}</td>
                <td className="px-4 py-3 text-muted">{s.sector ?? "—"}</td>
                <td className="px-4 py-3 text-left">
                  <Link
                    href={`/stock/${encodeURIComponent(s.symbol)}`}
                    className="text-brand hover:underline"
                  >
                    عرض ←
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
