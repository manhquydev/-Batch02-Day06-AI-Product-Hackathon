"use client";
import { useState } from "react";
import { runChat } from "@/lib/api";
import type { ChatResponse } from "@/lib/types";
import { ResultPanel } from "./result-panel";

type Props = { mode: string; models: string[]; maxSteps: number };

export function SingleTab({ mode, models, maxSteps }: Props) {
  const [model, setModel] = useState("");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ChatResponse | null>(null);

  const effectiveModel = models.includes(model) ? model : (models[0] ?? "");

  async function handleRun() {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    const [provider, ...rest] = effectiveModel.split("/");
    try {
      const r = await runChat({ message: query, mode, provider, model: rest.join("/"), max_steps: maxSteps });
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl space-y-4">
      <label className="flex flex-col gap-1">
        <span className="text-xs text-zinc-400">Model</span>
        <select
          className="bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:border-blue-500"
          value={effectiveModel}
          onChange={(e) => setModel(e.target.value)}
        >
          {models.length ? (
            models.map((m) => <option key={m}>{m}</option>)
          ) : (
            <option disabled>Loading models…</option>
          )}
        </select>
      </label>

      <div className="flex gap-2">
        <input
          className="flex-1 bg-zinc-800 border border-zinc-700 rounded px-4 py-2.5 text-sm text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:border-blue-500"
          placeholder="e.g. Tôi buồn, muốn xem phim nhẹ nhàng — gợi ý 3 phim."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleRun()}
        />
        <button
          onClick={handleRun}
          disabled={loading || !query.trim() || models.length === 0}
          className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-zinc-700 disabled:text-zinc-500 text-white text-sm font-medium rounded transition-colors"
        >
          {loading ? "Running…" : "Run"}
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
          Agent running…
        </div>
      )}
      {result && <ResultPanel result={result} />}
    </div>
  );
}
