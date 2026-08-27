import Link from "next/link";
import type { SignalWithStock } from "@/lib/types";
import {
  confidenceColor,
  fmtMoney,
  fmtNum,
  riskBadge,
  setupLabel,
  shariaBadge,
} from "@/lib/utils";

export function OpportunityCard({ s }: { s: SignalWithStock }) {
  const risk = riskBadge(s.risk_class);
  const sharia = shariaBadge(s.stock?.sharia_status ?? null);
  const upside = ((s.target_1 - s.entry) / s.entry) * 100;
  const riskPct = ((s.entry - s.stop_loss) / s.entry) * 100;

  return (
    <Link
      href={`/stock/${encodeURIComponent(s.symbol)}`}
      className="panel p-5 hover:border-brand/40 transition block"
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-lg font-bold truncate">{s.stock?.name_ar ?? s.symbol}</h3>
          </div>
          <div className="flex items-center gap-1.5 mt-1.5 flex-wrap">
            <span className={`chip ${risk.cls}`}>
              {risk.emoji} {risk.label}
            </span>
            <span className={`chip ${sharia.cls}`} title={sharia.label}>
              {sharia.emoji} {sharia.short}
            </span>
            <span className="text-[11px] text-muted">
              {s.symbol}{s.stock?.sector ? ` • ${s.stock.sector}` : ""}
            </span>
          </div>
        </div>
        <div className="text-center shrink-0">
          <div className={`text-3xl font-bold leading-none ${confidenceColor(s.confidence)}`}>
            {s.confidence ?? s.score}%
          </div>
          <div className="text-[10px] text-muted mt-1">ثقة</div>
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5 mb-3">
        {s.setups.map((x) => (
          <span key={x} className="chip bg-brand/10 text-brand border-brand/30">
            {setupLabel(x)}
          </span>
        ))}
      </div>

      {s.rationale_ar && (
        <div className="text-xs text-muted mb-3 leading-relaxed">💡 {s.rationale_ar}</div>
      )}

      <div className={`grid ${s.target_3 ? "grid-cols-5" : "grid-cols-4"} gap-2 text-center text-sm`}>
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
        {s.target_3 && (
          <div>
            <div className="text-[10px] text-muted">هدف 3</div>
            <div className="font-semibold text-success">{fmtNum(s.target_3)}</div>
          </div>
        )}
      </div>

      {s.suggested_shares_20k != null && s.suggested_shares_20k > 0 && (
        <div className="mt-3 p-2.5 bg-brand/5 border border-brand/20 rounded-lg text-xs">
          <span className="text-muted">لـ 20 ألف ج: </span>
          <span className="font-semibold">{s.suggested_shares_20k} سهم</span>
          <span className="text-muted"> ≈ </span>
          <span className="font-semibold">{fmtMoney(s.suggested_value_20k)}</span>
          <span className="text-muted"> • أقصى خسارة </span>
          <span className="text-danger font-semibold">{fmtMoney(s.max_loss_20k)}</span>
        </div>
      )}

      <div className="mt-3 pt-3 border-t border-border flex items-center justify-between text-xs text-muted">
        <span>R:R = {(s.blended_rr ?? 0).toFixed(1)}</span>
        <span>صعود ~{upside.toFixed(1)}%</span>
        <span>مخاطرة ~{riskPct.toFixed(1)}%</span>
        <span>{s.expected_days} جلسة</span>
      </div>
    </Link>
  );
}
