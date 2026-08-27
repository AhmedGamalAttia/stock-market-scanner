import { EquityChart } from "@/components/equity-chart";
import { getBacktest, getBacktestIndex } from "@/lib/data";
import type { BacktestReport, StatBlock } from "@/lib/types";
import { exitReasonLabel, fmtDate, fmtMoney, fmtNum } from "@/lib/utils";

const pct = (x: number | null | undefined, d = 0) => (x == null ? "—" : `${(x * 100).toFixed(d)}%`);
const r = (x: number | null | undefined) => (x == null ? "—" : `${x > 0 ? "+" : ""}${x.toFixed(2)}R`);

export default async function PerformancePage() {
  const index = await getBacktestIndex();
  if (!index) {
    return <div className="panel p-8 text-center text-muted">لسه مفيش نتائج backtest.</div>;
  }
  const reports = (
    await Promise.all(index.strategies.map((s) => getBacktest(s.strategy)))
  ).filter((x): x is BacktestReport => Boolean(x));
  const capital = Number(reports[0]?.config?.capital ?? 20000);

  return (
    <div className="space-y-5">
      <header className="panel p-5">
        <h1 className="text-2xl font-bold">الأداء — الأرقام الحقيقية</h1>
        <p className="text-muted text-sm mt-1 leading-relaxed max-w-3xl">
          كل استراتيجية اتجربت على {index.strategies[0]?.full.n_trades ? "" : ""}
          {reports[0]?.per_ticker.length ?? 42} سهم من {fmtDate(index.period.from)} إلى {fmtDate(index.period.to)}{" "}
          بنفس القواعد اللى بتشتغل بيها الأداة النهاردة: الدخول على افتتاح اليوم التالى، الوقف قبل الأهداف،
          عمولة ثاندر 0.8% رايح جاى، وانزلاق 0.1%. <b className="text-text">خارج العينة</b> = آخر فترة من{" "}
          {fmtDate(index.period.in_sample_until)} لم تُستخدم فى أى قرار تصميم — وهى الرقم اللى تثق فيه.
        </p>
        <p className="text-xs text-warning mt-2">
          ⚠️ الفترة خارج العينة كانت سوق صاعد فى الأغلب. الأداء السابق لا يضمن المستقبل. مفيش استراتيجية بتكسب
          كل الصفقات — الفكرة إن المتوسط موجب بعد العمولة مع التزام صارم بالوقف.
        </p>
      </header>

      <section className="panel overflow-x-auto">
        <div className="px-4 pt-4 text-sm">
          <b>المقارنة</b> <span className="text-muted">— قاعدة الاختيار: {index.selection_rule}</span>
        </div>
        <table className="w-full text-sm mt-2">
          <thead className="bg-panel2 text-muted text-xs">
            <tr>
              <th className="px-3 py-2 text-right">الاستراتيجية</th>
              <th className="px-3 py-2 text-right">صفقات</th>
              <th className="px-3 py-2 text-right">نجاح</th>
              <th className="px-3 py-2 text-right">متوسط R</th>
              <th className="px-3 py-2 text-right">معامل ربح</th>
              <th className="px-3 py-2 text-right" title="خارج العينة">نجاح (خارج)</th>
              <th className="px-3 py-2 text-right">متوسط R (خارج)</th>
              <th className="px-3 py-2 text-right">حساب 20k — عائد سنوى (خارج)</th>
              <th className="px-3 py-2 text-right">أقصى تراجع (خارج)</th>
            </tr>
          </thead>
          <tbody>
            {index.strategies.map((s) => {
              const rec = s.strategy === index.recommended;
              return (
                <tr key={s.strategy} className={`border-t border-border ${rec ? "bg-brand/5" : ""}`}>
                  <td className="px-3 py-2.5">
                    <div className="font-semibold">{s.label_ar}</div>
                    {rec && <span className="chip bg-brand/15 text-brand border-brand/30 mt-1">✓ المُفعّلة</span>}
                  </td>
                  <td className="px-3 py-2.5">{s.full.n_trades ?? "—"}</td>
                  <td className="px-3 py-2.5">{pct(s.full.win_rate)}</td>
                  <td className="px-3 py-2.5">{r(s.full.avg_r)}</td>
                  <td className="px-3 py-2.5">{s.full.profit_factor ?? "—"}</td>
                  <td className="px-3 py-2.5">{pct(s.out_of_sample.win_rate)}</td>
                  <td className="px-3 py-2.5">{r(s.out_of_sample.avg_r)}</td>
                  <td className="px-3 py-2.5 font-semibold">{pct(s.portfolio_oos.cagr_pct, 1)}</td>
                  <td className="px-3 py-2.5">{pct(s.portfolio_oos.max_drawdown_pct)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <p className="text-[11px] text-muted px-4 py-3">
          R = وحدة المخاطرة (المسافة من الدخول للوقف). متوسط R موجب = فى المتوسط الصفقة بتكسب أكتر مما بتخاطر.
          معامل الربح = إجمالى الأرباح ÷ إجمالى الخسائر. حساب 20k = محاكاة حساب واحد بحد أقصى 4 مراكز مفتوحة
          و2% مخاطرة لكل صفقة.
        </p>
      </section>

      {reports
        .sort((a, b) => (a.strategy === index.recommended ? -1 : b.strategy === index.recommended ? 1 : 0))
        .map((rep) => (
          <details key={rep.strategy} className="panel" open={rep.strategy === index.recommended}>
            <summary className="cursor-pointer px-5 py-4 font-semibold flex items-center gap-2">
              {rep.label_ar}
              {rep.strategy === index.recommended && (
                <span className="chip bg-brand/15 text-brand border-brand/30">المُفعّلة</span>
              )}
              <span className="text-xs text-muted font-normal">— {rep.aggregate.full.n_trades} صفقة</span>
            </summary>
            <div className="px-5 pb-5 space-y-5">
              <div>
                <h3 className="text-sm font-semibold mb-2">
                  منحنى حساب 20 ألف جنيه (بحد أقصى {String(rep.config.max_concurrent ?? 4)} مراكز) — كامل الفترة
                </h3>
                <EquityChart curve={rep.portfolio.full.equity_curve} baseline={capital} />
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3">
                  <Stat label="صافى الربح" value={fmtMoney(rep.portfolio.full.stats.total_pnl)} />
                  <Stat label="عائد سنوى مركّب" value={pct(rep.portfolio.full.stats.cagr_pct, 1)} />
                  <Stat label="أقصى تراجع" value={pct(rep.portfolio.full.stats.max_drawdown_pct)} />
                  <Stat
                    label="صفقات منفذة / متخطاة"
                    value={`${rep.portfolio.full.stats.n_trades} / ${rep.portfolio.full.stats.skipped_signals ?? 0}`}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <StatsBlock title="كامل الفترة" s={rep.aggregate.full} />
                <StatsBlock title="داخل العينة" s={rep.aggregate.in_sample} />
                <StatsBlock title="خارج العينة ⭐" s={rep.aggregate.out_of_sample} highlight />
              </div>

              <div>
                <h3 className="text-sm font-semibold mb-2">أحسن وأسوأ الأسهم مع الاستراتيجية دى (كامل الفترة)</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                  <TickerTable rows={rep.per_ticker.slice(0, 8)} />
                  <TickerTable rows={[...rep.per_ticker].reverse().slice(0, 8)} />
                </div>
              </div>
            </div>
          </details>
        ))}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="stat">
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value}</span>
    </div>
  );
}

function StatsBlock({ title, s, highlight }: { title: string; s: StatBlock; highlight?: boolean }) {
  if (!s || !s.n_trades) {
    return (
      <div className="panel p-4 bg-panel2">
        <div className="font-semibold text-sm mb-2">{title}</div>
        <div className="text-muted text-xs">لا توجد صفقات</div>
      </div>
    );
  }
  const reasons = Object.entries(s.exit_reasons ?? {}).sort((a, b) => b[1] - a[1]);
  return (
    <div className={`panel p-4 ${highlight ? "border-brand/40 bg-brand/5" : "bg-panel2"}`}>
      <div className="font-semibold text-sm mb-3">{title}</div>
      <dl className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-xs">
        <Row k="صفقات" v={String(s.n_trades)} />
        <Row k="نسبة نجاح" v={pct(s.win_rate)} />
        <Row k="متوسط R" v={r(s.avg_r)} />
        <Row k="معامل ربح" v={String(s.profit_factor ?? "—")} />
        <Row k="متوسط الربح" v={r(s.avg_win_r)} />
        <Row k="متوسط الخسارة" v={r(s.avg_loss_r)} />
        <Row k="متوسط المدة" v={`${fmtNum(s.avg_hold_bars, 0)} جلسة`} />
        <Row k="وصل الهدف 1" v={pct(s.tp1_hit_rate)} />
        <Row k="أحسن / أسوأ" v={`${r(s.best_r)} / ${r(s.worst_r)}`} />
      </dl>
      {reasons.length > 0 && (
        <div className="mt-3 text-[11px] text-muted">
          الخروج: {reasons.map(([k, v]) => `${exitReasonLabel(k)} ${Math.round((v / s.n_trades) * 100)}%`).join(" • ")}
        </div>
      )}
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <>
      <dt className="text-muted">{k}</dt>
      <dd className="font-medium text-left" dir="ltr">
        {v}
      </dd>
    </>
  );
}

function TickerTable({ rows }: { rows: BacktestReport["per_ticker"] }) {
  return (
    <table className="w-full">
      <thead className="text-muted text-xs">
        <tr>
          <th className="text-right py-1">السهم</th>
          <th className="text-right py-1">صفقات</th>
          <th className="text-right py-1">نجاح</th>
          <th className="text-right py-1">متوسط R</th>
          <th className="text-right py-1">صافى</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((t) => (
          <tr key={t.symbol} className="border-t border-border">
            <td className="py-1 font-mono text-brand">{t.symbol}</td>
            <td className="py-1">{t.full.n_trades}</td>
            <td className="py-1">{pct(t.full.win_rate)}</td>
            <td className="py-1">{r(t.full.avg_r)}</td>
            <td className={`py-1 ${(t.full.total_pnl ?? 0) >= 0 ? "text-success" : "text-danger"}`}>
              {fmtMoney(t.full.total_pnl)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
