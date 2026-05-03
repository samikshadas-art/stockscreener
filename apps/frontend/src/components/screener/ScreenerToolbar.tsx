"use client";
import { Loader2, Download, Save } from "lucide-react";
import { useScreenerStore } from "@/store/screenerStore";

interface Props {
  total?: number;
  isLoading: boolean;
}

export function ScreenerToolbar({ total, isLoading }: Props) {
  const { exchange, setExchange } = useScreenerStore();
  const exchanges = ["NSE", "BSE", "NYSE", "NASDAQ"];

  return (
    <div className="flex items-center gap-3 flex-wrap">
      <div className="flex items-center gap-1.5">
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
        ) : (
          <span className="text-sm text-muted-foreground">
            {total !== undefined ? (
              <><span className="font-semibold text-foreground">{total.toLocaleString()}</span> stocks</>
            ) : "—"}
          </span>
        )}
      </div>

      {/* Exchange toggles */}
      <div className="flex gap-1 ml-2">
        {exchanges.map((ex) => (
          <button
            key={ex}
            onClick={() => {
              const next = exchange.includes(ex)
                ? exchange.filter((e) => e !== ex)
                : [...exchange, ex];
              if (next.length > 0) setExchange(next);
            }}
            className={`text-xs px-2.5 py-1 rounded font-medium transition-colors border ${
              exchange.includes(ex)
                ? "bg-primary/15 border-primary/30 text-primary"
                : "border-border text-muted-foreground hover:bg-accent"
            }`}
          >
            {ex}
          </button>
        ))}
      </div>

      <div className="ml-auto flex items-center gap-2">
        <button className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors border border-border rounded px-3 py-1.5">
          <Save className="h-3.5 w-3.5" />
          Save
        </button>
        <button className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors border border-border rounded px-3 py-1.5">
          <Download className="h-3.5 w-3.5" />
          Export
        </button>
      </div>
    </div>
  );
}
