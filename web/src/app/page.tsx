import Link from "next/link";
import { ExitCard } from "@/components/exit-card";
import { OpportunitiesGrid } from "@/components/opportunities-grid";
import { PositionCard } from "@/components/position-card";
import { getBacktestIndex, getLatest, getMeta } from "@/lib/data";
import { fmtDate, fmtDateTime, fmtRelative, strategyLabel } from "@/lib/utils";

export default async function Home() {
  const [latest, meta, bt] = await Promise.all([getLatest(), getMeta(), getBacktestIndex()]);
  const buys = latest?.buys ?? [];
  const holds = latest?.holds ?? [];
  const exits = latest?.exits ?? [];
  const urgent = holds.filter((h) => h.pending_exit);
  const calm = holds.filter((h) => !h.pending_exit);
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
          {exits.length > 0 && (
            <Section
              emoji="🔴"
              title={`اخرج (${exits.length})`}
              hint="المراكز دى اتقفلت بقواعد الاستراتيجية فى جلسة اليوم. لو داخل فيها، اخرج على الافتتاح."
            >
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {exits.map((e) => (
                  <ExitCard key={e.id} e={e} />
                ))}
              </div>
            </Section>
          )}

          {urgent.length > 0 && (
            <Section
              emoji="⚠️"
              title={`اخرج بكرة على الافتتاح (${urgent.length})`}
              hint="الاتجاه انقلب على إقفال اليوم. الاستراتيجية بتبيع على افتتاح الجلسة الجاية."
            >
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {urgent.map((h) => (
                  <PositionCard key={h.id} h={h} />
                ))}
              </div>
            </Section>
          )}

          <Section
            emoji="🟢"
            title={`ادخل (${buys.length})`}
            hint="إشارات جديدة على إقفال اليوم. الدخول على افتتاح الجلسة الجاية بسعر الدخول أو أقل، والوقف من أول لحظة."
          >
            {buys.length === 0 ? (
              <div className="panel p-8 text-center">
                <div className="font-semibold mb-1">مفيش إشارات دخول جديدة النهاردة</div>
                <p className="text-muted text-sm max-w-lg mx-auto leading-relaxed">
                  ده طبيعى — الاستراتيجية بتدخل لما الاتجاه ينقلب لصاعد بس، وده بيحصل كام مرة فى الشهر على كل
                  الأسهم. الانتظار جزء من الخطة.
                </p>
              </div>
            ) : (
              <OpportunitiesGrid signals={buys} />
            )}
          </Section>

          <Section
            emoji="🔵"
            title={`استمر (${calm.length})`}
            hint="مراكز مفتوحة حسب الاستراتيجية. لو داخل فيها: سيبها شغالة، والتزم بالوقف المكتوب على كل كارت."
          >
            {calm.length === 0 ? (
              <div className="panel p-6 text-center text-muted text-sm">مفيش مراكز مفتوحة حالياً.</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {calm.map((h) => (
                  <PositionCard key={h.id} h={h} />
                ))}
              </div>
            )}
          </Section>

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

function Section({
  emoji,
  title,
  hint,
  children,
}: {
  emoji: string;
  title: string;
  hint: string;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-3">
      <div>
        <h2 className="text-xl font-bold">
          {emoji} {title}
        </h2>
        <p className="text-xs text-muted mt-0.5">{hint}</p>
      </div>
      {children}
    </section>
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
