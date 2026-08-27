"use client";

import { useEffect, useState } from "react";

type Trade = {
  id: string;
  symbol: string;
  entry_date: string;
  entry_price: number;
  quantity: number;
  stop_loss?: number;
  target?: number;
  exit_date?: string;
  exit_price?: number;
  notes?: string;
};

const KEY = "egx:journal";
// Same round-trip commission the calculator and the backtest assume (Thndr ≈ 0.8%).
const COMMISSION_RT = 0.008;

function tradePnl(t: Trade): number | null {
  if (t.exit_price == null) return null;
  const gross = (t.exit_price - t.entry_price) * t.quantity;
  const fees = ((t.entry_price + t.exit_price) * t.quantity * COMMISSION_RT) / 2;
  return gross - fees;
}

function read(): Trade[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(window.localStorage.getItem(KEY) ?? "[]");
  } catch {
    return [];
  }
}

function write(trades: Trade[]) {
  window.localStorage.setItem(KEY, JSON.stringify(trades));
}

export default function JournalPage() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [open, setOpen] = useState(false);

  useEffect(() => setTrades(read()), []);

  const onAdd = (t: Trade) => {
    const next = [t, ...trades];
    setTrades(next);
    write(next);
    setOpen(false);
  };

  const onClose = (id: string, exit_price: number, exit_date: string) => {
    const next = trades.map((t) =>
      t.id === id ? { ...t, exit_price, exit_date } : t,
    );
    setTrades(next);
    write(next);
  };

  const onDelete = (id: string) => {
    if (!confirm("حذف هذه الصفقة؟")) return;
    const next = trades.filter((t) => t.id !== id);
    setTrades(next);
    write(next);
  };

  const stats = computeStats(trades);

  return (
    <div className="space-y-4">
      <header className="panel p-5 flex items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">دفتر الصفقات</h1>
          <p className="text-muted text-sm mt-1">
            سجّل كل صفقة عشان تتعلم من نفسك. البيانات محفوظة محلياً على المتصفح. الربح/الخسارة بعد خصم عمولة
            0.8% رايح جاى.
          </p>
        </div>
        <button onClick={() => setOpen(true)} className="btn-primary">+ صفقة جديدة</button>
      </header>

      <section className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Stat label="إجمالى الصفقات" value={String(stats.total)} />
        <Stat label="مغلقة" value={String(stats.closed)} />
        <Stat label="نسبة النجاح" value={`${stats.winRate.toFixed(0)}%`} accent={stats.winRate >= 50 ? "text-success" : "text-danger"} />
        <Stat label="صافى الربح/الخسارة" value={`${stats.netPnl.toFixed(2)} ج`} accent={stats.netPnl >= 0 ? "text-success" : "text-danger"} />
      </section>

      {open && <NewTradeForm onAdd={onAdd} onCancel={() => setOpen(false)} />}

      {trades.length === 0 ? (
        <div className="panel p-10 text-center text-muted">لم تسجّل أى صفقة بعد.</div>
      ) : (
        <div className="panel overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-panel2 text-muted text-xs uppercase">
              <tr>
                <th className="px-3 py-3 text-right">السهم</th>
                <th className="px-3 py-3 text-right">تاريخ الدخول</th>
                <th className="px-3 py-3 text-right">سعر الدخول</th>
                <th className="px-3 py-3 text-right">الكمية</th>
                <th className="px-3 py-3 text-right">وقف</th>
                <th className="px-3 py-3 text-right">هدف</th>
                <th className="px-3 py-3 text-right">سعر الخروج</th>
                <th className="px-3 py-3 text-right">الربح/الخسارة</th>
                <th className="px-3 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {trades.map((t) => {
                const pnl = tradePnl(t);
                return (
                  <tr key={t.id} className="border-t border-border">
                    <td className="px-3 py-3 font-mono text-brand">{t.symbol}</td>
                    <td className="px-3 py-3">{t.entry_date}</td>
                    <td className="px-3 py-3">{t.entry_price.toFixed(2)}</td>
                    <td className="px-3 py-3">{t.quantity}</td>
                    <td className="px-3 py-3 text-danger">{t.stop_loss?.toFixed(2) ?? "—"}</td>
                    <td className="px-3 py-3 text-success">{t.target?.toFixed(2) ?? "—"}</td>
                    <td className="px-3 py-3">
                      {t.exit_price != null ? (
                        t.exit_price.toFixed(2)
                      ) : (
                        <CloseTradeMini onClose={(p, d) => onClose(t.id, p, d)} />
                      )}
                    </td>
                    <td className={`px-3 py-3 font-semibold ${pnl == null ? "" : pnl >= 0 ? "text-success" : "text-danger"}`}>
                      {pnl == null ? "—" : `${pnl.toFixed(2)} ج`}
                    </td>
                    <td className="px-3 py-3 text-left">
                      <button onClick={() => onDelete(t.id)} className="text-xs text-muted hover:text-danger">حذف</button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function computeStats(trades: Trade[]) {
  const closed = trades.filter((t) => t.exit_price != null);
  const wins = closed.filter((t) => (tradePnl(t) ?? 0) > 0);
  const netPnl = closed.reduce((acc, t) => acc + (tradePnl(t) ?? 0), 0);
  return {
    total: trades.length,
    closed: closed.length,
    winRate: closed.length ? (wins.length / closed.length) * 100 : 0,
    netPnl,
  };
}

function Stat({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div className="stat">
      <span className="stat-label">{label}</span>
      <span className={`stat-value ${accent ?? ""}`}>{value}</span>
    </div>
  );
}

function NewTradeForm({ onAdd, onCancel }: { onAdd: (t: Trade) => void; onCancel: () => void }) {
  const [symbol, setSymbol] = useState("");
  const [entry_date, setEntryDate] = useState(new Date().toISOString().slice(0, 10));
  const [entry_price, setEntry] = useState("");
  const [quantity, setQty] = useState("");
  const [stop_loss, setStop] = useState("");
  const [target, setTarget] = useState("");
  const [notes, setNotes] = useState("");

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!symbol || !entry_price || !quantity) return;
    onAdd({
      id: crypto.randomUUID(),
      symbol: symbol.toUpperCase(),
      entry_date,
      entry_price: parseFloat(entry_price),
      quantity: parseInt(quantity, 10),
      stop_loss: stop_loss ? parseFloat(stop_loss) : undefined,
      target: target ? parseFloat(target) : undefined,
      notes: notes || undefined,
    });
  };

  return (
    <form onSubmit={submit} className="panel p-5 grid grid-cols-1 sm:grid-cols-3 gap-3">
      <div>
        <label className="label">السهم</label>
        <input className="input font-mono" value={symbol} onChange={(e) => setSymbol(e.target.value)} placeholder="COMI" />
      </div>
      <div>
        <label className="label">تاريخ الدخول</label>
        <input type="date" className="input" value={entry_date} onChange={(e) => setEntryDate(e.target.value)} />
      </div>
      <div>
        <label className="label">سعر الدخول</label>
        <input type="number" step="0.01" className="input" value={entry_price} onChange={(e) => setEntry(e.target.value)} />
      </div>
      <div>
        <label className="label">الكمية</label>
        <input type="number" className="input" value={quantity} onChange={(e) => setQty(e.target.value)} />
      </div>
      <div>
        <label className="label">وقف الخسارة</label>
        <input type="number" step="0.01" className="input" value={stop_loss} onChange={(e) => setStop(e.target.value)} />
      </div>
      <div>
        <label className="label">الهدف</label>
        <input type="number" step="0.01" className="input" value={target} onChange={(e) => setTarget(e.target.value)} />
      </div>
      <div className="sm:col-span-3">
        <label className="label">ملاحظات (لماذا دخلت؟ ما هى الفرضية؟)</label>
        <textarea className="input min-h-[70px]" value={notes} onChange={(e) => setNotes(e.target.value)} />
      </div>
      <div className="sm:col-span-3 flex gap-2">
        <button type="submit" className="btn-primary">حفظ</button>
        <button type="button" onClick={onCancel} className="btn">إلغاء</button>
      </div>
    </form>
  );
}

function CloseTradeMini({ onClose }: { onClose: (price: number, date: string) => void }) {
  const [open, setOpen] = useState(false);
  const [price, setPrice] = useState("");
  const today = new Date().toISOString().slice(0, 10);
  if (!open) {
    return <button onClick={() => setOpen(true)} className="text-xs text-brand hover:underline">إغلاق...</button>;
  }
  return (
    <div className="flex items-center gap-1">
      <input
        type="number"
        step="0.01"
        className="input !py-1 !px-2 w-20 text-xs"
        value={price}
        onChange={(e) => setPrice(e.target.value)}
        placeholder="سعر"
      />
      <button
        onClick={() => price && onClose(parseFloat(price), today)}
        className="text-xs text-success"
      >
        ✓
      </button>
    </div>
  );
}
