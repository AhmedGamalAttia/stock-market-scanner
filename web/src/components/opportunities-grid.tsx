"use client";

import { useMemo, useState } from "react";
import type { SignalWithStock } from "@/lib/types";
import { OpportunityCard } from "./opportunity-card";

type SharaFilter = "all" | "halal_only" | "exclude_haram";
type RiskFilter = "all" | "محافظ" | "متوسط" | "جرىء";

export function OpportunitiesGrid({ signals }: { signals: SignalWithStock[] }) {
  const [sharia, setSharia] = useState<SharaFilter>("all");
  const [risk, setRisk] = useState<RiskFilter>("all");
  const [minConf, setMinConf] = useState<number>(0);

  const filtered = useMemo(() => {
    return signals.filter((s) => {
      const sh = s.stock?.sharia_status ?? null;
      if (sharia === "halal_only" && sh !== "halal") return false;
      if (sharia === "exclude_haram" && sh === "haram") return false;
      if (risk !== "all" && s.risk_class !== risk) return false;
      if (s.confidence != null && s.confidence < minConf) return false;
      return true;
    });
  }, [signals, sharia, risk, minConf]);

  return (
    <>
      <section className="panel p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted">الشريعة:</span>
            <div className="flex bg-panel2 rounded-xl p-1 border border-border">
              {(
                [
                  ["all", "الكل"],
                  ["exclude_haram", "بدون المحرّم"],
                  ["halal_only", "حلال فقط"],
                ] as [SharaFilter, string][]
              ).map(([val, lbl]) => (
                <button
                  key={val}
                  onClick={() => setSharia(val)}
                  className={`px-3 py-1.5 text-xs rounded-lg transition ${
                    sharia === val
                      ? "bg-brand text-bg font-medium"
                      : "text-muted hover:text-text"
                  }`}
                >
                  {lbl}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-muted">المخاطرة:</span>
            <div className="flex bg-panel2 rounded-xl p-1 border border-border">
              {(
                [
                  ["all", "الكل"],
                  ["محافظ", "🟢"],
                  ["متوسط", "🟡"],
                  ["جرىء", "🔴"],
                ] as [RiskFilter, string][]
              ).map(([val, lbl]) => (
                <button
                  key={val}
                  onClick={() => setRisk(val)}
                  className={`px-3 py-1.5 text-xs rounded-lg transition ${
                    risk === val
                      ? "bg-brand text-bg font-medium"
                      : "text-muted hover:text-text"
                  }`}
                >
                  {lbl}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-2 ml-auto">
            <span className="text-xs text-muted">حد أدنى للثقة:</span>
            <input
              type="range"
              min={0}
              max={100}
              step={5}
              value={minConf}
              onChange={(e) => setMinConf(parseInt(e.target.value, 10))}
              className="accent-brand"
            />
            <span className="text-xs font-mono w-8 text-center">{minConf}%</span>
          </div>

          <div className="text-xs text-muted ml-auto">
            {filtered.length} من {signals.length} فرصة
          </div>
        </div>
      </section>

      {filtered.length === 0 ? (
        <div className="panel p-10 text-center text-muted text-sm">
          لا توجد فرص تطابق الفلاتر الحالية. جرب تخفيف الفلاتر.
        </div>
      ) : (
        <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map((s) => (
            <OpportunityCard key={s.id} s={s} />
          ))}
        </section>
      )}
    </>
  );
}
