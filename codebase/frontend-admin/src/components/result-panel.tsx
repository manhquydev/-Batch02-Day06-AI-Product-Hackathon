"use client";
import type { Movie, TraceStep } from "@/lib/types";
import { TraceViewer } from "./trace-viewer";

type AnyResult = {
  ok?: boolean;
  error?: string;
  answer?: string;
  trace?: TraceStep[];
  steps?: number;
  latency_ms?: number;
  movies?: Movie[];
};

function MetricBadge({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex flex-col items-center px-4 py-2.5 bg-zinc-800 rounded-lg min-w-[72px]">
      <span className="text-lg font-bold text-white tabular-nums">{value}</span>
      <span className="text-xs text-zinc-400">{label}</span>
    </div>
  );
}

type Props = {
  result: AnyResult;
  label?: string;
};

export function ResultPanel({ result, label }: Props) {
  const toolCalls = result.trace?.filter((s) => Boolean(s.action)).length ?? 0;

  return (
    <div className="space-y-4">
      {label && (
        <h2 className="text-sm font-semibold text-zinc-200 font-mono truncate" title={label}>
          {label}
        </h2>
      )}
      {result.ok === false ? (
        <div className="p-4 bg-red-900/40 border border-red-700 rounded-lg">
          <p className="text-red-300 text-sm">{result.error ?? "Unknown error"}</p>
        </div>
      ) : (
        <>
          <div className="flex gap-2 flex-wrap">
            <MetricBadge label="Latency" value={`${result.latency_ms ?? 0}ms`} />
            <MetricBadge label="Steps" value={result.steps ?? 0} />
            <MetricBadge label="Tool calls" value={toolCalls} />
          </div>
          {result.answer && (
            <div className="p-4 bg-zinc-800 rounded-lg">
              <p className="text-xs text-zinc-400 font-semibold uppercase tracking-wide mb-2">Answer</p>
              <p className="text-sm text-zinc-100 leading-relaxed whitespace-pre-wrap">{result.answer}</p>
            </div>
          )}
          {result.trace && result.trace.length > 0 && <TraceViewer steps={result.trace} />}
        </>
      )}
    </div>
  );
}
