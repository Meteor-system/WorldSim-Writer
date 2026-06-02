# E2E Smoke Auth Token Type Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Stop smoke at register/login when successful auth responses return malformed `access_token` values.

**Architecture:** Add one small string-field validation helper in `backend/scripts/e2e_smoke.py`, then call it after the existing auth required-field check. Preserve the existing diagnostics vocabulary by using `INVALID_FIELD_TYPES` with `invalid_fields`.

**Tech Stack:** Python, httpx, pytest.

---

### Task 1: Add failing register token type regression

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_requires_register_access_token_to_be_string` near the auth validation tests.
- [ ] Return a successful register response with `{'access_token': True, 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}`.
- [ ] Assert:

```python
assert summary['ok'] is False
assert summary['failed_step'] == 'register'
assert summary['error'] == 'INVALID_FIELD_TYPES'
assert summary['invalid_fields'] == ['access_token']
assert [request.url.path for request in transport.requests] == [
    '/health',
    '/auth/register',
]
```

- [ ] Run the focused test and confirm RED.

### Task 2: Add failing login fallback token type regression

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_requires_login_access_token_to_be_string` near the login fallback auth tests.
- [ ] Return `400` from register, then a successful login response with `{'access_token': {'token': 'bad'}, 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}`.
- [ ] Assert `failed_step == 'login'`, `error == 'INVALID_FIELD_TYPES'`, and `invalid_fields == ['access_token']`.
- [ ] Assert smoke does not call `/worlds/from-template`.
- [ ] Run the focused test and confirm RED.

### Task 3: Implement auth token string validation

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Add:

```python
def _require_string_fields(summary: dict, step: str, payload: dict, fields: list[str]) -> bool:
    invalid = [field for field in fields if not isinstance(payload.get(field), str) or not payload.get(field)]
    if not invalid:
        return True
    summary['failed_step'] = step
    summary['error'] = 'INVALID_FIELD_TYPES'
    summary['invalid_fields'] = invalid
    return False
```

- [ ] Call it immediately after `_require_fields(summary, auth_step, auth_payload, ['access_token'])`.
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
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_register_access_token_to_be_string tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_login_access_token_to_be_string -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest -q
cd /opt/WorldSim-Writer && git diff --check
cd /opt/WorldSim-Writer && git diff --cached --check
```
