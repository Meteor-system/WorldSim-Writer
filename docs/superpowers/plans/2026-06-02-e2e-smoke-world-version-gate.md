# E2E Smoke World Version Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Make smoke fail when chapter approval does not advance the world version.

**Architecture:** Reuse existing world creation and approval response data in the smoke script. Add a derived boolean under `checks.approve` and include it in the final `summary.ok` criteria.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing world-version gate test

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add a test where world creation returns `world_version: 1` and approval returns `approved_version: 1`.
- [ ] Assert `summary.ok is False` and `checks.approve.world_version_incremented is False`.
- [ ] Run the focused test and confirm RED.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_fails_when_approval_does_not_increment_world_version -q
```

Expected RED: the smoke summary still reports `ok: true` or lacks `world_version_incremented`.

### Task 2: Implement world-version gate

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Store `initial_world_version` from the create-world response.
- [ ] Compute `expected_world_version_after = initial_world_version + 1` when the initial value is an integer.
- [ ] Store `world_version_incremented` in `checks.approve`.
- [ ] Add `world_version_incremented` to `summary.ok` criteria.

### Task 3: Document and verify

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add a docs assertion for `world_version_incremented`.
- [ ] Document the smoke pass criterion.
- [ ] Run focused tests, related backend tests, and diff checks.
- [ ] Commit intended files only.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py tests/test_event_docs.py -q
cd /opt/WorldSim-Writer && git diff --check
```
