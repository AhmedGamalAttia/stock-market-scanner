import { supabase } from "./supabase";
import type { DailyPrice, RunMeta, Signal, SignalWithStock, Stock } from "./types";

export async function getLatestSignals(limit = 30): Promise<SignalWithStock[]> {
  if (!supabase) return [];
  const latest = await supabase
    .from("signals")
    .select("signal_date")
    .order("signal_date", { ascending: false })
    .limit(1)
    .single();
  if (latest.error || !latest.data) return [];
  const day = latest.data.signal_date as string;
  const res = await supabase
    .from("signals")
    .select("*, stock:stocks(*)")
    .eq("signal_date", day)
    .order("score", { ascending: false })
    .limit(limit);
  if (res.error || !res.data) return [];
  return res.data as unknown as SignalWithStock[];
}

export async function getSignalForSymbol(symbol: string): Promise<Signal | null> {
  if (!supabase) return null;
  const res = await supabase
    .from("signals")
    .select("*")
    .eq("symbol", symbol)
    .order("signal_date", { ascending: false })
    .limit(1)
    .maybeSingle();
  if (res.error || !res.data) return null;
  return res.data as unknown as Signal;
}

export async function getStock(symbol: string): Promise<Stock | null> {
  if (!supabase) return null;
  const res = await supabase
    .from("stocks")
    .select("*")
    .eq("symbol", symbol)
    .maybeSingle();
  if (res.error || !res.data) return null;
  return res.data as unknown as Stock;
}

export async function getPriceHistory(symbol: string, days = 90): Promise<DailyPrice[]> {
  if (!supabase) return [];
  const res = await supabase
    .from("daily_prices")
    .select("*")
    .eq("symbol", symbol)
    .order("date", { ascending: false })
    .limit(days);
  if (res.error || !res.data) return [];
  return (res.data as unknown as DailyPrice[]).reverse();
}

export async function getAllStocks(): Promise<Stock[]> {
  if (!supabase) return [];
  const res = await supabase
    .from("stocks")
    .select("*")
    .order("symbol", { ascending: true });
  if (res.error || !res.data) return [];
  return res.data as unknown as Stock[];
}

export async function getLastRun(): Promise<RunMeta | null> {
  if (!supabase) return null;
  const res = await supabase
    .from("run_meta")
    .select("*")
    .order("ran_at", { ascending: false })
    .limit(1)
    .maybeSingle();
  if (res.error || !res.data) return null;
  return res.data as unknown as RunMeta;
}
