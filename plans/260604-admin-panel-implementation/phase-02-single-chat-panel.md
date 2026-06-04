---
phase: 2
title: "Single Chat Panel"
status: pending
priority: P1
effort: "45m"
dependencies: [1]
---

# Phase 02: Single Chat Panel

## Overview

Build trang `/dashboard` với form để chọn model + nhập query + chạy single chat. Đây là flow cơ bản nhất của admin.

## Requirements

- Functional:
  - Dropdown chọn model (fetch từ `GET /api/models`)
  - Dropdown chọn mode (Chatbot Baseline / ReAct Agent v1 / ReAct Agent v2)
  - Number input cho `max_steps` (2–8, default 5)
  - Textarea nhập query
  - Nút "Run" → gọi `POST /api/chat`
  - Loading state rõ ràng ("Đang chạy agent...")
  - Error state khi API fail
  - Sau khi có result: pass xuống Trace Viewer (phase 03) và Metrics (phase 04)
- Non-functional:
  - Không block UI khi fetch models lúc load
  - Disable nút Run khi đang loading

## Architecture

```
src/app/dashboard/
└── page.tsx     ← Client Component ("use client")
    ├── fetchModels() on mount → populate model dropdown
    ├── form state: { model, mode, max_steps, query }
    ├── result state: ChatResult | null
    ├── loading: boolean
    └── renders: <QueryForm />, <TraceViewer result={result} />, <MetricsCard result={result} />
```

**Lưu ý:** Dùng `"use client"` vì form cần state. Không cần Server Component phức tạp cho hackathon.

## Component Structure (inline trong page.tsx cho nhanh)

```tsx
"use client"
import { useEffect, useState } from "react"
import { fetchModels, runChat } from "@/lib/api"
import type { ChatResult } from "@/lib/types"

const MODES = ["ReAct Agent v2", "ReAct Agent v1", "Chatbot Baseline"]

export default function DashboardPage() {
  const [models, setModels] = useState<string[]>([])
  const [model, setModel] = useState("")
  const [mode, setMode] = useState(MODES[0])
  const [maxSteps, setMaxSteps] = useState(5)
  const [query, setQuery] = useState("")
  const [result, setResult] = useState<ChatResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchModels().then(ms => { setModels(ms); setModel(ms[0] ?? "") }).catch(() => {})
  }, [])

  async function handleRun() {
    if (!query.trim() || !model) return
    setLoading(true); setError(null); setResult(null)
    try {
      const [provider, ...rest] = model.split("/")
      const res = await runChat({ message: query, mode, provider, model: rest.join("/"), max_steps: maxSteps })
      setResult(res)
      // Note: res.latency_ms and res.steps are top-level, not nested under metrics
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi không xác định")
    } finally {
      setLoading(false)
    }
  }

  return (
    <main>
      {/* Form */}
      {/* TraceViewer — phase 03 */}
      {/* MetricsCard — phase 04 */}
    </main>
  )
}
```

## Related Code Files

- Create: `src/app/dashboard/page.tsx`
- Read: `src/lib/api.ts` (phase 01)
- Read: `src/lib/types.ts` (phase 01)

## Implementation Steps

1. Tạo `src/app/dashboard/page.tsx` với `"use client"`
2. Implement `useEffect` fetch models on mount
3. Implement form UI: model select, mode select, max_steps number input, query textarea, Run button
4. Implement `handleRun` async function
5. Hiển thị loading state (spinner hoặc text "Đang chạy agent...")
6. Hiển thị error state nếu có
7. Placeholder cho TraceViewer và MetricsCard (sẽ add trong phase 03, 04)
8. Verify: nhập query → Run → nhận raw JSON result (console.log tạm)

## Success Criteria

- [ ] `/dashboard` load được, không 404
- [ ] Dropdown model populated từ API
- [ ] Nhấn Run → fetch đúng endpoint → nhận response
- [ ] Loading state hiện khi đang chờ
- [ ] Error message hiện khi API fail hoặc offline

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| `model` string format "provider/model" → split sai | Medium | Test với "openai/gpt-4o-mini" — split on first "/" |
| CORS error khi call backend | Low | Backend đã có `allow_origins=["*"]` |
| Model list empty (backend offline) | Medium | Show "Backend offline" message, không crash |
