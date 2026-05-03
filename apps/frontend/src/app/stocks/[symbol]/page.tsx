"use client";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { stocksApi } from "@/lib/api";
import { formatLargeNumber, formatNumber, formatPct, gainColor, gainBg } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { ExternalLink, TrendingUp, TrendingDown } from "lucide-react";

export default function StockPage({ params }: { params: { symbol: string } }) {
  const searchParams = useSearchParams();
  const exchange = searchParams.get("exchange") || "NSE";
  const symbol = params.symbol.toUpperCase();

  const { data: stock, isLoading } = useQuery({
    queryKey: ["stock", symbol, exchange],
    queryFn: () => stocksApi.overview(symbol, exchange),
  });

  const { data: history } = useQuery({
    queryKey: ["price-history", symbol, exchange],
    queryFn: () => stocksApi.priceHistory(symbol, exchange),
  });

  const { data: peers } = useQuery({
    queryKey: ["peers", symbol, exchange],
    queryFn: () => stocksApi.peers(symbol, exchange),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!stock) {
    return <div className="text-center text-muted-foreground py-20">Stock not found.</div>;
  }

  const isUp = (stock.pct_change_1d ?? 0) >= 0;

  return (
    <div className="max-w-6xl mx-auto space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-2xl font-bold">{stock.symbol}</h1>
            <span className="text-xs bg-muted text-muted-foreground px-2 py-0.5 rounded">{stock.exchange}</span>
            {stock.sector && <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded">{stock.sector}</span>}
          </div>
          <p className="text-muted-foreground text-sm">{stock.name}</p>
          {stock.website && (
            <a href={stock.website} target="_blank" rel="noreferrer"
              className="flex items-center gap-1 text-xs text-primary mt-1 hover:underline">
              {stock.website} <ExternalLink className="h-3 w-3" />
            </a>
          )}
        </div>

        <div className="text-right">
          {stock.current_price ? (
            <>
              <div className="text-3xl font-bold font-mono">
                {stock.currency === "INR" ? "₹" : "$"}{stock.current_price?.toLocaleString()}
              </div>
              <div className={cn("flex items-center gap-1 justify-end text-sm mt-0.5", gainColor(stock.pct_change_1d))}>
                {isUp ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                {formatPct(stock.pct_change_1d)} today
              </div>
            </>
          ) : (
            <div className="text-muted-foreground text-sm">Price unavailable</div>
          )}
        </div>
      </div>

      {/* Key metrics row */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        {[
          { label: "Market Cap", value: formatLargeNumber(stock.market_cap) },
          { label: "P/E Ratio", value: formatNumber(stock.pe_ratio) },
          { label: "P/B Ratio", value: formatNumber(stock.pb_ratio) },
          { label: "ROE", value: stock.roe ? `${formatNumber(stock.roe)}%` : "—" },
          { label: "Div Yield", value: stock.dividend_yield ? `${formatNumber(stock.dividend_yield)}%` : "—" },
          { label: "52W High", value: formatNumber(stock.week_52_high) },
          { label: "52W Low", value: formatNumber(stock.week_52_low) },
          { label: "RSI (14)", value: formatNumber(stock.rsi_14, 1) },
          { label: "SMA 50", value: formatNumber(stock.sma_50) },
          { label: "SMA 200", value: formatNumber(stock.sma_200) },
          { label: "Volume", value: stock.volume?.toLocaleString() ?? "—" },
          {
            label: "Quality Score",
            value: stock.composite_score != null ? `${Math.round(stock.composite_score)}/100` : "—",
            highlight: stock.composite_score != null && stock.composite_score >= 70 ? "text-green-500" : "",
          },
        ].map(({ label, value, highlight }) => (
          <div key={label} className="bg-card border border-border rounded-lg px-3 py-2.5">
            <div className="text-xs text-muted-foreground mb-0.5">{label}</div>
            <div className={cn("text-sm font-semibold font-mono", highlight)}>{value}</div>
          </div>
        ))}
      </div>

      {/* Chart placeholder */}
      <div className="bg-card border border-border rounded-xl p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold">Price Chart</h2>
          <div className="flex gap-1 text-xs">
            {["1W", "1M", "3M", "6M", "1Y", "5Y"].map((p) => (
              <button key={p} className="px-2.5 py-1 rounded hover:bg-accent text-muted-foreground transition-colors">
                {p}
              </button>
            ))}
          </div>
        </div>
        {history?.data && history.data.length > 0 ? (
          <div className="h-48 flex items-end gap-px overflow-hidden">
            {history.data.slice(-60).map((d: any, i: number) => {
              const allCloses = history.data.map((x: any) => x.close);
              const min = Math.min(...allCloses);
              const max = Math.max(...allCloses);
              const height = ((d.close - min) / (max - min || 1)) * 100;
              const isGreen = i === 0 || d.close >= history.data[Math.max(0, i - 1)].close;
              return (
                <div
                  key={i}
                  className={cn("flex-1 rounded-t", isGreen ? "bg-green-500/60" : "bg-red-500/60")}
                  style={{ height: `${Math.max(4, height)}%` }}
                  title={`${d.date}: ₹${d.close}`}
                />
              );
            })}
          </div>
        ) : (
          <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">
            Chart data will appear after price history is seeded.
          </div>
        )}
      </div>

      {/* Description */}
      {stock.description && (
        <div className="bg-card border border-border rounded-xl p-4">
          <h2 className="font-semibold mb-2">About</h2>
          <p className="text-sm text-muted-foreground leading-relaxed">{stock.description}</p>
        </div>
      )}

      {/* Peers */}
      {peers && peers.length > 0 && (
        <div className="bg-card border border-border rounded-xl p-4">
          <h2 className="font-semibold mb-3">Sector Peers</h2>
          <div className="flex flex-wrap gap-2">
            {peers.map((p: any) => (
              <a
                key={`${p.symbol}-${p.exchange}`}
                href={`/stocks/${p.symbol}?exchange=${p.exchange}`}
                className="px-3 py-1.5 bg-muted rounded-lg text-sm hover:bg-accent transition-colors"
              >
                {p.symbol}
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
