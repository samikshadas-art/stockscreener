"use client";
import { Star } from "lucide-react";

export default function WatchlistPage() {
  return (
    <div className="max-w-4xl mx-auto py-10 text-center text-muted-foreground">
      <Star className="h-12 w-12 mx-auto mb-4 opacity-20" />
      <h1 className="text-xl font-bold text-foreground mb-2">Watchlist</h1>
      <p className="text-sm">Watchlist feature coming in Phase 6. You can add stocks here to monitor live prices and set alerts.</p>
    </div>
  );
}
