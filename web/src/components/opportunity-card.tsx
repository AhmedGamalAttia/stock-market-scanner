import Link from "next/link";
import type { SignalWithStock } from "@/lib/types";
import { fmtNum, rrRatio, scoreColor, setupLabel, trendBadge } from "@/lib/utils";

export function OpportunityCard({ s }: { s: SignalWithStock }) {
  const trend = trendBadge(s.trend);
  const rr = rrRatio(s.entry, s.stop_loss, s.target_1);
  const upside = ((s.target_1 - s.entry) / s.entry) * 100;
  const riskPct = ((s.entry - s.stop_loss) / s.entry) * 100;

  return (
    <Link
      href={`/stock/${encodeURIComponent(s.symbol)}`}
      className="panel p-5 hover:border-brand/40 transition block"
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold">{s.stock?.name_ar ?? s.symbol}</h3>
            <span className={`chip ${trend.cls}`}>{trend.label}</span>
          </div>
          <p className="text-xs text-muted mt-1">
            {s.symbol}
            {s.stock?.sector ? ` • ${s.stock.sector}` : ""}
          </p>
        </div>
        <div className="text-center">
          <div className={`text-2xl font-bold leading-none ${scoreColor(s.score)}`}>{s.score}</div>
          <div className="text-[10px] text-muted mt-0.5">SCORE</div>
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5 mb-4">
        {s.setups.map((x) => (
          <span key={x} className="chip bg-brand/10 text-brand border-brand/30">
            {setupLabel(x)}
          </span>
        ))}
      </div>

      <div className="grid grid-cols-4 gap-2 text-center text-sm">
        <div>
          <div className="text-[10px] text-muted">دخول</div>
          <div className="font-semibold">{fmtNum(s.entry)}</div>
        </div>
        <div>
          <div className="text-[10px] text-muted">وقف</div>
          <div className="font-semibold text-danger">{fmtNum(s.stop_loss)}</div>
        </div>
        <div>
          <div className="text-[10px] text-muted">هدف 1</div>
          <div className="font-semibold text-success">{fmtNum(s.target_1)}</div>
        </div>
        <div>
          <div className="text-[10px] text-muted">هدف 2</div>
          <div className="font-semibold text-success">{fmtNum(s.target_2)}</div>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-border flex items-center justify-between text-xs text-muted">
        <span>R:R = {rr.toFixed(1)}</span>
        <span>الصعود ~{upside.toFixed(1)}%</span>
        <span>المخاطرة ~{riskPct.toFixed(1)}%</span>
        <span>{s.expected_days} جلسة</span>
      </div>
    </Link>
  );
}
