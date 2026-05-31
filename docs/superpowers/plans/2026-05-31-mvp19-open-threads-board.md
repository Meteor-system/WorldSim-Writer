# MVP19 Open Threads Board / Story Convergence 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use sequential inline execution because this repository request explicitly forbids subagents and dynamic workflows. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only Open Threads Board that surfaces narrative obligations, convergence pressure, and next actions from existing world signals.

**Architecture:** Extend the existing `narrative_control_center` backend domain with a deterministic read-only endpoint that aggregates foreshadow ledger entries, character goals, latest progression hints, narrative health risks, and recent event counts. Add typed frontend API support plus an `OpenThreadsPanel` mounted in the existing World page Narrative Control Center. No migrations, LLM calls, or formal world-state mutation are introduced.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, React, TypeScript, Vitest, Testing Library, Vite.

---

## File structure

- Create: `backend/tests/test_open_threads.py`
  - Backend TDD coverage for open foreshadow/character goal threads, high-pressure classification, health-risk threads, and owner scope.
- Modify: `backend/app/narrative_control_center/schemas.py`
  - Add `OpenThreadItem`, `OpenThreadsSummary`, and `OpenThreadsResponse` schemas.
- Modify: `backend/app/narrative_control_center/service.py`
  - Add pure helper functions plus `get_open_threads()`.
- Modify: `backend/app/narrative_control_center/router.py`
  - Add `GET /worlds/{world_id}/open-threads`.
- Modify: `frontend/src/api/types.ts`
  - Add open-thread response types.
- Modify: `frontend/src/api/client.ts`
  - Add `getOpenThreads(worldId)` helper.
- Modify: `frontend/src/api/client.test.ts`
  - Add URL-construction test for `getOpenThreads()`.
- Create: `frontend/src/world/OpenThreadsPanel.tsx`
  - Render convergence summary and prioritized thread cards.
- Create: `frontend/src/world/OpenThreadsPanel.test.tsx`
  - Component behavior tests for data, empty, loading, and error states.
- Modify: `frontend/src/world/WorldPage.tsx`
  - Load and mount `OpenThreadsPanel` near Narrative Health and Next Chapter Prep.
- Modify: `frontend/src/world/WorldPage.test.tsx`
  - Mock `getOpenThreads()` and assert the panel loads.

---

## Task 1: Backend Open Threads endpoint

**Files:**
- Create: `backend/tests/test_open_threads.py`
- Modify: `backend/app/narrative_control_center/schemas.py`
- Modify: `backend/app/narrative_control_center/service.py`
- Modify: `backend/app/narrative_control_center/router.py`

- [ ] **Step 1: Write failing backend tests**

Create `backend/tests/test_open_threads.py` with tests for:

```python
def test_open_threads_returns_character_goal_and_foreshadow_threads(client):
    token = register(client)
    world = client.post('/worlds', headers=auth(token), json=custom_world_payload()).json()

    response = client.get(f"/worlds/{world['id']}/open-threads", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['world_id'] == world['id']
    assert payload['summary']['total_open_threads'] >= 2
    assert payload['summary']['should_advance_count'] >= 1
    assert payload['summary']['narrative_entropy_level'] in {'low', 'medium', 'high'}
    thread_types = {thread['thread_type'] for thread in payload['threads']}
    assert {'foreshadow', 'character_goal'}.issubset(thread_types)
    assert any(thread['title'] == '黑匣子脉冲' for thread in payload['threads'])
    assert any(thread['can_seed_next_chapter_goal'] for thread in payload['threads'])
```

```python
def test_open_threads_surfaces_high_pressure_foreshadow_as_should_advance(client):
    token = register(client, 'threads-pressure@example.com')
    world = client.post('/worlds', headers=auth(token), json=custom_world_payload()).json()

    response = client.get(f"/worlds/{world['id']}/open-threads", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    foreshadow_thread = next(thread for thread in payload['threads'] if thread['thread_type'] == 'foreshadow')
    assert foreshadow_thread['priority'] in {'should_advance', 'must_close'}
    assert foreshadow_thread['pressure_level'] in {'high', 'critical'}
    assert foreshadow_thread['related_foreshadow_ids']
```

```python
def test_open_threads_surfaces_health_risks_as_must_close(client, db_session):
    token = register(client, 'threads-health-risk@example.com')
    world = client.post('/worlds', headers=auth(token), json=custom_world_payload()).json()
    overview = client.get(f"/worlds/{world['id']}/overview", headers=auth(token)).json()
    character_id = overview['characters'][0]['id']
    create_approved_chapter_with_high_risk_report(db_session, world['id'], character_id)

    response = client.get(f"/worlds/{world['id']}/open-threads", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['summary']['must_close_count'] >= 1
    assert any(thread['thread_type'] == 'health_risk' and thread['priority'] == 'must_close' for thread in payload['threads'])
```

```python
def test_open_threads_is_limited_to_owner(client):
    owner_token = register(client, 'threads-owner@example.com')
    other_token = register(client, 'threads-other@example.com')
    world = client.post('/worlds', headers=auth(owner_token), json=custom_world_payload()).json()

    response = client.get(f"/worlds/{world['id']}/open-threads", headers=auth(other_token))

    assert response.status_code == 403
    assert response.json()['detail'] == 'FORBIDDEN'
```

- [ ] **Step 2: Run backend RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_open_threads.py -q
```

Expected: fail with `404 Not Found` because the endpoint is not implemented.

- [ ] **Step 3: Add backend schemas**

Append to `backend/app/narrative_control_center/schemas.py`:

```python
class OpenThreadItem(BaseModel):
    thread_id: str
    thread_type: str
    priority: str
    pressure_level: str
    title: str
    summary: str
    related_object_type: str | None = None
    related_object_id: int | None = None
    related_character_ids: list[int]
    related_foreshadow_ids: list[int]
    suggested_action: str
    can_seed_next_chapter_goal: bool


class OpenThreadsSummary(BaseModel):
    total_open_threads: int
    must_close_count: int
    should_advance_count: int
    can_delay_count: int
    can_leave_open_count: int
    convergence_ratio: float
    narrative_entropy_level: str
    recent_event_count: int


class OpenThreadsResponse(BaseModel):
    world_id: int
    world_version: int
    summary: OpenThreadsSummary
    threads: list[OpenThreadItem]
    suggested_next_actions: list[dict]
```

- [ ] **Step 4: Add backend service**

In `backend/app/narrative_control_center/service.py`, add helper functions and `get_open_threads()` after `get_narrative_health()`.

Key behavior:

- Call `require_owned_world(db, user, world_id)` first.
- Use `build_foreshadow_ledger(db, world)`.
- Query characters by `world_id`.
- Query latest approved chapter and progression hints.
- Reuse `get_narrative_health(db, user, world_id)` for health risk signals.
- Build stable thread ids like `foreshadow:{id}`, `character_goal:{character_id}:{index}`, `progression_hint:{index}`, `health_risk:{source}:{index}`.
- Sort priority by `must_close`, `should_advance`, `can_delay`, `can_leave_open`, then pressure level, then thread id.

- [ ] **Step 5: Add backend route**

Modify `backend/app/narrative_control_center/router.py`:

- import `OpenThreadsResponse`;
- import `get_open_threads`;
- add:

```python
@router.get('/worlds/{world_id}/open-threads', response_model=OpenThreadsResponse)
def open_threads(
    world_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> OpenThreadsResponse:
    return OpenThreadsResponse.model_validate(get_open_threads(db, current_user, world_id))
```

- [ ] **Step 6: Run backend GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_open_threads.py -q
```

Expected: pass.

---

## Task 2: Frontend API helper and types

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/api/client.test.ts`

- [ ] **Step 1: Write failing API helper test**

In `frontend/src/api/client.test.ts`, import `getOpenThreads` and add:

```ts
it('calls open threads endpoint', async () => {
  const fetchMock = vi.fn().mockResolvedValueOnce(jsonResponse({
    world_id: 7,
    world_version: 3,
    summary: {
      total_open_threads: 1,
      must_close_count: 0,
      should_advance_count: 1,
      can_delay_count: 0,
      can_leave_open_count: 0,
      convergence_ratio: 0.25,
      narrative_entropy_level: 'medium',
      recent_event_count: 4,
    },
    threads: [],
    suggested_next_actions: [],
  }));
  vi.stubGlobal('fetch', fetchMock);

  const response = await getOpenThreads(7);

  expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/worlds/7/open-threads', expect.any(Object));
  expect(response.summary.narrative_entropy_level).toBe('medium');
});
```

- [ ] **Step 2: Run frontend API RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts
```

Expected: fail because `getOpenThreads` is missing.

- [ ] **Step 3: Add types and helper**

Add open-thread types to `frontend/src/api/types.ts` and `getOpenThreads()` to `frontend/src/api/client.ts`.

- [ ] **Step 4: Run frontend API GREEN**

Run the same command. Expected: pass.

---

## Task 3: Open Threads panel

**Files:**
- Create: `frontend/src/world/OpenThreadsPanel.tsx`
- Create: `frontend/src/world/OpenThreadsPanel.test.tsx`

- [ ] **Step 1: Write failing panel tests**

Create tests that verify:

- summary renders `Open Threads Board`, counts, convergence ratio, entropy level;
- thread cards render priority, pressure, title, summary, suggested action, and next-chapter seed marker;
- empty state renders when no threads exist;
- loading and error states render.

- [ ] **Step 2: Run panel RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/OpenThreadsPanel.test.tsx
```

Expected: fail because `OpenThreadsPanel` is missing.

- [ ] **Step 3: Implement panel**

Create `OpenThreadsPanel.tsx` with props:

```ts
type Props = {
  openThreads: OpenThreadsResponse | null;
  loading?: boolean;
  error?: string;
};
```

Render loading, error, empty, summary, action, and thread states using existing card classes.

- [ ] **Step 4: Run panel GREEN**

Run the same command. Expected: pass.

---

## Task 4: WorldPage integration

**Files:**
- Modify: `frontend/src/world/WorldPage.tsx`
- Modify: `frontend/src/world/WorldPage.test.tsx`

- [ ] **Step 1: Write failing integration test**

Update `WorldPage.test.tsx`:

- import and mock `getOpenThreads`;
- reset and mock it in `beforeEach()`;
- assert `getOpenThreads(7)` is called;
- assert `Open Threads Board` appears.

- [ ] **Step 2: Run WorldPage RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: fail because WorldPage does not load or mount open threads yet.

- [ ] **Step 3: Wire WorldPage**

In `WorldPage.tsx`:

- import `getOpenThreads` and `OpenThreadsResponse`;
- add open-thread state/loading/error;
- load it inside `loadNarrativeControlCenter()` with degraded error path `开放线索看板暂不可用`;
- mount `<OpenThreadsPanel />` near `NarrativeHealthPanel`.

- [ ] **Step 4: Run WorldPage GREEN**

Run the same command. Expected: pass.

---

## Task 5: Final verification, commit, merge

- [ ] **Step 1: Run backend targeted tests**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_open_threads.py tests/test_narrative_health.py tests/test_narrative_control_center.py tests/test_foreshadow_crud.py -q
```

- [ ] **Step 2: Run frontend targeted tests**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts src/world/OpenThreadsPanel.test.tsx src/world/WorldPage.test.tsx src/world/NarrativeHealthPanel.test.tsx
```

- [ ] **Step 3: Run frontend build**

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

- [ ] **Step 4: Inline self-review**

Check:

- endpoint is read-only and owner-scoped;
- no LLM calls or DB writes were added;
- no dynamic workflows/subagents/code-review subagent were used;
- thread priorities are deterministic;
- frontend degraded errors do not block other World page panels.

- [ ] **Step 5: Commit implementation**

```bash
git add backend frontend docs/superpowers/plans/2026-05-31-mvp19-open-threads-board.md
git commit -m "feat: add open threads board"
```

- [ ] **Step 6: Merge to main without push**

```bash
git switch main
git merge feat/mvp19-open-threads-board
```

- [ ] **Step 7: Post-merge verification**

Repeat backend targeted tests, frontend targeted tests, and frontend build on `main`.

## Plan self-review

- Spec coverage: backend endpoint, aggregation, priority rules, summary metrics, frontend helper, panel, WorldPage integration, tests, commit, merge, and no-push are covered.
- Placeholder scan: no TBD/TODO placeholders remain.
- Type consistency: `OpenThreadsResponse`, `OpenThreadItem`, `getOpenThreads`, and `OpenThreadsPanel` names align across backend and frontend.
- Scope: this remains a read-only Story Convergence board and does not implement persisted Closure Plan, Arc Mode writes, audience steering, migrations, or model calls.
