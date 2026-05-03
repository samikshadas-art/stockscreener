"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart2, Search, Star, TrendingUp, Bell, Settings } from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/screener",  label: "Screener",  icon: Search },
  { href: "/portfolio", label: "Portfolio", icon: BarChart2 },
  { href: "/watchlist", label: "Watchlist", icon: Star },
  { href: "/alerts",    label: "Alerts",    icon: Bell },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden md:flex flex-col w-56 border-r border-border bg-card shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-2 px-4 py-5 border-b border-border">
        <TrendingUp className="h-5 w-5 text-primary" />
        <span className="font-bold text-sm tracking-tight">StockScreener</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 px-2 space-y-1">
        {navItems.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
              pathname.startsWith(href)
                ? "bg-primary/15 text-primary"
                : "text-muted-foreground hover:bg-accent hover:text-foreground"
            )}
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        ))}
      </nav>

      {/* Bottom */}
      <div className="px-2 py-4 border-t border-border">
        <Link
          href="/settings"
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
        >
          <Settings className="h-4 w-4" />
          Settings
        </Link>
      </div>
    </aside>
  );
}
