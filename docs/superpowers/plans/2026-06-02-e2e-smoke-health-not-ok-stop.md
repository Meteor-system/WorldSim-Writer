# E2E Smoke Health Not-OK Stop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Stop smoke before any state-changing calls when `/health` reports a non-`ok` status.

**Architecture:** Extend the existing health preflight in `backend/scripts/e2e_smoke.py` with an early return after safe health diagnostics are recorded. Cover the behavior with a focused smoke-script test and document the beta remediation path.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing health-not-ok smoke test

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_stops_when_health_status_is_not_ok`.
- [ ] Mock `/health` as `{'status': 'degraded', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}`.
- [ ] Assert `summary['ok'] is False`.
- [ ] Assert `summary['failed_step'] == 'health'`.
- [ ] Assert `summary['error'] == 'HEALTH_STATUS_NOT_OK'`.
- [ ] Assert `summary['checks']['health']['status'] == 'degraded'`.
- [ ] Assert the request path list is only `['/health']`.
- [ ] Run the focused test and confirm RED because the script currently continues past a non-`ok` health status.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_stops_when_health_status_is_not_ok -q
```

### Task 2: Add health-not-ok early stop

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] After `summary['checks']['health']` is populated, return with `failed_step: "health"` and `error: "HEALTH_STATUS_NOT_OK"` when `summary['checks']['health']['status'] != "ok"`.
- [ ] Keep the existing migration and LLM-mode checks after the status check.
- [ ] Rerun the focused test and confirm GREEN.
- [ ] Rerun all smoke-script tests.

### Task 3: Document beta diagnostic

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add `HEALTH_STATUS_NOT_OK` and `checks.health.status` to docs regression terms.
- [ ] Run the focused docs test and confirm RED.
- [ ] Update the mock-smoke pass criteria to require `checks.health.status` is `ok` and explain `HEALTH_STATUS_NOT_OK`.
- [ ] Rerun the focused docs test and confirm GREEN.

### Task 4: Verify and commit

**Files:**
- No frontend changes expected.

- [ ] Run `backend/tests/test_e2e_scripts.py`.
- [ ] Run `backend/tests/test_event_docs.py`.
- [ ] Run full backend tests or cite the user's independent fresh full-suite evidence only if no production/test code changed after it.
- [ ] Skip frontend tests/build unless frontend files changed; state that no frontend files changed.
- [ ] Run `git diff --check` and `git diff --cached --check`.
- [ ] Commit intended files only.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest -q
cd /opt/WorldSim-Writer && git diff --check
cd /opt/WorldSim-Writer && git diff --cached --check
```
