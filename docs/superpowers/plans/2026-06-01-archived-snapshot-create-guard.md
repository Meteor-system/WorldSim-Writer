# Archived Snapshot Create Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent archived worlds from creating persisted snapshots while preserving archive reads/exports.

**Architecture:** Reuse the existing world update governance helper on snapshot creation only. Add a `readOnly` prop to the archive panel and wire `isArchivedWorld` from `WorldPage`.

**Tech Stack:** FastAPI, SQLAlchemy, pytest, React, TypeScript, Vitest, Testing Library.

---

### Task 1: Backend archived snapshot write guard

**Files:**
- Modify: `backend/tests/test_snapshot_export.py`
- Modify: `backend/app/snapshot_export/service.py`

- [ ] Step 1: Add failing test `test_archived_world_rejects_snapshot_creation_but_allows_archive_reads`.
- [ ] Step 2: Run the focused test and verify it fails because snapshot creation returns 200 instead of 409.
- [ ] Step 3: Change `create_world_snapshot()` to use `require_owned_world_for_update()` instead of read-only ownership lookup.
- [ ] Step 4: Run focused test and snapshot export suite.

### Task 2: Frontend archive panel read-only controls

**Files:**
- Modify: `frontend/src/world/WorldArchivePanel.tsx`
- Modify: `frontend/src/world/WorldArchivePanel.test.tsx`
- Modify: `frontend/src/world/WorldPage.tsx`
- Modify: `frontend/src/world/WorldPage.test.tsx`

- [ ] Step 1: Add failing read-only archive panel test.
- [ ] Step 2: Run focused panel test and verify it fails because the create button is still visible.
- [ ] Step 3: Add `readOnly?: boolean`, hide snapshot creation only, and wire `readOnly={isArchivedWorld}` from `WorldPage`.
- [ ] Step 4: Run focused panel and WorldPage tests.

### Task 3: Final verification and commit

- [ ] Run backend snapshot export tests.
- [ ] Run frontend archive panel and WorldPage tests.
- [ ] Run frontend build.
- [ ] Run `git diff --check` and `git diff --cached --check`.
- [ ] Commit only relevant docs/code/tests.
