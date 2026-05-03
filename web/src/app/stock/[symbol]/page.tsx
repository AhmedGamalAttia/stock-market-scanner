import { notFound } from "next/navigation";
import { PriceChart } from "@/components/price-chart";
import { WatchlistButton } from "@/components/watchlist-button";
import {
  getPriceHistory,
  getSignalForSymbol,
  getStock,
} from "@/lib/queries";
import {
  confidenceColor,
  fmtDate,
  fmtMoney,
  fmtNum,
  riskBadge,
  setupLabel,
  shariaBadge,
  trendBadge,
} from "@/lib/utils";

export const revalidate = 600;

export default async function StockPage({
  params,
}: {
  params: Promise<{ symbol: string }>;
}) {
  const { symbol: rawSymbol } = await params;
  const symbol = decodeURIComponent(rawSymbol);

  const [stock, signal, prices] = await Promise.all([
    getStock(symbol),
    getSignalForSymbol(symbol),
    getPriceHistory(symbol, 120),
  ]);

  if (!stock && !signal && prices.length === 0) {
    notFound();
  }

  const trend = trendBadge(signal?.trend ?? null);
  const risk = riskBadge(signal?.risk_class ?? null);
  const sharia = shariaBadge(stock?.sharia_status ?? null);
  const lastClose = prices.length ? prices[prices.length - 1].close : signal?.entry ?? 0;

  return (
    <div className="space-y-6">
      <header className="panel p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">{stock?.name_ar ?? symbol}</h1>
          <div className="flex items-center gap-1.5 mt-2 flex-wrap">
            <span className={`chip ${trend.cls}`}>{trend.label}</span>
            {signal && <span className={`chip ${risk.cls}`}>{risk.emoji} {risk.label}</span>}
            <span className={`chip ${sharia.cls}`}>{sharia.emoji} {sharia.label}</span>
            <span className="text-xs text-muted">
              {symbol}{stock?.sector ? ` • ${stock.sector}` : ""}
              {stock?.name_en ? ` • ${stock.name_en}` : ""}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-xs text-muted">آخر إغلاق</div>
            <div className="text-2xl font-bold">{fmtNum(lastClose ?? 0)}</div>
          </div>
          <WatchlistButton symbol={symbol} />
        </div>
      </header>

      <PriceChart
        prices={prices}
        entry={signal?.entry}
        stop={signal?.stop_loss}
        target1={signal?.target_1}
        target2={signal?.target_2}
      />

      {signal ? (
        <>
          {signal.warnings_ar && signal.warnings_ar.length > 0 && (
            <section className="panel border-warning/40 bg-warning/5 p-4">
              <h3 className="text-sm font-semibold text-warning mb-2">⚠️ تنبيهات قبل الدخول</h3>
              <ul className="space-y-1 text-sm">
                {signal.warnings_ar.map((w, i) => (
                  <li key={i} className="text-warning/90">• {w}</li>
                ))}
              </ul>
            </section>
          )}

          <section className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Trade Plan */}
            <div className="lg:col-span-2 panel p-5">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h2 className="text-lg font-semibold">خطة الصفقة</h2>
                  <p className="text-xs text-muted mt-1">مبنية على ATR — تذبذب السهم الفعلى</p>
                </div>
                <div className="text-right">
                  <div className={`text-3xl font-bold leading-none ${confidenceColor(signal.confidence)}`}>
                    {signal.confidence ?? signal.score}%
                  </div>
                  <div className="text-[10px] text-muted mt-1">نسبة الثقة</div>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <Stat label="دخول" value={fmtNum(signal.entry)} hint="ادخل عند هذا السعر أو أقل" />
                <Stat label="وقف خسارة" value={fmtNum(signal.stop_loss)} accent="text-danger" hint="اخرج فوراً لو وصله" />
                <Stat label="هدف 1" value={fmtNum(signal.target_1)} accent="text-success" hint="بِع 50% وحرّك الوقف" />
                <Stat label="هدف 2" value={fmtNum(signal.target_2)} accent="text-success" hint="بِع الباقى" />
              </div>

              <div className="grid grid-cols-3 gap-3 mt-3">
                <Stat label="R:R هدف 1" value={(signal.rr_t1 ?? 0).toFixed(2)} accent={(signal.rr_t1 ?? 0) >= 1.5 ? "text-success" : "text-warning"} />
                <Stat label="R:R هدف 2" value={(signal.rr_t2 ?? 0).toFixed(2)} accent="text-success" />
                <Stat label="مدة قصوى" value={`${signal.expected_days} جلسة`} />
              </div>

              {/* Position sizing for 20K capital */}
              {signal.suggested_shares_20k != null && signal.suggested_shares_20k > 0 && (
                <div className="mt-4 p-4 bg-brand/5 border border-brand/30 rounded-xl">
                  <h3 className="text-sm font-semibold text-brand mb-3">حجم الصفقة المقترح لرأس مال 20 ألف ج (مخاطرة 2%)</h3>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                    <div>
                      <div className="text-xs text-muted">عدد الأسهم</div>
                      <div className="font-semibold text-lg">{signal.suggested_shares_20k}</div>
                    </div>
                    <div>
                      <div className="text-xs text-muted">قيمة الصفقة</div>
                      <div className="font-semibold text-lg">{fmtMoney(signal.suggested_value_20k)}</div>
                    </div>
                    <div>
                      <div className="text-xs text-muted">أقصى خسارة</div>
                      <div className="font-semibold text-lg text-danger">{fmtMoney(signal.max_loss_20k)}</div>
                    </div>
                    <div>
                      <div className="text-xs text-muted">ربح هدف 1 (نصف)</div>
                      <div className="font-semibold text-lg text-success">
                        {fmtMoney(((signal.suggested_shares_20k ?? 0) * (signal.target_1 - signal.entry)) / 2)}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Setups */}
              <div className="mt-4 flex flex-wrap gap-1.5">
                {signal.setups.map((x) => (
                  <span key={x} className="chip bg-brand/10 text-brand border-brand/30">
                    {setupLabel(x)}
                  </span>
                ))}
              </div>

              {/* Strategy narrative */}
              {signal.strategy_ar && (
                <div className="mt-4 p-4 bg-panel2 rounded-xl border border-border">
                  <h3 className="text-sm font-semibold text-muted mb-2 uppercase">الإستراتيجية بالتفصيل</h3>
                  <p className="text-sm leading-relaxed">{signal.strategy_ar}</p>
                </div>
              )}

              {/* Execution playbook */}
              <div className="mt-4 p-4 bg-panel2 rounded-xl border border-border">
                <h3 className="text-sm font-semibold text-muted mb-3 uppercase">خطة التنفيذ خطوة بخطوة</h3>
                <ol className="space-y-2 text-sm">
                  <li><span className="text-brand font-bold">1.</span> ادخل اليوم أو غداً عند سعر <span className="font-mono text-brand">{fmtNum(signal.entry)}</span> أو أقل بـ 0.5%.</li>
                  <li><span className="text-brand font-bold">2.</span> ضع وقف خسارة فورى عند <span className="font-mono text-danger">{fmtNum(signal.stop_loss)}</span> — التزم به مهما حدث.</li>
                  <li><span className="text-brand font-bold">3.</span> عند الوصول لـ <span className="font-mono text-success">{fmtNum(signal.target_1)}</span>: بِع 50% من المركز وحرّك وقف الخسارة لسعر الدخول (Break-even).</li>
                  <li><span className="text-brand font-bold">4.</span> اترك النصف المتبقى ليصل لـ <span className="font-mono text-success">{fmtNum(signal.target_2)}</span> أو يتفعّل الوقف الجديد.</li>
                  <li><span className="text-brand font-bold">5.</span> لو السعر لم يتحرك بشكل ملحوظ خلال {Math.ceil(signal.expected_days / 2)} جلسة، اخرج بسعر التكلفة. الإشارة فقدت زخمها.</li>
                </ol>
              </div>
            </div>

            {/* Side panel: technical readouts + meta */}
            <aside className="space-y-4">
              <div className="panel p-5 space-y-3">
                <h3 className="text-sm font-semibold text-muted uppercase">المؤشرات الفنية</h3>
                <Row label="RSI(14)" value={signal.rsi != null ? signal.rsi.toFixed(1) : "—"} />
                <Row label="MACD Histogram" value={signal.macd_hist != null ? signal.macd_hist.toFixed(3) : "—"} />
                <Row label="MA20" value={fmtNum(signal.ma20)} />
                <Row label="MA50" value={fmtNum(signal.ma50)} />
                <Row label="ATR(14)" value={`${signal.atr.toFixed(3)} (${((signal.atr_pct ?? 0) * 100).toFixed(2)}%)`} />
                <Row label="Volume Z-score" value={signal.volume_z != null ? signal.volume_z.toFixed(2) : "—"} />
              </div>

              <div className="panel p-5 space-y-3">
                <h3 className="text-sm font-semibold text-muted uppercase">معلومات السهم</h3>
                <Row label="السيولة اليومية" value={fmtMoney(signal.adv_20)} />
                <Row label="القطاع" value={stock?.sector ?? "—"} />
                <Row label="الحالة الشرعية" value={sharia.short} />
                <Row label="نسبة الصعود لهدف 1" value={`+${(((signal.target_1 - signal.entry) / signal.entry) * 100).toFixed(2)}%`} />
                <Row label="نسبة الخسارة المحتملة" value={`-${(((signal.entry - signal.stop_loss) / signal.entry) * 100).toFixed(2)}%`} />
                <div className="text-xs text-muted pt-2 border-t border-border">
                  تاريخ الإشارة: {fmtDate(signal.signal_date)}
                </div>
              </div>
            </aside>
          </section>
        </>
      ) : (
        <div className="panel p-6 text-sm text-muted">
          لا توجد إشارة حالية على هذا السهم. الشارت يعرض البيانات التاريخية فقط.
        </div>
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  accent,
  hint,
}: {
  label: string;
  value: string;
  accent?: string;
  hint?: string;
}) {
  return (
    <div className="stat">
      <span className="stat-label">{label}</span>
      <span className={`stat-value ${accent ?? ""}`}>{value}</span>
      {hint && <span className="text-[10px] text-muted leading-tight">{hint}</span>}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-muted">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
