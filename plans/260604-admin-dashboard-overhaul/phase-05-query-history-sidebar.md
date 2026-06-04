---
phase: 5
title: "Query History Sidebar"
status: pending
priority: P2
effort: "30m"
dependencies: [1, 2, 3]
---

# Phase 5: Query History Sidebar

## Overview

Right-side collapsible panel that logs each completed query (query text + timestamp + latency). Click any entry to restore the result into the main panel. Backed by component state (not localStorage — no persistence needed for demo). **Cuttable** — adds polish but not required.

## Architecture

```
DashboardPage
├── [main content — existing]
└── HistorySidebar (fixed right panel, toggle button)
    └── HistoryEntry × N
        ├── query text (truncated)
        ├── latency badge
        └── timestamp (HH:MM:SS)
```

## Related Code Files

- Modify: `codebase/frontend-admin/src/app/dashboard/page.tsx`
- Create: `codebase/frontend-admin/src/components/history-sidebar.tsx`

## Implementation Steps

### Step 1 — Define history state in `DashboardPage`

```tsx
import type { ChatResponse } from "@/lib/types";

type HistoryEntry = {
  id: number;
  query: string;
  result: ChatResponse;
  timestamp: string; // HH:MM:SS
  latency: number;
};
const [history, setHistory] = useState<HistoryEntry[]>([]);
const [historyOpen, setHistoryOpen] = useState(false);
const historyCounter = useRef(0);
```

### Step 2 — Push to history after each SingleTab result

Pass `onResult` callback to `SingleTab`:
```ts
onResult: (query: string, result: ChatResponse) => {
  const now = new Date();
  const ts = now.toTimeString().slice(0, 8);
  setHistory((prev) => [
    { id: ++historyCounter.current, query, result, timestamp: ts, latency: result.latency_ms },
    ...prev,
  ].slice(0, 20)); // cap at 20 entries
};
```

### Step 3 — Create `history-sidebar.tsx`

```tsx
"use client";
import type { ChatResponse } from "@/lib/types";

type HistoryEntry = {
  id: number;
  query: string;
  result: ChatResponse;
  timestamp: string;
  latency: number;
};

type Props = {
  entries: HistoryEntry[];
  open: boolean;
  onToggle: () => void;
  onSelect: (entry: HistoryEntry) => void;
};

export function HistorySidebar({ entries, open, onToggle, onSelect }: Props) {
  return (
    <>
      {/* Toggle tab */}
      <button
        onClick={onToggle}
        className="fixed right-0 top-1/2 -translate-y-1/2 bg-zinc-800 border border-zinc-700 rounded-l-lg px-2 py-3 text-xs text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700 transition-colors writing-mode-vertical"
        style={{ writingMode: "vertical-rl" }}
        title={open ? "Close history" : "Open history"}
      >
        {open ? "✕ Close" : `History (${entries.length})`}
      </button>

      {/* Panel */}
      {open && (
        <div className="fixed right-0 top-0 h-full w-72 bg-zinc-900 border-l border-zinc-700 flex flex-col z-50 shadow-2xl">
          <div className="px-4 py-3 border-b border-zinc-700 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-zinc-200">Query History</h2>
            <button onClick={onToggle} className="text-zinc-500 hover:text-zinc-300 text-lg">✕</button>
          </div>
          <div className="flex-1 overflow-y-auto">
            {entries.length === 0 && (
              <p className="text-xs text-zinc-500 p-4">No queries yet.</p>
            )}
            {entries.map((e) => (
              <button
                key={e.id}
                onClick={() => onSelect(e)}
                className="w-full text-left px-4 py-3 border-b border-zinc-800 hover:bg-zinc-800 transition-colors group"
              >
                <p className="text-sm text-zinc-300 truncate group-hover:text-white">{e.query}</p>
                <div className="flex gap-3 mt-1">
                  <span className="text-xs text-zinc-500">{e.timestamp}</span>
                  <span className="text-xs text-blue-400">{e.latency}ms</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
```

### Step 4 — Wire into `DashboardPage` layout

Wrap main area and sidebar in a relative container. Pass `onSelect` callback that sets `selectedResult` state shown in a modal or replaces the current result.

## Success Criteria

- [ ] History toggle button visible on right edge
- [ ] Panel slides in when toggled
- [ ] Clicking entry restores query text and result into SingleTab
- [ ] History capped at 20 entries (oldest dropped)
- [ ] `npx tsc --noEmit` passes
