/**
 * Browser-side twin of scanner/strategies/kalman_supertrend.py — used only to
 * DRAW the Supertrend line on charts. The scanner remains the source of truth
 * for signals; this exists so price files stay small (bars only).
 */
import type { Bar } from "./types";

export const KALMAN_GAIN = 0.7;
export const KALMAN_MOMENTUM = 0.3;
export const ATR_PERIOD = 10;
export const ATR_MULT = 3.0;

export function kalman(src: number[], gain: number, momentum: number): number[] {
  const out = new Array<number>(src.length).fill(NaN);
  let est = NaN;
  let vel = 0;
  for (let i = 0; i < src.length; i++) {
    const x = src[i];
    if (Number.isNaN(x)) {
      out[i] = est;
      continue;
    }
    if (Number.isNaN(est)) {
      est = x;
      vel = 0;
    } else {
      const pred = est + vel;
      const err = x - pred;
      est = pred + gain * err;
      vel = vel * momentum + gain * err;
    }
    out[i] = est;
  }
  return out;
}

/** pandas ewm(alpha=1/p, adjust=False, min_periods=p) */
export function rma(x: number[], period: number): number[] {
  const out = new Array<number>(x.length).fill(NaN);
  const alpha = 1 / period;
  let y = NaN;
  for (let i = 0; i < x.length; i++) {
    y = Number.isNaN(y) ? x[i] : alpha * x[i] + (1 - alpha) * y;
    if (i >= period - 1) out[i] = y;
  }
  return out;
}

export type SupertrendResult = {
  upper: number[];
  lower: number[];
  trend: number[]; // +1 / -1
  line: number[]; // lower band in uptrend, upper band in downtrend
};

export function supertrend(bars: Bar[]): SupertrendResult {
  const n = bars.length;
  const hl2 = bars.map((b) => (b.h + b.l) / 2);
  const tr = bars.map((b, i) => {
    if (i === 0) return b.h - b.l;
    const pc = bars[i - 1].c;
    return Math.max(b.h - b.l, Math.abs(b.h - pc), Math.abs(b.l - pc));
  });
  const kHl2 = kalman(hl2, KALMAN_GAIN, KALMAN_MOMENTUM);
  const atr = rma(tr, ATR_PERIOD);
  const atrF = kalman(atr, KALMAN_GAIN * 0.5, KALMAN_MOMENTUM);

  const upper = new Array<number>(n).fill(NaN);
  const lower = new Array<number>(n).fill(NaN);
  const trend = new Array<number>(n).fill(1);
  const line = new Array<number>(n).fill(NaN);

  for (let i = 0; i < n; i++) {
    const up = kHl2[i] + ATR_MULT * atrF[i];
    const lo = kHl2[i] - ATR_MULT * atrF[i];
    if (Number.isNaN(up) || Number.isNaN(lo)) {
      trend[i] = i ? trend[i - 1] : 1;
      continue;
    }
    const c1 = i ? bars[i - 1].c : NaN;
    upper[i] = i === 0 || Number.isNaN(upper[i - 1]) ? up : c1 > upper[i - 1] ? up : Math.min(up, upper[i - 1]);
    lower[i] = i === 0 || Number.isNaN(lower[i - 1]) ? lo : c1 < lower[i - 1] ? lo : Math.max(lo, lower[i - 1]);
    const prev = i ? trend[i - 1] : 1;
    if (i && !Number.isNaN(upper[i - 1]) && bars[i].c > upper[i - 1]) trend[i] = 1;
    else if (i && !Number.isNaN(lower[i - 1]) && bars[i].c < lower[i - 1]) trend[i] = -1;
    else trend[i] = prev;
    line[i] = trend[i] === 1 ? lower[i] : upper[i];
  }
  return { upper, lower, trend, line };
}
