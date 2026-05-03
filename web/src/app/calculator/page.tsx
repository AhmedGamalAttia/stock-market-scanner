"use client";

import { useMemo, useState } from "react";

const COMMISSION_RT = 0.008; // 0.4% × 2 sides

export default function CalculatorPage() {
  const [capital, setCapital] = useState("20000");
  const [riskPct, setRiskPct] = useState("2");
  const [entry, setEntry] = useState("");
  const [stop, setStop] = useState("");
  const [target, setTarget] = useState("");

  const result = useMemo(() => {
    const cap = parseFloat(capital);
    const rp = parseFloat(riskPct) / 100;
    const e = parseFloat(entry);
    const s = parseFloat(stop);
    const t = parseFloat(target);
    if (!cap || !rp || !e || !s || s >= e) return null;

    const riskPerShare = e - s;
    const maxLoss = cap * rp;
    const sharesByRisk = Math.floor(maxLoss / riskPerShare);
    const sharesByCapital = Math.floor(cap / e);
    const shares = Math.min(sharesByRisk, sharesByCapital);
    const positionValue = shares * e;
    const commission = positionValue * COMMISSION_RT;
    const actualLoss = shares * riskPerShare + commission;
    const breakEvenMove = commission / positionValue;

    let reward: number | null = null;
    let rr: number | null = null;
    if (t && t > e) {
      reward = shares * (t - e) - commission;
      rr = (t - e) / riskPerShare;
    }

    return {
      shares,
      positionValue,
      pctOfCapital: (positionValue / cap) * 100,
      commission,
      actualLoss,
      breakEvenMove: breakEvenMove * 100,
      reward,
      rr,
    };
  }, [capital, riskPct, entry, stop, target]);

  return (
    <div className="space-y-4">
      <header className="panel p-5">
        <h1 className="text-2xl font-bold">حاسبة حجم الصفقة والمخاطرة</h1>
        <p className="text-muted text-sm mt-1">
          القاعدة الذهبية: لا تخاطر بأكثر من 1-2% من رأس مالك فى صفقة واحدة. الحاسبة بتاخد فى الحسبان عمولة ثاندر (~0.4% × 2).
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="panel p-5 space-y-3">
          <div>
            <label className="label">رأس المال (جنيه)</label>
            <input type="number" className="input" value={capital} onChange={(e) => setCapital(e.target.value)} />
          </div>
          <div>
            <label className="label">نسبة المخاطرة فى الصفقة (%)</label>
            <input type="number" step="0.1" className="input" value={riskPct} onChange={(e) => setRiskPct(e.target.value)} />
          </div>
          <div>
            <label className="label">سعر الدخول</label>
            <input type="number" step="0.01" className="input" value={entry} onChange={(e) => setEntry(e.target.value)} />
          </div>
          <div>
            <label className="label">وقف الخسارة</label>
            <input type="number" step="0.01" className="input" value={stop} onChange={(e) => setStop(e.target.value)} />
          </div>
          <div>
            <label className="label">الهدف (اختيارى)</label>
            <input type="number" step="0.01" className="input" value={target} onChange={(e) => setTarget(e.target.value)} />
          </div>
        </div>

        <div className="panel p-5">
          <h2 className="text-lg font-semibold mb-4">النتيجة</h2>
          {!result ? (
            <p className="text-muted text-sm">املأ البيانات (تأكد إن وقف الخسارة أقل من الدخول).</p>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              <Stat label="عدد الأسهم" value={result.shares.toLocaleString()} />
              <Stat label="قيمة الصفقة" value={`${result.positionValue.toFixed(2)} ج`} />
              <Stat label="% من رأس المال" value={`${result.pctOfCapital.toFixed(1)}%`} />
              <Stat label="العمولة الكلية" value={`${result.commission.toFixed(2)} ج`} />
              <Stat label="أقصى خسارة فعلية" value={`${result.actualLoss.toFixed(2)} ج`} accent="text-danger" />
              <Stat label="السعر اللى تتعادل عنده" value={`+${result.breakEvenMove.toFixed(2)}%`} accent="text-warning" />
              {result.reward != null && result.rr != null && (
                <>
                  <Stat label="الربح المتوقع" value={`${result.reward.toFixed(2)} ج`} accent="text-success" />
                  <Stat label="نسبة العائد/المخاطرة" value={`${result.rr.toFixed(2)} : 1`} accent={result.rr >= 2 ? "text-success" : "text-warning"} />
                </>
              )}
            </div>
          )}

          <div className="mt-5 pt-4 border-t border-border text-xs text-muted leading-relaxed">
            <p>• إذا كانت R:R أقل من 2:1، الصفقة قد لا تستحق المخاطرة على المدى الطويل.</p>
            <p>• إذا كان % من رأس المال أكتر من 30%، الصفقة كبيرة جداً برأس مال صغير.</p>
            <p>• قاعدة عامة: لا تفتح أكتر من 3-4 صفقات فى نفس الوقت برأس مال 20 ألف.</p>
          </div>
        </div>
      </div>
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
