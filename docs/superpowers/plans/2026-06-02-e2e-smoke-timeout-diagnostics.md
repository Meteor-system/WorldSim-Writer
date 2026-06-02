# E2E Smoke Request Timeout Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Emit stable `REQUEST_TIMEOUT` smoke diagnostics when httpx client-side timeouts occur.

**Architecture:** Add one small helper in `backend/scripts/e2e_smoke.py` to map `httpx.TimeoutException` to `REQUEST_TIMEOUT` and preserve existing non-timeout request error strings. Use it from `_step_json` and `_register_or_login`. Document the new diagnostic in `BETA_TESTING.md` and keep docs coverage enforced in `backend/tests/test_event_docs.py`.

**Tech Stack:** Python, httpx, pytest.

---

### Task 1: Add failing draft timeout regression

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_reports_request_timeout_for_draft_timeout` near existing request-error diagnostics.
- [ ] Use a sequenced transport that succeeds through health/register/create-world, then raises `httpx.ReadTimeout('draft timed out', request=request)` for `/worlds/10/chapters/draft`.
- [ ] Assert:

```python
assert summary['ok'] is False
assert summary['failed_step'] == 'draft'
assert summary['error'] == 'REQUEST_TIMEOUT'
assert summary['timeout_seconds'] == 60.0
assert 'status_code' not in summary
assert 'response_body' not in summary
```

- [ ] Run the focused test and confirm RED with `error` still equal to the raw timeout message.

### Task 2: Add failing register timeout regression

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_reports_request_timeout_for_register_timeout` near auth fallback diagnostics.
- [ ] Use a custom transport that returns healthy `/health`, then raises `httpx.ConnectTimeout('register timed out', request=request)` for `/auth/register`.
- [ ] Assert:

```python
assert summary['ok'] is False
assert summary['failed_step'] == 'register'
assert summary['error'] == 'REQUEST_TIMEOUT'
assert [request.url.path for request in transport.requests] == ['/health', '/auth/register']
```

- [ ] Run the focused test and confirm RED.

### Task 3: Implement shared request timeout diagnostic

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Add:

```python
def _mark_request_error(summary: dict, step: str, exc: httpx.RequestError) -> None:
    summary['failed_step'] = step
    summary['error'] = 'REQUEST_TIMEOUT' if isinstance(exc, httpx.TimeoutException) else str(exc)
```

- [ ] Replace duplicated request-error handling in `_step_json` with `_mark_request_error(summary, step, exc)`.
- [ ] Replace duplicated request-error handling in `_register_or_login` with `_mark_request_error(summary, 'register', exc)`.
- [ ] Rerun focused tests and confirm GREEN.

### Task 4: Document and verify

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add `REQUEST_TIMEOUT` to the required playbook terms in `test_beta_testing_playbook_documents_main_flow_smoke_and_reporting`.
- [ ] Update the real-LLM smoke troubleshooting text to say `REQUEST_TIMEOUT` means the smoke client timed out waiting for a backend response and testers should increase `E2E_TIMEOUT_SECONDS`.
- [ ] Run docs coverage test.
- [ ] Run all smoke script tests.
- [ ] Run full backend pytest.
- [ ] Run `git diff --check`.
- [ ] Stage intended files only; preserve `.hermes/plans/*` and `backend/worldsim-dev.db`.
- [ ] Run `git diff --cached --check`.
- [ ] Commit on the current feature branch.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_reports_request_timeout_for_draft_timeout tests/test_e2e_scripts.py::test_e2e_smoke_script_reports_request_timeout_for_register_timeout -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py::test_beta_testing_playbook_documents_main_flow_smoke_and_reporting -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest -q
cd /opt/WorldSim-Writer && git diff --check
cd /opt/WorldSim-Writer && git diff --cached --check
```
