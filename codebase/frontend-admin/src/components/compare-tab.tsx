"use client";
import { useState } from "react";
import { runCompare } from "@/lib/api";
import type { CompareResponse } from "@/lib/types";
import { ResultPanel } from "./result-panel";

type Props = { mode: string; models: string[]; maxSteps: number };

export function CompareTab({ mode, models, maxSteps }: Props) {
  const [selected, setSelected] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CompareResponse | null>(null);

  function toggleModel(m: string) {
    setSelected((prev) =>
      prev.includes(m) ? prev.filter((x) => x !== m) : prev.length < 4 ? [...prev, m] : prev
    );
  }

  async function handleRun() {
    if (!query.trim() || selected.length < 2) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const r = await runCompare({ query, models: selected, mode, max_steps: maxSteps });
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  const resultCount = Object.keys(result?.results ?? {}).length;
  const colClass =
    resultCount <= 2 ? "md:grid-cols-2" : resultCount === 4 ? "grid-cols-2 xl:grid-cols-4" : "md:grid-cols-2 xl:grid-cols-3";

  return (
    <div className="space-y-4">
      <div>
        <p className="text-xs text-zinc-400 mb-2">
          Select 2–4 models{selected.length > 0 ? ` (${selected.length}/4 selected)` : ""}
        </p>
        <div className="flex flex-wrap gap-2">
          {models.length === 0 && <span className="text-xs text-zinc-500">Loading models…</span>}
          {models.map((m) => {
            const on = selected.includes(m);
            return (
              <button
                key={m}
                onClick={() => toggleModel(m)}
                className={`px-3 py-1.5 text-xs rounded border font-mono transition-colors ${
                  on
                    ? "bg-blue-600 border-blue-500 text-white"
                    : "bg-zinc-800 border-zinc-700 text-zinc-300 hover:border-zinc-500"
                }`}
              >
                {m}
              </button>
            );
          })}
        </div>
        {selected.length === 1 && (
          <p className="text-xs text-yellow-400 mt-1">Select at least 2 models</p>
        )}
      </div>

      <div className="flex gap-2">
        <input
          className="flex-1 bg-zinc-800 border border-zinc-700 rounded px-4 py-2.5 text-sm text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:border-blue-500"
          placeholder="e.g. So sánh Inception, Interstellar và The Prestige."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleRun()}
        />
        <button
          onClick={handleRun}
          disabled={loading || selected.length < 2 || !query.trim()}
          className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-zinc-700 disabled:text-zinc-500 text-white text-sm font-medium rounded transition-colors"
        >
          {loading ? "Running…" : "Compare"}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-900/40 border border-red-700 rounded-lg">
          <p className="text-red-300 text-sm">{error}</p>
        </div>
      )}
      {loading && (
        <div className="flex items-center gap-2 text-zinc-400 text-sm">
          <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          Running {selected.length} models in parallel…
        </div>
      )}
      {result && (
        <div className={`grid gap-4 ${colClass}`}>
          {Object.entries(result.results).map(([key, res]) => (
            <div key={key} className="bg-zinc-800/50 border border-zinc-700 rounded-xl p-4 min-w-0">
              <ResultPanel result={res} label={key} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
