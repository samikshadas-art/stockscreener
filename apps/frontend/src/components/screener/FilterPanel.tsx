"use client";
import { useState } from "react";
import { Plus, X, RotateCcw, ChevronDown, ChevronRight } from "lucide-react";
import { useScreenerStore } from "@/store/screenerStore";
import { FILTER_FIELDS, CATEGORIES, OPERATOR_LABELS, type FilterField } from "@/lib/screenerConfig";
import type { FilterCondition } from "@/lib/api";
import { cn } from "@/lib/utils";

export function FilterPanel() {
  const { filters, logic, addFilter, removeFilter, updateFilter, clearFilters, setLogic } = useScreenerStore();
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
  const [adding, setAdding] = useState(false);
  const [selectedField, setSelectedField] = useState<FilterField | null>(null);

  const toggleCategory = (cat: string) =>
    setCollapsed((s) => ({ ...s, [cat]: !s[cat] }));

  const handleAdd = () => {
    if (!selectedField) return;
    const operators = selectedField.operators;
    const newFilter: FilterCondition = {
      field: selectedField.field,
      operator: operators[0],
      value: operators[0] === "between" ? [0, 100] : 0,
    };
    addFilter(newFilter);
    setAdding(false);
    setSelectedField(null);
  };

  return (
    <aside className="w-64 shrink-0 flex flex-col border-r border-border bg-card overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <span className="text-sm font-semibold">Filters</span>
        <div className="flex items-center gap-2">
          {/* AND/OR toggle */}
          <div className="flex text-xs border border-border rounded overflow-hidden">
            {(["AND", "OR"] as const).map((l) => (
              <button
                key={l}
                onClick={() => setLogic(l)}
                className={cn(
                  "px-2 py-0.5 transition-colors",
                  logic === l ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-accent"
                )}
              >
                {l}
              </button>
            ))}
          </div>
          {filters.length > 0 && (
            <button onClick={clearFilters} className="text-muted-foreground hover:text-foreground transition-colors">
              <RotateCcw className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Active filters */}
      <div className="flex-1 overflow-y-auto">
        {filters.length > 0 && (
          <div className="p-3 space-y-2 border-b border-border">
            <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Active ({filters.length})</p>
            {filters.map((f, i) => (
              <ActiveFilter key={i} filter={f} index={i} onRemove={removeFilter} onUpdate={updateFilter} />
            ))}
          </div>
        )}

        {/* Add filter picker */}
        {!adding ? (
          <button
            onClick={() => setAdding(true)}
            className="flex items-center gap-2 w-full px-4 py-3 text-sm text-primary hover:bg-primary/5 transition-colors border-b border-border"
          >
            <Plus className="h-4 w-4" />
            Add Filter
          </button>
        ) : (
          <div className="p-3 border-b border-border space-y-2">
            <p className="text-xs text-muted-foreground font-medium">Select parameter</p>
            <div className="max-h-64 overflow-y-auto space-y-1">
              {CATEGORIES.map((cat) => (
                <div key={cat}>
                  <button
                    onClick={() => toggleCategory(cat)}
                    className="flex items-center gap-1 text-xs font-semibold text-muted-foreground w-full py-1 hover:text-foreground transition-colors"
                  >
                    {collapsed[cat] ? <ChevronRight className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                    {cat}
                  </button>
                  {!collapsed[cat] && (
                    <div className="pl-3 space-y-0.5">
                      {FILTER_FIELDS.filter((f) => f.category === cat).map((field) => (
                        <button
                          key={field.field}
                          onClick={() => setSelectedField(field)}
                          className={cn(
                            "w-full text-left text-xs px-2 py-1.5 rounded transition-colors",
                            selectedField?.field === field.field
                              ? "bg-primary/20 text-primary"
                              : "hover:bg-accent text-muted-foreground"
                          )}
                        >
                          {field.label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
            <div className="flex gap-2 pt-1">
              <button
                onClick={handleAdd}
                disabled={!selectedField}
                className="flex-1 bg-primary text-primary-foreground text-xs py-1.5 rounded font-medium disabled:opacity-40"
              >
                Add
              </button>
              <button
                onClick={() => { setAdding(false); setSelectedField(null); }}
                className="text-xs px-3 py-1.5 rounded hover:bg-accent text-muted-foreground"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Field browser by category */}
        {!adding && (
          <div className="p-3 space-y-3">
            {CATEGORIES.map((cat) => (
              <div key={cat}>
                <button
                  onClick={() => toggleCategory(cat)}
                  className="flex items-center gap-1 text-xs font-semibold text-muted-foreground/60 w-full mb-1 hover:text-muted-foreground transition-colors"
                >
                  {collapsed[cat] ? <ChevronRight className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                  {cat}
                </button>
                {!collapsed[cat] && (
                  <div className="space-y-0.5 pl-3">
                    {FILTER_FIELDS.filter((f) => f.category === cat).map((field) => (
                      <button
                        key={field.field}
                        onClick={() => { setAdding(true); setSelectedField(field); }}
                        className="w-full text-left text-xs px-2 py-1 rounded text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
                      >
                        + {field.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}

function ActiveFilter({
  filter, index, onRemove, onUpdate,
}: {
  filter: FilterCondition;
  index: number;
  onRemove: (i: number) => void;
  onUpdate: (i: number, f: FilterCondition) => void;
}) {
  const field = FILTER_FIELDS.find((f) => f.field === filter.field);
  const label = field?.label ?? filter.field;

  const handleValueChange = (val: string) => {
    if (filter.operator === "between") {
      const parts = val.split(",").map(Number);
      onUpdate(index, { ...filter, value: [parts[0] || 0, parts[1] || 0] });
    } else {
      onUpdate(index, { ...filter, value: parseFloat(val) || 0 });
    }
  };

  const valueDisplay = Array.isArray(filter.value)
    ? filter.value.join(",")
    : String(filter.value);

  return (
    <div className="flex items-center gap-1.5 bg-accent/50 rounded-lg px-2.5 py-1.5 text-xs">
      <span className="font-medium text-foreground truncate flex-1">{label}</span>
      <select
        value={filter.operator}
        onChange={(e) => onUpdate(index, { ...filter, operator: e.target.value as any })}
        className="bg-transparent text-muted-foreground text-xs outline-none"
      >
        {field?.operators.map((op) => (
          <option key={op} value={op}>{OPERATOR_LABELS[op]}</option>
        ))}
      </select>
      <input
        value={valueDisplay}
        onChange={(e) => handleValueChange(e.target.value)}
        className="w-16 bg-background rounded px-1.5 py-0.5 outline-none focus:ring-1 ring-primary text-foreground"
      />
      <button onClick={() => onRemove(index)} className="text-muted-foreground hover:text-red-400 transition-colors">
        <X className="h-3 w-3" />
      </button>
    </div>
  );
}
