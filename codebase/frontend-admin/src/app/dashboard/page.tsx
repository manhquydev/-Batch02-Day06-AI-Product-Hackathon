"use client";
import { useEffect, useRef, useState } from "react";
import { fetchModels } from "@/lib/api";
import { SingleTab } from "@/components/single-tab";
import { CompareTab } from "@/components/compare-tab";
import { UsersTab } from "@/components/users-tab";
import { HistorySidebar, type HistoryEntry } from "@/components/history-sidebar";

const MODES = ["ReAct Agent"] as const;
type Tab = "single" | "compare" | "users";

type SessionEntry = { latency: number; model: string };

export default function DashboardPage() {
  const [models, setModels] = useState<string[]>([]);
  const [mode, setMode] = useState<string>("ReAct Agent");
  const [maxSteps, setMaxSteps] = useState(5);
  const [tab, setTab] = useState<Tab>("single");
  const [backendError, setBackendError] = useState<string | null>(null);
  const [sessionEntries, setSessionEntries] = useState<SessionEntry[]>([]);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [historyOpen, setHistoryOpen] = useState(false);
  const historyIdRef = useRef(0);

  useEffect(() => {
    fetchModels()
      .then((r) => setModels(r.models))
      .catch((e: unknown) => setBackendError(e instanceof Error ? e.message : String(e)));
  }, []);

  function handleResult(latency: number, model: string, query?: string) {
    setSessionEntries((prev) => [...prev, { latency, model }]);
    if (query) {
      const now = new Date();
      const timestamp = now.toTimeString().slice(0, 8);
      const id = ++historyIdRef.current;
      setHistory((prev) =>
        [{ id, query, latency, model, timestamp }, ...prev].slice(0, 20)
      );
    }
  }

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

      {tab !== "users" && <div className="border-b border-zinc-800 px-6 py-3 flex flex-wrap items-center gap-6">
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
      </div>}

      <div className="border-b border-zinc-800 px-6 flex gap-1">
        {(["single", "compare", "users"] as Tab[]).map((t) => (
          <button
            key={t}
            className={`py-3 px-1 mr-4 text-sm font-medium border-b-2 capitalize transition-colors ${
              tab === t
                ? "border-blue-500 text-blue-400"
                : "border-transparent text-zinc-400 hover:text-zinc-200"
            }`}
            onClick={() => setTab(t)}
          >
            {t === "single" ? "Single Model" : t === "compare" ? "Compare Models" : "Users"}
          </button>
        ))}
      </div>

      {sessionEntries.length > 0 && (() => {
        const avgLatency = Math.round(
          sessionEntries.reduce((s, e) => s + e.latency, 0) / sessionEntries.length
        );
        const modelMap = new Map<string, number[]>();
        sessionEntries.forEach(({ model, latency }) => {
          modelMap.set(model, [...(modelMap.get(model) ?? []), latency]);
        });
        const bestModel = [...modelMap.entries()].sort(
          (a, b) =>
            a[1].reduce((s, v) => s + v, 0) / a[1].length -
            b[1].reduce((s, v) => s + v, 0) / b[1].length
        )[0]?.[0];
        return (
          <div className="border-b border-zinc-800 px-6 py-2 flex gap-6 text-xs text-zinc-500">
            <span>Queries: <strong className="text-zinc-300">{sessionEntries.length}</strong></span>
            <span>Avg latency: <strong className="text-zinc-300">{avgLatency}ms</strong></span>
            {bestModel && (
              <span>Fastest: <strong className="text-emerald-400">{bestModel}</strong></span>
            )}
          </div>
        );
      })()}

      <main className="flex-1 p-6 overflow-auto">
        {tab === "single" ? (
          <SingleTab mode={mode} models={models} maxSteps={maxSteps} onResult={handleResult} />
        ) : tab === "compare" ? (
          <CompareTab mode={mode} models={models} maxSteps={maxSteps} onResult={handleResult} />
        ) : (
          <UsersTab />
        )}
      </main>

      <HistorySidebar
        entries={history}
        open={historyOpen}
        onToggle={() => setHistoryOpen((p) => !p)}
        onSelect={(_e) => {
          // TODO: restore query/result into SingleTab (requires lifting state or controlled props)
          setHistoryOpen(false);
          setTab("single");
        }}
      />
    </div>
  );
}
