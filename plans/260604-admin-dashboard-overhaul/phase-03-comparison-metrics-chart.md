---
phase: 3
title: "Comparison Metrics Chart"
status: pending
priority: P1
effort: "45m"
dependencies: [1]
---

# Phase 3: Comparison Metrics Chart

## Overview

Add a CSS-only bar chart component below the compare results grid. Shows latency (ms) and steps per model with winner badge. No external chart library — pure Tailwind CSS `width` percentage bars. Also adds a 1-click JSON export button.

## Architecture

```
CompareTab
└── [existing results grid]
└── CompareChart (new — renders after results arrive)
    ├── MetricSection: Latency (lower = better)  🏆 winner badge
    │   └── ModelBar × N
    ├── MetricSection: Steps (lower = better)    🏆 winner badge
    │   └── ModelBar × N
    └── ExportButton → download results.json
```

**Bar rendering logic:**
```ts
// Width = (value / maxValue) * 100%
// Winner = entry with minimum value (latency, steps)
// Color: winner = emerald, rest = blue, scale from dim to bright by rank
```

## Related Code Files

- Create: `codebase/frontend-admin/src/components/compare-chart.tsx`
- Modify: `codebase/frontend-admin/src/components/compare-tab.tsx` — import + render `<CompareChart>`

## Implementation Steps

### Step 1 — Create `compare-chart.tsx`

```tsx
"use client";
import type { CompareResult } from "@/lib/types";

type ChartEntry = { key: string; result: CompareResult };

function MetricSection({
  title,
  unit,
  entries,
  getValue,
  lowerIsBetter,
}: {
  title: string;
  unit: string;
  entries: ChartEntry[];
  getValue: (r: CompareResult) => number;
  lowerIsBetter: boolean;
}) {
  const values = entries.map((e) => getValue(e.result));
  const maxVal = Math.max(...values, 1);
  const bestVal = lowerIsBetter ? Math.min(...values) : Math.max(...values);

  return (
    <div>
      <p className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">
        {title}
        <span className="ml-1 text-zinc-600 normal-case font-normal">
          ({lowerIsBetter ? "lower = better" : "higher = better"})
        </span>
      </p>
      <div className="space-y-2">
        {entries.map(({ key, result }) => {
          const val = getValue(result);
          const isWinner = val === bestVal;
          const pct = Math.round((val / maxVal) * 100);
          return (
            <div key={key} className="flex items-center gap-3">
              <span className="text-xs font-mono text-zinc-400 w-36 shrink-0 truncate" title={key}>
                {key}
              </span>
              <div className="flex-1 bg-zinc-800 rounded-full h-4 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    isWinner ? "bg-emerald-500" : "bg-blue-600"
                  }`}
                  style={{ width: `${pct}%` }}
                />
              </div>
              <span
                className={`text-xs font-mono tabular-nums w-20 text-right shrink-0 ${
                  isWinner ? "text-emerald-400 font-bold" : "text-zinc-400"
                }`}
              >
                {val.toLocaleString()}{unit}
              </span>
              {isWinner && (
                <span className="text-sm shrink-0" title="Winner">🏆</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function exportResults(results: Record<string, CompareResult>) {
  const blob = new Blob([JSON.stringify(results, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `compare-results-${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

export function CompareChart({ results }: { results: Record<string, CompareResult> }) {
  const entries: ChartEntry[] = Object.entries(results)
    .filter(([, r]) => r.ok !== false && r.latency_ms != null)
    .map(([key, result]) => ({ key, result }));

  if (entries.length < 2) return null;

  return (
    <div className="mt-6 p-5 bg-zinc-800/50 border border-zinc-700 rounded-xl space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-zinc-200">Model Comparison</h3>
        <button
          onClick={() => exportResults(results)}
          className="text-xs px-3 py-1.5 bg-zinc-700 hover:bg-zinc-600 text-zinc-300 rounded transition-colors"
        >
          Export JSON
        </button>
      </div>
      <MetricSection
        title="Latency"
        unit="ms"
        entries={entries}
        getValue={(r) => r.latency_ms ?? 0}
        lowerIsBetter
      />
      <MetricSection
        title="Steps"
        unit=""
        entries={entries}
        getValue={(r) => r.steps ?? 0}
        lowerIsBetter
      />
    </div>
  );
}
```

### Step 2 — Add to `compare-tab.tsx`

Add import at top:
```tsx
import { CompareChart } from "./compare-chart";
```

After the results grid (after the `{result && (` block closing `</div>`):
```tsx
{result && <CompareChart results={result.results} />}
```

### Step 3 — TypeScript check

Run `npx tsc --noEmit` in `codebase/frontend-admin`.

## Success Criteria

- [ ] Bar chart appears below compare results when ≥2 models succeed
- [ ] Winner highlighted in emerald with 🏆
- [ ] Failed model results (ok=false) excluded from chart
- [ ] Export JSON downloads valid JSON file
- [ ] `npx tsc --noEmit` passes
