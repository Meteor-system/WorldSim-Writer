# MVP21 Arc Mode / Closure Plan 0.5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use sequential inline execution because this repository request explicitly forbids subagents and dynamic workflows. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only Arc Mode / Closure Plan advisory surface that tells authors whether the next chapter should expand, organize, pressure, converge, payoff, or endgame, and which open threads should be closed, advanced, merged, deferred, or left open.

**Architecture:** Extend `app.narrative_control_center` with deterministic read-only schemas, service logic, and a `GET /worlds/{world_id}/arc-plan` route composed from existing World Pulse, Open Threads, Narrative Health, Next Chapter Prep, approved chapter count, and story arc data. Add typed frontend API support and an `ArcPlanPanel` mounted between World Pulse and the detailed Narrative Control Center diagnostics. No migrations, LLM calls, EventLog writes, or formal world-state mutation are introduced.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, React, TypeScript, Vite, Vitest, Testing Library.

---

## File map

- Create `backend/tests/test_arc_plan.py` — backend RED/GREEN tests for arc plan endpoint, mode rules, closure items, and ownership.
- Modify `backend/app/narrative_control_center/schemas.py` — add `ArcPlanClosureItem`, `ArcPlanGuidance`, and `ArcPlanResponse`.
- Modify `backend/app/narrative_control_center/service.py` — add deterministic arc-plan helpers and `get_arc_plan()`.
- Modify `backend/app/narrative_control_center/router.py` — expose `GET /worlds/{world_id}/arc-plan`.
- Modify `frontend/src/api/types.ts` — add Arc Plan response types.
- Modify `frontend/src/api/client.ts` — import `ArcPlanResponse` and add `getArcPlan(worldId)`.
- Modify `frontend/src/api/client.test.ts` — add API helper RED/GREEN coverage.
- Create `frontend/src/world/ArcPlanPanel.tsx` — render Arc Mode / Closure Plan UI.
- Create `frontend/src/world/ArcPlanPanel.test.tsx` — RED/GREEN component coverage.
- Modify `frontend/src/world/WorldPage.tsx` — load arc plan and mount panel.
- Modify `frontend/src/world/WorldPage.test.tsx` — mock `getArcPlan()` and assert integration.

---

### Task 1: Backend RED test for Arc Plan endpoint

**Files:**
- Create: `backend/tests/test_arc_plan.py`

- [ ] **Step 1: Write failing backend tests**

Create `backend/tests/test_arc_plan.py` with tests that call `/worlds/{world_id}/arc-plan` before implementation exists. Cover baseline expand mode, high-risk organize mode, convergence closure items, late-arc payoff/endgame mode, and owner scoping.

- [ ] **Step 2: Run backend test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_arc_plan.py -q
```

Expected: fail with 404 for the missing `/worlds/{world_id}/arc-plan` endpoint.

---

### Task 2: Backend GREEN implementation

**Files:**
- Modify: `backend/app/narrative_control_center/schemas.py`
- Modify: `backend/app/narrative_control_center/service.py`
- Modify: `backend/app/narrative_control_center/router.py`

- [ ] **Step 1: Add schemas**

Add Pydantic models matching the design response shape.

- [ ] **Step 2: Add service helpers and `get_arc_plan()`**

Compose existing services and implement deterministic mode, budget, closure item, and guidance rules.

- [ ] **Step 3: Add route**

Add `GET /worlds/{world_id}/arc-plan` to `narrative_control_center/router.py`.

- [ ] **Step 4: Run backend test to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_arc_plan.py -q
```

Expected: all tests pass.

---

### Task 3: Frontend API RED/GREEN

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/api/client.test.ts`

- [ ] **Step 1: Add failing API helper test**

Add a test that imports `getArcPlan()`, stubs fetch, expects `/worlds/7/arc-plan`, and reads `arc_mode`.

- [ ] **Step 2: Run API test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts
```

Expected: fail because `getArcPlan` is not implemented.

- [ ] **Step 3: Add types and helper**

Add `ArcPlanClosureItem`, `ArcPlanGuidance`, `ArcPlanResponse`, import `ArcPlanResponse`, and implement `getArcPlan(worldId)`.

- [ ] **Step 4: Run API test to verify GREEN**

Run the same command. Expected: pass.

---

### Task 4: Frontend panel RED/GREEN

**Files:**
- Create: `frontend/src/world/ArcPlanPanel.test.tsx`
- Create: `frontend/src/world/ArcPlanPanel.tsx`

- [ ] **Step 1: Add failing panel tests**

Test rendering of heading, arc mode, expansion budget, recommended goal, guidance, closure items, empty state, loading state, and error state.

- [ ] **Step 2: Run panel test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/ArcPlanPanel.test.tsx
```

Expected: fail because `ArcPlanPanel` does not exist.

- [ ] **Step 3: Create `ArcPlanPanel.tsx`**

Implement the minimal UI to satisfy tests and match nearby World Pulse/Open Threads style.

- [ ] **Step 4: Run panel test to verify GREEN**

Run the same command. Expected: pass.

---

### Task 5: WorldPage integration RED/GREEN

**Files:**
- Modify: `frontend/src/world/WorldPage.tsx`
- Modify: `frontend/src/world/WorldPage.test.tsx`

- [ ] **Step 1: Add failing WorldPage integration test**

Mock `getArcPlan`, assert it is called with the loaded world id, and assert `Arc Mode / Closure Plan` appears in the Narrative Control Center.

- [ ] **Step 2: Run WorldPage test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: fail because WorldPage does not call `getArcPlan` or mount `ArcPlanPanel`.

- [ ] **Step 3: Wire WorldPage state/loading/error/load/mount**

Import `getArcPlan`, `ArcPlanResponse`, and `ArcPlanPanel`. Add state and load handling inside `loadNarrativeControlCenter()`. Mount panel after `WorldPulsePanel`.

- [ ] **Step 4: Run WorldPage test to verify GREEN**

Run the same command. Expected: pass.

---

### Task 6: Final verification, commit, and merge

**Files:**
- All changed MVP21 files.

- [ ] **Step 1: Run targeted backend tests**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_arc_plan.py tests/test_world_pulse.py tests/test_open_threads.py tests/test_narrative_health.py tests/test_narrative_control_center.py -q
```

Expected: pass.

- [ ] **Step 2: Run targeted frontend tests and build**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts src/world/ArcPlanPanel.test.tsx src/world/WorldPage.test.tsx src/world/WorldPulsePanel.test.tsx src/world/OpenThreadsPanel.test.tsx && npm run build
```

Expected: pass.

- [ ] **Step 3: Commit feature work**

Commit all MVP21 implementation and plan changes on `feat/mvp21-arc-closure-plan`.

- [ ] **Step 4: Fast-forward merge to main**

Checkout `main` and fast-forward merge `feat/mvp21-arc-closure-plan`.

- [ ] **Step 5: Post-merge verification**

Run the same targeted backend tests and frontend tests/build from `main`.

- [ ] **Step 6: Do not push**

Report final status with commit hashes and verification evidence. Do not push.

---

## Self-review

- No placeholders remain.
- The plan implements all design goals without migrations or write paths.
- TDD RED/GREEN gates are explicit for backend, API, panel, and WorldPage integration.
- The plan respects the user constraints: inline execution, no dynamic workflows, no subagents, skip code-review subagent, commit and merge to `main`, no push.
