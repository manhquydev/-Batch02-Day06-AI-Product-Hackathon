---
phase: 3
title: "Trace Viewer Component"
status: pending
priority: P1
effort: "45m"
dependencies: [2]
---

# Phase 03: Trace Viewer Component

## Overview

Component hiển thị từng bước ReAct trace (Thought → Action → Observation) dạng timeline có thể expand/collapse. Đây là tính năng differentiator chính của admin panel.

## Requirements

- Functional:
  - Nhận `trace: TraceStep[]` làm prop
  - Hiển thị mỗi step dạng card với: step number, thought, action + action_input, observation
  - Syntax highlight cho JSON action_input và observation (dùng `<pre>` + Geist Mono)
  - Hiển thị error nếu step có `error` field
  - Collapse/expand từng step (accordion pattern)
  - Step có tool call: highlight action name
- Non-functional:
  - Hiển thị đúng khi `trace` là empty array
  - Không crash khi field `thought`/`action`/`observation` là undefined

## Architecture

```
src/app/dashboard/
└── page.tsx
    └── <TraceViewer trace={result.trace} />
```

Inline component trong `page.tsx` hoặc tách ra `src/components/trace-viewer.tsx` nếu > 60 lines.

## Component Design

Verified từ `agent_v2.py:89`: `action` là raw string, không có `action_input`. Không có `error` field trong step.

```tsx
// TraceViewer — hiển thị ReAct trace steps
type Props = { trace: TraceStep[] }

export function TraceViewer({ trace }: Props) {
  const [expanded, setExpanded] = useState<Record<number, boolean>>({})
  
  if (!trace.length) return <p>Không có trace</p>
  
  return (
    <section>
      <h2>ReAct Trace ({trace.length} steps)</h2>
      {trace.map((step) => (
        <div key={step.step}>
          {/* Header: Step N · tool_name(...) — click to toggle */}
          <button onClick={() => setExpanded(prev => ({ ...prev, [step.step]: !prev[step.step] }))}>
            Step {step.step} {step.action ? `· ${step.action}` : "· (no action)"}
          </button>
          
          {/* Body: visible khi expanded */}
          {expanded[step.step] && (
            <div>
              {step.thought && (
                <div><strong>Thought:</strong> <p>{step.thought}</p></div>
              )}
              {step.action && (
                <div>
                  <strong>Action:</strong>
                  {/* action là raw string: "search_movies('Inception', 5)" */}
                  <pre><code>{step.action}</code></pre>
                </div>
              )}
              {step.observation && (
                <div>
                  <strong>Observation:</strong>
                  {/* observation là string — có thể chứa JSON stringified */}
                  <pre>{step.observation}</pre>
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </section>
  )
}
```

## Styling Notes (Tailwind v4)

- Dùng Geist Mono cho `<pre>` và `<code>` — đã có sẵn qua CSS var `--font-mono`
- Background tối cho pre blocks: `bg-zinc-900 text-zinc-100` hoặc `bg-zinc-100 dark:bg-zinc-900`
- Step header: subtle border bottom, cursor pointer
- Error step: red left border accent

## Related Code Files

- Create (hoặc inline): `src/components/trace-viewer.tsx`
- Modify: `src/app/dashboard/page.tsx` — import và render `<TraceViewer>`
- Read: `src/lib/types.ts` — `TraceStep` type

## Implementation Steps

1. Quyết định inline hay tách component (nếu > 60 lines → tách `src/components/trace-viewer.tsx`)
2. Implement accordion state với `useState<Record<number, boolean>>`
3. Render từng step: header (click to toggle) + body (thought/action/observation)
4. Format JSON với `JSON.stringify(x, null, 2)` trong `<pre>` tag
5. Handle `step.error` — hiển thị warning style khác biệt
6. Add vào `DashboardPage`: `{result && <TraceViewer trace={result.trace} />}`
7. Test với mock data (copy một trace từ `POST /api/chat` response)
8. Đảm bảo: empty trace → "Không có trace", undefined fields → không crash

## Success Criteria

- [ ] TraceViewer render đúng với trace có 5 steps
- [ ] Accordion expand/collapse hoạt động
- [ ] JSON action_input hiển thị formatted, không garbled
- [ ] Error step hiển thị khác biệt với step bình thường
- [ ] Empty trace → graceful empty state

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| `observation` là object, không phải string | Medium | `typeof obs === "string" ? obs : JSON.stringify(obs, null, 2)` |
| `action_input` null/undefined | Low | Optional chaining `step.action_input &&` |
| Quá nhiều steps → long scroll | Low | Hackathon scope: scroll is fine, no virtualization needed |
