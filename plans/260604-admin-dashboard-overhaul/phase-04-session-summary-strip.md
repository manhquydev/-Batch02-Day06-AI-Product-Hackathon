---
phase: 4
title: "Session Summary Strip"
status: pending
priority: P2
effort: "20m"
dependencies: [1]
---

# Phase 4: Session Summary Strip

## Overview

Track queries run during the session and show a summary strip below the header. Appears after the first query completes. Shows: total queries, average latency, best model (fastest avg). **Cuttable** — Phase 1-3 is sufficient for demo if time runs short.

## Related Code Files

- Modify: `codebase/frontend-admin/src/app/dashboard/page.tsx`

## Implementation Steps

### Step 1 — Add session state to `DashboardPage`

```tsx
type SessionEntry = { latency: number; model: string };
const [sessionEntries, setSessionEntries] = useState<SessionEntry[]>([]);
```

### Step 2 — Pass a callback down to `SingleTab` and `CompareTab`

Add `onResult` prop to both tabs. After a successful query, call:
```ts
onResult({ latency: result.latency_ms, model: effectiveModel });
```

For `CompareTab`, iterate over `result.results` and push one entry per successful model.

### Step 3 — Render strip below the controls bar

```tsx
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
```

## Success Criteria

- [ ] Strip hidden until first query completes
- [ ] Avg latency and best model update after each query
- [ ] No impact on existing Single/Compare tab behavior
- [ ] `npx tsc --noEmit` passes
