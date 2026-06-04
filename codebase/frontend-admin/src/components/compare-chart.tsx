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
      <p className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2.5">
        {title}
        <span className="ml-1.5 text-zinc-600 normal-case font-normal">
          ({lowerIsBetter ? "lower = better" : "higher = better"})
        </span>
      </p>
      <div className="space-y-2.5">
        {entries.map(({ key, result }) => {
          const val = getValue(result);
          const isWinner = val === bestVal;
          const pct = Math.max(4, Math.round((val / maxVal) * 100));
          return (
            <div key={key} className="flex items-center gap-3">
              <span
                className="text-xs font-mono text-zinc-400 shrink-0 truncate"
                style={{ width: "9rem" }}
                title={key}
              >
                {key}
              </span>
              <div className="flex-1 bg-zinc-800 rounded-full h-3.5 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    isWinner ? "bg-emerald-500" : "bg-blue-600/70"
                  }`}
                  style={{ width: `${pct}%` }}
                />
              </div>
              <span
                className={`text-xs font-mono tabular-nums shrink-0 text-right ${
                  isWinner ? "text-emerald-400 font-bold" : "text-zinc-400"
                }`}
                style={{ width: "5rem" }}
              >
                {val.toLocaleString()}
                {unit}
              </span>
              <span className="text-sm shrink-0 w-5 text-center">
                {isWinner ? "🏆" : ""}
              </span>
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

  const hasSteps = entries.some((e) => (e.result.steps ?? 0) > 0);

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
      {hasSteps && (
        <>
          <div className="border-t border-zinc-700/50" />
          <MetricSection
            title="Steps"
            unit=""
            entries={entries}
            getValue={(r) => r.steps ?? 0}
            lowerIsBetter
          />
        </>
      )}
    </div>
  );
}
