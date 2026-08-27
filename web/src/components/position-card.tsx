import Link from "next/link";
import type { Hold } from "@/lib/types";
import { fmtMoney, fmtNum, fmtR, fmtSignedPct, pnlColor } from "@/lib/utils";

export function PositionCard({ h }: { h: Hold }) {
  const pending = h.status === "pending";
  const urgent = Boolean(h.pending_exit);
  const border = urgent ? "border-warning/60" : h.bootstrap ? "border-border" : "border-brand/30";

  return (
    <Link
      href={`/stock/${encodeURIComponent(h.symbol)}`}
      className={`panel p-4 block hover:border-brand/50 transition ${border}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-bold truncate">{h.name_ar ?? h.symbol}</h3>
          <div className="text-[11px] text-muted mt-0.5">
            {h.symbol} • {pending ? `إشارة ${h.signal_date}` : `دخول ${h.entry_date}`} • {h.bars_held} جلسة
          </div>
        </div>
        {!pending && (
          <div className="text-left shrink-0">
            <div className={`text-xl font-bold leading-none ${pnlColor(h.change_pct)}`}>{fmtSignedPct(h.change_pct)}</div>
            <div className={`text-[11px] mt-1 ${pnlColor(h.unrealized_pnl)}`}>
              {fmtR(h.unrealized_r)} • {fmtMoney(h.unrealized_pnl)}
            </div>
          </div>
        )}
      </div>

      {pending ? (
        <div className="mt-3 text-sm text-brand">⏳ ينفذ الدخول عند افتتاح الجلسة القادمة قرب {fmtNum(h.entry)}</div>
      ) : (
        <div className="mt-3 grid grid-cols-4 gap-2 text-center text-xs">
          <div>
            <div className="text-[10px] text-muted">دخول</div>
            <div className="font-semibold">{fmtNum(h.entry)}</div>
          </div>
          <div>
            <div className="text-[10px] text-muted">الآن</div>
            <div className="font-semibold">{fmtNum(h.last_close)}</div>
          </div>
          <div>
            <div className="text-[10px] text-muted">وقف</div>
            <div className="font-semibold text-danger">{fmtNum(h.stop)}</div>
            <div className="text-[10px] text-muted">−{fmtNum(h.stop_distance_pct, 1)}%</div>
          </div>
          <div>
            <div className="text-[10px] text-muted">أهداف</div>
            <div className="font-semibold tracking-widest" dir="ltr">
              {(h.tp_hit ?? []).map((x, i) =>
                h.tps[i] == null ? null : (
                  <span key={i} className={x ? "text-success" : "text-muted"} title={fmtNum(h.tps[i])}>
                    {x ? "✓" : "○"}
                  </span>
                ),
              )}
            </div>
          </div>
        </div>
      )}

      {h.note_ar && (
        <div className={`mt-3 text-xs rounded-lg px-3 py-2 ${urgent ? "bg-warning/10 text-warning" : "bg-panel2 text-muted"}`}>
          {h.note_ar}
        </div>
      )}
    </Link>
  );
}
