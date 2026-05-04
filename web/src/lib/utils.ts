import type { ShariaStatus } from "./types";

export const SETUP_LABELS_AR: Record<string, string> = {
  breakout_20d: "اختراق 20 جلسة",
  macd_cross_up: "تقاطع MACD صاعد",
  golden_cross_20_50: "تقاطع ذهبى",
  pullback_bounce: "ارتداد من تشبع البيع",
};

export function setupLabel(s: string): string {
  return SETUP_LABELS_AR[s] ?? s;
}

export function fmtPct(n: number, digits = 2): string {
  return `${(n * 100).toFixed(digits)}%`;
}

export function fmtNum(n: number | null | undefined, digits = 2): string {
  if (n == null || Number.isNaN(n)) return "—";
  return n.toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function fmtMoney(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}م ج`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}ك ج`;
  return `${n.toFixed(0)} ج`;
}

export function fmtDate(s: string): string {
  try {
    const d = new Date(s);
    return d.toLocaleDateString("ar-EG", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return s;
  }
}

export function fmtDateTime(s: string): string {
  try {
    const d = new Date(s);
    const date = d.toLocaleDateString("ar-EG", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
    const time = d.toLocaleTimeString("ar-EG", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
      timeZone: "Africa/Cairo",
    });
    return `${date} — ${time}`;
  } catch {
    return s;
  }
}

export function fmtRelative(s: string, now: Date = new Date()): string {
  try {
    const then = new Date(s).getTime();
    const diffSec = Math.round((now.getTime() - then) / 1000);
    if (diffSec < 0) return "الآن";
    if (diffSec < 60) return "منذ لحظات";
    const diffMin = Math.round(diffSec / 60);
    if (diffMin < 60) return `منذ ${diffMin} دقيقة`;
    const diffH = Math.round(diffMin / 60);
    if (diffH < 24) return `منذ ${diffH} ساعة`;
    const diffD = Math.round(diffH / 24);
    if (diffD < 30) return `منذ ${diffD} يوم`;
    return fmtDate(s);
  } catch {
    return s;
  }
}

export function rrRatio(entry: number, stop: number, target: number): number {
  const risk = entry - stop;
  const reward = target - entry;
  if (risk <= 0) return 0;
  return reward / risk;
}

export function scoreColor(score: number): string {
  if (score >= 70) return "text-success";
  if (score >= 50) return "text-brand";
  if (score >= 30) return "text-warning";
  return "text-muted";
}

export function trendBadge(trend: string | null): { label: string; cls: string } {
  switch (trend) {
    case "صاعد":
      return { label: "صاعد", cls: "bg-success/15 text-success border-success/30" };
    case "هابط":
      return { label: "هابط", cls: "bg-danger/15 text-danger border-danger/30" };
    case "محايد":
      return { label: "محايد", cls: "bg-muted/15 text-muted border-muted/30" };
    default:
      return { label: "—", cls: "bg-muted/10 text-muted border-border" };
  }
}

export function riskBadge(rc: string | null): { label: string; cls: string; emoji: string } {
  switch (rc) {
    case "محافظ":
      return { label: "محافظ", cls: "bg-success/15 text-success border-success/30", emoji: "🟢" };
    case "متوسط":
      return { label: "متوسط", cls: "bg-warning/15 text-warning border-warning/30", emoji: "🟡" };
    case "جرىء":
      return { label: "جرىء", cls: "bg-danger/15 text-danger border-danger/30", emoji: "🔴" };
    default:
      return { label: "—", cls: "bg-muted/10 text-muted border-border", emoji: "⚪" };
  }
}

export function shariaBadge(s: ShariaStatus | string | null | undefined): {
  label: string;
  cls: string;
  emoji: string;
  short: string;
} {
  switch (s) {
    case "halal":
      return {
        label: "متوافق مع الشريعة",
        short: "حلال",
        cls: "bg-success/15 text-success border-success/30",
        emoji: "⭐",
      };
    case "haram":
      return {
        label: "غير متوافق شرعياً",
        short: "حرام",
        cls: "bg-danger/15 text-danger border-danger/30",
        emoji: "✕",
      };
    case "mixed":
      return {
        label: "مختلط — يحتاج مراجعة",
        short: "مختلط",
        cls: "bg-warning/15 text-warning border-warning/30",
        emoji: "⚠",
      };
    default:
      return {
        label: "غير مصنّف",
        short: "—",
        cls: "bg-muted/10 text-muted border-border",
        emoji: "—",
      };
  }
}

export function confidenceColor(c: number | null | undefined): string {
  if (c == null) return "text-muted";
  if (c >= 75) return "text-success";
  if (c >= 55) return "text-brand";
  if (c >= 35) return "text-warning";
  return "text-danger";
}
