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
  strategy?: string;
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
  target_3?: number | null;
  rr_t1: number | null;
  rr_t2: number | null;
  blended_rr: number | null;
  expected_days: number;
  max_hold?: number | null;
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

/** An open (or pending) paper position as published in latest.json / positions.json */
export type Hold = {
  id: string;
  symbol: string;
  name_ar: string | null;
  status: "pending" | "open";
  signal_date: string;
  entry_date: string | null;
  entry: number | null;
  stop: number | null;
  tps: (number | null)[];
  tp_hit: boolean[];
  shares: number | null;
  shares_open: number | null;
  last_close: number | null;
  change_pct: number | null;
  stop_distance_pct: number | null;
  unrealized_pnl: number | null;
  unrealized_r: number | null;
  bars_held: number;
  pending_exit: string | null;
  note_ar: string | null;
  bootstrap?: boolean;
};

/** A position closed on the latest data date */
export type ExitRow = {
  id: string;
  symbol: string;
  name_ar: string | null;
  entry_date: string | null;
  entry: number | null;
  exit_date: string | null;
  exit_price: number | null;
  reason: string | null;
  reason_ar: string | null;
  realized_pnl: number | null;
  realized_r: number | null;
  bars_held: number | null;
  tp_hit: boolean[] | null;
};

/** Full closed-position record from trades_live.json */
export type TradeLive = ExitRow & {
  strategy?: string;
  signal_date?: string;
  closed_date?: string;
  shares?: number | null;
  initial_stop?: number | null;
  tps?: (number | null)[];
  exits?: { date: string; price: number; shares: number; reason: string }[];
  bootstrap?: boolean;
};

export type Latest = {
  date: string | null;
  generated_at: string;
  strategy: string;
  strategy_label_ar?: string;
  buys: Signal[];
  holds: Hold[];
  exits: ExitRow[];
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

export type PositionsFile = {
  updated: string | null;
  positions: Record<string, unknown>[];
};

// ---------- backtest ----------

export type StatBlock = {
  n_trades: number;
  win_rate?: number;
  avg_r?: number;
  avg_win_r?: number;
  avg_loss_r?: number;
  profit_factor?: number | null;
  expectancy_egp?: number;
  total_pnl?: number;
  avg_hold_bars?: number;
  best_r?: number;
  worst_r?: number;
  exit_reasons?: Record<string, number>;
  tp1_hit_rate?: number;
  total_return_pct?: number;
  max_drawdown_pct?: number;
  years?: number;
  cagr_pct?: number;
  skipped_signals?: number;
  max_concurrent?: number;
};

export type EquityPoint = { date: string; equity: number };

export type BacktestReport = {
  strategy: string;
  label_ar: string;
  generated_at: string;
  config: Record<string, unknown>;
  period: { from: string; to: string; in_sample_until: string };
  aggregate: { full: StatBlock; in_sample: StatBlock; out_of_sample: StatBlock };
  portfolio: {
    full: { stats: StatBlock; equity_curve: EquityPoint[] };
    out_of_sample: { stats: StatBlock; equity_curve: EquityPoint[] };
  };
  pooled_equity_curve: EquityPoint[];
  per_ticker: { symbol: string; full: StatBlock; out_of_sample: StatBlock }[];
};

export type BacktestIndexRow = {
  strategy: string;
  label_ar: string;
  full: Partial<StatBlock>;
  out_of_sample: Partial<StatBlock>;
  portfolio_full: Partial<StatBlock>;
  portfolio_oos: Partial<StatBlock>;
  oos_calmar?: number;
};

export type BacktestIndex = {
  generated_at: string;
  period: { from: string; to: string; in_sample_until: string };
  selection_rule: string;
  recommended: string | null;
  strategies: BacktestIndexRow[];
};
