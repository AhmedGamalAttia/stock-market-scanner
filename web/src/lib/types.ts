export type ShariaStatus = "halal" | "haram" | "mixed";

export type Stock = {
  symbol: string;
  name_ar: string | null;
  name_en: string | null;
  sector: string | null;
  sharia_status: ShariaStatus | null;
  is_active: boolean;
  updated_at: string;
};

export type DailyPrice = {
  symbol: string;
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
};

export type Signal = {
  id: number;
  symbol: string;
  signal_date: string;
  generated_at: string;
  score: number;
  confidence: number | null;
  risk_class: string | null;
  setups: string[];
  trend: string | null;
  rsi: number | null;
  macd_hist: number | null;
  ma20: number | null;
  ma50: number | null;
  volume_z: number | null;
  atr: number;
  atr_pct: number | null;
  adv_20: number | null;
  entry: number;
  stop_loss: number;
  target_1: number;
  target_2: number;
  rr_t1: number | null;
  rr_t2: number | null;
  blended_rr: number | null;
  expected_days: number;
  suggested_shares_20k: number | null;
  suggested_value_20k: number | null;
  max_loss_20k: number | null;
  rationale_ar: string | null;
  strategy_ar: string | null;
  warnings_ar: string[] | null;
};

export type SignalWithStock = Signal & { stock: Stock | null };

export type RunMeta = {
  id: number;
  ran_at: string;
  ok: boolean;
  symbols_total: number;
  symbols_failed: number;
  signals_emitted: number;
  notes: string | null;
};
