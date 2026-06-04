---
phase: 1
title: "Fix Stale Modes"
status: pending
priority: P1
effort: "10m"
dependencies: []
---

# Phase 1: Fix Stale Modes

## Overview

Remove legacy mode strings (v1/v2/chatbot) from frontend dropdown and backend ModeType. Only "ReAct Agent" is valid after the async refactor — the other modes silently produce wrong results.

## Related Code Files

- Modify: `codebase/frontend-admin/src/app/dashboard/page.tsx`
- Modify: `codebase/backend/src/api/main.py`

## Implementation Steps

1. **`dashboard/page.tsx`** — update `MODES` const and default state:
   ```ts
   // Before
   const MODES = ["ReAct Agent v2", "ReAct Agent v1", "Chatbot Baseline"] as const;
   const [mode, setMode] = useState<string>("ReAct Agent v2");

   // After
   const MODES = ["ReAct Agent"] as const;
   const [mode, setMode] = useState<string>("ReAct Agent");
   ```

2. **`backend/src/api/main.py`** — update `ModeType` Literal:
   ```python
   # Before
   ModeType = Literal["ReAct Agent", "ReAct Agent v2", "ReAct Agent v1", "Chatbot Baseline"]

   # After
   ModeType = Literal["ReAct Agent"]
   ```
   Note: `ChatRequest.mode` and `CompareRequest.mode` default is already `"ReAct Agent"` — no change needed there.

3. Run TypeScript check: `cd codebase/frontend-admin && npx tsc --noEmit`

## Success Criteria

- [ ] Admin mode dropdown shows only "ReAct Agent"
- [ ] Backend `ModeType` rejects any other string at the Pydantic layer
- [ ] `npx tsc --noEmit` passes with zero new errors
