---
phase: 1
title: "Layout Shell + API Client"
status: pending
priority: P1
effort: "30m"
dependencies: []
---

# Phase 01: Layout Shell + API Client

## Overview

Dựng khung layout cho admin dashboard và tạo API client tập trung. Đây là foundation cho tất cả các phase sau.

## Requirements

- Functional:
  - Root layout có title "Movie Agent Admin"
  - Navigation header hiển thị tên app
  - `lib/types.ts` định nghĩa đủ TypeScript types cho API response
  - `lib/api.ts` wrap fetch calls đến backend
- Non-functional:
  - Không crash khi `NEXT_PUBLIC_API_URL` chưa set (fallback `http://localhost:8000`)
  - Error boundary cơ bản

## Architecture

```
src/
├── app/
│   ├── layout.tsx       ← update metadata, add header
│   ├── page.tsx         ← redirect hoặc landing đơn giản
│   └── globals.css      ← giữ nguyên Tailwind v4 setup
└── lib/
    ├── types.ts         ← TraceStep, Metrics, Movie, ModelInfo
    └── api.ts           ← fetchModels(), fetchTools(), runChat(), runCompare()
```

## TypeScript Types (types.ts)

Verified từ `backend/src/agent/agent_v2.py:89` và `api/main.py:67`.

```ts
export type TraceStep = {
  step: number
  thought: string | null
  action: string | null   // raw string: "search_movies('Inception', 5)"
  observation: string | null
  raw: string             // raw LLM output
}

export type Usage = {
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
}

export type Movie = {
  id: number
  title: string
  poster_path?: string
  vote_average?: number
  overview?: string
}

// Top-level fields — NO nested `metrics` object
export type ChatResult = {
  answer: string
  trace: TraceStep[]
  steps: number           // top-level, NOT metrics.steps
  latency_ms: number      // top-level, NOT metrics.latency_ms
  usage: Usage
  mode: string
  movies: Movie[]
  ok?: boolean            // added by compare endpoint
  error?: string          // added by compare endpoint on failure
}

export type CompareResult = {
  results: Record<string, ChatResult>
}

export type ModelInfo = string  // "provider/model"
```

**tool_calls** không có trong response — tính thủ công:
```ts
const toolCalls = result.trace.filter(s => s.action !== null).length
```

## API Client (api.ts)

```ts
const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export async function fetchModels(): Promise<string[]> {
  const r = await fetch(`${BASE}/api/models`)
  const d = await r.json()
  return d.models
}

export async function runChat(body: {
  message: string; mode: string; provider: string; model: string; max_steps: number
}): Promise<ChatResult> {
  const r = await fetch(`${BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function runCompare(body: {
  query: string; models: string[]; mode: string; max_steps: number
}): Promise<CompareResult> {
  const r = await fetch(`${BASE}/api/compare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}
```

## Related Code Files

- Modify: `src/app/layout.tsx` — update metadata title/description, thêm header
- Modify: `src/app/page.tsx` — redirect đến `/dashboard` hoặc hiện link
- Create: `src/lib/types.ts`
- Create: `src/lib/api.ts`

## Implementation Steps

1. Đọc docs Next.js trong `node_modules/next/dist/docs/` — xác nhận App Router conventions không thay đổi
2. Update `layout.tsx`: set `metadata.title = "Movie Agent Admin"`, thêm `<header>` đơn giản
3. Update `page.tsx`: replace boilerplate bằng link/redirect đến `/dashboard`
4. Tạo `src/lib/types.ts` với đủ types ở trên
5. Tạo `src/lib/api.ts` với 3 functions: `fetchModels`, `runChat`, `runCompare`
6. Tạo `.env.local` với `NEXT_PUBLIC_API_URL=http://localhost:8000`
7. Chạy `npm run dev` để verify compile OK

## Success Criteria

- [ ] `npm run dev` không có compile error
- [ ] Header hiển thị "Movie Agent Admin"
- [ ] `src/lib/types.ts` và `src/lib/api.ts` tồn tại và compile clean
- [ ] `.env.local` đã tạo

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Tailwind v4 class không work | Medium | Kiểm tra `globals.css` import, dùng inline style nếu cần |
| Next.js App Router breaking change | Low | Đọc docs trước khi code |

## Env Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```
