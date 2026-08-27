"use client";

import { useEffect, useRef } from "react";
import { AreaSeries, ColorType, createChart, type UTCTimestamp } from "lightweight-charts";
import type { EquityPoint } from "@/lib/types";

type Props = { curve: EquityPoint[]; height?: number; baseline?: number };

export function EquityChart({ curve, height = 260, baseline }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el || curve.length === 0) return;
    // strictly ascending unique times: keep the last point per day
    const byDay = new Map<string, number>();
    for (const p of curve) byDay.set(p.date, p.equity);
    const data = [...byDay.entries()]
      .sort(([a], [b]) => (a < b ? -1 : 1))
      .map(([d, v]) => ({ time: (Date.parse(d + "T00:00:00Z") / 1000) as UTCTimestamp, value: v }));

    const chart = createChart(el, {
      layout: { background: { type: ColorType.Solid, color: "transparent" }, textColor: "#9aa4b2", fontFamily: "inherit" },
      grid: { vertLines: { color: "#1c2430" }, horzLines: { color: "#1c2430" } },
      rightPriceScale: { borderColor: "#2a3441" },
      timeScale: { borderColor: "#2a3441" },
      localization: { locale: "en-US" },
      width: el.clientWidth,
      height,
    });
    const last = data[data.length - 1]?.value ?? 0;
    const up = baseline == null || last >= baseline;
    const series = chart.addSeries(AreaSeries, {
      lineColor: up ? "#22c55e" : "#ef4444",
      topColor: up ? "rgba(34,197,94,0.35)" : "rgba(239,68,68,0.35)",
      bottomColor: "rgba(0,0,0,0)",
      lineWidth: 2,
      priceLineVisible: false,
    });
    series.setData(data);
    if (baseline != null) {
      series.createPriceLine({ price: baseline, color: "#7a8699", lineWidth: 1, lineStyle: 2, axisLabelVisible: true, title: "رأس المال" });
    }
    chart.timeScale().fitContent();
    const ro = new ResizeObserver(() => chart.applyOptions({ width: el.clientWidth }));
    ro.observe(el);
    return () => {
      ro.disconnect();
      chart.remove();
    };
  }, [curve, height, baseline]);

  if (!curve.length) return <div className="text-muted text-sm p-4">لا توجد بيانات</div>;
  return <div ref={ref} dir="ltr" className="w-full" style={{ height }} />;
}
