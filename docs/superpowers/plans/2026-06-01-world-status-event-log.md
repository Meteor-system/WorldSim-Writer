# World Status Event Log Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record archive/restore lifecycle changes in append-only event history without changing canon world version.

**Architecture:** Extend `update_world_status()` in `backend/app/world/service.py` to add an `EventLog` row only when status actually changes. Keep the route and schema unchanged.

**Tech Stack:** FastAPI, SQLAlchemy, pytest.

---

### Task 1: Add backend regression tests

**Files:**
- Modify: `backend/tests/test_world_routes.py`

- [ ] Step 1: Add a failing test that archives and restores a world, then verifies two `world_status_changed` events.
- [ ] Step 2: Add a failing test that repeats an unchanged status and verifies no event is written.
- [ ] Step 3: Run focused tests and verify they fail because status events are missing.

### Task 2: Implement event writing

**Files:**
- Modify: `backend/app/world/service.py`

- [ ] Step 1: Capture `previous_status` before assignment.
- [ ] Step 2: If unchanged, commit/refresh as before but skip event creation.
- [ ] Step 3: If changed, add `EventLog(event_type='world_status_changed', source_type='world_status', payload={...}, world_version_before=world.world_version, world_version_after=world.world_version)`.
- [ ] Step 4: Run focused tests and full world route tests.

### Task 3: Verification and commit

- [ ] Run backend world route tests.
- [ ] Run related frontend WorldPage tests and frontend build.
- [ ] Run `git diff --check` and `git diff --cached --check`.
- [ ] Commit only relevant files.
