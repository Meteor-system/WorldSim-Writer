# E2E Smoke Register Conflict Login Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Let smoke reruns with an existing `E2E_EMAIL` fall back to login when the current backend returns `409 EMAIL_ALREADY_REGISTERED`.

**Architecture:** Add a focused duplicate-email response helper in `backend/scripts/e2e_smoke.py`, then use it in `_register_or_login`. Preserve existing register failure diagnostics for unrelated conflicts.

**Tech Stack:** Python, httpx, pytest.

---

### Task 1: Add failing current-backend duplicate email fallback regression

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_logs_in_when_register_returns_email_conflict` near existing auth fallback tests.
- [ ] Mock `/auth/register` as `json_response({'detail': 'EMAIL_ALREADY_REGISTERED'}, status_code=409)`.
- [ ] Mock `/auth/login` as a valid auth response.
- [ ] Continue the normal happy path through export.
- [ ] Assert:

```python
assert summary['ok'] is True
assert 'login' in summary['checks']
assert 'register' not in summary['checks']
assert [request.url.path for request in transport.requests][:3] == [
    '/health',
    '/auth/register',
    '/auth/login',
]
```

- [ ] Run the focused test and confirm RED.

### Task 2: Add unrelated register conflict non-fallback regression

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_does_not_login_for_unrelated_register_conflict`.
- [ ] Mock `/auth/register` as `httpx.Response(409, json={'detail': 'ACCOUNT_LOCKED'})`.
- [ ] Assert:

```python
assert summary['ok'] is False
assert summary['failed_step'] == 'register'
assert summary['status_code'] == 409
assert summary['response_body'] == '{"detail":"ACCOUNT_LOCKED"}'
assert [request.url.path for request in transport.requests] == [
    '/health',
    '/auth/register',
]
```

- [ ] Run the focused test and confirm behavior is already correct or fails for the expected reason.

### Task 3: Implement duplicate-email response helper

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Add:

```python
def _is_duplicate_email_register_response(response: httpx.Response) -> bool:
    if response.status_code == 400:
        return True
    if response.status_code != 409:
        return False
    try:
        payload = response.json()
    except ValueError:
        return False
    return isinstance(payload, dict) and payload.get('detail') == 'EMAIL_ALREADY_REGISTERED'
```

- [ ] Update `_register_or_login` to call this helper instead of checking `response.status_code == 400`.
- [ ] Rerun focused tests and confirm GREEN.

### Task 4: Verify and commit

**Files:**
- Backend smoke script/tests and planning docs only; no frontend changes expected.

- [ ] Run focused new smoke tests.
- [ ] Run all smoke script tests.
- [ ] Run full backend pytest.
- [ ] Run `git diff --check`.
- [ ] Stage intended files only; preserve `.hermes/plans/*` and `backend/worldsim-dev.db`.
- [ ] Run `git diff --cached --check`.
- [ ] Commit on the current feature branch.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_logs_in_when_register_returns_email_conflict tests/test_e2e_scripts.py::test_e2e_smoke_script_does_not_login_for_unrelated_register_conflict -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest -q
cd /opt/WorldSim-Writer && git diff --check
cd /opt/WorldSim-Writer && git diff --cached --check
```
