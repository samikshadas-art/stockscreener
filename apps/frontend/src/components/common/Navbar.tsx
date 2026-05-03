"use client";
import { Search } from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { stocksApi } from "@/lib/api";

export function Navbar() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [open, setOpen] = useState(false);
  const router = useRouter();

  const handleSearch = async (q: string) => {
    setQuery(q);
    if (q.length < 1) { setResults([]); setOpen(false); return; }
    try {
      const data = await stocksApi.search(q);
      setResults(data);
      setOpen(true);
    } catch { setResults([]); }
  };

  const go = (symbol: string, exchange: string) => {
    setOpen(false);
    setQuery("");
    router.push(`/stocks/${symbol}?exchange=${exchange}`);
  };

  return (
    <header className="h-14 border-b border-border bg-card flex items-center px-4 gap-4 shrink-0">
      {/* Search */}
      <div className="relative flex-1 max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          value={query}
          onChange={(e) => handleSearch(e.target.value)}
          onBlur={() => setTimeout(() => setOpen(false), 200)}
          placeholder="Search stocks…"
          className="w-full pl-9 pr-3 py-1.5 bg-muted rounded-lg text-sm outline-none focus:ring-1 ring-primary placeholder:text-muted-foreground"
        />
        {open && results.length > 0 && (
          <div className="absolute top-full mt-1 left-0 right-0 bg-card border border-border rounded-lg shadow-xl z-50 overflow-hidden">
            {results.map((s) => (
              <button
                key={`${s.symbol}-${s.exchange}`}
                onClick={() => go(s.symbol, s.exchange)}
                className="flex items-center gap-3 w-full px-4 py-2.5 hover:bg-accent text-left transition-colors"
              >
                <div>
                  <div className="text-sm font-medium">{s.symbol}</div>
                  <div className="text-xs text-muted-foreground truncate max-w-[200px]">{s.name}</div>
                </div>
                <span className="ml-auto text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded">
                  {s.exchange}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Market status */}
      <div className="hidden md:flex items-center gap-1.5 text-xs text-muted-foreground ml-auto">
        <span className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse" />
        Market Open
      </div>
    </header>
  );
}
