# MVP15 Timeline / Event Log Explorer 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans inline for this repository because the user explicitly forbids subagents and dynamic workflows. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read-only in-app timeline explorer for formal world EventLog history with summary counts, filtering, and user-readable event descriptions.

**Architecture:** Extend the existing `GET /worlds/{world_id}/events` endpoint additively with a `summary` object. Add a focused `WorldTimelinePanel` React component that consumes `getWorldEvents()`, renders summary/filter UI, and is mounted in the World overview Narrative Control Center area.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, React, TypeScript, Vite, Vitest, Testing Library.

---

## File map

- Modify `backend/app/event/schemas.py`
  - Add `EventLogSummaryResponse`.
  - Add `summary` to `EventLogListResponse`.
- Modify `backend/app/world/service.py`
  - Extend `list_world_events()` to compute all-world event type counts and latest world version.
- Modify `backend/tests/test_world_template.py`
  - Add backend tests for summary counts, filter behavior, and ownership boundary.
- Modify `frontend/src/api/types.ts`
  - Add `EventLogSummary` and `EventLogListResponse` types.
- Modify `frontend/src/api/client.ts`
  - Type `getWorldEvents()` with `EventLogListResponse`.
- Modify `frontend/src/api/client.test.ts`
  - Add event helper assertions for filters/pagination and summary-compatible response.
- Create `frontend/src/world/WorldTimelinePanel.tsx`
  - Render event summary counts, filter buttons, event cards, loading, empty, and error states.
- Create `frontend/src/world/WorldTimelinePanel.test.tsx`
  - Cover loading, summary rendering, filter calls, event descriptions, and error state.
- Modify `frontend/src/world/WorldPage.tsx`
  - Import and mount `WorldTimelinePanel`.
- Modify `frontend/src/world/WorldPage.test.tsx`
  - Mock `getWorldEvents()` and assert the timeline panel loads.

## Task 1: Backend event summary contract

**Files:**
- Modify: `backend/tests/test_world_template.py`
- Modify: `backend/app/event/schemas.py`
- Modify: `backend/app/world/service.py`

- [ ] **Step 1: Write failing backend summary/filter tests**

Add these tests to `backend/tests/test_world_template.py` after `test_create_custom_world_records_world_created_event_and_export_timeline`:

```python
def test_world_events_include_summary_counts_and_latest_world_version(client):
    token = register(client, 'timeline-summary@example.com')
    create_response = client.post('/worlds', headers=auth(token), json=custom_world_payload())
    world_id = create_response.json()['id']

    events = client.get(f'/worlds/{world_id}/events', headers=auth(token)).json()

    assert events['total'] == 1
    assert events['summary']['total'] == 1
    assert events['summary']['event_type_counts'] == {'WORLD_CREATED': 1}
    assert events['summary']['latest_world_version'] == 1


def test_world_events_filter_items_but_keep_all_world_summary(client):
    token = register(client, 'timeline-filter@example.com')
    create_response = client.post('/worlds', headers=auth(token), json=custom_world_payload())
    world_id = create_response.json()['id']
    character_id = client.get(f'/worlds/{world_id}/overview', headers=auth(token)).json()['characters'][0]['id']
    update_response = client.put(
        f'/characters/{character_id}',
        headers=auth(token),
        json={'status': '追查灯塔异常', 'edit_reason': '推进角色线索'},
    )
    assert update_response.status_code == 200

    events = client.get(f'/worlds/{world_id}/events?event_type=character_change', headers=auth(token)).json()

    assert events['total'] == 1
    assert [event['event_type'] for event in events['items']] == ['character_change']
    assert events['summary']['total'] == 3
    assert events['summary']['event_type_counts'] == {
        'WORLD_CREATED': 1,
        'character_change': 1,
        'world_version_increment': 1,
    }
    assert events['summary']['latest_world_version'] == 2


def test_world_events_summary_is_limited_to_owner(client):
    owner_token = register(client, 'timeline-owner@example.com')
    other_token = register(client, 'timeline-other@example.com')
    world_id = client.post('/worlds/from-template', headers=auth(owner_token)).json()['id']

    response = client.get(f'/worlds/{world_id}/events', headers=auth(other_token))

    assert response.status_code == 403
    assert response.json()['detail'] == 'FORBIDDEN'
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_world_template.py::test_world_events_include_summary_counts_and_latest_world_version tests/test_world_template.py::test_world_events_filter_items_but_keep_all_world_summary tests/test_world_template.py::test_world_events_summary_is_limited_to_owner -v
```

Expected: first two tests fail with missing `summary`; owner test should pass or remain green.

- [ ] **Step 3: Implement backend summary schema and service**

In `backend/app/event/schemas.py`, replace the list response section with:

```python
class EventLogSummaryResponse(BaseModel):
    total: int
    event_type_counts: dict[str, int]
    latest_world_version: int


class EventLogListResponse(BaseModel):
    items: list[EventLogResponse]
    total: int
    limit: int
    offset: int
    summary: EventLogSummaryResponse
```

In `backend/app/world/service.py`, update `list_world_events()`:

```python
def list_world_events(db: Session, user: User, world_id: int, event_type: str | None = None, limit: int = 20, offset: int = 0) -> dict:
    world = require_owned_world(db, user, world_id)
    query = select(EventLog).where(EventLog.world_id == world.id)
    count_query = select(func.count()).select_from(EventLog).where(EventLog.world_id == world.id)
    if event_type is not None:
        query = query.where(EventLog.event_type == event_type)
        count_query = count_query.where(EventLog.event_type == event_type)
    total = db.scalar(count_query) or 0
    items = list(db.scalars(query.order_by(desc(EventLog.id)).limit(limit).offset(offset)))
    type_rows = db.execute(
        select(EventLog.event_type, func.count()).where(EventLog.world_id == world.id).group_by(EventLog.event_type)
    ).all()
    latest_world_version = db.scalar(
        select(func.max(EventLog.world_version_after)).where(EventLog.world_id == world.id)
    ) or world.world_version
    return {
        'items': items,
        'total': total,
        'limit': limit,
        'offset': offset,
        'summary': {
            'total': sum(count for _, count in type_rows),
            'event_type_counts': {event_type: count for event_type, count in type_rows},
            'latest_world_version': latest_world_version,
        },
    }
```

- [ ] **Step 4: Run backend tests to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_world_template.py -v
```

Expected: PASS.

## Task 2: Frontend API typing and Timeline panel

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/api/client.test.ts`
- Create: `frontend/src/world/WorldTimelinePanel.tsx`
- Create: `frontend/src/world/WorldTimelinePanel.test.tsx`

- [ ] **Step 1: Write failing API helper test**

In `frontend/src/api/client.test.ts`, import `getWorldEvents` and add this test in a new `describe('world event API helpers', ...)` block:

```ts
it('calls event list endpoint with filters and pagination', async () => {
  const fetchMock = vi.fn().mockResolvedValueOnce(jsonResponse({
    items: [],
    total: 0,
    limit: 10,
    offset: 20,
    summary: { total: 0, event_type_counts: {}, latest_world_version: 1 },
  }));
  vi.stubGlobal('fetch', fetchMock);

  const response = await getWorldEvents(7, { event_type: 'character_change', limit: 10, offset: 20 });

  expect(fetchMock).toHaveBeenCalledWith(
    'http://localhost:8000/worlds/7/events?event_type=character_change&limit=10&offset=20',
    expect.any(Object),
  );
  expect(response.summary.latest_world_version).toBe(1);
});
```

- [ ] **Step 2: Implement frontend types/client typing**

In `frontend/src/api/types.ts`, add:

```ts
export type EventLogSummary = {
  total: number;
  event_type_counts: Record<string, number>;
  latest_world_version: number;
};

export type EventLogListResponse = {
  items: EventLog[];
  total: number;
  limit: number;
  offset: number;
  summary: EventLogSummary;
};
```

In `frontend/src/api/client.ts`, import `EventLogListResponse` and change `getWorldEvents()` return type to:

```ts
return apiRequest<EventLogListResponse>(`/worlds/${worldId}/events${query ? `?${query}` : ''}`);
```

- [ ] **Step 3: Write failing `WorldTimelinePanel` tests**

Create `frontend/src/world/WorldTimelinePanel.test.tsx`:

```tsx
import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { EventLogListResponse } from '../api/types';
import { WorldTimelinePanel } from './WorldTimelinePanel';

afterEach(() => cleanup());

const timeline: EventLogListResponse = {
  items: [
    {
      id: 2,
      world_id: 7,
      chapter_id: null,
      event_type: 'character_change',
      source_type: 'manual_edit',
      commit_id: 'commit-character',
      payload: { action: 'updated', object_type: 'character', object_id: 1, edit_reason: '推进角色线索' },
      world_version_before: 1,
      world_version_after: 2,
      created_at: '2026-05-31T10:00:00Z',
    },
    {
      id: 1,
      world_id: 7,
      chapter_id: null,
      event_type: 'WORLD_CREATED',
      source_type: 'world_creation',
      commit_id: 'commit-created',
      payload: { title: '群星边境', genre_template: 'sci_fi', starter_counts: { characters: 2, relations: 1, foreshadows: 1 } },
      world_version_before: 0,
      world_version_after: 1,
      created_at: '2026-05-31T09:00:00Z',
    },
  ],
  total: 2,
  limit: 20,
  offset: 0,
  summary: {
    total: 3,
    event_type_counts: { WORLD_CREATED: 1, character_change: 1, world_version_increment: 1 },
    latest_world_version: 2,
  },
};

describe('WorldTimelinePanel', () => {
  it('renders timeline summary and user-readable event descriptions', async () => {
    render(<WorldTimelinePanel worldId={7} onLoadEvents={vi.fn().mockResolvedValue(timeline)} />);

    expect(await screen.findByText('Timeline Explorer')).toBeInTheDocument();
    expect(screen.getByText('总事件：3')).toBeInTheDocument();
    expect(screen.getByText('最新世界版本：v2')).toBeInTheDocument();
    expect(screen.getByText('WORLD_CREATED × 1')).toBeInTheDocument();
    expect(screen.getByText('character_change × 1')).toBeInTheDocument();
    expect(screen.getByText('世界「群星边境」创建，题材 sci_fi，初始角色 2、关系 1、伏笔 1。')).toBeInTheDocument();
    expect(screen.getByText('character 已 updated：#1；原因：推进角色线索')).toBeInTheDocument();
  });

  it('reloads events when an event-type filter is selected', async () => {
    const user = userEvent.setup();
    const onLoadEvents = vi.fn().mockResolvedValue(timeline);
    render(<WorldTimelinePanel worldId={7} onLoadEvents={onLoadEvents} />);

    await screen.findByText('Timeline Explorer');
    await user.click(screen.getByRole('button', { name: 'character_change × 1' }));

    await waitFor(() => expect(onLoadEvents).toHaveBeenLastCalledWith(7, { limit: 20, event_type: 'character_change' }));
  });

  it('shows a localized error if timeline loading fails', async () => {
    render(<WorldTimelinePanel worldId={7} onLoadEvents={vi.fn().mockRejectedValue(new Error('timeline down'))} />);

    expect(await screen.findByRole('alert')).toHaveTextContent('timeline down');
  });
});
```

- [ ] **Step 4: Run panel test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTimelinePanel.test.tsx
```

Expected: FAIL because `WorldTimelinePanel` does not exist.

- [ ] **Step 5: Implement `WorldTimelinePanel`**

Create `frontend/src/world/WorldTimelinePanel.tsx` implementing the props and behavior from the tests. Use `useEffect`, local state, and no new dependencies.

- [ ] **Step 6: Run API and panel tests to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts src/world/WorldTimelinePanel.test.tsx
```

Expected: PASS.

## Task 3: Mount Timeline panel in WorldPage

**Files:**
- Modify: `frontend/src/world/WorldPage.tsx`
- Modify: `frontend/src/world/WorldPage.test.tsx`

- [ ] **Step 1: Write failing WorldPage integration test**

In `frontend/src/world/WorldPage.test.tsx`:

- import `getWorldEvents` from `../api/client`;
- add it to the `vi.mock('../api/client', ...)` object;
- reset and mock it in `beforeEach`:

```ts
vi.mocked(getWorldEvents).mockReset();
vi.mocked(getWorldEvents).mockResolvedValue({
  items: [],
  total: 0,
  limit: 20,
  offset: 0,
  summary: { total: 1, event_type_counts: { WORLD_CREATED: 1 }, latest_world_version: 2 },
});
```

Add an assertion to `loads and displays Chapter History and Next Chapter Prep panels`:

```ts
expect(await screen.findByText('Timeline Explorer')).toBeInTheDocument();
expect(getWorldEvents).toHaveBeenCalledWith(7, { limit: 20 });
```

Expected RED: Timeline panel is not mounted.

- [ ] **Step 2: Implement WorldPage mount**

In `frontend/src/world/WorldPage.tsx`:

```ts
import { WorldTimelinePanel } from './WorldTimelinePanel';
```

Add below `NextChapterPrepPanel` in the overview Narrative Control Center section:

```tsx
<WorldTimelinePanel worldId={world.id} onLoadEvents={getWorldEvents} />
```

Also import `getWorldEvents` from `../api/client`.

- [ ] **Step 3: Run WorldPage test to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: PASS.

## Task 4: Final verification, commit, and merge

**Files:** all modified files plus docs.

- [ ] **Step 1: Confirm branch and status**

Run:

```bash
git status --short --branch
```

Expected: on `feat/mvp15-timeline-event-explorer`.

- [ ] **Step 2: Run backend targeted tests**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_world_template.py tests/test_narrative_approval.py tests/test_foreshadow_crud.py tests/test_snapshot_export.py -v
```

Expected: PASS.

- [ ] **Step 3: Run frontend targeted tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts src/world/WorldTimelinePanel.test.tsx src/world/WorldPage.test.tsx src/world/ChapterHistoryPanel.test.tsx src/world/WorldArchivePanel.test.tsx
```

Expected: PASS.

- [ ] **Step 4: Run frontend build**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: PASS.

- [ ] **Step 5: Inline self-review**

Check:

- no Workflow tool used;
- no subagents or code-review subagent used;
- event explorer is read-only;
- existing `/events` endpoint remains backward compatible except for additive `summary`;
- owner boundary is covered;
- UI failure does not block other World overview panels;
- tests cover summary/filter/error states.

- [ ] **Step 6: Commit**

Run:

```bash
git add docs/superpowers/specs/2026-05-31-mvp15-timeline-event-explorer-design.md docs/superpowers/plans/2026-05-31-mvp15-timeline-event-explorer.md backend/app/event/schemas.py backend/app/world/service.py backend/tests/test_world_template.py frontend/src/api/types.ts frontend/src/api/client.ts frontend/src/api/client.test.ts frontend/src/world/WorldTimelinePanel.tsx frontend/src/world/WorldTimelinePanel.test.tsx frontend/src/world/WorldPage.tsx frontend/src/world/WorldPage.test.tsx
git commit -m "feat: add timeline event explorer" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 7: Merge back to main without pushing**

Run:

```bash
git switch main
git merge feat/mvp15-timeline-event-explorer
```

- [ ] **Step 8: Post-merge verification**

Run backend targeted tests, frontend targeted tests, and frontend build again on `main`.

Expected: all pass.

- [ ] **Step 9: Final status**

Run:

```bash
git status --short --branch
```

Expected: `main...origin/main [领先 11]` and clean worktree. Do not push.

## Plan self-review

- Spec coverage: backend summary, event filtering, owner boundary, frontend timeline panel, WorldPage mount, tests, build, commit, merge, and no-push are covered.
- Placeholder scan: no TBD/TODO placeholders are present.
- Type consistency: backend `summary` fields align with frontend `EventLogSummary`; `getWorldEvents()` accepts the existing params shape.
- Scope: the MVP remains read-only and does not introduce rollback, branch-world creation, global search, tags, or event editing.
