export type Stock = {
  symbol: string;
  name_ar: string | null;
  name_en: string | null;
  sector: string | null;
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
  setups: string[];
  trend: string | null;
  rsi: number | null;
  macd_hist: number | null;
  ma20: number | null;
  ma50: number | null;
  volume_z: number | null;
  atr: number;
  entry: number;
  stop_loss: number;
  target_1: number;
  target_2: number;
  expected_days: number;
  rationale_ar: string | null;
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
