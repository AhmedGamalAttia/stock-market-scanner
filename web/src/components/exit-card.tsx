import Link from "next/link";
import type { ExitRow } from "@/lib/types";
import { fmtMoney, fmtNum, fmtR, pnlColor } from "@/lib/utils";

export function ExitCard({ e }: { e: ExitRow }) {
  return (
    <Link
      href={`/stock/${encodeURIComponent(e.symbol)}`}
      className="panel p-4 block border-danger/30 hover:border-danger/60 transition"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-bold truncate">{e.name_ar ?? e.symbol}</h3>
          <div className="text-[11px] text-muted mt-0.5">
            {e.symbol} • {e.entry_date ?? "—"} ← {e.exit_date ?? "—"} • {e.bars_held ?? "—"} جلسة
          </div>
        </div>
        <div className="text-left shrink-0">
          <div className={`text-xl font-bold leading-none ${pnlColor(e.realized_r)}`}>{fmtR(e.realized_r)}</div>
          <div className={`text-[11px] mt-1 ${pnlColor(e.realized_pnl)}`}>{fmtMoney(e.realized_pnl)}</div>
        </div>
      </div>
      <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
        <div>
          <div className="text-[10px] text-muted">دخول</div>
          <div className="font-semibold">{fmtNum(e.entry)}</div>
        </div>
        <div>
          <div className="text-[10px] text-muted">خروج</div>
          <div className="font-semibold">{fmtNum(e.exit_price)}</div>
        </div>
        <div>
          <div className="text-[10px] text-muted">أهداف</div>
          <div className="font-semibold tracking-widest" dir="ltr">
            {(e.tp_hit ?? []).map((x, i) => (
              <span key={i} className={x ? "text-success" : "text-muted"}>
                {x ? "✓" : "○"}
              </span>
            ))}
          </div>
        </div>
      </div>
      <div className="mt-3 text-xs rounded-lg px-3 py-2 bg-danger/10 text-danger">🔴 {e.reason_ar ?? e.reason}</div>
    </Link>
  );
}
