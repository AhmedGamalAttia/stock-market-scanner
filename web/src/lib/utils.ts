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
