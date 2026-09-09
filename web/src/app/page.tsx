import Link from "next/link";
import { TodayBoard } from "@/components/today-board";
import { getAllStocks, getBacktestIndex, getLatest, getMeta } from "@/lib/data";
import { fmtDate, fmtDateTime, fmtRelative, strategyLabel } from "@/lib/utils";

export default async function Home() {
  const [latest, meta, bt, stocks] = await Promise.all([
    getLatest(),
    getMeta(),
    getBacktestIndex(),
    getAllStocks(),
  ]);
  const buys = latest?.buys ?? [];
  const holds = latest?.holds ?? [];
  const exits = latest?.exits ?? [];
  const statusBySymbol = Object.fromEntries(stocks.map((s) => [s.symbol, s.sharia_status]));
  const live = bt?.strategies.find((s) => s.strategy === (latest?.strategy ?? bt?.recommended));

  return (
    <div className="space-y-5">
      <section className="panel p-6 flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold">قرارات اليوم — البورصة المصرية</h1>
          <p className="text-muted mt-1 text-sm leading-relaxed max-w-2xl">
            كل يوم بعد الإقفال: إيه اللى تدخله، إيه اللى تستمر فيه، وإيه اللى تخرج منه — بسعر دخول ووقف وأهداف
            محددة وحجم صفقة لرأس مال 20 ألف جنيه. القرارات بتتنفذ على افتتاح الجلسة التالية.
          </p>
        </div>
        <div className="text-sm text-muted text-right shrink-0">
          {latest?.date ? (
            <>
              <div>
                بيانات جلسة: <span className="text-text">{fmtDate(latest.date)}</span>
              </div>
              {meta && (
                <>
                  <div className="text-xs mt-1">
                    آخر تشغيل: <span className="text-text">{fmtDateTime(meta.ran_at)}</span>{" "}
                    <span className="text-muted">({fmtRelative(meta.ran_at)})</span>
                  </div>
                  <div className="text-xs mt-0.5">
                    <span className={meta.ok ? "text-success" : "text-danger"}>{meta.ok ? "● ناجح" : "● فشل"}</span>{" "}
                    • {meta.symbols_total - meta.symbols_failed}/{meta.symbols_total} سهم
                  </div>
                </>
              )}
            </>
          ) : (
            <span>لم يتم تشغيل المسح بعد</span>
          )}
        </div>
      </section>

      {latest && (
        <section className="panel p-4 flex flex-col md:flex-row md:items-center justify-between gap-3 border-brand/30">
          <div className="text-sm">
            <span className="text-muted">الاستراتيجية المُفعّلة: </span>
            <span className="font-semibold text-brand">{latest.strategy_label_ar ?? strategyLabel(latest.strategy)}</span>
            {live && (
              <span className="text-muted">
                {" "}— على 5 سنين بعد العمولة: نسبة نجاح{" "}
                <b className="text-text">{Math.round((live.full.win_rate ?? 0) * 100)}%</b>، معامل ربح{" "}
                <b className="text-text">{live.full.profit_factor ?? "—"}</b>، عائد سنوى على حساب 20 ألف{" "}
                <b className="text-text">{((live.portfolio_full.cagr_pct ?? 0) * 100).toFixed(1)}%</b> بأقصى تراجع{" "}
                <b className="text-text">{((live.portfolio_full.max_drawdown_pct ?? 0) * 100).toFixed(0)}%</b>
              </span>
            )}
          </div>
          <Link href="/performance" className="btn text-xs shrink-0">
            الأرقام كاملة ←
          </Link>
        </section>
      )}

      {!latest ? (
        <EmptyState
          title="البيانات لسه ما وصلتش"
          body="أول مسح يومى لسه ما اتنفذش. النتايج بتتحدث أوتوماتيك بعد إقفال البورصة."
        />
      ) : (
        <>
          <TodayBoard buys={buys} holds={holds} exits={exits} statusBySymbol={statusBySymbol} />

          <section className="panel p-5 text-sm leading-relaxed">
            <h3 className="font-semibold mb-2">إزاى تستخدم الصفحة دى (3 قواعد)</h3>
            <ol className="space-y-1.5 text-muted">
              <li>
                <b className="text-text">1.</b> افتحها مرة واحدة بعد الإقفال (أو استنى رسالة تليجرام). نفّذ قرارات
                بكرة على الافتتاح — مش مطلوب تتابع الشاشة.
              </li>
              <li>
                <b className="text-text">2.</b> الوقف مش اختيارى. الأرقام اللى فى صفحة الأداء اتحسبت بافتراض إنك
                بتخرج على الوقف كل مرة — من غيره الأرقام دى مالهاش معنى.
              </li>
              <li>
                <b className="text-text">3.</b> مش أكتر من 4 مراكز مفتوحة فى نفس الوقت برأس مال 20 ألف، وكل مركز
                بيخاطر 2% بس (400 جنيه). الكميات المكتوبة محسوبة على الأساس ده.
              </li>
            </ol>
          </section>
        </>
      )}
    </div>
  );
}

function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="panel p-10 text-center">
      <h2 className="text-lg font-semibold mb-2">{title}</h2>
      <p className="text-muted text-sm max-w-lg mx-auto leading-relaxed">{body}</p>
    </div>
  );
}
