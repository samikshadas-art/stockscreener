"use client";
import { useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
} from "@tanstack/react-table";
import { useState } from "react";
import { ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";
import { useScreenerStore } from "@/store/screenerStore";
import {
  formatPct, formatLargeNumber, formatNumber,
  gainColor, gainBg,
} from "@/lib/formatters";
import type { ScreenerRunResponse, ScreenerResultRow } from "@/lib/api";
import { cn } from "@/lib/utils";

const columnHelper = createColumnHelper<ScreenerResultRow>();

const ALL_COLUMNS = [
  columnHelper.accessor("symbol", {
    header: "Symbol",
    cell: (info) => (
      <div>
        <div className="font-semibold text-sm">{info.getValue()}</div>
        <div className="text-xs text-muted-foreground">{info.row.original.exchange}</div>
      </div>
    ),
  }),
  columnHelper.accessor("name", {
    header: "Name",
    cell: (info) => (
      <div className="text-sm truncate max-w-[180px]" title={info.getValue()}>
        {info.getValue()}
      </div>
    ),
  }),
  columnHelper.accessor("pct_change_1d", {
    header: "1D %",
    cell: (info) => (
      <span className={cn("text-sm font-medium px-2 py-0.5 rounded", gainBg(info.getValue()))}>
        {formatPct(info.getValue())}
      </span>
    ),
  }),
  columnHelper.accessor("market_cap", {
    header: "Mkt Cap",
    cell: (info) => <span className="text-sm font-mono">{formatLargeNumber(info.getValue())}</span>,
  }),
  columnHelper.accessor("pe_ratio", {
    header: "P/E",
    cell: (info) => <span className="text-sm font-mono">{formatNumber(info.getValue())}</span>,
  }),
  columnHelper.accessor("pb_ratio", {
    header: "P/B",
    cell: (info) => <span className="text-sm font-mono">{formatNumber(info.getValue())}</span>,
  }),
  columnHelper.accessor("roe", {
    header: "ROE %",
    cell: (info) => <span className={cn("text-sm font-mono", info.getValue() && info.getValue()! > 15 ? "text-green-500" : "")}>{formatNumber(info.getValue())}%</span>,
  }),
  columnHelper.accessor("debt_to_equity", {
    header: "D/E",
    cell: (info) => <span className="text-sm font-mono">{formatNumber(info.getValue())}</span>,
  }),
  columnHelper.accessor("eps_growth_yoy", {
    header: "EPS Growth",
    cell: (info) => <span className={cn("text-sm font-mono", gainColor(info.getValue()))}>{formatPct(info.getValue())}</span>,
  }),
  columnHelper.accessor("dividend_yield", {
    header: "Div Yield",
    cell: (info) => <span className="text-sm font-mono">{formatNumber(info.getValue())}%</span>,
  }),
  columnHelper.accessor("rsi_14", {
    header: "RSI",
    cell: (info) => {
      const v = info.getValue();
      const color = v == null ? "" : v < 30 ? "text-green-500" : v > 70 ? "text-red-500" : "";
      return <span className={cn("text-sm font-mono", color)}>{formatNumber(v, 1)}</span>;
    },
  }),
  columnHelper.accessor("pct_change_1m", {
    header: "1M %",
    cell: (info) => <span className={cn("text-sm font-mono", gainColor(info.getValue()))}>{formatPct(info.getValue())}</span>,
  }),
  columnHelper.accessor("pct_change_1y", {
    header: "1Y %",
    cell: (info) => <span className={cn("text-sm font-mono", gainColor(info.getValue()))}>{formatPct(info.getValue())}</span>,
  }),
  columnHelper.accessor("composite_score", {
    header: "Score",
    cell: (info) => {
      const v = info.getValue();
      const color = v == null ? "" : v >= 70 ? "text-green-500" : v >= 40 ? "text-amber-500" : "text-red-400";
      return <span className={cn("text-sm font-bold", color)}>{v != null ? Math.round(v) : "—"}</span>;
    },
  }),
];

interface Props {
  data?: ScreenerRunResponse;
  isLoading: boolean;
}

export function ScreenerTable({ data, isLoading }: Props) {
  const router = useRouter();
  const { visibleColumns, setSortBy, setSortOrder, setPage, page, perPage } = useScreenerStore();
  const [sorting, setSorting] = useState<SortingState>([]);

  const columns = useMemo(
    () => ALL_COLUMNS.filter((c) => {
      const id = (c as any).accessorKey as string;
      return visibleColumns.includes(id) || id === "symbol" || id === "name";
    }),
    [visibleColumns]
  );

  const table = useReactTable({
    data: data?.results ?? [],
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    manualSorting: true,
    state: { sorting },
    onSortingChange: (updater) => {
      const newSorting = typeof updater === "function" ? updater(sorting) : updater;
      setSorting(newSorting);
      if (newSorting.length > 0) {
        setSortBy(newSorting[0].id);
        setSortOrder(newSorting[0].desc ? "desc" : "asc");
      }
    },
  });

  const totalPages = data?.total_pages ?? 1;

  if (isLoading && !data) {
    return (
      <div className="flex-1 flex items-center justify-center text-muted-foreground">
        <div className="text-center space-y-2">
          <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm">Running screener…</p>
        </div>
      </div>
    );
  }

  if (!data || data.results.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-muted-foreground">
        <div className="text-center space-y-2">
          <p className="text-sm">No results match your filters.</p>
          <p className="text-xs">Try relaxing your conditions or adding more exchanges.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-h-0 border border-border rounded-xl overflow-hidden bg-card">
      <div className="overflow-auto flex-1">
        <table className="w-full screener-table">
          <thead className="sticky top-0 bg-card z-10 border-b border-border">
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id}>
                {hg.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-4 py-2.5 text-left whitespace-nowrap cursor-pointer select-none"
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    <div className="flex items-center gap-1">
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {header.column.getIsSorted() === "asc" ? (
                        <ArrowUp className="h-3 w-3 text-primary" />
                      ) : header.column.getIsSorted() === "desc" ? (
                        <ArrowDown className="h-3 w-3 text-primary" />
                      ) : (
                        <ArrowUpDown className="h-3 w-3 text-muted-foreground/30" />
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className="border-b border-border/50 cursor-pointer transition-colors hover:bg-accent/30"
                onClick={() =>
                  router.push(`/stocks/${row.original.symbol}?exchange=${row.original.exchange}`)
                }
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-4 py-2.5 whitespace-nowrap">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between px-4 py-2.5 border-t border-border bg-card text-xs text-muted-foreground shrink-0">
        <span>
          Showing {((page - 1) * perPage) + 1}–{Math.min(page * perPage, data.total)} of {data.total.toLocaleString()}
        </span>
        <div className="flex items-center gap-1">
          <button
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
            className="px-2.5 py-1 rounded border border-border hover:bg-accent disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            ← Prev
          </button>
          <span className="px-3">{page} / {totalPages}</span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage(page + 1)}
            className="px-2.5 py-1 rounded border border-border hover:bg-accent disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            Next →
          </button>
        </div>
      </div>
    </div>
  );
}
