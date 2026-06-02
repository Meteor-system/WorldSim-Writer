# E2E Smoke Approval Readiness Blocker Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Make smoke fail when approval readiness reports blocking reasons, even if later mocked responses appear successful.

**Architecture:** Reuse the existing approval-readiness smoke step. Add a derived `blocked` boolean to `checks.approval_readiness` and require it to be false in the final `summary.ok` criteria. Keep warnings non-blocking.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing readiness blocker smoke test

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add a test where approval readiness returns `status: "blocked"` and a non-empty `blocking_reasons` list.
- [ ] Keep later approve/events/export responses successful to prove final `ok` depends on readiness.
- [ ] Assert `summary['ok'] is False` and `checks.approval_readiness.blocked is True`.
- [ ] Run the focused test and confirm RED.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_fails_when_approval_readiness_is_blocked -q
```

Expected RED: the smoke summary still reports `ok: true` or lacks `checks.approval_readiness.blocked`.

### Task 2: Implement readiness blocker gate

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Compute `readiness_blocked = readiness.get('status') == 'blocked' or bool(readiness.get('blocking_reasons') or [])` after the readiness response.
- [ ] Store `blocked: readiness_blocked` under `checks.approval_readiness`.
- [ ] Add `not readiness_blocked` to the final `summary.ok` criteria.
- [ ] Do not fail smoke for `status: "needs_review"` when `blocking_reasons` is empty.

### Task 3: Document and verify

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add a docs assertion for `checks.approval_readiness.blocked`.
- [ ] Document the smoke pass criterion and the rerun/review instruction for blocked readiness.
- [ ] Run related tests and full backend tests.
- [ ] Run frontend tests/build because the user requested relevant build/test gates and no frontend changes are expected.
- [ ] Run `git diff --check` and `git diff --cached --check`.
- [ ] Commit intended files only.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py tests/test_event_docs.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest -q
cd /opt/WorldSim-Writer/frontend && npm run test -- --run
cd /opt/WorldSim-Writer/frontend && npm run build
cd /opt/WorldSim-Writer && git diff --check
```
