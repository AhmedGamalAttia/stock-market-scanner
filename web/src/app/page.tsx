import { OpportunityCard } from "@/components/opportunity-card";
import { getLastRun, getLatestSignals } from "@/lib/queries";
import { fmtDate } from "@/lib/utils";
import { supabaseConfigured } from "@/lib/supabase";

export const revalidate = 600;

export default async function Home() {
  if (!supabaseConfigured) {
    return <NotConfigured />;
  }

  const [signals, lastRun] = await Promise.all([getLatestSignals(50), getLastRun()]);

  return (
    <div className="space-y-6">
      <section className="panel p-6 flex flex-col sm:flex-row sm:items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold">فرص اليوم على البورصة المصرية</h1>
          <p className="text-muted mt-1">
            تم اكتشافها بمؤشرات فنية: اختراق 20 جلسة، تقاطع MACD، تقاطع ذهبى، ارتداد من تشبع البيع.
          </p>
        </div>
        <div className="text-sm text-muted text-right">
          {signals.length > 0 ? (
            <>
              <div>تاريخ المسح: <span className="text-text">{fmtDate(signals[0].signal_date)}</span></div>
              {lastRun && (
                <div className="text-xs mt-1">
                  آخر تشغيل: {fmtDate(lastRun.ran_at)} • {lastRun.symbols_total - lastRun.symbols_failed}/{lastRun.symbols_total} سهم
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
        <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {signals.map((s) => (
            <OpportunityCard key={s.id} s={s} />
          ))}
        </section>
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
        ضِف <code className="text-brand">NEXT_PUBLIC_SUPABASE_URL</code> و <code className="text-brand">NEXT_PUBLIC_SUPABASE_ANON_KEY</code> فى ملف <code>.env.local</code> ثم أعد التشغيل.
      </p>
    </div>
  );
}
