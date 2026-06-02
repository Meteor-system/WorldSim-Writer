# State Consistency WORLD_CREATED Event Test Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore backend full pytest by updating stale state consistency EventLog expectations without weakening product behavior.

**Architecture:** Treat `WORLD_CREATED` as the initial world lifecycle event. Filter approval-specific assertions to non-creation events and update endpoint totals/offset expectations to include the creation event.

**Tech Stack:** pytest, FastAPI TestClient, SQLAlchemy.

---

### Task 1: Confirm failure and root cause

**Files:**
- Inspect: `backend/tests/test_state_consistency.py`
- Inspect: `backend/app/world/service.py`

- [x] Run `pytest tests/test_state_consistency.py -q`.
- [x] Confirm failures are stale expectations caused by `WORLD_CREATED`.
- [x] Confirm `WORLD_CREATED` is current product behavior in world creation service.

### Task 2: Update stale EventLog expectations

**Files:**
- Modify: `backend/tests/test_state_consistency.py`

- [ ] In approval projection test, assert the first event is `WORLD_CREATED`, then assert the approval events separately.
- [ ] In rollback test, assert only `WORLD_CREATED` remains after failed approval.
- [ ] In event endpoint test, update total and offset expectations to include `WORLD_CREATED`.

### Task 3: Verify and commit

- [ ] Run `pytest tests/test_state_consistency.py -q`.
- [ ] Run backend full `pytest -q`.
- [ ] Skip frontend verification unless backend-only test changes unexpectedly affect contracts.
- [ ] Run `git diff --check` and `git diff --cached --check`.
- [ ] Commit relevant files only.
