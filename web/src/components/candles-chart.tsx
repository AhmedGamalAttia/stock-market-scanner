"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  CandlestickSeries,
  ColorType,
  HistogramSeries,
  LineSeries,
  LineStyle,
  createChart,
  type IChartApi,
  type UTCTimestamp,
} from "lightweight-charts";
import type { Bar } from "@/lib/types";
import { supertrend } from "@/lib/kalman";

type Level = { price: number; label: string; color: string; dashed?: boolean };

type Props = {
  bars: Bar[];
  entry?: number | null;
  stop?: number | null;
  targets?: (number | null | undefined)[];
  visibleBars?: number;
  height?: number;
};

const C = {
  text: "#9aa4b2",
  grid: "#1c2430",
  border: "#2a3441",
  up: "#22c55e",
  down: "#ef4444",
  stUp: "#22c55e",
  stDown: "#ef4444",
  entry: "#22d3ee",
  stop: "#ef4444",
  tp: ["#4ade80", "#22c55e", "#16a34a"],
};

function toTime(d: string): UTCTimestamp {
  return (Date.parse(d + "T00:00:00Z") / 1000) as UTCTimestamp;
}

export function CandlesChart({ bars, entry, stop, targets = [], visibleBars = 130, height = 400 }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const [showSt, setShowSt] = useState(true);
  const [showVol, setShowVol] = useState(true);

  const st = useMemo(() => supertrend(bars), [bars]);
  const last = bars[bars.length - 1];
  const lastTrend = st.trend[st.trend.length - 1];
  const lastLine = st.line[st.line.length - 1];

  useEffect(() => {
    const el = ref.current;
    if (!el || bars.length === 0) return;

    const chart: IChartApi = createChart(el, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: C.text,
        fontFamily: "inherit",
      },
      grid: { vertLines: { color: C.grid }, horzLines: { color: C.grid } },
      rightPriceScale: { borderColor: C.border },
      timeScale: { borderColor: C.border, rightOffset: 4 },
      crosshair: { mode: 0 },
      localization: { locale: "en-US" },
      width: el.clientWidth,
      height,
    });

    const candles = chart.addSeries(CandlestickSeries, {
      upColor: C.up,
      downColor: C.down,
      borderVisible: false,
      wickUpColor: C.up,
      wickDownColor: C.down,
      priceLineVisible: false,
    });
    candles.setData(bars.map((b) => ({ time: toTime(b.d), open: b.o, high: b.h, low: b.l, close: b.c })));

    if (showVol) {
      const vol = chart.addSeries(HistogramSeries, {
        priceFormat: { type: "volume" },
        priceScaleId: "vol",
        lastValueVisible: false,
        priceLineVisible: false,
      });
      chart.priceScale("vol").applyOptions({ scaleMargins: { top: 0.82, bottom: 0 } });
      vol.setData(
        bars.map((b) => ({
          time: toTime(b.d),
          value: b.v,
          color: b.c >= b.o ? "rgba(34,197,94,0.28)" : "rgba(239,68,68,0.28)",
        })),
      );
    }

    if (showSt) {
      // Two series so the line is green in up-trends and red in down-trends;
      // whitespace points create the gaps at flips.
      const upSeries = chart.addSeries(LineSeries, {
        color: C.stUp, lineWidth: 2, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false,
      });
      const dnSeries = chart.addSeries(LineSeries, {
        color: C.stDown, lineWidth: 2, priceLineVisible: false, lastValueVisible: false, crosshairMarkerVisible: false,
      });
      upSeries.setData(
        bars.map((b, i) =>
          st.trend[i] === 1 && !Number.isNaN(st.line[i]) ? { time: toTime(b.d), value: st.line[i] } : { time: toTime(b.d) },
        ),
      );
      dnSeries.setData(
        bars.map((b, i) =>
          st.trend[i] === -1 && !Number.isNaN(st.line[i]) ? { time: toTime(b.d), value: st.line[i] } : { time: toTime(b.d) },
        ),
      );
    }

    const levels: Level[] = [];
    if (entry) levels.push({ price: entry, label: "دخول", color: C.entry });
    if (stop) levels.push({ price: stop, label: "وقف", color: C.stop, dashed: true });
    targets.forEach((t, i) => {
      if (t) levels.push({ price: t, label: `هدف ${i + 1}`, color: C.tp[i] ?? C.up, dashed: true });
    });
    for (const lv of levels) {
      candles.createPriceLine({
        price: lv.price,
        color: lv.color,
        lineWidth: 1,
        lineStyle: lv.dashed ? LineStyle.Dashed : LineStyle.Solid,
        axisLabelVisible: true,
        title: lv.label,
      });
    }

    const n = bars.length;
    chart.timeScale().setVisibleLogicalRange({ from: Math.max(0, n - visibleBars), to: n + 3 });

    const ro = new ResizeObserver(() => chart.applyOptions({ width: el.clientWidth }));
    ro.observe(el);
    return () => {
      ro.disconnect();
      chart.remove();
    };
  }, [bars, entry, stop, targets, showSt, showVol, st, visibleBars, height]);

  if (!bars.length) {
    return <div className="panel p-6 text-center text-muted text-sm">لا توجد بيانات سعرية</div>;
  }

  return (
    <div className="panel p-3">
      <div className="flex items-center justify-between flex-wrap gap-2 mb-2 text-xs">
        <div className="flex items-center gap-3">
          <span className="text-muted">
            الاتجاه الحالى (سوبرترند):{" "}
            <span className={lastTrend === 1 ? "text-success font-semibold" : "text-danger font-semibold"}>
              {lastTrend === 1 ? "صاعد ▲" : "هابط ▼"}
            </span>
          </span>
          {!Number.isNaN(lastLine) && (
            <span className="text-muted">
              خط السوبرترند: <span className="font-mono text-text">{lastLine.toFixed(2)}</span>
            </span>
          )}
          <span className="text-muted">
            آخر إغلاق: <span className="font-mono text-text">{last.c.toFixed(2)}</span> ({last.d})
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowSt((v) => !v)}
            className={`px-2 py-1 rounded-lg border ${showSt ? "border-brand/40 text-brand bg-brand/10" : "border-border text-muted"}`}
          >
            سوبرترند
          </button>
          <button
            onClick={() => setShowVol((v) => !v)}
            className={`px-2 py-1 rounded-lg border ${showVol ? "border-brand/40 text-brand bg-brand/10" : "border-border text-muted"}`}
          >
            الحجم
          </button>
        </div>
      </div>
      <div ref={ref} dir="ltr" className="w-full" style={{ height }} />
      <p className="text-[11px] text-muted mt-2">
        الخط الأخضر تحت السعر = اتجاه صاعد (وهو نفسه مستوى الوقف المتحرك). لما السعر يقفل تحته يتحول لأحمر فوق
        السعر = اتجاه هابط = خروج.
      </p>
    </div>
  );
}
