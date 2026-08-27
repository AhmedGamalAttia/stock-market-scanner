/**
 * Data layer — reads the JSON files the scanner commits under public/data.
 *
 * Server-only (uses fs). Pages that call these are statically generated at
 * build time; every data commit triggers a Vercel rebuild, so there is no
 * runtime database and nothing that can expire or get paused.
 *
 * The browser can fetch the very same files at /data/... for client charts.
 */
import { promises as fs } from "fs";
import path from "path";
import type {
  BacktestIndex,
  BacktestReport,
  DailyPrice,
  Hold,
  Latest,
  Meta,
  PriceFile,
  Signal,
  Stock,
  TradeLive,
} from "./types";

const DATA_DIR = path.join(process.cwd(), "public", "data");
const SYMBOL_RE = /^[A-Z0-9]{1,8}$/;

async function readJson<T>(rel: string): Promise<T | null> {
  try {
    const txt = await fs.readFile(path.join(DATA_DIR, rel), "utf-8");
    return JSON.parse(txt) as T;
  } catch {
    return null;
  }
}

function safeSymbol(symbol: string): string | null {
  const s = symbol.toUpperCase();
  return SYMBOL_RE.test(s) ? s : null;
}

export async function getLatest(): Promise<Latest | null> {
  return readJson<Latest>("latest.json");
}

export async function getMeta(): Promise<Meta | null> {
  return readJson<Meta>("meta.json");
}

export async function getAllStocks(): Promise<Stock[]> {
  return (await readJson<Stock[]>("stocks.json")) ?? [];
}

export async function getStock(symbol: string): Promise<Stock | null> {
  const s = safeSymbol(symbol);
  if (!s) return null;
  const stocks = await getAllStocks();
  return stocks.find((x) => x.symbol === s) ?? null;
}

export async function listSymbols(): Promise<string[]> {
  return (await getAllStocks()).map((s) => s.symbol);
}

export async function getLatestSignals(): Promise<Signal[]> {
  const latest = await getLatest();
  return latest?.buys ?? [];
}

export async function getSignalForSymbol(symbol: string): Promise<Signal | null> {
  const s = safeSymbol(symbol);
  if (!s) return null;
  const latest = await getLatest();
  return latest?.buys.find((x) => x.symbol === s) ?? null;
}

export async function getPriceFile(symbol: string): Promise<PriceFile | null> {
  const s = safeSymbol(symbol);
  if (!s) return null;
  return readJson<PriceFile>(`prices/${s}.json`);
}

export async function getHoldForSymbol(symbol: string): Promise<Hold | null> {
  const s = safeSymbol(symbol);
  if (!s) return null;
  const latest = await getLatest();
  return latest?.holds.find((x) => x.symbol === s) ?? null;
}

export async function getTradesLive(): Promise<TradeLive[]> {
  return (await readJson<TradeLive[]>("trades_live.json")) ?? [];
}

export async function getBacktestIndex(): Promise<BacktestIndex | null> {
  return readJson<BacktestIndex>("backtest/index.json");
}

export async function getBacktest(strategy: string): Promise<BacktestReport | null> {
  if (!/^[a-z0-9_]{1,40}$/.test(strategy)) return null;
  return readJson<BacktestReport>(`backtest/${strategy}.json`);
}

export async function getPriceHistory(symbol: string, days = 120): Promise<DailyPrice[]> {
  const file = await getPriceFile(symbol);
  if (!file) return [];
  return file.bars.slice(-days).map((b) => ({
    date: b.d,
    open: b.o,
    high: b.h,
    low: b.l,
    close: b.c,
    volume: b.v,
  }));
}
