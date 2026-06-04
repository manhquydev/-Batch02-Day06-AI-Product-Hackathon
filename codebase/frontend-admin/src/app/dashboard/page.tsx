"use client";
import { useEffect, useState } from "react";
import { fetchModels } from "@/lib/api";
import { SingleTab } from "@/components/single-tab";
import { CompareTab } from "@/components/compare-tab";

const MODES = ["ReAct Agent v2", "ReAct Agent v1", "Chatbot Baseline"] as const;
type Tab = "single" | "compare";

export default function DashboardPage() {
  const [models, setModels] = useState<string[]>([]);
  const [mode, setMode] = useState<string>("ReAct Agent v2");
  const [maxSteps, setMaxSteps] = useState(5);
  const [tab, setTab] = useState<Tab>("single");
  const [backendError, setBackendError] = useState<string | null>(null);

  useEffect(() => {
    fetchModels()
      .then((r) => setModels(r.models))
      .catch((e: unknown) => setBackendError(e instanceof Error ? e.message : String(e)));
  }, []);

  return (
    <div className="min-h-screen bg-zinc-900 text-zinc-100 flex flex-col">
      <header className="border-b border-zinc-800 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-base font-bold text-white tracking-tight">Movie ReAct Agent — Admin</h1>
          <p className="text-xs text-zinc-500">Trace viewer · Metrics dashboard</p>
        </div>
        {backendError && (
          <span className="text-xs text-red-400 bg-red-900/30 border border-red-800 px-3 py-1 rounded">
            Backend offline
          </span>
        )}
      </header>

      <div className="border-b border-zinc-800 px-6 py-3 flex flex-wrap items-center gap-6">
        <label className="flex items-center gap-2">
          <span className="text-xs text-zinc-400 whitespace-nowrap">Mode</span>
          <select
            className="bg-zinc-800 border border-zinc-700 rounded px-3 py-1.5 text-sm text-zinc-100 focus:outline-none focus:border-blue-500"
            value={mode}
            onChange={(e) => setMode(e.target.value)}
          >
            {MODES.map((m) => <option key={m}>{m}</option>)}
          </select>
        </label>
        <label className="flex items-center gap-3">
          <span className="text-xs text-zinc-400 whitespace-nowrap">Max steps: {maxSteps}</span>
          <input
            type="range"
            min={2}
            max={8}
            value={maxSteps}
            onChange={(e) => setMaxSteps(Number(e.target.value))}
            className="w-28 accent-blue-500"
          />
        </label>
      </div>

      <div className="border-b border-zinc-800 px-6 flex gap-1">
        {(["single", "compare"] as Tab[]).map((t) => (
          <button
            key={t}
            className={`py-3 px-1 mr-4 text-sm font-medium border-b-2 capitalize transition-colors ${
              tab === t
                ? "border-blue-500 text-blue-400"
                : "border-transparent text-zinc-400 hover:text-zinc-200"
            }`}
            onClick={() => setTab(t)}
          >
            {t === "single" ? "Single Model" : "Compare Models"}
          </button>
        ))}
      </div>

      <main className="flex-1 p-6 overflow-auto">
        {tab === "single" ? (
          <SingleTab mode={mode} models={models} maxSteps={maxSteps} />
        ) : (
          <CompareTab mode={mode} models={models} maxSteps={maxSteps} />
        )}
      </main>
    </div>
  );
}
