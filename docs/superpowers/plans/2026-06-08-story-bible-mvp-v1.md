# Story Bible MVP v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Inline execution only for this task. Do not use subagents or dynamic workflows. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a MVP Story Bible editor so users can manually maintain canon text, characters, relations, and foreshadows while preserving world-version and draft-approval invariants.

**Architecture:** Reuse existing projection tables and CRUD services. Add the missing world canon editor endpoint around `World.truth_canon`, then complete existing frontend managers for create/delete and Chinese labels. Every formal manual edit uses `source_type='manual_edit'`, writes event logs, increments `world_version`, and leaves model draft approval logic unchanged.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, Vite React, TypeScript, Vitest, React Testing Library.

---

## Files

- Modify: `backend/app/world/schemas.py` — add `WorldCanonUpdateRequest`.
- Modify: `backend/app/world/service.py` — add `update_world_canon()` and reuse `refresh_world_projection()`.
- Modify: `backend/app/world/router.py` — add `PUT /worlds/{world_id}/canon`.
- Test: `backend/tests/test_world_routes.py` — cover canon edit version/event behavior, ownership, archived rejection.
- Test: `backend/tests/test_character_crud.py` — ensure create/update/delete manual events and version increments are covered.
- Test: `backend/tests/test_relation_crud.py` — ensure delete manual event/version behavior is covered.
- Test: `backend/tests/test_foreshadow_crud.py` — ensure create/update/delete manual event/version behavior is covered.
- Test: `backend/tests/test_narrative_pipeline.py` or existing narrative test file — assert post-manual-edit prompt/context uses latest canon/character/foreshadow state.
- Modify: `frontend/src/api/types.ts` — add `WorldCanonUpdateRequest` if missing.
- Modify: `frontend/src/api/client.ts` — add `updateWorldCanon()`, confirm CRUD helpers exist.
- Modify: `frontend/src/components/CharacterManager.tsx` — add create/delete UI and edit core fields, keep archived read-only behavior.
- Modify: `frontend/src/components/RelationManager.tsx` — add delete UI and Chinese labels for visibility.
- Modify: `frontend/src/components/ForeshadowManager.tsx` — ensure UI labels avoid raw enum/id in primary visible copy.
- Modify: `frontend/src/world/WorldPage.tsx` — add/rename Story Bible / 正史资料 tab with canon editor.
- Test: `frontend/src/components/CharacterManager.test.tsx` — create/edit/delete regression tests.
- Test: `frontend/src/components/RelationManager.test.tsx` — delete and Chinese label regression tests.
- Test: `frontend/src/components/ForeshadowManager.test.tsx` — Chinese label regression if needed.
- Test: `frontend/src/world/WorldPage.test.tsx` — canon editor and tab regression tests.

---

### Task 1: Backend canon editor endpoint

- [ ] **Step 1: Write failing tests** in `backend/tests/test_world_routes.py`:
  - `PUT /worlds/{world_id}/canon` updates `truth_canon`.
  - `truth_canon_version` increments by 1.
  - `world_version` increments by 1.
  - Event logs include `world_canon_change` and `world_version_increment` with `source_type='manual_edit'`.
  - Blank canon returns validation error.
  - Archived world returns `409 WORLD_ARCHIVED`.

- [ ] **Step 2: Run red test**:
  - `cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 ./.venv/bin/pytest tests/test_world_routes.py -q`
  - Expected: fails because `/worlds/{world_id}/canon` does not exist.

- [ ] **Step 3: Implement minimal backend**:
  - Add `WorldCanonUpdateRequest` with `truth_canon: str` and `edit_reason: str | None`.
  - Add `update_world_canon(db, user, world_id, data)` that locks owned active world, updates `truth_canon`, increments `truth_canon_version`, calls a manual event commit path with `object_type='world_canon'`, and returns the world.
  - Add route `PUT /worlds/{world_id}/canon` returning `WorldResponse`.

- [ ] **Step 4: Run green test**:
  - Same pytest command.

### Task 2: Backend CRUD invariant coverage

- [ ] **Step 1: Write or tighten failing tests**:
  - Character create/update/delete each increments `world_version` and writes `source_type='manual_edit'` event.
  - Relation delete increments `world_version` and writes `relation_change`.
  - Foreshadow create/update/delete each writes `foreshadow_change`; status transitions remain strict.

- [ ] **Step 2: Run red/focused tests**:
  - `cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 ./.venv/bin/pytest tests/test_character_crud.py tests/test_relation_crud.py tests/test_foreshadow_crud.py -q`

- [ ] **Step 3: Implement only missing behavior**:
  - Prefer existing `commit_manual_world_change()`.
  - Do not change chapter approval logic.
  - Do not add aggregate changeset APIs.

- [ ] **Step 4: Run green tests** with the same command.

### Task 3: Backend latest-state narrative context regression

- [ ] **Step 1: Write failing test**:
  - Mutate canon/character/foreshadow manually.
  - Build outline or generation messages for next draft.
  - Assert latest `truth_canon`, character status/goals, foreshadow status/title, and incremented `world_version` appear.

- [ ] **Step 2: Run red test**:
  - `cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 ./.venv/bin/pytest <narrative-test-file>::<test-name> -q`

- [ ] **Step 3: Implement only if needed**:
  - If prompt builders already query latest projection, no production change is needed after the regression test passes.

- [ ] **Step 4: Run green test**.

### Task 4: Frontend API and Story Bible canon editor

- [ ] **Step 1: Write failing frontend tests**:
  - In `WorldPage.test.tsx`, open `正史资料` tab, edit canon text, submit, assert `updateWorldCanon(7, { truth_canon, edit_reason })` is called and overview refreshes.
  - Assert archived worlds show read-only copy and no edit button.

- [ ] **Step 2: Run red test**:
  - `cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx --run`

- [ ] **Step 3: Implement frontend API/UI**:
  - Add `WorldCanonUpdateRequest` type.
  - Add `updateWorldCanon(worldId, data)` in API client.
  - Add WorldPage `正史资料` tab/editor using existing button/input classes and Chinese copy.

- [ ] **Step 4: Run green test**.

### Task 5: Frontend character manager create/delete

- [ ] **Step 1: Write failing tests** in `CharacterManager.test.tsx`:
  - Click `新增角色`, fill name/role/status/goals/reason, submit, assert `createCharacter()` called and `onChanged` invoked.
  - Click delete, confirm with optional reason, assert `deleteCharacter()` called and `onChanged` invoked.
  - Assert user-facing role/status labels are Chinese and raw internal ids are not primary visible labels.

- [ ] **Step 2: Run red test**:
  - `cd /opt/WorldSim-Writer/frontend && npm run test -- src/components/CharacterManager.test.tsx --run`

- [ ] **Step 3: Implement minimal UI**:
  - Import/create API helpers.
  - Add create modal and delete confirmation.
  - Expand edit payload to include name, role_type, status, destiny_flag, current_goals, edit_reason.

- [ ] **Step 4: Run green test**.

### Task 6: Frontend relation and foreshadow polish

- [ ] **Step 1: Write failing tests**:
  - Relation delete calls `deleteRelation()` and refreshes.
  - Relation visibility labels render as `公开` / `私下` / `秘密` instead of raw enum text.
  - Foreshadow type/status primary labels are Chinese.

- [ ] **Step 2: Run red tests**:
  - `cd /opt/WorldSim-Writer/frontend && npm run test -- src/components/RelationManager.test.tsx src/components/ForeshadowManager.test.tsx --run`

- [ ] **Step 3: Implement minimal UI changes**.

- [ ] **Step 4: Run green tests**.

### Task 7: Final verification and commit

- [ ] **Step 1: Run backend verification**:
  - `cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 ./.venv/bin/pytest tests/test_world_routes.py tests/test_character_crud.py tests/test_relation_crud.py tests/test_foreshadow_crud.py tests/test_narrative_approval.py -q`

- [ ] **Step 2: Run frontend targeted tests**:
  - `cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx src/components/CharacterManager.test.tsx src/components/RelationManager.test.tsx src/components/ForeshadowManager.test.tsx --run`

- [ ] **Step 3: Run frontend build**:
  - `cd /opt/WorldSim-Writer/frontend && npm run build`

- [ ] **Step 4: Run diff check**:
  - `git -C /opt/WorldSim-Writer diff --check`

- [ ] **Step 5: Inspect status and commit**:
  - `git -C /opt/WorldSim-Writer status --short`
  - Commit message: `feat: add story bible editor`
  - Include co-author trailer.

---

## Self-review

- Spec coverage: covers characters, relations, foreshadows, canon text, event logs, world_version, latest narrative context, frontend Chinese UI, tests, build, diff check, commit.
- Scope check: no aggregate changeset endpoint, no branch worlds, no diff UI, no graph DB, no collaboration, no bidirectional export/import.
- Type consistency: backend request name `WorldCanonUpdateRequest`; frontend helper `updateWorldCanon`; event object type `world_canon` and event type `world_canon_change` through existing governance naming.
