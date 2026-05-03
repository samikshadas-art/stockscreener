import Link from "next/link";
import { TrendingUp, BarChart2, Search, Star } from "lucide-react";

const cards = [
  {
    href: "/screener",
    icon: Search,
    title: "Stock Screener",
    description: "Filter across 40+ parameters. Find your next trade.",
    color: "from-blue-500/20 to-blue-600/5",
    border: "border-blue-500/20",
  },
  {
    href: "/portfolio",
    icon: BarChart2,
    title: "Portfolio",
    description: "Track P&L, sector allocation, and vs benchmark.",
    color: "from-emerald-500/20 to-emerald-600/5",
    border: "border-emerald-500/20",
  },
  {
    href: "/watchlist",
    icon: Star,
    title: "Watchlist",
    description: "Monitor your shortlisted stocks with live prices.",
    color: "from-amber-500/20 to-amber-600/5",
    border: "border-amber-500/20",
  },
];

export default function Home() {
  return (
    <div className="max-w-4xl mx-auto py-8">
      <div className="mb-10">
        <div className="flex items-center gap-2 mb-3">
          <TrendingUp className="h-7 w-7 text-primary" />
          <h1 className="text-3xl font-bold tracking-tight">StockScreener</h1>
        </div>
        <p className="text-muted-foreground text-lg">
          Institutional-grade equity analysis for Indian &amp; US markets. Screen, research, and track — all in one place.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10">
        {cards.map(({ href, icon: Icon, title, description, color, border }) => (
          <Link
            key={href}
            href={href}
            className={`group relative block rounded-xl border ${border} bg-gradient-to-br ${color} p-6 transition-all hover:scale-[1.02] hover:shadow-lg`}
          >
            <Icon className="h-6 w-6 text-foreground/70 mb-3 group-hover:text-primary transition-colors" />
            <h2 className="font-semibold text-lg mb-1">{title}</h2>
            <p className="text-sm text-muted-foreground">{description}</p>
          </Link>
        ))}
      </div>

      <div className="rounded-xl border border-border bg-card p-6">
        <h3 className="font-semibold mb-3 text-muted-foreground text-sm uppercase tracking-wider">Quick Start</h3>
        <ol className="space-y-2 text-sm text-foreground/80">
          <li><span className="font-mono text-primary">1.</span> Run the backend seed: <code className="bg-muted px-2 py-0.5 rounded text-xs">python scripts/seed_stocks.py --exchange NSE --limit 50</code></li>
          <li><span className="font-mono text-primary">2.</span> Open <Link href="/screener" className="text-primary underline">Screener</Link> and add filters like <em>P/E &lt; 20</em> and <em>ROE &gt; 15%</em></li>
          <li><span className="font-mono text-primary">3.</span> Click any stock to see its full analysis page</li>
          <li><span className="font-mono text-primary">4.</span> Add holdings to your <Link href="/portfolio" className="text-primary underline">Portfolio</Link> to track P&amp;L</li>
        </ol>
      </div>
    </div>
  );
}
