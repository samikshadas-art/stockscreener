/**
 * All screener filter field definitions.
 * Drives the FilterPanel UI — category, label, type, operators.
 */

export type FilterOperator = "gt" | "lt" | "gte" | "lte" | "eq" | "neq" | "between";

export interface FilterField {
  field: string;
  label: string;
  category: "Fundamental" | "Technical" | "Price" | "Quality";
  type: "number" | "pct" | "score";
  operators: FilterOperator[];
  unit?: string;
  description?: string;
  min?: number;
  max?: number;
}

export const FILTER_FIELDS: FilterField[] = [
  // ── Fundamental ──────────────────────────────────────────────
  {
    field: "market_cap",
    label: "Market Cap",
    category: "Fundamental",
    type: "number",
    unit: "₹",
    operators: ["gt", "lt", "between"],
    description: "Total market capitalisation in INR",
  },
  {
    field: "pe_ratio",
    label: "P/E Ratio",
    category: "Fundamental",
    type: "number",
    operators: ["gt", "lt", "between"],
    min: 0,
    max: 200,
  },
  {
    field: "forward_pe",
    label: "Forward P/E",
    category: "Fundamental",
    type: "number",
    operators: ["gt", "lt", "between"],
  },
  {
    field: "pb_ratio",
    label: "P/B Ratio",
    category: "Fundamental",
    type: "number",
    operators: ["gt", "lt", "between"],
  },
  {
    field: "ev_ebitda",
    label: "EV/EBITDA",
    category: "Fundamental",
    type: "number",
    operators: ["gt", "lt", "between"],
  },
  {
    field: "roe",
    label: "ROE (%)",
    category: "Fundamental",
    type: "pct",
    unit: "%",
    operators: ["gt", "lt", "between"],
    description: "Return on Equity",
  },
  {
    field: "roce",
    label: "ROCE (%)",
    category: "Fundamental",
    type: "pct",
    unit: "%",
    operators: ["gt", "lt", "between"],
  },
  {
    field: "roa",
    label: "ROA (%)",
    category: "Fundamental",
    type: "pct",
    unit: "%",
    operators: ["gt", "lt", "between"],
  },
  {
    field: "net_margin",
    label: "Net Margin (%)",
    category: "Fundamental",
    type: "pct",
    unit: "%",
    operators: ["gt", "lt", "between"],
  },
  {
    field: "debt_to_equity",
    label: "Debt/Equity",
    category: "Fundamental",
    type: "number",
    operators: ["gt", "lt", "between"],
  },
  {
    field: "current_ratio",
    label: "Current Ratio",
    category: "Fundamental",
    type: "number",
    operators: ["gt", "lt", "between"],
  },
  {
    field: "eps",
    label: "EPS",
    category: "Fundamental",
    type: "number",
    operators: ["gt", "lt", "between"],
  },
  {
    field: "eps_growth_yoy",
    label: "EPS Growth YoY (%)",
    category: "Fundamental",
    type: "pct",
    unit: "%",
    operators: ["gt", "lt", "between"],
  },
  {
    field: "revenue_growth_yoy",
    label: "Revenue Growth YoY (%)",
    category: "Fundamental",
    type: "pct",
    unit: "%",
    operators: ["gt", "lt", "between"],
  },
  {
    field: "dividend_yield",
    label: "Dividend Yield (%)",
    category: "Fundamental",
    type: "pct",
    unit: "%",
    operators: ["gt", "lt", "between"],
  },
  // ── Technical ─────────────────────────────────────────────────
  {
    field: "rsi_14",
    label: "RSI (14)",
    category: "Technical",
    type: "number",
    operators: ["gt", "lt", "between"],
    min: 0,
    max: 100,
    description: "RSI below 30 = oversold, above 70 = overbought",
  },
  {
    field: "macd",
    label: "MACD",
    category: "Technical",
    type: "number",
    operators: ["gt", "lt", "between"],
  },
  {
    field: "sma_20",
    label: "SMA 20",
    category: "Technical",
    type: "number",
    operators: ["gt", "lt"],
  },
  {
    field: "sma_50",
    label: "SMA 50",
    category: "Technical",
    type: "number",
    operators: ["gt", "lt"],
  },
  {
    field: "sma_200",
    label: "SMA 200",
    category: "Technical",
    type: "number",
    operators: ["gt", "lt"],
  },
  {
    field: "beta",
    label: "Beta",
    category: "Technical",
    type: "number",
    operators: ["gt", "lt", "between"],
  },
  {
    field: "relative_volume",
    label: "Relative Volume",
    category: "Technical",
    type: "number",
    operators: ["gt", "lt", "between"],
    description: "Volume relative to 20-day average",
  },
  {
    field: "volatility_30d",
    label: "Volatility 30D (%)",
    category: "Technical",
    type: "pct",
    unit: "%",
    operators: ["gt", "lt", "between"],
  },
  // ── Price ─────────────────────────────────────────────────────
  {
    field: "pct_change_1d",
    label: "Change 1D (%)",
    category: "Price",
    type: "pct",
    unit: "%",
    operators: ["gt", "lt", "between"],
  },
  {
    field: "pct_change_1w",
    label: "Change 1W (%)",
    category: "Price",
    type: "pct",
    unit: "%",
    operators: ["gt", "lt", "between"],
  },
  {
    field: "pct_change_1m",
    label: "Change 1M (%)",
    category: "Price",
    type: "pct",
    unit: "%",
    operators: ["gt", "lt", "between"],
  },
  {
    field: "pct_change_3m",
    label: "Change 3M (%)",
    category: "Price",
    type: "pct",
    unit: "%",
    operators: ["gt", "lt", "between"],
  },
  {
    field: "pct_change_1y",
    label: "Change 1Y (%)",
    category: "Price",
    type: "pct",
    unit: "%",
    operators: ["gt", "lt", "between"],
  },
  // ── Quality ───────────────────────────────────────────────────
  {
    field: "piotroski_score",
    label: "Piotroski Score",
    category: "Quality",
    type: "score",
    operators: ["gt", "gte", "lt", "eq", "between"],
    min: 0,
    max: 9,
    description: "Score 0-9: ≥7 = high quality",
  },
  {
    field: "altman_z_score",
    label: "Altman Z-Score",
    category: "Quality",
    type: "number",
    operators: ["gt", "lt", "between"],
    description: ">2.99 = safe zone; <1.81 = distress",
  },
  {
    field: "composite_score",
    label: "Composite Score",
    category: "Quality",
    type: "score",
    operators: ["gt", "gte", "lt", "between"],
    min: 0,
    max: 100,
    description: "Proprietary quality + technical + momentum score",
  },
];

export const CATEGORIES = ["Fundamental", "Technical", "Price", "Quality"] as const;

export const OPERATOR_LABELS: Record<FilterOperator, string> = {
  gt: ">",
  lt: "<",
  gte: "≥",
  lte: "≤",
  eq: "=",
  neq: "≠",
  between: "between",
};

export const DEFAULT_COLUMNS = [
  "symbol", "name", "pct_change_1d", "market_cap",
  "pe_ratio", "roe", "rsi_14", "composite_score",
];
