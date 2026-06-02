# E2E Smoke Approval Consistency Blocker Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Make smoke fail when approval consistency reports blocking issues, even if later mocked responses appear successful.

**Architecture:** Reuse the existing approval-consistency smoke step. Add a derived `blocked` boolean to `checks.approval_consistency` and require it to be false in the final `summary.ok` criteria. Keep warning-only consistency results non-blocking.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing consistency blocker smoke test

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add a test where approval consistency returns `consistency_summary: {"status": "blocked", "blocking_count": 1}`.
- [ ] Keep later approve/events/export responses successful to prove final `ok` depends on consistency.
- [ ] Assert `summary['ok'] is False` and `checks.approval_consistency.blocked is True`.
- [ ] Run the focused test and confirm RED.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_fails_when_approval_consistency_is_blocked -q
```

Expected RED: the smoke summary still reports `ok: true` or lacks `checks.approval_consistency.blocked`.

### Task 2: Implement consistency blocker gate

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Store `consistency_summary = consistency.get('consistency_summary') or {}`.
- [ ] Compute `consistency_blocked = consistency_summary.get('status') == 'blocked' or (consistency_summary.get('blocking_count') or 0) > 0`.
- [ ] Store `blocked: consistency_blocked` under `checks.approval_consistency`.
- [ ] Add `not consistency_blocked` to the final `summary.ok` criteria.
- [ ] Do not fail smoke for warning-only `needs_review` consistency results.

### Task 3: Document and verify

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add a docs assertion for `checks.approval_consistency.blocked`.
- [ ] Document the smoke pass criterion and triage instruction for consistency blockers.
- [ ] Run related tests and full backend tests.
- [ ] Run frontend tests/build because the user requested tests/build and no frontend changes are expected.
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
