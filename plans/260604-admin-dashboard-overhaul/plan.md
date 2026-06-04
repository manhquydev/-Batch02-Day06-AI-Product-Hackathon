---
title: "Admin Dashboard Visual Overhaul"
description: "WOW factor visual upgrades for hackathon demo + post-hackathon cleanup"
status: pending
priority: P1
branch: "develop"
tags: ["frontend-admin", "ux", "demo"]
blockedBy: []
blocks: []
created: "2026-06-04T07:25:46.066Z"
createdBy: "ck:plan"
source: skill
---

# Admin Dashboard Visual Overhaul

## Overview

Nâng cấp visual WOW factor cho admin dashboard trước demo 16:00/06/04/2026.
Implement theo thứ tự priority — dừng khi đủ đẹp hoặc hết giờ.
Phase 1-3 là non-negotiable; Phase 4-5 cuttable nếu cần.

**Context:** `plans/260604-admin-dashboard-overhaul/brainstorm-admin-dashboard-overhaul.md`

**Stack:** Next.js 16.2.7 + React 19 + TypeScript + Tailwind CSS v4 (no chart lib)

## Phases

| Phase | Name | Status | Effort | Priority | Cuttable? |
|-------|------|--------|--------|----------|-----------|
| 1 | [Fix Stale Modes](./phase-01-fix-stale-modes.md) | Pending | 10m | P1 | No |
| 2 | [Trace Timeline Visual](./phase-02-trace-timeline-visual.md) | Pending | 45m | P1 | No |
| 3 | [Comparison Metrics Chart](./phase-03-comparison-metrics-chart.md) | Pending | 45m | P1 | No |
| 4 | [Session Summary Strip](./phase-04-session-summary-strip.md) | Pending | 20m | P2 | Yes |
| 5 | [Query History Sidebar](./phase-05-query-history-sidebar.md) | Pending | 30m | P2 | Yes |

## Files Modified

| File | Change |
|------|--------|
| `codebase/frontend-admin/src/app/dashboard/page.tsx` | Fix MODES, add session state |
| `codebase/backend/src/api/main.py` | Fix ModeType literal |
| `codebase/frontend-admin/src/components/trace-viewer.tsx` | Full rewrite — timeline |
| `codebase/frontend-admin/src/components/compare-chart.tsx` | New — CSS bar chart |
| `codebase/frontend-admin/src/components/compare-tab.tsx` | Import compare-chart |

## Dependencies

Extends completed plan: `plans/260604-admin-panel-implementation/`

## Definition of Done (Demo)

- [ ] Mode dropdown shows only "ReAct Agent"
- [ ] Trace viewer shows step-by-step timeline with tool icons + color coding
- [ ] Compare tab shows latency/steps bar chart with winner badge
- [ ] No TypeScript compile errors
