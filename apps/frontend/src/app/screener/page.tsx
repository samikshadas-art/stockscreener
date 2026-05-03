"use client";
import { useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { screenerApi } from "@/lib/api";
import { useScreenerStore } from "@/store/screenerStore";
import { FilterPanel } from "@/components/screener/FilterPanel";
import { ScreenerTable } from "@/components/screener/ScreenerTable";
import { ScreenerToolbar } from "@/components/screener/ScreenerToolbar";

export default function ScreenerPage() {
  const {
    filters, logic, exchange, sortBy, sortOrder, page, perPage,
    setResults, setLoading,
  } = useScreenerStore();

  const { data, isLoading, isFetching } = useQuery({
    queryKey: ["screener", filters, logic, exchange, sortBy, sortOrder, page, perPage],
    queryFn: () =>
      screenerApi.run({ filters, logic, exchange, sort_by: sortBy, sort_order: sortOrder, page, per_page: perPage }),
    placeholderData: (prev) => prev,
  });

  return (
    <div className="flex h-full gap-4 min-h-0">
      {/* Sticky left filter panel */}
      <FilterPanel />

      {/* Main content */}
      <div className="flex-1 flex flex-col gap-3 min-w-0 min-h-0">
        <ScreenerToolbar total={data?.total} isLoading={isLoading || isFetching} />
        <ScreenerTable data={data} isLoading={isLoading} />
      </div>
    </div>
  );
}
