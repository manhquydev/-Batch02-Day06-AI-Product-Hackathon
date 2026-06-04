---
phase: 2
title: "Trace Timeline Visual"
status: pending
priority: P1
effort: "45m"
dependencies: [1]
---

# Phase 2: Trace Timeline Visual

## Overview

Rewrite `trace-viewer.tsx` — replace the flat accordion with a vertical timeline that visually separates Thought / Tool-call / Observation / Answer. Each tool call gets a recognizable icon. Color-coded by type. Collapses observations to keep the view scannable.

## Architecture

```
TraceViewer
└── TimelineLine (left border strip)
    └── TimelineStep × N
        ├── StepNumber (circle badge)
        ├── ThoughtCard   [blue border, collapsible]
        ├── ToolCallPill  [amber bg, font-mono, tool icon]
        └── ObservationCard [green border, collapsible pre/JSON]
└── AnswerCard [emerald border, always expanded]
```

**Tool icon map** (emoji — no external icon dep):
| Tool substring | Icon |
|---|---|
| `search` | 🔍 |
| `detail` | 🎬 |
| `compare` | ⚖️ |
| `trending` | 📈 |
| `watch` / `provider` | 📺 |
| `mood` / `discover` | 🎭 |
| `person` | 🎭 |
| default | ⚡ |

**Color tokens (Tailwind v4):**
- Thought: `border-blue-700/60 bg-blue-950/40`
- Tool call pill: `bg-amber-950/70 border-amber-700/50 text-amber-300`
- Observation: `border-green-800/60 bg-green-950/30`
- Answer: `border-emerald-600 bg-emerald-950/40`
- Connecting line: `border-l-2 border-zinc-700/60`

## Related Code Files

- Modify (full rewrite): `codebase/frontend-admin/src/components/trace-viewer.tsx`
- No other files touched — `ResultPanel` imports `TraceViewer` with same props signature `{ steps: TraceStep[] }`

## Implementation Steps

1. Read current `trace-viewer.tsx` (already done in codebase analysis).

2. Replace full file content with new `TraceViewer` and `TimelineStep` components:

```tsx
"use client";
import { useState } from "react";
import type { TraceStep } from "@/lib/types";

const TOOL_ICONS: [string, string][] = [
  ["search", "🔍"],
  ["detail", "🎬"],
  ["compare", "⚖️"],
  ["trending", "📈"],
  ["watch", "📺"],
  ["provider", "📺"],
  ["mood", "🎭"],
  ["discover", "🎭"],
  ["person", "🎭"],
];

function toolIcon(action: string): string {
  const lower = action.toLowerCase();
  return TOOL_ICONS.find(([k]) => lower.includes(k))?.[1] ?? "⚡";
}

function parseToolCall(action: string): { name: string; args: string } {
  const parenIdx = action.indexOf("(");
  if (parenIdx === -1) return { name: action.trim(), args: "" };
  return {
    name: action.slice(0, parenIdx).trim(),
    args: action.slice(parenIdx),
  };
}

function ObservationCard({ text }: { text: string }) {
  const [open, setOpen] = useState(false);
  const preview = text.slice(0, 120) + (text.length > 120 ? "…" : "");
  return (
    <div className="mt-1.5 rounded-lg border border-green-800/60 bg-green-950/30 overflow-hidden">
      <button
        className="w-full text-left px-3 py-2 flex items-center gap-2 hover:bg-green-950/50 transition-colors"
        onClick={() => setOpen((p) => !p)}
      >
        <span className="text-xs font-semibold text-green-400 uppercase tracking-wide shrink-0">
          Observation
        </span>
        <span className="text-xs text-zinc-400 truncate flex-1">{preview}</span>
        <span className="text-zinc-500 text-xs shrink-0">{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <pre className="px-3 pb-3 text-xs text-zinc-300 whitespace-pre-wrap break-all border-t border-green-800/40 pt-2">
          {text}
        </pre>
      )}
    </div>
  );
}

function TimelineStep({ step, isLast }: { step: TraceStep; isLast: boolean }) {
  const [thoughtOpen, setThoughtOpen] = useState(true);
  const { name: toolName, args: toolArgs } = step.action
    ? parseToolCall(step.action)
    : { name: "", args: "" };

  return (
    <div className="flex gap-3">
      {/* Vertical connector */}
      <div className="flex flex-col items-center">
        <div className="w-7 h-7 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center shrink-0 z-10">
          {step.step}
        </div>
        {!isLast && <div className="w-px flex-1 bg-zinc-700/60 mt-1" />}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 pb-4">
        {/* Thought */}
        {step.thought && (
          <div className="rounded-lg border border-blue-700/60 bg-blue-950/40 overflow-hidden">
            <button
              className="w-full text-left px-3 py-2 flex items-start gap-2 hover:bg-blue-950/60 transition-colors"
              onClick={() => setThoughtOpen((p) => !p)}
            >
              <span className="text-xs font-semibold text-blue-400 uppercase tracking-wide shrink-0 mt-0.5">
                Thought
              </span>
              <span className="text-sm text-zinc-300 flex-1 leading-relaxed">
                {thoughtOpen ? step.thought : step.thought.slice(0, 80) + "…"}
              </span>
              <span className="text-zinc-500 text-xs shrink-0 mt-0.5">
                {thoughtOpen ? "▲" : "▼"}
              </span>
            </button>
          </div>
        )}

        {/* Tool call */}
        {step.action && (
          <div className="mt-1.5 flex items-center gap-2 px-3 py-2 rounded-lg border border-amber-700/50 bg-amber-950/70">
            <span className="text-base leading-none shrink-0">{toolIcon(step.action)}</span>
            <span className="text-amber-300 font-mono text-sm font-semibold shrink-0">
              {toolName}
            </span>
            {toolArgs && (
              <span className="text-amber-500/80 font-mono text-xs truncate">{toolArgs}</span>
            )}
          </div>
        )}

        {/* Observation */}
        {step.observation && <ObservationCard text={step.observation} />}
      </div>
    </div>
  );
}

export function TraceViewer({ steps }: { steps: TraceStep[] }) {
  if (!steps.length) return null;
  return (
    <div className="space-y-1">
      <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-3">
        Trace — {steps.length} step{steps.length !== 1 ? "s" : ""}
      </h3>
      <div>
        {steps.map((s, i) => (
          <TimelineStep key={s.step} step={s} isLast={i === steps.length - 1} />
        ))}
      </div>
    </div>
  );
}
```

3. Run `npx tsc --noEmit` to confirm no type errors.

## Success Criteria

- [ ] Trace renders as vertical timeline, not accordion list
- [ ] Each tool call shows icon + function name + args
- [ ] Thought cards are blue, tool calls amber, observations green
- [ ] Observation collapse/expand works
- [ ] Props signature unchanged (`{ steps: TraceStep[] }`) — no changes needed in `result-panel.tsx`
- [ ] `npx tsc --noEmit` passes
