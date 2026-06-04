---
title: "Admin Panel — Trace Viewer & Metrics Dashboard"
status: in-progress
priority: P1
created: 2026-06-04
scope: project
owner: Nguyễn Mạnh Quý (2A202600643)
---

# Admin Panel Implementation Plan

**Deadline:** 23:59 ngày 04/06/2026 (hôm nay)
**Stack:** Next.js App Router + TypeScript + Tailwind CSS v4
**Backend:** FastAPI tại `http://localhost:8000`
**Owned files:** `codebase/frontend-admin/src/`

## Mục tiêu

Build admin dashboard để:
1. Chọn model + chạy query (single hoặc compare 2–4 models)
2. Xem ReAct trace step-by-step
3. Xem metrics (latency, steps, tool calls)

## Cảnh báo kỹ thuật

> **AGENTS.md:** Next.js này có breaking changes — đọc docs trong `node_modules/next/dist/docs/` trước khi viết code. Tailwind v4 cũng khác v3.

## API Endpoints tiêu thụ

| Method | Path | Admin dùng để |
|--------|------|---------------|
| `GET` | `/api/models` | Populate model selector |
| `GET` | `/api/tools` | Hiển thị 9 TMDB tools |
| `POST` | `/api/chat` | Single model run |
| `POST` | `/api/compare` | Multi-model run |

**Response shape** (`/api/chat`):
```ts
{ answer: string, trace: TraceStep[], metrics: { latency_ms: number, steps: number, tool_calls: number }, movies: Movie[] }
```

## Phases

| ID | Phase | Status | Effort | Priority |
|----|-------|--------|--------|----------|
| 01 | Layout shell + API client | pending | 30m | P1 |
| 02 | Single chat panel | pending | 45m | P1 |
| 03 | Trace viewer component | pending | 45m | P1 |
| 04 | Metrics + Compare view | pending | 45m | P1 |

## Định nghĩa "done" cho demo

- [ ] Chọn model → nhập query → nhận trace hiển thị step-by-step
- [ ] Metrics: latency (ms), steps (#), tool calls (#) hiện dưới trace
- [ ] Compare: 2 model chạy song song, trace mỗi model riêng
- [ ] Không crash khi backend offline (hiện error state)

## File structure sau khi build

```
frontend-admin/src/
├── app/
│   ├── layout.tsx          (cập nhật title/meta)
│   ├── page.tsx            (home → redirect to /dashboard)
│   ├── dashboard/
│   │   └── page.tsx        (main dashboard)
│   └── globals.css
└── lib/
    ├── api.ts              (fetch wrappers)
    └── types.ts            (shared TypeScript types)
```
