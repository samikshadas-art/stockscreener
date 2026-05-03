/**
 * Number + currency formatters for financial data.
 */

export function formatCurrency(
  value: number | undefined | null,
  currency = "INR",
  compact = false
): string {
  if (value == null) return "—";
  const opts: Intl.NumberFormatOptions = {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
    minimumFractionDigits: 0,
  };
  if (compact) {
    opts.notation = "compact";
    opts.maximumFractionDigits = 1;
  }
  return new Intl.NumberFormat("en-IN", opts).format(value);
}

export function formatNumber(
  value: number | undefined | null,
  decimals = 2
): string {
  if (value == null) return "—";
  return new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: decimals,
    minimumFractionDigits: 0,
  }).format(value);
}

export function formatLargeNumber(value: number | undefined | null): string {
  if (value == null) return "—";
  if (Math.abs(value) >= 1e12) return `₹${(value / 1e12).toFixed(2)}T`;
  if (Math.abs(value) >= 1e9) return `₹${(value / 1e9).toFixed(2)}B`;
  if (Math.abs(value) >= 1e7) return `₹${(value / 1e7).toFixed(2)}Cr`;
  if (Math.abs(value) >= 1e5) return `₹${(value / 1e5).toFixed(2)}L`;
  return formatCurrency(value);
}

export function formatPct(
  value: number | undefined | null,
  decimals = 2,
  showSign = true
): string {
  if (value == null) return "—";
  const sign = showSign && value > 0 ? "+" : "";
  return `${sign}${value.toFixed(decimals)}%`;
}

export function formatVolume(value: number | undefined | null): string {
  if (value == null) return "—";
  if (value >= 1e7) return `${(value / 1e7).toFixed(2)}Cr`;
  if (value >= 1e5) return `${(value / 1e5).toFixed(2)}L`;
  if (value >= 1e3) return `${(value / 1e3).toFixed(1)}K`;
  return value.toString();
}

export function gainColor(value: number | undefined | null): string {
  if (value == null) return "text-slate-400";
  if (value > 0) return "text-green-500";
  if (value < 0) return "text-red-500";
  return "text-slate-400";
}

export function gainBg(value: number | undefined | null): string {
  if (value == null) return "bg-slate-800";
  if (value > 0) return "bg-green-500/10 text-green-500";
  if (value < 0) return "bg-red-500/10 text-red-500";
  return "bg-slate-800 text-slate-400";
}
