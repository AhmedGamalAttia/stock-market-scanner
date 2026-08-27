import Link from "next/link";
import { PositionCard } from "@/components/position-card";
import { getLatest, getTradesLive } from "@/lib/data";
import { exitReasonLabel, fmtMoney, fmtNum, fmtR, pnlColor, strategyLabel } from "@/lib/utils";

export default async function PositionsPage() {
  const [latest, trades] = await Promise.all([getLatest(), getTradesLive()]);
  const holds = latest?.holds ?? [];
  const closed = trades
    .filter((t) => t.reason !== "invalid")
    .sort((a, b) => ((a.closed_date ?? "") < (b.closed_date ?? "") ? 1 : -1));

  const wins = closed.filter((t) => (t.realized_pnl ?? 0) > 0).length;
  const net = closed.reduce((acc, t) => acc + (t.realized_pnl ?? 0), 0);
  const avgR = closed.length ? closed.reduce((acc, t) => acc + (t.realized_r ?? 0), 0) / closed.length : 0;
  const openPnl = holds.reduce((acc, h) => acc + (h.unrealized_pnl ?? 0), 0);

  return (
    <div className="space-y-5">
      <header className="panel p-5">
        <h1 className="text-2xl font-bold">المراكز — المحفظة الورقية</h1>
        <p className="text-muted text-sm mt-1 leading-relaxed max-w-3xl">
          كل إشارة بتتحول لمركز ورقى بيتدار بنفس قواعد الاستراتيجية بالظبط (دخول على الافتتاح، وقف، أهداف،
          انقلاب اتجاه). ده السجل الحقيقى للأداة من يوم ما اشتغلت — مش backtest. صفقاتك الفعلية سجّلها فى{" "}
          <Link href="/journal" className="text-brand hover:underline">دفتر الصفقات</Link>.
        </p>
      </header>

      <section className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Stat label="مراكز مفتوحة" value={String(holds.length)} />
        <Stat label="ربح/خسارة غير محقق" value={fmtMoney(openPnl)} accent={pnlColor(openPnl)} />
        <Stat label="صفقات مغلقة" value={`${closed.length} (${closed.length ? Math.round((wins / closed.length) * 100) : 0}% ناجحة)`} />
        <Stat label="صافى المحقق" value={`${fmtMoney(net)} • ${fmtR(avgR)}/صفقة`} accent={pnlColor(net)} />
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-bold">🔵 المفتوحة ({holds.length})</h2>
        {holds.length === 0 ? (
          <div className="panel p-6 text-center text-muted text-sm">مفيش مراكز مفتوحة.</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {holds.map((h) => (
              <PositionCard key={h.id} h={h} />
            ))}
          </div>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-bold">📁 المغلقة ({closed.length})</h2>
        {closed.length === 0 ? (
          <div className="panel p-6 text-center text-muted text-sm">
            لسه مفيش صفقات مغلقة — السجل بيبدأ من أول مركز يتقفل.
          </div>
        ) : (
          <div className="panel overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-panel2 text-muted text-xs uppercase">
                <tr>
                  <th className="px-3 py-3 text-right">السهم</th>
                  <th className="px-3 py-3 text-right">دخول</th>
                  <th className="px-3 py-3 text-right">خروج</th>
                  <th className="px-3 py-3 text-right">السبب</th>
                  <th className="px-3 py-3 text-right">جلسات</th>
                  <th className="px-3 py-3 text-right">النتيجة</th>
                  <th className="px-3 py-3 text-right">الاستراتيجية</th>
                </tr>
              </thead>
              <tbody>
                {closed.map((t) => (
                  <tr key={t.id} className="border-t border-border hover:bg-panel2/50">
                    <td className="px-3 py-2.5">
                      <Link href={`/stock/${encodeURIComponent(t.symbol)}`} className="font-mono text-brand hover:underline">
                        {t.symbol}
                      </Link>
                      <div className="text-[11px] text-muted">{t.name_ar}</div>
                    </td>
                    <td className="px-3 py-2.5">
                      {fmtNum(t.entry)} <span className="text-[11px] text-muted">{t.entry_date}</span>
                    </td>
                    <td className="px-3 py-2.5">
                      {fmtNum(t.exit_price)} <span className="text-[11px] text-muted">{t.closed_date}</span>
                    </td>
                    <td className="px-3 py-2.5">{t.reason_ar ?? exitReasonLabel(t.reason)}</td>
                    <td className="px-3 py-2.5">{t.bars_held ?? "—"}</td>
                    <td className={`px-3 py-2.5 font-semibold ${pnlColor(t.realized_pnl)}`}>
                      {fmtR(t.realized_r)} <span className="text-xs">({fmtMoney(t.realized_pnl)})</span>
                    </td>
                    <td className="px-3 py-2.5 text-muted text-xs">{strategyLabel(t.strategy)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

function Stat({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div className="stat">
      <span className="stat-label">{label}</span>
      <span className={`stat-value ${accent ?? ""}`}>{value}</span>
    </div>
  );
}
