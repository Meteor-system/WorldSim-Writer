# MVP20 World Pulse / Operational Overview 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use sequential inline execution because this repository request explicitly forbids subagents and dynamic workflows. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only World Pulse that summarizes the current operational state of a story world and recommends whether to draft, repair, converge, or archive.

**Architecture:** Extend the existing `narrative_control_center` backend with a deterministic read-only endpoint that composes existing Narrative Health, Open Threads, Next Chapter Prep, EventLog, approved chapter count, and WorldSnapshot signals. Add typed frontend API support and a `WorldPulsePanel` mounted above the detailed Narrative Control Center panels. No migrations, LLM calls, EventLog writes, or formal world-state mutation are introduced.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, React, TypeScript, Vitest, Testing Library, Vite.

---

## File structure

- Create: `backend/tests/test_world_pulse.py`
  - Backend TDD coverage for baseline pulse, repair mode, convergence focus, snapshot freshness, and owner scope.
- Modify: `backend/app/narrative_control_center/schemas.py`
  - Add `WorldPulseIndicator`, `WorldPulseFocus`, `WorldPulseAction`, and `WorldPulseResponse` schemas.
- Modify: `backend/app/narrative_control_center/service.py`
  - Add pure helper functions plus `get_world_pulse()`.
- Modify: `backend/app/narrative_control_center/router.py`
  - Add `GET /worlds/{world_id}/pulse`.
- Modify: `frontend/src/api/types.ts`
  - Add world pulse response types.
- Modify: `frontend/src/api/client.ts`
  - Add `getWorldPulse(worldId)` helper.
- Modify: `frontend/src/api/client.test.ts`
  - Add URL-construction test for `getWorldPulse()`.
- Create: `frontend/src/world/WorldPulsePanel.tsx`
  - Render pulse status, mode, headline, indicators, focus cards, and next actions.
- Create: `frontend/src/world/WorldPulsePanel.test.tsx`
  - Component behavior tests for data, empty, loading, and error states.
- Modify: `frontend/src/world/WorldPage.tsx`
  - Load and mount `WorldPulsePanel` above Narrative Health and Open Threads.
- Modify: `frontend/src/world/WorldPage.test.tsx`
  - Mock `getWorldPulse()` and assert the panel loads.

---

## Task 1: Backend World Pulse endpoint

**Files:**
- Create: `backend/tests/test_world_pulse.py`
- Modify: `backend/app/narrative_control_center/schemas.py`
- Modify: `backend/app/narrative_control_center/service.py`
- Modify: `backend/app/narrative_control_center/router.py`

- [ ] **Step 1: Write failing backend tests**

Create `backend/tests/test_world_pulse.py` with tests for:

```python
def test_world_pulse_returns_watchful_baseline_for_new_world(client):
    token = register(client)
    world = client.post('/worlds', headers=auth(token), json=custom_world_payload()).json()

    response = client.get(f"/worlds/{world['id']}/pulse", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['world_id'] == world['id']
    assert payload['pulse_status'] == 'watch'
    assert payload['primary_mode'] == 'draft'
    assert 'World Pulse' in payload['headline'] or payload['headline']
    indicator_keys = {indicator['key'] for indicator in payload['indicators']}
    assert {'narrative_health', 'open_threads', 'next_chapter', 'recent_events', 'archive_freshness'}.issubset(indicator_keys)
    assert any(action['action_key'] == 'write_first_chapter' for action in payload['next_actions'])
```

```python
def test_world_pulse_uses_repair_mode_for_high_risk_reports(client, db_session):
    token = register(client, 'pulse-risk@example.com')
    world = client.post('/worlds', headers=auth(token), json=custom_world_payload()).json()
    overview = client.get(f"/worlds/{world['id']}/overview", headers=auth(token)).json()
    create_approved_chapter_with_high_risk_report(db_session, world['id'], overview['characters'][0]['id'])

    response = client.get(f"/worlds/{world['id']}/pulse", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['pulse_status'] == 'urgent'
    assert payload['primary_mode'] == 'repair'
    assert any(focus['focus_key'] == 'repair_health' and focus['priority'] == 'urgent' for focus in payload['focus'])
    assert any(action['action_key'] == 'repair_narrative_health' for action in payload['next_actions'])
```

```python
def test_world_pulse_surfaces_convergence_focus_for_open_threads(client):
    token = register(client, 'pulse-converge@example.com')
    world = client.post('/worlds', headers=auth(token), json=high_pressure_world_payload()).json()

    response = client.get(f"/worlds/{world['id']}/pulse", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['pulse_status'] in {'watch', 'urgent'}
    assert any(focus['focus_key'] == 'converge_threads' for focus in payload['focus'])
    assert any(action['action_key'] == 'open_threads_board' for action in payload['next_actions'])
```

```python
def test_world_pulse_reports_snapshot_freshness(client, db_session):
    token = register(client, 'pulse-snapshot@example.com')
    world = client.post('/worlds', headers=auth(token), json=custom_world_payload()).json()

    response = client.get(f"/worlds/{world['id']}/pulse", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    archive_indicator = next(indicator for indicator in payload['indicators'] if indicator['key'] == 'archive_freshness')
    assert archive_indicator['status'] == 'watch'
    assert payload['source_summary']['snapshot_count'] == 0
```

```python
def test_world_pulse_is_limited_to_owner(client):
    owner_token = register(client, 'pulse-owner@example.com')
    other_token = register(client, 'pulse-other@example.com')
    world = client.post('/worlds', headers=auth(owner_token), json=custom_world_payload()).json()

    response = client.get(f"/worlds/{world['id']}/pulse", headers=auth(other_token))

    assert response.status_code == 403
    assert response.json()['detail'] == 'FORBIDDEN'
```

- [ ] **Step 2: Run backend RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_world_pulse.py -q
```

Expected: fail with `404 Not Found` because the endpoint is not implemented.

- [ ] **Step 3: Add backend schemas**

Append these schemas to `backend/app/narrative_control_center/schemas.py`:

```python
class WorldPulseIndicator(BaseModel):
    key: str
    label: str
    value: str
    status: str
    detail: str


class WorldPulseFocus(BaseModel):
    focus_key: str
    priority: str
    title: str
    detail: str
    suggested_action: str
    related_thread_id: str | None = None


class WorldPulseAction(BaseModel):
    action_key: str
    label: str
    detail: str
    target: str | None = None


class WorldPulseResponse(BaseModel):
    world_id: int
    world_version: int
    pulse_status: str
    primary_mode: str
    headline: str
    indicators: list[WorldPulseIndicator]
    focus: list[WorldPulseFocus]
    next_actions: list[WorldPulseAction]
    source_summary: dict
```

- [ ] **Step 4: Add backend service**

In `backend/app/narrative_control_center/service.py`, import `WorldSnapshot` and add `get_world_pulse()` after `get_open_threads()`.

Key behavior:

- Call `require_owned_world(db, user, world_id)` first.
- Reuse `get_narrative_health()`, `get_open_threads()`, and `get_next_chapter_prep()`.
- Query approved chapter count with `count_approved_chapters()`.
- Query recent event count from `EventLog`.
- Query latest snapshot version and snapshot count from `WorldSnapshot`.
- Determine status and mode deterministically:
  - `repair` first when health status is `at_risk` or high risks exist;
  - `converge` when must-close threads exist or entropy is high;
  - otherwise `draft` when a next chapter goal exists;
  - otherwise `archive` when stable but archive freshness is behind.
- Return indicators and actions as plain dictionaries.

- [ ] **Step 5: Add backend route**

Modify `backend/app/narrative_control_center/router.py`:

- import `WorldPulseResponse`;
- import `get_world_pulse`;
- add:

```python
@router.get('/worlds/{world_id}/pulse', response_model=WorldPulseResponse)
def world_pulse(
    world_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> WorldPulseResponse:
    return WorldPulseResponse.model_validate(get_world_pulse(db, current_user, world_id))
```

- [ ] **Step 6: Run backend GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_world_pulse.py -q
```

Expected: pass.

---

## Task 2: Frontend API helper and types

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/api/client.test.ts`

- [ ] **Step 1: Write failing API helper test**

In `frontend/src/api/client.test.ts`, import `getWorldPulse` and add:

```ts
it('calls world pulse endpoint', async () => {
  const fetchMock = vi.fn().mockResolvedValueOnce(jsonResponse({
    world_id: 7,
    world_version: 3,
    pulse_status: 'watch',
    primary_mode: 'converge',
    headline: 'World Pulse：建议先处理开放线索。',
    indicators: [],
    focus: [],
    next_actions: [],
    source_summary: { approved_chapter_count: 2 },
  }));
  vi.stubGlobal('fetch', fetchMock);

  const response = await getWorldPulse(7);

  expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/worlds/7/pulse', expect.any(Object));
  expect(response.primary_mode).toBe('converge');
});
```

- [ ] **Step 2: Run frontend API RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts
```

Expected: fail because `getWorldPulse` is missing.

- [ ] **Step 3: Add types and helper**

Add world pulse types to `frontend/src/api/types.ts` and `getWorldPulse()` to `frontend/src/api/client.ts`.

- [ ] **Step 4: Run frontend API GREEN**

Run the same command. Expected: pass.

---

## Task 3: World Pulse panel

**Files:**
- Create: `frontend/src/world/WorldPulsePanel.tsx`
- Create: `frontend/src/world/WorldPulsePanel.test.tsx`

- [ ] **Step 1: Write failing panel tests**

Create tests that verify:

- heading `World Pulse`, headline, status, mode, indicators, focus cards, and actions render;
- empty state renders when `pulse` is null;
- loading and error states render.

- [ ] **Step 2: Run panel RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPulsePanel.test.tsx
```

Expected: fail because `WorldPulsePanel` is missing.

- [ ] **Step 3: Implement panel**

Create `WorldPulsePanel.tsx` with props:

```ts
type Props = {
  pulse: WorldPulseResponse | null;
  loading?: boolean;
  error?: string;
};
```

Render loading, error, empty, summary, indicator, focus, and action states using existing card classes.

- [ ] **Step 4: Run panel GREEN**

Run the same command. Expected: pass.

---

## Task 4: WorldPage integration

**Files:**
- Modify: `frontend/src/world/WorldPage.tsx`
- Modify: `frontend/src/world/WorldPage.test.tsx`

- [ ] **Step 1: Write failing integration test**

Update `WorldPage.test.tsx`:

- import and mock `getWorldPulse`;
- reset and mock it in `beforeEach()`;
- assert `getWorldPulse(7)` is called;
- assert `World Pulse` appears.

- [ ] **Step 2: Run WorldPage RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: fail because WorldPage does not load or mount world pulse yet.

- [ ] **Step 3: Wire WorldPage**

In `WorldPage.tsx`:

- import `getWorldPulse`, `WorldPulseResponse`, and `WorldPulsePanel`;
- add pulse state/loading/error;
- load it inside `loadNarrativeControlCenter()` with degraded error path `世界心跳暂不可用`;
- mount `<WorldPulsePanel />` before `NarrativeHealthPanel`.

- [ ] **Step 4: Run WorldPage GREEN**

Run the same command. Expected: pass.

---

## Task 5: Final verification, commit, merge

- [ ] **Step 1: Run backend targeted tests**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_world_pulse.py tests/test_open_threads.py tests/test_narrative_health.py tests/test_narrative_control_center.py tests/test_snapshot_export.py -q
```

- [ ] **Step 2: Run frontend targeted tests**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts src/world/WorldPulsePanel.test.tsx src/world/WorldPage.test.tsx src/world/OpenThreadsPanel.test.tsx src/world/NarrativeHealthPanel.test.tsx
```

- [ ] **Step 3: Run frontend build**

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

- [ ] **Step 4: Inline self-review**

Check:

- endpoint is read-only and owner-scoped;
- no LLM calls, DB writes, migrations, EventLog writes, or `world_version` mutations were added;
- no dynamic workflows/subagents/code-review subagent were used;
- status/mode rules are deterministic;
- frontend degraded pulse errors do not block other World page panels.

- [ ] **Step 5: Commit implementation**

```bash
git add backend frontend docs/superpowers/plans/2026-05-31-mvp20-world-pulse.md
git commit -m "feat: add world pulse overview"
```

- [ ] **Step 6: Merge to main without push**

```bash
git switch main
git merge feat/mvp20-world-pulse
```

- [ ] **Step 7: Post-merge verification**

Repeat backend targeted tests, frontend targeted tests, and frontend build on `main`.

## Plan self-review

- Spec coverage: backend endpoint, source aggregation, status/mode rules, frontend helper, panel, WorldPage integration, tests, commit, merge, and no-push are covered.
- Placeholder scan: no TBD/TODO placeholders remain.
- Type consistency: `WorldPulseResponse`, `getWorldPulse`, and `WorldPulsePanel` names align across backend and frontend.
- Scope: this remains a read-only operational overview and does not implement persisted Arc Mode, Closure Plan, audience steering, migrations, or model calls.
