import Link from "next/link";
import { notFound } from "next/navigation";
import { CandlesChart } from "@/components/candles-chart";
import { PositionCard } from "@/components/position-card";
import { WatchlistButton } from "@/components/watchlist-button";
import {
  getHoldForSymbol,
  getPriceFile,
  getSignalForSymbol,
  getStock,
  listSymbols,
} from "@/lib/data";
import {
  confidenceColor,
  fmtDate,
  fmtMoney,
  fmtNum,
  riskBadge,
  setupLabel,
  shariaBadge,
  strategyLabel,
  trendBadge,
} from "@/lib/utils";

// Fully static: one page per tracked symbol, rebuilt on every data commit.
export const dynamicParams = false;

export async function generateStaticParams() {
  const symbols = await listSymbols();
  return symbols.map((symbol) => ({ symbol }));
}

export default async function StockPage({ params }: { params: Promise<{ symbol: string }> }) {
  const { symbol: rawSymbol } = await params;
  const symbol = decodeURIComponent(rawSymbol);

  const [stock, signal, hold, priceFile] = await Promise.all([
    getStock(symbol),
    getSignalForSymbol(symbol),
    getHoldForSymbol(symbol),
    getPriceFile(symbol),
  ]);
  const bars = priceFile?.bars.slice(-420) ?? [];

  if (!stock && !signal && bars.length === 0) {
    notFound();
  }

  const trend = trendBadge(signal?.trend ?? null);
  const risk = riskBadge(signal?.risk_class ?? null);
  const sharia = shariaBadge(stock?.sharia_status ?? null);
  const lastBar = bars[bars.length - 1];
  const lastClose = lastBar?.c ?? signal?.entry ?? 0;
  const targets = signal ? [signal.target_1, signal.target_2, signal.target_3 ?? null] : hold ? hold.tps : [];
  const entry = signal?.entry ?? hold?.entry ?? null;
  const stop = signal?.stop_loss ?? hold?.stop ?? null;

  return (
    <div className="space-y-6">
      <header className="panel p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">{stock?.name_ar ?? symbol}</h1>
          <div className="flex items-center gap-1.5 mt-2 flex-wrap">
            {signal && <span className={`chip ${trend.cls}`}>{trend.label}</span>}
            {signal && <span className={`chip ${risk.cls}`}>{risk.emoji} {risk.label}</span>}
            <span className={`chip ${sharia.cls}`}>{sharia.emoji} {sharia.label}</span>
            {hold && (
              <span className="chip bg-brand/10 text-brand border-brand/30">
                🔵 مركز {hold.status === "pending" ? "قيد التنفيذ" : "مفتوح"}
              </span>
            )}
            <span className="text-xs text-muted">
              {symbol}
              {stock?.sector ? ` • ${stock.sector}` : ""}
              {stock?.name_en ? ` • ${stock.name_en}` : ""}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-xs text-muted">آخر إغلاق {lastBar ? `(${lastBar.d})` : ""}</div>
            <div className="text-2xl font-bold">{fmtNum(lastClose)}</div>
          </div>
          <WatchlistButton symbol={symbol} />
        </div>
      </header>

      <CandlesChart bars={bars} entry={entry} stop={stop} targets={targets} />

      {hold && !signal && (
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 space-y-3">
            <h2 className="text-lg font-semibold">المركز الحالى</h2>
            <PositionCard h={hold} />
            <div className="panel p-4 text-sm leading-relaxed text-muted">
              <b className="text-text">إيه اللى بيحصل دلوقتى:</b> السهم فى اتجاه صاعد حسب السوبرترند. الخط الأخضر
              تحت السعر هو الوقف المتحرك — لو السعر قفل تحته الاستراتيجية بتخرج على افتتاح اليوم التالى وهتلاقى
              السهم فى قسم &quot;اخرج&quot; فى الصفحة الرئيسية ورسالة تليجرام.
              {hold.bootstrap && (
                <>
                  {" "}
                  <b className="text-warning">تنبيه:</b> ده مركز دخل قبل ما الأداة تشتغل — معروض للمتابعة فقط، مش
                  توصية بالدخول الآن.
                </>
              )}
            </div>
          </div>
          <aside className="panel p-5 space-y-3">
            <h3 className="text-sm font-semibold text-muted uppercase">مستويات المركز</h3>
            <Row label="دخول" value={fmtNum(hold.entry)} />
            <Row label="وقف" value={fmtNum(hold.stop)} />
            {hold.tps.map((t, i) =>
              t == null ? null : (
                <Row key={i} label={`هدف ${i + 1} ${hold.tp_hit[i] ? "✓" : ""}`} value={fmtNum(t)} />
              ),
            )}
            <Row label="الكمية (لـ 20 ألف)" value={`${hold.shares_open ?? hold.shares ?? "—"} سهم`} />
          </aside>
        </section>
      )}

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
                  <p className="text-xs text-muted mt-1">
                    {strategyLabel(signal.strategy)} • إشارة {fmtDate(signal.signal_date)}
                  </p>
                </div>
                <div className="text-right">
                  <div className={`text-3xl font-bold leading-none ${confidenceColor(signal.confidence)}`}>
                    {signal.confidence ?? signal.score}%
                  </div>
                  <div className="text-[10px] text-muted mt-1">نسبة الثقة</div>
                </div>
              </div>

              {signal.rationale_ar && (
                <div className="mb-4 text-sm text-brand bg-brand/5 border border-brand/20 rounded-xl px-4 py-2.5">
                  💡 {signal.rationale_ar}
                </div>
              )}

              <div className={`grid grid-cols-2 ${signal.target_3 ? "sm:grid-cols-5" : "sm:grid-cols-4"} gap-3`}>
                <Stat label="دخول" value={fmtNum(signal.entry)} hint="على الافتتاح، عند هذا السعر أو أقل" />
                <Stat label="وقف خسارة" value={fmtNum(signal.stop_loss)} accent="text-danger" hint="اخرج فوراً لو وصله" />
                <Stat label="هدف 1" value={fmtNum(signal.target_1)} accent="text-success" hint={signal.target_3 ? "بِع الثلث" : "بِع النصف وحرّك الوقف"} />
                <Stat label="هدف 2" value={fmtNum(signal.target_2)} accent="text-success" hint={signal.target_3 ? "بِع الثلث" : "بِع الباقى"} />
                {signal.target_3 && <Stat label="هدف 3" value={fmtNum(signal.target_3)} accent="text-success" hint="بِع الباقى" />}
              </div>

              <div className="grid grid-cols-3 gap-3 mt-3">
                <Stat label="R:R هدف 1" value={(signal.rr_t1 ?? 0).toFixed(2)} accent={(signal.rr_t1 ?? 0) >= 1 ? "text-success" : "text-warning"} />
                <Stat label="R:R هدف 2" value={(signal.rr_t2 ?? 0).toFixed(2)} accent="text-success" />
                <Stat label="المدة المتوقعة" value={`~${signal.expected_days} جلسة`} />
              </div>

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
                      <div className="text-xs text-muted">ربح لو اتحققت كل الأهداف</div>
                      <div className="font-semibold text-lg text-success">
                        {fmtMoney(
                          ((signal.suggested_shares_20k ?? 0) *
                            ((signal.target_1 - signal.entry) + (signal.target_2 - signal.entry) + ((signal.target_3 ?? signal.target_2) - signal.entry))) /
                            3,
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div className="mt-4 flex flex-wrap gap-1.5">
                {signal.setups.map((x) => (
                  <span key={x} className="chip bg-brand/10 text-brand border-brand/30">
                    {setupLabel(x)}
                  </span>
                ))}
              </div>

              {signal.strategy_ar && (
                <div className="mt-4 p-4 bg-panel2 rounded-xl border border-border">
                  <h3 className="text-sm font-semibold text-muted mb-2 uppercase">الشرح بالتفصيل</h3>
                  <p className="text-sm leading-relaxed">{signal.strategy_ar}</p>
                </div>
              )}

              <div className="mt-4 p-4 bg-panel2 rounded-xl border border-border">
                <h3 className="text-sm font-semibold text-muted mb-3 uppercase">خطة التنفيذ خطوة بخطوة</h3>
                <ol className="space-y-2 text-sm">
                  <li><span className="text-brand font-bold">1.</span> على افتتاح الجلسة الجاية ادخل بـ {signal.suggested_shares_20k} سهم عند <span className="font-mono text-brand">{fmtNum(signal.entry)}</span> أو أقل. لو فتح أعلى بأكتر من 1% استنى ولا تطاردش.</li>
                  <li><span className="text-brand font-bold">2.</span> حط أمر وقف خسارة فوراً عند <span className="font-mono text-danger">{fmtNum(signal.stop_loss)}</span> — ده خط السوبرترند، ومفيش نقاش فيه.</li>
                  {signal.target_3 ? (
                    <>
                      <li><span className="text-brand font-bold">3.</span> عند <span className="font-mono text-success">{fmtNum(signal.target_1)}</span> بِع الثلث، عند <span className="font-mono text-success">{fmtNum(signal.target_2)}</span> بِع الثلث التانى، وعند <span className="font-mono text-success">{fmtNum(signal.target_3)}</span> بِع الباقى.</li>
                      <li><span className="text-brand font-bold">4.</span> فى أى وقت لو السهم قفل تحت خط السوبرترند (هيظهر فى قسم &quot;اخرج&quot; ورسالة تليجرام) — اخرج بالكامل على الافتتاح التالى حتى لو الأهداف ما اتحققتش.</li>
                    </>
                  ) : (
                    <>
                      <li><span className="text-brand font-bold">3.</span> عند <span className="font-mono text-success">{fmtNum(signal.target_1)}</span>: بِع النصف وحرّك الوقف لسعر الدخول.</li>
                      <li><span className="text-brand font-bold">4.</span> اترك النصف المتبقى ليصل لـ <span className="font-mono text-success">{fmtNum(signal.target_2)}</span> أو يتفعّل الوقف الجديد.</li>
                      <li><span className="text-brand font-bold">5.</span> لو السعر لم يتحرك خلال {signal.max_hold ?? signal.expected_days * 2} جلسة، اخرج. الإشارة فقدت زخمها.</li>
                    </>
                  )}
                </ol>
              </div>
            </div>

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
              </div>
            </aside>
          </section>
        </>
      ) : !hold ? (
        <div className="panel p-6 text-sm text-muted leading-relaxed">
          لا توجد إشارة حالية على هذا السهم. الشارت بيعرض السوبرترند: لما ينقلب من أحمر لأخضر هتظهر إشارة دخول فى
          الصفحة الرئيسية. شوف{" "}
          <Link href="/performance" className="text-brand hover:underline">صفحة الأداء</Link> لتعرف نتائج الاستراتيجية
          على هذا السهم تاريخياً.
        </div>
      ) : null}
    </div>
  );
}

function Stat({ label, value, accent, hint }: { label: string; value: string; accent?: string; hint?: string }) {
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
