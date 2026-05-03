"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { portfolioApi } from "@/lib/api";
import { formatLargeNumber, formatPct, gainColor, gainBg } from "@/lib/formatters";
import { cn } from "@/lib/utils";
import { useState } from "react";
import { Plus, TrendingUp, TrendingDown, Briefcase } from "lucide-react";
import Link from "next/link";

export default function PortfolioPage() {
  const qc = useQueryClient();
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");

  const { data: portfolios, isLoading } = useQuery({
    queryKey: ["portfolios"],
    queryFn: portfolioApi.list,
  });

  const createMutation = useMutation({
    mutationFn: (name: string) => portfolioApi.create({ name, benchmark: "NIFTY50", currency: "INR" }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["portfolios"] }); setCreating(false); setNewName(""); },
  });

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Portfolio</h1>
          <p className="text-muted-foreground text-sm mt-0.5">Track your holdings, P&amp;L, and allocation</p>
        </div>
        <button
          onClick={() => setCreating(true)}
          className="flex items-center gap-2 bg-primary text-primary-foreground px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-4 w-4" />
          New Portfolio
        </button>
      </div>

      {creating && (
        <div className="bg-card border border-border rounded-xl p-4 flex items-center gap-3">
          <Briefcase className="h-5 w-5 text-muted-foreground" />
          <input
            autoFocus
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Portfolio name…"
            className="flex-1 bg-muted rounded px-3 py-1.5 text-sm outline-none focus:ring-1 ring-primary"
            onKeyDown={(e) => { if (e.key === "Enter" && newName.trim()) createMutation.mutate(newName.trim()); }}
          />
          <button
            onClick={() => createMutation.mutate(newName.trim())}
            disabled={!newName.trim()}
            className="bg-primary text-primary-foreground px-4 py-1.5 rounded text-sm font-medium disabled:opacity-40"
          >
            Create
          </button>
          <button onClick={() => setCreating(false)} className="text-muted-foreground hover:text-foreground text-sm">
            Cancel
          </button>
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      ) : !portfolios || portfolios.length === 0 ? (
        <div className="text-center py-20 text-muted-foreground">
          <Briefcase className="h-12 w-12 mx-auto mb-3 opacity-20" />
          <p className="font-medium">No portfolios yet</p>
          <p className="text-sm mt-1">Create one and add your holdings to start tracking P&amp;L.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {portfolios.map((p: any) => (
            <Link
              key={p.id}
              href={`/portfolio/${p.id}`}
              className="bg-card border border-border rounded-xl p-5 hover:border-primary/30 hover:bg-accent/20 transition-all group"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-semibold group-hover:text-primary transition-colors">{p.name}</h3>
                  <p className="text-xs text-muted-foreground mt-0.5">vs {p.benchmark} • {p.holding_count} holdings</p>
                </div>
                <span className="text-xs bg-muted text-muted-foreground px-2 py-0.5 rounded">{p.currency}</span>
              </div>
              <p className="text-xs text-muted-foreground">Click to view performance →</p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
