export type ShariaStatus = "halal" | "haram" | "mixed";

export type Stock = {
  symbol: string;
  yahoo_symbol?: string | null;
  name_ar: string | null;
  name_en: string | null;
  sector: string | null;
  sharia_status: ShariaStatus | null;
  is_active: boolean;
};

export type StockLite = Pick<Stock, "symbol" | "name_ar" | "name_en" | "sector" | "sharia_status">;

/** Compact bar as stored in /data/prices/{SYM}.json */
export type Bar = {
  d: string; // YYYY-MM-DD (Cairo)
  o: number;
  h: number;
  l: number;
  c: number; // raw close (what you trade)
  a: number; // adjusted close (splits/dividends)
  v: number;
};

export type PriceFile = {
  symbol: string;
  yahoo: string | null;
  updated: string | null;
  count: number;
  bars: Bar[];
};

export type DailyPrice = {
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
};

export type Signal = {
  symbol: string;
  signal_date: string;
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
  close?: number | null;
  stock: StockLite | null;
};

/** Kept for component compatibility — signals now embed their stock. */
export type SignalWithStock = Signal;

export type Latest = {
  date: string | null;
  generated_at: string;
  strategy: string;
  buys: Signal[];
  holds: unknown[];
  exits: unknown[];
};

export type Meta = {
  ran_at: string;
  ok: boolean;
  data_date: string | null;
  symbols_total: number;
  symbols_failed: number;
  symbols_stale?: number;
  signals_emitted: number;
  strategy?: string;
  notes: string | null;
};
