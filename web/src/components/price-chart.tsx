"use client";

import type { DailyPrice } from "@/lib/types";

type Props = {
  prices: DailyPrice[];
  entry?: number;
  stop?: number;
  target1?: number;
  target2?: number;
};

export function PriceChart({ prices, entry, stop, target1, target2 }: Props) {
  if (!prices.length) {
    return (
      <div className="panel p-6 text-center text-muted text-sm">لا توجد بيانات سعرية</div>
    );
  }

  const w = 900;
  const h = 320;
  const pad = { l: 50, r: 12, t: 12, b: 24 };
  const innerW = w - pad.l - pad.r;
  const innerH = h - pad.t - pad.b;

  const closes = prices.map((p) => p.close ?? 0);
  const highs = prices.map((p) => p.high ?? 0);
  const lows = prices.map((p) => p.low ?? 0);
  const refs = [entry, stop, target1, target2].filter((v): v is number => typeof v === "number");
  const allMin = Math.min(...lows.filter((v) => v > 0), ...refs);
  const allMax = Math.max(...highs.filter((v) => v > 0), ...refs);
  const range = allMax - allMin || 1;
  const padR = range * 0.05;
  const yMin = allMin - padR;
  const yMax = allMax + padR;

  const x = (i: number) => pad.l + (i / Math.max(prices.length - 1, 1)) * innerW;
  const y = (v: number) => pad.t + (1 - (v - yMin) / (yMax - yMin)) * innerH;

  const path = closes
    .map((c, i) => `${i === 0 ? "M" : "L"} ${x(i).toFixed(2)} ${y(c).toFixed(2)}`)
    .join(" ");

  const areaPath = `${path} L ${x(prices.length - 1)} ${y(yMin)} L ${x(0)} ${y(yMin)} Z`;

  const yTicks = 5;
  const ticks = Array.from({ length: yTicks + 1 }, (_, i) => yMin + (i * (yMax - yMin)) / yTicks);

  const refLines: { v: number; label: string; color: string; dash?: string }[] = [];
  if (entry) refLines.push({ v: entry, label: `دخول ${entry.toFixed(2)}`, color: "#22d3ee" });
  if (stop) refLines.push({ v: stop, label: `وقف ${stop.toFixed(2)}`, color: "#ef4444", dash: "4 3" });
  if (target1) refLines.push({ v: target1, label: `هدف 1 ${target1.toFixed(2)}`, color: "#22c55e", dash: "4 3" });
  if (target2) refLines.push({ v: target2, label: `هدف 2 ${target2.toFixed(2)}`, color: "#16a34a", dash: "2 4" });

  return (
    <div className="panel p-3 overflow-x-auto">
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-auto" preserveAspectRatio="none">
        <defs>
          <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#22d3ee" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#22d3ee" stopOpacity="0" />
          </linearGradient>
        </defs>

        {ticks.map((t, i) => (
          <g key={i}>
            <line
              x1={pad.l}
              x2={w - pad.r}
              y1={y(t)}
              y2={y(t)}
              stroke="#222a36"
              strokeWidth={1}
            />
            <text
              x={pad.l - 6}
              y={y(t) + 3}
              textAnchor="end"
              fontSize="10"
              fill="#7a8699"
            >
              {t.toFixed(2)}
            </text>
          </g>
        ))}

        <path d={areaPath} fill="url(#areaGrad)" />
        <path d={path} fill="none" stroke="#22d3ee" strokeWidth={2} />

        {refLines.map((r, i) => (
          <g key={i}>
            <line
              x1={pad.l}
              x2={w - pad.r}
              y1={y(r.v)}
              y2={y(r.v)}
              stroke={r.color}
              strokeWidth={1.2}
              strokeDasharray={r.dash}
              opacity={0.85}
            />
            <text
              x={w - pad.r - 4}
              y={y(r.v) - 4}
              textAnchor="end"
              fontSize="10"
              fill={r.color}
            >
              {r.label}
            </text>
          </g>
        ))}

        {prices.length > 0 && (
          <text
            x={pad.l}
            y={h - 6}
            fontSize="10"
            fill="#7a8699"
          >
            {prices[0].date} → {prices[prices.length - 1].date}
          </text>
        )}
      </svg>
    </div>
  );
}
