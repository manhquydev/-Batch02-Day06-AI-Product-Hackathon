# Brainstorm: Admin Dashboard Full Visual Overhaul

**Date:** 2026-06-04  
**Context:** Hackathon demo 16:00 + post-hackathon cleanup  
**Focus:** WOW factor visual upgrades for admin dashboard

---

## Problem Statement

Admin dashboard hiện tại là MVP trạng thái:
- Metric badges đơn giản (latency/steps/tool calls — 3 số)
- Trace viewer là accordion text thuần, không visual flow
- Compare tab = grid text, không có comparison chart
- Mode dropdown hiển thị stale modes (v1/v2/chatbot) đã bị xóa khỏi backend
- Không có session history, không có trend tracking

Cần nâng visual WOW factor trước 16:00 đồng thời clean code cho post-hackathon.

---

## Constraints

- `frontend-admin` chỉ có: `next@16.2.7`, `react@19`, `tailwindcss@4` — không có chart library
- Timeline: ~2-3h trước 16:00
- Deploy target: local demo (không cần production deploy)

---

## Approved Approach: Full Overhaul (Priority-Ordered)

### Phase 1: Fix Stale Modes (10 min) — NON-CUTTABLE

**Files:**
- `codebase/frontend-admin/src/app/dashboard/page.tsx` — `MODES` array → `["ReAct Agent"]` only
- `codebase/backend/src/api/main.py` — `ModeType` literal → `"ReAct Agent"` only, remove legacy literals

**Why non-cuttable:** correctness bug — dropdown advertises modes that return wrong results.

---

### Phase 2: Trace Timeline Visual (45 min) — HIGH PRIORITY

**File:** `codebase/frontend-admin/src/components/trace-viewer.tsx` — full rewrite

**Design:**
```
Step 1  ─┐  💭 Thought   "User muốn tìm phim kinh dị..."       [blue]
         │
         ▼  🔍 search_movies  query="inception"                 [amber pill]
            👁 Observation   3 results found                    [green, collapsible]

Step 2  ─┐  💭 Thought   "Cần details phim đầu tiên..."
         ▼  🎬 get_movie_details  id=27205                      [amber pill]
            👁 Observation   Inception, 2010, 8.8...            [green, collapsible]

Final   ─┘  ✅ Answer                                           [emerald highlight]
```

**Tool icon map:**
| Tool | Icon |
|------|------|
| search_movies | 🔍 |
| get_movie_details | 🎬 |
| compare_movies | ⚖️ |
| trending_movies | 📈 |
| watch_providers | 📺 |
| discover_by_mood | 🎭 |
| Default | ⚡ |

**Color coding (Tailwind):**
- Thought: `border-blue-700 bg-blue-950/40`
- Tool call: `bg-amber-950/60 text-amber-300 font-mono`
- Observation: `border-green-800 bg-green-950/30` (collapsible JSON)
- Answer (final): `border-emerald-600 bg-emerald-950/40`

**Connecting line:** `border-l-2 border-zinc-700 ml-3.5 pl-6`

---

### Phase 3: Comparison Metrics Chart (45 min) — HIGH PRIORITY

**Files:**
- `codebase/frontend-admin/src/components/compare-chart.tsx` — new file
- `codebase/frontend-admin/src/components/compare-tab.tsx` — import + render chart after results

**CSS-only bar chart design:**

```tsx
// Bar = div with width as % of max value
<div style={{ width: `${(value / max) * 100}%` }} className="bg-blue-500 h-4 rounded-r" />
```

**Metrics shown:**
1. Latency (ms) — lower is better → winner badge 🏆
2. Steps — lower is better → winner badge 🏆
3. Tool calls — informational only

**Export button:** JSON stringify results → download as `.json` file

---

### Phase 4: Session Summary Strip (20 min) — CUTTABLE

**File:** `codebase/frontend-admin/src/app/dashboard/page.tsx`

**State:**
```ts
const [sessionStats, setSessionStats] = useState({
  totalQueries: 0,
  totalLatency: 0,
  bestModel: null as string | null,
})
```

**UI:** Strip dưới header, ẩn cho đến query đầu tiên:
```
Queries: 3  |  Avg Latency: 940ms  |  Best model this session: gemini/flash
```

---

### Phase 5: Query History Sidebar (30 min) — CUTTABLE

**File:** `codebase/frontend-admin/src/app/dashboard/page.tsx`

State: `history: {id, query, result, timestamp}[]`

**UI:** Right sidebar, collapsed by default, expand button. Click item → restore result to main panel.

---

## Files Modified

| File | Change |
|------|--------|
| `frontend-admin/src/components/trace-viewer.tsx` | Full rewrite — timeline layout |
| `frontend-admin/src/components/compare-chart.tsx` | New — CSS bar chart + export |
| `frontend-admin/src/components/compare-tab.tsx` | Add chart after results |
| `frontend-admin/src/app/dashboard/page.tsx` | Fix modes, add session state, optional history sidebar |
| `backend/src/api/main.py` | Fix ModeType literal |

## Risks

| Risk | Mitigation |
|------|-----------|
| Trace Timeline CSS complex | Fallback: keep current accordion if time runs out |
| Phase 4-5 not finish before 16:00 | Cut both — Phase 1-3 enough for WOW demo |
| Backend ModeType needs redeploy | Frontend-only fix adequate for local demo |

## Success Criteria

- [ ] Mode dropdown shows only "ReAct Agent"
- [ ] Trace viewer shows step-by-step timeline with tool icons + color coding
- [ ] Compare tab shows latency/steps bar chart with winner badge
- [ ] Demo takes < 30 sec to explain what each panel shows
