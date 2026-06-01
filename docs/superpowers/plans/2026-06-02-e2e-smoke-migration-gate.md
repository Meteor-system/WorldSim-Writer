# E2E Smoke Migration Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Stop smoke early when `/health` reports pending or unknown migrations.

**Architecture:** Add a small health-gate branch immediately after the existing health check summary is recorded. The branch reuses the current JSON summary format and existing step diagnostics.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing migration-gate test

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add a test where `/health` returns `migration.up_to_date: false`.
- [ ] Assert `ok: false`, `failed_step: "health"`, `error: "MIGRATION_NOT_UP_TO_DATE"`, migration details are preserved, and only `/health` was requested.
- [ ] Run the focused test and confirm RED.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_stops_when_migration_is_not_up_to_date -q
```

Expected RED: the script continues to `/auth/register` and the sequenced transport reports an unexpected request or the summary lacks the migration gate error.

### Task 2: Implement migration gate

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] After recording `checks.health`, check whether `migration_up_to_date is False`.
- [ ] If false, set `failed_step` to `health`, set `error` to `MIGRATION_NOT_UP_TO_DATE`, and return the summary.
- [ ] Leave `migration_up_to_date is True` behavior unchanged.

### Task 3: Document and verify

**Files:**
- Modify: `BETA_TESTING.md`

- [ ] Document that smoke stops at health when migrations are stale and testers should run `alembic upgrade head`.
- [ ] Run focused smoke tests and docs tests.
- [ ] Run `git diff --check` and `git diff --cached --check` before commit.
- [ ] Commit intended files only.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py tests/test_event_docs.py -q
cd /opt/WorldSim-Writer && git diff --check
```
