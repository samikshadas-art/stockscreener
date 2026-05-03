import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { FilterCondition, ScreenerRunResponse } from "@/lib/api";

interface ScreenerState {
  filters: FilterCondition[];
  logic: "AND" | "OR";
  exchange: string[];
  sortBy: string;
  sortOrder: "asc" | "desc";
  page: number;
  perPage: number;
  results: ScreenerRunResponse | null;
  isLoading: boolean;
  visibleColumns: string[];

  // Actions
  addFilter: (filter: FilterCondition) => void;
  updateFilter: (index: number, filter: FilterCondition) => void;
  removeFilter: (index: number) => void;
  clearFilters: () => void;
  setLogic: (logic: "AND" | "OR") => void;
  setExchange: (exchange: string[]) => void;
  setSortBy: (field: string) => void;
  setSortOrder: (order: "asc" | "desc") => void;
  setPage: (page: number) => void;
  setResults: (results: ScreenerRunResponse | null) => void;
  setLoading: (loading: boolean) => void;
  setVisibleColumns: (cols: string[]) => void;
}

export const useScreenerStore = create<ScreenerState>()(
  persist(
    (set) => ({
      filters: [],
      logic: "AND",
      exchange: ["NSE", "BSE", "NYSE", "NASDAQ"],
      sortBy: "market_cap",
      sortOrder: "desc",
      page: 1,
      perPage: 50,
      results: null,
      isLoading: false,
      visibleColumns: [
        "symbol", "name", "pct_change_1d", "market_cap",
        "pe_ratio", "roe", "rsi_14", "composite_score",
      ],

      addFilter: (filter) => set((s) => ({ filters: [...s.filters, filter], page: 1 })),
      updateFilter: (index, filter) =>
        set((s) => {
          const updated = [...s.filters];
          updated[index] = filter;
          return { filters: updated, page: 1 };
        }),
      removeFilter: (index) =>
        set((s) => ({ filters: s.filters.filter((_, i) => i !== index), page: 1 })),
      clearFilters: () => set({ filters: [], page: 1, results: null }),
      setLogic: (logic) => set({ logic, page: 1 }),
      setExchange: (exchange) => set({ exchange, page: 1 }),
      setSortBy: (sortBy) => set({ sortBy, page: 1 }),
      setSortOrder: (sortOrder) => set({ sortOrder }),
      setPage: (page) => set({ page }),
      setResults: (results) => set({ results }),
      setLoading: (isLoading) => set({ isLoading }),
      setVisibleColumns: (visibleColumns) => set({ visibleColumns }),
    }),
    { name: "screener-state", partialize: (s) => ({ filters: s.filters, logic: s.logic, exchange: s.exchange, visibleColumns: s.visibleColumns }) }
  )
);
