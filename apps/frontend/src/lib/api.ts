/**
 * Typed API client.
 * Proxies through Next.js /api rewrite → FastAPI backend.
 */
import axios from "axios";

const BASE = process.env.NEXT_PUBLIC_API_URL
  ? `${process.env.NEXT_PUBLIC_API_URL}/v1`
  : "/api";

export const apiClient = axios.create({
  baseURL: BASE,
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

// ─── Types ────────────────────────────────────────────────────────────────

export interface FilterCondition {
  field: string;
  operator: "gt" | "lt" | "gte" | "lte" | "eq" | "neq" | "between" | "in";
  value: number | number[] | string | string[];
}

export interface ScreenerRunRequest {
  filters: FilterCondition[];
  logic: "AND" | "OR";
  exchange: string[];
  sort_by: string;
  sort_order: "asc" | "desc";
  page: number;
  per_page: number;
}

export interface ScreenerResultRow {
  id: number;
  symbol: string;
  exchange: string;
  name: string;
  sector?: string;
  market_cap_category?: string;
  currency: string;
  current_price?: number;
  pct_change_1d?: number;
  market_cap?: number;
  pe_ratio?: number;
  forward_pe?: number;
  pb_ratio?: number;
  ev_ebitda?: number;
  roe?: number;
  roce?: number;
  debt_to_equity?: number;
  eps?: number;
  eps_growth_yoy?: number;
  revenue_growth_yoy?: number;
  dividend_yield?: number;
  piotroski_score?: number;
  composite_score?: number;
  rsi_14?: number;
  macd?: number;
  sma_20?: number;
  sma_50?: number;
  sma_200?: number;
  week_52_high?: number;
  week_52_low?: number;
  pct_change_1w?: number;
  pct_change_1m?: number;
  pct_change_1y?: number;
  volatility_30d?: number;
  beta?: number;
}

export interface ScreenerRunResponse {
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  results: ScreenerResultRow[];
}

export interface StockOverview {
  id: number;
  symbol: string;
  exchange: string;
  name: string;
  sector?: string;
  industry?: string;
  currency: string;
  description?: string;
  website?: string;
  logo_url?: string;
  current_price?: number;
  pct_change_1d?: number;
  volume?: number;
  week_52_high?: number;
  week_52_low?: number;
  market_cap?: number;
  pe_ratio?: number;
  pb_ratio?: number;
  roe?: number;
  dividend_yield?: number;
  composite_score?: number;
  rsi_14?: number;
  sma_50?: number;
  sma_200?: number;
}

export interface PricePoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface HoldingPerformance {
  id: number;
  stock_id: number;
  symbol: string;
  exchange: string;
  name: string;
  sector?: string;
  quantity: number;
  avg_buy_price: number;
  buy_date?: string;
  current_price: number;
  invested_value: number;
  current_value: number;
  gain: number;
  gain_pct: number;
  weight_pct: number;
  pct_change_1d?: number;
}

export interface PortfolioPerformance {
  portfolio_id: string;
  name: string;
  benchmark: string;
  currency: string;
  total_invested: number;
  current_value: number;
  total_gain: number;
  total_gain_pct: number;
  today_gain: number;
  today_gain_pct: number;
  holdings: HoldingPerformance[];
  sector_allocation: Record<string, number>;
  cap_allocation: Record<string, number>;
}

// ─── API Functions ────────────────────────────────────────────────────────

export const screenerApi = {
  run: (req: ScreenerRunRequest) =>
    apiClient.post<ScreenerRunResponse>("/screener/run", req).then((r) => r.data),
  listSaved: () =>
    apiClient.get("/screener/saved").then((r) => r.data),
  save: (data: object) =>
    apiClient.post("/screener/saved", data).then((r) => r.data),
  update: (id: string, data: object) =>
    apiClient.put(`/screener/saved/${id}`, data).then((r) => r.data),
  delete: (id: string) =>
    apiClient.delete(`/screener/saved/${id}`),
  getShared: (token: string) =>
    apiClient.get(`/screener/share/${token}`).then((r) => r.data),
};

export const stocksApi = {
  search: (q: string, exchange?: string) =>
    apiClient.get<StockOverview[]>("/stocks/search", { params: { q, exchange } }).then((r) => r.data),
  overview: (symbol: string, exchange = "NSE") =>
    apiClient.get<StockOverview>(`/stocks/${symbol}/overview`, { params: { exchange } }).then((r) => r.data),
  priceHistory: (symbol: string, exchange = "NSE", from?: string, to?: string) =>
    apiClient.get(`/stocks/${symbol}/price-history`, { params: { exchange, from_date: from, to_date: to } }).then((r) => r.data),
  peers: (symbol: string, exchange = "NSE") =>
    apiClient.get(`/stocks/${symbol}/peers`, { params: { exchange } }).then((r) => r.data),
};

export const portfolioApi = {
  list: () => apiClient.get("/portfolio").then((r) => r.data),
  create: (data: object) => apiClient.post("/portfolio", data).then((r) => r.data),
  get: (id: string) => apiClient.get(`/portfolio/${id}`).then((r) => r.data),
  update: (id: string, data: object) => apiClient.put(`/portfolio/${id}`, data).then((r) => r.data),
  delete: (id: string) => apiClient.delete(`/portfolio/${id}`),
  performance: (id: string) => apiClient.get<PortfolioPerformance>(`/portfolio/${id}/performance`).then((r) => r.data),
  addHolding: (id: string, data: object) => apiClient.post(`/portfolio/${id}/holdings`, data).then((r) => r.data),
  updateHolding: (portfolioId: string, holdingId: number, data: object) =>
    apiClient.put(`/portfolio/${portfolioId}/holdings/${holdingId}`, data).then((r) => r.data),
  deleteHolding: (portfolioId: string, holdingId: number) =>
    apiClient.delete(`/portfolio/${portfolioId}/holdings/${holdingId}`),
  getShared: (token: string) => apiClient.get(`/portfolio/share/${token}`).then((r) => r.data),
};
