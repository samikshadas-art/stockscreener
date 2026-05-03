"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { portfolioApi, stocksApi } from "@/lib/api";
import { formatLargeNumber, formatPct, formatNumber, gainColor, gainBg } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { useState } from "react";
import { Plus, Trash2, TrendingUp, TrendingDown } from "lucide-react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";

const PIE_COLORS = ["#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#f97316"];

export default function PortfolioDetailPage({ params }: { params: { id: string } }) {
  const qc = useQueryClient();
  const [addingHolding, setAddingHolding] = useState(false);
  const [holdingForm, setHoldingForm] = useState({ symbol: "", exchange: "NSE", quantity: "", price: "" });
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [selectedStock, setSelectedStock] = useState<any>(null);

  const { data: perf, isLoading } = useQuery({
    queryKey: ["portfolio-performance", params.id],
    queryFn: () => portfolioApi.performance(params.id),
    refetchInterval: 60_000,
  });

  const addMutation = useMutation({
    mutationFn: (data: any) => portfolioApi.addHolding(params.id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["portfolio-performance", params.id] });
      setAddingHolding(false);
      setHoldingForm({ symbol: "", exchange: "NSE", quantity: "", price: "" });
      setSelectedStock(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (holdingId: number) => portfolioApi.deleteHolding(params.id, holdingId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["portfolio-performance", params.id] }),
  });

  const searchStocks = async (q: string) => {
    if (q.length < 1) { setSearchResults([]); return; }
    const res = await stocksApi.search(q, holdingForm.exchange);
    setSearchResults(res);
  };

  if (isLoading) {
    return <div className="flex items-center justify-center h-64"><div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin" /></div>;
  }

  if (!perf) return <div className="text-center text-muted-foreground py-20">Portfolio not found.</div>;

  const isUp = perf.total_gain >= 0;
  const sectorData = Object.entries(perf.sector_allocation).map(([name, value]) => ({ name, value }));

  return (
    <div className="max-w-6xl mx-auto space-y-5">
      {/* Header summary */}
      <div className="bg-card border border-border rounded-xl p-5">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-xl font-bold">{perf.name}</h1>
            <p className="text-xs text-muted-foreground mt-0.5">vs {perf.benchmark} benchmark</p>
          </div>
          <button
            onClick={() => setAddingHolding(true)}
            className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-lg text-sm font-medium"
          >
            <Plus className="h-4 w-4" /> Add Holding
          </button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-5">
          {[
            { label: "Invested", value: formatLargeNumber(perf.total_invested) },
            { label: "Current Value", value: formatLargeNumber(perf.current_value), bold: true },
            {
              label: "Total Gain/Loss",
              value: formatLargeNumber(perf.total_gain),
              sub: formatPct(perf.total_gain_pct),
              color: gainColor(perf.total_gain),
            },
            {
              label: "Today's Gain",
              value: formatLargeNumber(perf.today_gain),
              sub: formatPct(perf.today_gain_pct),
              color: gainColor(perf.today_gain),
            },
          ].map(({ label, value, sub, color, bold }) => (
            <div key={label}>
              <div className="text-xs text-muted-foreground mb-1">{label}</div>
              <div className={cn("text-lg font-semibold font-mono", bold ? "" : color, color)}>{value}</div>
              {sub && <div className={cn("text-xs", color)}>{sub}</div>}
            </div>
          ))}
        </div>
      </div>

      {/* Add holding form */}
      {addingHolding && (
        <div className="bg-card border border-primary/30 rounded-xl p-4 space-y-3">
          <h3 className="font-semibold text-sm">Add Holding</h3>
          <div className="flex gap-2 flex-wrap">
            <div className="relative flex-1 min-w-40">
              <input
                placeholder="Search symbol…"
                value={holdingForm.symbol}
                onChange={(e) => { setHoldingForm(f => ({ ...f, symbol: e.target.value })); searchStocks(e.target.value); }}
                className="w-full bg-muted rounded px-3 py-1.5 text-sm outline-none focus:ring-1 ring-primary"
              />
              {searchResults.length > 0 && (
                <div className="absolute top-full left-0 right-0 bg-card border border-border rounded-lg shadow-xl z-20 overflow-hidden">
                  {searchResults.map((s) => (
                    <button
                      key={s.id}
                      onClick={() => { setSelectedStock(s); setHoldingForm(f => ({ ...f, symbol: s.symbol, exchange: s.exchange })); setSearchResults([]); }}
                      className="w-full text-left px-3 py-2 text-sm hover:bg-accent flex justify-between"
                    >
                      <span className="font-medium">{s.symbol}</span>
                      <span className="text-muted-foreground text-xs">{s.exchange}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
            <input
              type="number"
              placeholder="Qty"
              value={holdingForm.quantity}
              onChange={(e) => setHoldingForm(f => ({ ...f, quantity: e.target.value }))}
              className="w-24 bg-muted rounded px-3 py-1.5 text-sm outline-none focus:ring-1 ring-primary"
            />
            <input
              type="number"
              placeholder="Avg Price"
              value={holdingForm.price}
              onChange={(e) => setHoldingForm(f => ({ ...f, price: e.target.value }))}
              className="w-32 bg-muted rounded px-3 py-1.5 text-sm outline-none focus:ring-1 ring-primary"
            />
            <button
              onClick={() => {
                if (!selectedStock || !holdingForm.quantity || !holdingForm.price) return;
                addMutation.mutate({
                  stock_id: selectedStock.id,
                  quantity: parseFloat(holdingForm.quantity),
                  avg_buy_price: parseFloat(holdingForm.price),
                });
              }}
              disabled={addMutation.isPending}
              className="bg-primary text-primary-foreground px-4 py-1.5 rounded text-sm font-medium disabled:opacity-40"
            >
              Add
            </button>
            <button onClick={() => setAddingHolding(false)} className="text-muted-foreground text-sm hover:text-foreground">Cancel</button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Holdings table */}
        <div className="lg:col-span-2 bg-card border border-border rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-border">
            <h2 className="font-semibold text-sm">Holdings</h2>
          </div>
          {perf.holdings.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground text-sm">No holdings yet. Add your first holding above.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full screener-table">
                <thead className="border-b border-border">
                  <tr>
                    {["Stock", "Qty", "Avg Price", "Current", "Value", "Gain", "Weight"].map((h) => (
                      <th key={h} className="px-3 py-2.5 text-left">{h}</th>
                    ))}
                    <th className="px-3 py-2.5" />
                  </tr>
                </thead>
                <tbody>
                  {perf.holdings.map((h: any) => (
                    <tr key={h.id} className="border-b border-border/50 hover:bg-accent/20 transition-colors">
                      <td className="px-3 py-2.5">
                        <div className="font-medium text-sm">{h.symbol}</div>
                        <div className="text-xs text-muted-foreground truncate max-w-[100px]">{h.name}</div>
                      </td>
                      <td className="px-3 py-2.5 text-sm font-mono">{h.quantity}</td>
                      <td className="px-3 py-2.5 text-sm font-mono">₹{formatNumber(h.avg_buy_price)}</td>
                      <td className="px-3 py-2.5 text-sm font-mono">₹{formatNumber(h.current_price)}</td>
                      <td className="px-3 py-2.5 text-sm font-mono">{formatLargeNumber(h.current_value)}</td>
                      <td className="px-3 py-2.5">
                        <span className={cn("text-xs px-1.5 py-0.5 rounded", gainBg(h.gain))}>
                          {formatPct(h.gain_pct)}
                        </span>
                      </td>
                      <td className="px-3 py-2.5 text-xs text-muted-foreground">{h.weight_pct}%</td>
                      <td className="px-3 py-2.5">
                        <button
                          onClick={() => deleteMutation.mutate(h.id)}
                          className="text-muted-foreground hover:text-red-400 transition-colors"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Allocation chart */}
        <div className="bg-card border border-border rounded-xl p-4">
          <h2 className="font-semibold text-sm mb-4">Sector Allocation</h2>
          {sectorData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={sectorData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={2} dataKey="value">
                  {sectorData.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(v: any) => `${v}%`} contentStyle={{ background: "hsl(222 47% 11%)", border: "1px solid hsl(217 33% 17%)", borderRadius: "8px" }} />
                <Legend iconSize={8} wrapperStyle={{ fontSize: "11px" }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[220px] flex items-center justify-center text-muted-foreground text-sm">Add holdings to see allocation</div>
          )}
        </div>
      </div>
    </div>
  );
}
