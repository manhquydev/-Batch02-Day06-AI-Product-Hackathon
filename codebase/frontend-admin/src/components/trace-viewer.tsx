"use client";
import { useState } from "react";
import type { TraceStep } from "@/lib/types";

function StepRow({ step }: { step: TraceStep }) {
  const [open, setOpen] = useState(false);
  const hasObs = Boolean(step.observation);

  return (
    <div className="border border-zinc-700 rounded-lg overflow-hidden">
      <button
        className="w-full text-left px-4 py-3 flex items-start gap-3 hover:bg-zinc-800 transition-colors"
        onClick={() => hasObs && setOpen((p) => !p)}
      >
        <span className="shrink-0 w-7 h-7 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center mt-0.5">
          {step.step}
        </span>
        <div className="flex-1 min-w-0">
          {step.thought && (
            <p className="text-sm text-zinc-300">
              <span className="text-blue-400 font-medium">Thought: </span>
              {step.thought}
            </p>
          )}
          {step.action && (
            <p className="mt-1 text-sm font-mono bg-zinc-900 px-2 py-1 rounded text-amber-300 truncate">
              <span className="text-zinc-500">→ </span>
              {step.action}
            </p>
          )}
          {!step.thought && !step.action && (
            <p className="text-sm text-zinc-500 italic truncate">{step.raw.slice(0, 120)}</p>
          )}
        </div>
        {hasObs && (
          <span className="shrink-0 text-zinc-500 text-xs mt-1 select-none">{open ? "▲" : "▼"}</span>
        )}
      </button>
      {open && step.observation && (
        <div className="px-4 py-3 bg-zinc-900/80 border-t border-zinc-700">
          <p className="text-xs text-zinc-400 font-semibold mb-1 uppercase tracking-wide">Observation</p>
          <pre className="text-xs text-zinc-300 whitespace-pre-wrap break-all">{step.observation}</pre>
        </div>
      )}
    </div>
  );
}

export function TraceViewer({ steps }: { steps: TraceStep[] }) {
  if (!steps.length) return null;
  return (
    <div className="space-y-2">
      <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
        Trace — {steps.length} step{steps.length !== 1 ? "s" : ""}
      </h3>
      <div className="space-y-1.5">
        {steps.map((s) => (
          <StepRow key={s.step} step={s} />
        ))}
      </div>
    </div>
  );
}
