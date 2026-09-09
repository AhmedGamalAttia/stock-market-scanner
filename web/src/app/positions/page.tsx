import { PositionsView } from "@/components/positions-view";
import { getAllStocks, getLatest, getTradesLive } from "@/lib/data";

export default async function PositionsPage() {
  const [latest, trades, stocks] = await Promise.all([
    getLatest(),
    getTradesLive(),
    getAllStocks(),
  ]);
  const holds = latest?.holds ?? [];
  const closed = trades
    .filter((t) => t.reason !== "invalid")
    .sort((a, b) => ((a.closed_date ?? "") < (b.closed_date ?? "") ? 1 : -1));
  const statusBySymbol = Object.fromEntries(stocks.map((s) => [s.symbol, s.sharia_status]));

  return <PositionsView holds={holds} closed={closed} statusBySymbol={statusBySymbol} />;
}
