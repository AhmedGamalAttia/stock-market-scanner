import { OpportunitiesGrid } from "@/components/opportunities-grid";
import { getLatest, getMeta } from "@/lib/data";
import { fmtDate, fmtDateTime, fmtRelative } from "@/lib/utils";

export default async function Home() {
  const [latest, meta] = await Promise.all([getLatest(), getMeta()]);
  const signals = latest?.buys ?? [];

  return (
    <div className="space-y-4">
      <section className="panel p-6 flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold">فرص اليوم على البورصة المصرية</h1>
          <p className="text-muted mt-1 text-sm leading-relaxed max-w-2xl">
            توصيات مرتبة حسب نسبة الثقة، مع تصنيف للمخاطرة، حالة شرعية، خطة دخول/خروج
            كاملة، وحجم صفقة محسوب لرأس مال 20 ألف جنيه. كل توصية مرّت بخمس طبقات فلترة:
            قوة الإشارة، السيولة، الاتجاه العام، نسبة العائد/المخاطرة، وتأكيدات متعددة.
          </p>
        </div>
        <div className="text-sm text-muted text-right shrink-0">
          {latest?.date ? (
            <>
              <div>
                بيانات جلسة:{" "}
                <span className="text-text">{fmtDate(latest.date)}</span>
              </div>
              {meta && (
                <>
                  <div className="text-xs mt-1">
                    آخر تشغيل:{" "}
                    <span className="text-text">{fmtDateTime(meta.ran_at)}</span>{" "}
                    <span className="text-muted">({fmtRelative(meta.ran_at)})</span>
                  </div>
                  <div className="text-xs mt-0.5">
                    <span className={meta.ok ? "text-success" : "text-danger"}>
                      {meta.ok ? "● ناجح" : "● فشل"}
                    </span>{" "}
                    • {meta.signals_emitted} إشارة •{" "}
                    {meta.symbols_total - meta.symbols_failed}/{meta.symbols_total} سهم
                  </div>
                </>
              )}
            </>
          ) : (
            <span>لم يتم تشغيل المسح بعد</span>
          )}
        </div>
      </section>

      {!latest ? (
        <EmptyState
          title="البيانات لسه ما وصلتش"
          body="أول مسح يومى لسه ما اتنفذش. النتايج بتتحدث أوتوماتيك بعد إقفال البورصة."
        />
      ) : signals.length === 0 ? (
        <EmptyState
          title="لا توجد إشارات جديدة اليوم"
          body="مفيش سهم حقق شروط الدخول فى جلسة اليوم. ده طبيعى — أغلب الأيام مفيهاش فرص واضحة، والانتظار جزء من الخطة."
        />
      ) : (
        <OpportunitiesGrid signals={signals} />
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
