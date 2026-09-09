import { StocksTable } from "@/components/stocks-table";
import { getAllStocks } from "@/lib/data";

export default async function StocksPage() {
  const stocks = await getAllStocks();
  return <StocksTable stocks={stocks} />;
}
