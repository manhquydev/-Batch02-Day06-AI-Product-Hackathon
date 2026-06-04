---
phase: 4
title: "Metrics Card + Compare View"
status: pending
priority: P1
effort: "45m"
dependencies: [3]
---

# Phase 04: Metrics Card + Compare View

## Overview

Thêm MetricsCard hiển thị 3 số chính (latency, steps, tool calls) và tab/toggle để chuyển giữa Single Chat và Compare (2–4 models song song).

## Requirements

- Functional:
  - **MetricsCard**: hiển thị `latency_ms`, `steps`, `tool_calls` từ `ChatResult.metrics`
  - **Compare mode**: multi-select model (2–4), shared query, gọi `POST /api/compare`
  - **Compare layout**: 2 cột (hoặc scroll ngang) — mỗi cột là một model + trace + metrics
  - Tab hoặc toggle để chuyển Single ↔ Compare
- Non-functional:
  - Compare call có thể mất 30–60s — loading state rõ ("Đang so sánh 2 models...")
  - Disable Run khi < 2 models được chọn trong Compare mode

## Architecture

```
DashboardPage
├── Tab: [Single Chat] [Compare]
├── Single Chat (phase 02–03 result)
│   ├── QueryForm (model, mode, max_steps, query)
│   ├── MetricsCard (result.metrics)
│   └── TraceViewer (result.trace)
└── Compare
    ├── CompareForm (multi-model checkboxes, mode, max_steps, shared query)
    ├── Run Compare button
    └── CompareResults
        └── [ModelColumn × N]
            ├── model name header
            ├── MetricsCard (model metrics)
            └── TraceViewer (model trace)
```

## MetricsCard Component

Verified từ `agent_v2.py:151`: `latency_ms` và `steps` là top-level trong response, không nested. `tool_calls` tính thủ công từ trace.

```tsx
// Props nhận trực tiếp từ ChatResult (top-level fields)
type Props = {
  latency_ms: number
  steps: number
  toolCalls: number   // computed: trace.filter(s => s.action).length
  label?: string
}

export function MetricsCard({ latency_ms, steps, toolCalls, label }: Props) {
  return (
    <div>
      {label && <h3>{label}</h3>}
      <div style={{ display: "flex", gap: "1rem" }}>
        <Stat label="Latency" value={`${latency_ms}ms`} />
        <Stat label="Steps" value={steps} />
        <Stat label="Tool Calls" value={toolCalls} />
      </div>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <p>{label}</p>
      <p><strong>{value}</strong></p>
    </div>
  )
}
```

**Usage trong dashboard:**
```tsx
{result && (
  <MetricsCard
    latency_ms={result.latency_ms}
    steps={result.steps}
    toolCalls={result.trace.filter(s => s.action !== null).length}
  />
)}
```

## Compare Form + Results

```tsx
// Compare mode state
const [compareModels, setCompareModels] = useState<string[]>([])
const [compareResult, setCompareResult] = useState<CompareResult | null>(null)

function toggleModel(m: string) {
  setCompareModels(prev =>
    prev.includes(m) ? prev.filter(x => x !== m) : prev.length < 4 ? [...prev, m] : prev
  )
}

async function handleCompare() {
  if (compareModels.length < 2 || !query.trim()) return
  setLoading(true); setError(null); setCompareResult(null)
  try {
    const res = await runCompare({ query, models: compareModels, mode, max_steps: maxSteps })
    setCompareResult(res)
  } catch (e) {
    setError(e instanceof Error ? e.message : "Lỗi so sánh")
  } finally {
    setLoading(false)
  }
}

// Render compare results
{compareResult && Object.entries(compareResult.results).map(([modelKey, res]) => (
  <div key={modelKey}>
    <h3>{modelKey}</h3>
    <MetricsCard metrics={res.metrics} />
    <TraceViewer trace={res.trace} />
  </div>
))}
```

## Tab Toggle Implementation

```tsx
const [tab, setTab] = useState<"single" | "compare">("single")

// Header tabs
<div>
  <button onClick={() => setTab("single")} aria-selected={tab === "single"}>Single Chat</button>
  <button onClick={() => setTab("compare")} aria-selected={tab === "compare"}>Compare Models</button>
</div>

{tab === "single" && <SingleChatSection />}
{tab === "compare" && <CompareSection />}
```

**Đơn giản nhất:** chia sẻ `query`, `mode`, `maxSteps` state giữa cả 2 tab.

## Related Code Files

- Modify: `src/app/dashboard/page.tsx` — thêm tab toggle, compare state, compare form
- Create (hoặc inline): `src/components/metrics-card.tsx`
- Read: `src/lib/api.ts` — `runCompare()`
- Read: `src/lib/types.ts` — `CompareResult`, `Metrics`

## Implementation Steps

1. Thêm `MetricsCard` component (inline hoặc `src/components/metrics-card.tsx`)
2. Add vào Single tab: `{result && <MetricsCard metrics={result.metrics} />}` ngay trên `<TraceViewer>`
3. Thêm tab state `"single" | "compare"` + tab button UI
4. Implement Compare tab: checkbox list từ `models` state (fetch từ API), giới hạn 4
5. Implement `handleCompare` function dùng `runCompare()`
6. Render `compareResult`: loop `Object.entries(compareResult.results)` → mỗi entry hiện `MetricsCard` + `TraceViewer`
7. Loading/error state cho compare call
8. End-to-end test: chọn 2 models → nhập query → Run Compare → xem 2 traces side-by-side

## Success Criteria

- [ ] MetricsCard hiển thị đúng 3 số sau single chat
- [ ] Tab Single ↔ Compare chuyển được, không mất query
- [ ] Compare: checkbox list, chọn 2–4 models
- [ ] Compare results: mỗi model có metrics + trace riêng
- [ ] Run Compare disabled khi < 2 models chọn
- [ ] Loading/error state cho cả 2 modes

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Compare call timeout (>30s) | Medium | Hackathon: chấp nhận slow, chỉ cần không crash. Hiện "Đang so sánh..." |
| `compareResult.results` key format khác dự kiến | Low | Log raw response trước khi render; dùng `Object.entries()` linh hoạt |
| Layout 2 cột vỡ trên màn hình nhỏ | Low | Hackathon: demo trên laptop → không cần mobile responsive |
| State shared giữa tabs bị lẫn lộn | Medium | Tách `result` (single) và `compareResult` (compare) rõ ràng |

## Demo Checklist (cuối cùng trước khi demo)

- [ ] Backend chạy tại localhost:8000 (`uvicorn src.api.main:app --reload`)
- [ ] Frontend chạy tại localhost:3001 (`npm run dev -- -p 3001`)
- [ ] `.env.local` có `NEXT_PUBLIC_API_URL=http://localhost:8000`
- [ ] Thử query "tôi buồn muốn xem phim nhẹ nhàng" → xem trace 5 steps
- [ ] Thử compare openai/gpt-4o-mini vs deepseek/deepseek-chat
- [ ] Screenshot trace + metrics để backup nếu internet chậm khi demo
