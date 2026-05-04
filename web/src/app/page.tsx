import { OpportunitiesGrid } from "@/components/opportunities-grid";
import { getLastRun, getLatestSignals } from "@/lib/queries";
import { fmtDate, fmtDateTime } from "@/lib/utils";
import { supabaseConfigured } from "@/lib/supabase";

export const revalidate = 600;

export default async function Home() {
  if (!supabaseConfigured) {
    return <NotConfigured />;
  }

  const [signals, lastRun] = await Promise.all([getLatestSignals(50), getLastRun()]);

  return (
    <div className="space-y-4">
      <section className="panel p-6 flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold">فرص اليوم على البورصة المصرية</h1>
          <p className="text-muted mt-1 text-sm leading-relaxed max-w-2xl">
            توصيات مرتبة حسب نسبة الثقة، مع تصنيف للمخاطرة، حالة شرعية، خطة دخول/خروج
            كاملة، وحجم صفقة محسوب لرأس مال 20 ألف جنيه. كل توصية مرّت بـ 6 طبقات فلترة:
            قوة الإشارة، السيولة، الاتجاه العام، نسبة العائد/المخاطرة، وتأكيدات متعددة.
          </p>
        </div>
        <div className="text-sm text-muted text-right shrink-0">
          {signals.length > 0 ? (
            <>
              <div>
                تاريخ المسح:{" "}
                <span className="text-text">{fmtDate(signals[0].signal_date)}</span>
              </div>
              {lastRun && (
                <div className="text-xs mt-1">
                  آخر تشغيل: {fmtDateTime(lastRun.ran_at)} •{" "}
                  {lastRun.symbols_total - lastRun.symbols_failed}/
                  {lastRun.symbols_total} سهم
                </div>
              )}
            </>
          ) : (
            <span>لم يتم تشغيل المسح بعد</span>
          )}
        </div>
      </section>

      {signals.length === 0 ? (
        <EmptyState />
      ) : (
        <OpportunitiesGrid signals={signals} />
      )}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="panel p-10 text-center">
      <h2 className="text-lg font-semibold mb-2">لا توجد إشارات بعد</h2>
      <p className="text-muted text-sm max-w-lg mx-auto">
        شغّل الـ Scanner مرة على الأقل لإنشاء بيانات. شوف الـ README للخطوات.
      </p>
      <pre className="mt-4 inline-block text-left text-xs bg-panel2 border border-border rounded-xl p-4 text-brand">
        cd scanner{"\n"}python main.py
      </pre>
    </div>
  );
}

function NotConfigured() {
  return (
    <div className="panel p-10 text-center">
      <h2 className="text-lg font-semibold mb-2">Supabase غير مهيّأ</h2>
      <p className="text-muted text-sm max-w-lg mx-auto">
        ضِف <code className="text-brand">NEXT_PUBLIC_SUPABASE_URL</code> و{" "}
        <code className="text-brand">NEXT_PUBLIC_SUPABASE_ANON_KEY</code> فى ملف{" "}
        <code>.env.local</code> ثم أعد التشغيل.
      </p>
    </div>
  );
}
