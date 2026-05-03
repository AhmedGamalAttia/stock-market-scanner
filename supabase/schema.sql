-- EGX Scanner schema (idempotent — safe to re-run)
-- Run this in Supabase SQL Editor (Database > SQL Editor > New query)

create table if not exists stocks (
  symbol text primary key,
  name_ar text,
  name_en text,
  sector text,
  is_active boolean default true,
  updated_at timestamptz default now()
);

alter table stocks add column if not exists sharia_status text;

create table if not exists daily_prices (
  symbol text references stocks(symbol) on delete cascade,
  date date not null,
  open numeric,
  high numeric,
  low numeric,
  close numeric,
  volume bigint,
  primary key (symbol, date)
);

create index if not exists idx_daily_prices_symbol_date on daily_prices (symbol, date desc);

create table if not exists signals (
  id bigserial primary key,
  symbol text references stocks(symbol) on delete cascade,
  signal_date date not null,
  generated_at timestamptz default now(),
  score int not null,
  setups text[] not null default '{}',
  trend text,
  rsi numeric,
  macd_hist numeric,
  ma20 numeric,
  ma50 numeric,
  volume_z numeric,
  atr numeric not null,
  entry numeric not null,
  stop_loss numeric not null,
  target_1 numeric not null,
  target_2 numeric not null,
  expected_days int not null,
  rationale_ar text,
  unique (symbol, signal_date)
);

-- Expert layer fields (additive, safe to re-run)
alter table signals add column if not exists risk_class text;
alter table signals add column if not exists confidence int;
alter table signals add column if not exists adv_20 numeric;
alter table signals add column if not exists atr_pct numeric;
alter table signals add column if not exists rr_t1 numeric;
alter table signals add column if not exists rr_t2 numeric;
alter table signals add column if not exists blended_rr numeric;
alter table signals add column if not exists suggested_shares_20k int;
alter table signals add column if not exists suggested_value_20k numeric;
alter table signals add column if not exists max_loss_20k numeric;
alter table signals add column if not exists strategy_ar text;
alter table signals add column if not exists warnings_ar text[];

create index if not exists idx_signals_date_score on signals (signal_date desc, score desc);
create index if not exists idx_signals_date_confidence on signals (signal_date desc, confidence desc);

create table if not exists run_meta (
  id bigserial primary key,
  ran_at timestamptz default now(),
  ok boolean not null,
  symbols_total int,
  symbols_failed int,
  signals_emitted int,
  notes text
);

-- Public read access (dashboard is public)
alter table stocks enable row level security;
alter table daily_prices enable row level security;
alter table signals enable row level security;
alter table run_meta enable row level security;

drop policy if exists "public read stocks" on stocks;
create policy "public read stocks" on stocks for select using (true);

drop policy if exists "public read daily_prices" on daily_prices;
create policy "public read daily_prices" on daily_prices for select using (true);

drop policy if exists "public read signals" on signals;
create policy "public read signals" on signals for select using (true);

drop policy if exists "public read run_meta" on run_meta;
create policy "public read run_meta" on run_meta for select using (true);

-- Writes go through the service_role key (used only by the scanner).
