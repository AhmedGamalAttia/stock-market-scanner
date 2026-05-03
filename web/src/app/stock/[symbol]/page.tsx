import { notFound } from "next/navigation";
import { PriceChart } from "@/components/price-chart";
import { WatchlistButton } from "@/components/watchlist-button";
import {
  getPriceHistory,
  getSignalForSymbol,
  getStock,
} from "@/lib/queries";
import { fmtDate, fmtNum, rrRatio, scoreColor, setupLabel, trendBadge } from "@/lib/utils";

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
  const lastClose = prices.length ? prices[prices.length - 1].close : signal?.entry ?? 0;

  return (
    <div className="space-y-6">
      <header className="panel p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold">{stock?.name_ar ?? symbol}</h1>
            <span className={`chip ${trend.cls}`}>{trend.label}</span>
          </div>
          <p className="text-sm text-muted mt-1">
            {symbol}
            {stock?.sector ? ` • ${stock.sector}` : ""}
            {stock?.name_en ? ` • ${stock.name_en}` : ""}
          </p>
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
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 panel p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">خطة الصفقة</h2>
              <div className={`text-3xl font-bold ${scoreColor(signal.score)}`}>{signal.score}</div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <Stat label="دخول" value={fmtNum(signal.entry)} />
              <Stat label="وقف خسارة" value={fmtNum(signal.stop_loss)} accent="text-danger" />
              <Stat label="هدف 1" value={fmtNum(signal.target_1)} accent="text-success" />
              <Stat label="هدف 2" value={fmtNum(signal.target_2)} accent="text-success" />
            </div>

            <div className="grid grid-cols-3 gap-3 mt-3">
              <Stat label="نسبة العائد/المخاطرة" value={`${rrRatio(signal.entry, signal.stop_loss, signal.target_1).toFixed(2)} : 1`} />
              <Stat label="الصعود لهدف 1" value={`${(((signal.target_1 - signal.entry) / signal.entry) * 100).toFixed(2)}%`} accent="text-success" />
              <Stat label="المدة المتوقعة" value={`${signal.expected_days} جلسة`} />
            </div>

            <div className="mt-4 flex flex-wrap gap-1.5">
              {signal.setups.map((x) => (
                <span key={x} className="chip bg-brand/10 text-brand border-brand/30">
                  {setupLabel(x)}
                </span>
              ))}
            </div>

            {signal.rationale_ar && (
              <p className="mt-4 text-sm text-muted leading-relaxed">{signal.rationale_ar}</p>
            )}
          </div>

          <aside className="panel p-5 space-y-3">
            <h3 className="text-sm font-semibold text-muted uppercase">المؤشرات الفنية</h3>
            <Row label="RSI(14)" value={signal.rsi != null ? signal.rsi.toFixed(1) : "—"} />
            <Row label="MACD Histogram" value={signal.macd_hist != null ? signal.macd_hist.toFixed(3) : "—"} />
            <Row label="MA20" value={fmtNum(signal.ma20)} />
            <Row label="MA50" value={fmtNum(signal.ma50)} />
            <Row label="ATR(14)" value={signal.atr.toFixed(3)} />
            <Row label="Volume Z-score" value={signal.volume_z != null ? signal.volume_z.toFixed(2) : "—"} />
            <div className="text-xs text-muted pt-2 border-t border-border">
              تاريخ الإشارة: {fmtDate(signal.signal_date)}
            </div>
          </aside>
        </section>
      ) : (
        <div className="panel p-6 text-sm text-muted">
          لا توجد إشارة حالية على هذا السهم. الشارت يعرض البيانات التاريخية فقط.
        </div>
      )}
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

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-muted">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
