# MVP18 Snapshot Compare / Archive Diff 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use sequential inline execution because this project request explicitly forbids subagents and dynamic workflows. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add read-only snapshot comparison so users can inspect differences between two frozen world archive snapshots.

**Architecture:** Reuse existing `WorldSnapshot` payloads and snapshot/export router. Add a pure service-level diff helper, a FastAPI compare route, typed frontend API helper, and an archive-panel comparison UI. The comparison is read-only and does not create events, snapshots, world-version increments, or LLM calls.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, Vite React, TypeScript, Vitest, Testing Library.

---

## File structure

- Modify `backend/tests/test_snapshot_export.py`
  - Add backend RED tests for snapshot comparison, same-snapshot zero diff, cross-world rejection, and authentication.
- Modify `backend/app/snapshot_export/schemas.py`
  - Add compare response schemas.
- Modify `backend/app/snapshot_export/service.py`
  - Add pure diff helpers and `compare_world_snapshots()`.
- Modify `backend/app/snapshot_export/router.py`
  - Add `GET /snapshots/{base_snapshot_id}/compare/{target_snapshot_id}`.
- Modify `frontend/src/api/types.ts`
  - Add snapshot compare response types.
- Modify `frontend/src/api/client.ts`
  - Add `compareWorldSnapshots()` helper.
- Modify `frontend/src/api/client.test.ts`
  - Add RED test for compare helper URL.
- Modify `frontend/src/world/WorldArchivePanel.tsx`
  - Add snapshot list loading, selection, comparison, and rendering.
- Modify `frontend/src/world/WorldArchivePanel.test.tsx`
  - Add RED tests for compare UI.
- Modify `frontend/src/world/WorldPage.tsx`
  - Pass list and compare helpers into `WorldArchivePanel`.
- Modify `frontend/src/world/WorldPage.test.tsx`
  - Mock and assert compare/list helpers are wired.

---

## Task 1: Backend snapshot compare endpoint

**Files:**
- Test: `backend/tests/test_snapshot_export.py`
- Modify: `backend/app/snapshot_export/schemas.py`
- Modify: `backend/app/snapshot_export/service.py`
- Modify: `backend/app/snapshot_export/router.py`

- [ ] **Step 1: Write failing backend tests**

Add tests that create snapshots, mutate projection state directly, create a second snapshot, then assert a structured diff. Add auth and cross-world rejection tests.

- [ ] **Step 2: Run backend RED**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_snapshot_export.py -q'
```

Expected: fails with 404 for the compare endpoint.

- [ ] **Step 3: Add schemas**

Add Pydantic models for snapshot compare summary and change items.

- [ ] **Step 4: Add service diff logic**

Implement deterministic object-level diff helpers:

- compare dictionaries field-by-field
- compare object lists by `id`
- emit `added`, `removed`, and `changed`
- group counts by object type
- reject missing snapshots with `404 NOT_FOUND`
- reject cross-world snapshots with `403 FORBIDDEN`

- [ ] **Step 5: Add route**

Wire `GET /snapshots/{base_snapshot_id}/compare/{target_snapshot_id}` to the service.

- [ ] **Step 6: Run backend GREEN**

Run the same test command. Expected: all snapshot export tests pass.

---

## Task 2: Frontend API helper and types

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/api/client.test.ts`

- [ ] **Step 1: Write failing API helper test**

Add a test that calls `compareWorldSnapshots(12, 13)` and expects fetch URL:

```text
http://localhost:8000/snapshots/12/compare/13
```

- [ ] **Step 2: Run frontend API RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts
```

Expected: fails because `compareWorldSnapshots` is missing.

- [ ] **Step 3: Add types and helper**

Add compare response types to `types.ts` and helper to `client.ts`.

- [ ] **Step 4: Run frontend API GREEN**

Run the same test command. Expected: pass.

---

## Task 3: Archive panel compare UI

**Files:**
- Modify: `frontend/src/world/WorldArchivePanel.test.tsx`
- Modify: `frontend/src/world/WorldArchivePanel.tsx`

- [ ] **Step 1: Write failing panel tests**

Add tests that assert:

- snapshot compare section renders
- load button calls `onListSnapshots`
- compare button is disabled until two different snapshots are selected
- compare action calls `onCompareSnapshots(baseId, targetId)` and renders counts/change cards
- compare errors show localized alert

- [ ] **Step 2: Run panel RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldArchivePanel.test.tsx
```

Expected: fails because compare UI is missing.

- [ ] **Step 3: Implement minimal UI**

Extend props with `onListSnapshots` and `onCompareSnapshots`. Add local state for snapshot list, selected ids, loading/error, and compare response. Render a compact diff summary.

- [ ] **Step 4: Run panel GREEN**

Run the same command. Expected: pass.

---

## Task 4: WorldPage integration

**Files:**
- Modify: `frontend/src/world/WorldPage.tsx`
- Modify: `frontend/src/world/WorldPage.test.tsx`

- [ ] **Step 1: Write failing integration test**

Update mocks/imports for `listWorldSnapshots` and `compareWorldSnapshots`; assert archive panel can trigger snapshot list loading from `WorldPage`.

- [ ] **Step 2: Run WorldPage RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: fails because helpers are not wired.

- [ ] **Step 3: Wire helpers**

Import `listWorldSnapshots` and `compareWorldSnapshots` and pass them into `WorldArchivePanel`.

- [ ] **Step 4: Run WorldPage GREEN**

Run the same command. Expected: pass.

---

## Task 5: Final verification, commit, merge

- [ ] **Step 1: Run backend targeted tests**

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_snapshot_export.py tests/test_world_search.py tests/test_narrative_health.py -q'
```

- [ ] **Step 2: Run frontend targeted tests**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts src/world/WorldArchivePanel.test.tsx src/world/WorldPage.test.tsx
```

- [ ] **Step 3: Run frontend build**

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

- [ ] **Step 4: Inline self-review**

Check diff for unintended mutation paths, route exposure, naming consistency, and user-facing copy.

- [ ] **Step 5: Commit implementation**

```bash
git add backend frontend docs/superpowers/plans/2026-05-31-mvp18-snapshot-compare.md
git commit -m "feat: add snapshot compare view"
```

- [ ] **Step 6: Merge to main, no push**

```bash
git checkout main
git merge feat/mvp18-snapshot-compare
```

- [ ] **Step 7: Post-merge verification**

Repeat backend targeted tests, frontend targeted tests, and frontend build on `main`.

## Self-review checklist

- The plan covers backend, frontend API, UI, integration, tests, commit, and merge.
- No dynamic workflows or subagents are used.
- Every production change has a preceding RED test step.
- Snapshot compare is read-only and owner-scoped.
