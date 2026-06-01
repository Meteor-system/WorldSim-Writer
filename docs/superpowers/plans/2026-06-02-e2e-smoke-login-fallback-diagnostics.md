# E2E Smoke Login Fallback Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Report malformed fallback-login auth responses as login-step failures instead of register-step failures.

**Architecture:** Have `_register_or_login` return the response payload plus the successful auth step label, then use that label for required-field validation and auth check summary naming.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing fallback-login diagnostics test

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_reports_missing_access_token_for_login_fallback`.
- [ ] Mock `/health` as valid.
- [ ] Mock `/auth/register` as HTTP 400 so the script falls back to login.
- [ ] Mock `/auth/login` as a successful JSON response missing `access_token`.
- [ ] Assert `summary['ok'] is False`, `failed_step == 'login'`, `error == 'MISSING_REQUIRED_FIELDS'`, and `missing_fields == ['access_token']`.
- [ ] Assert no world creation request is made after malformed fallback login.
- [ ] Run the focused test and confirm RED because auth validation currently labels missing fallback-login tokens as `register`.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_reports_missing_access_token_for_login_fallback -q
```

### Task 2: Track the auth source step

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Change `_register_or_login` to return a tuple of `(payload, auth_step)`.
- [ ] Return `({}, 'register')` when the initial register request fails before an HTTP response.
- [ ] Return `(login_payload, 'login')` when register returns `400` and login fallback is attempted.
- [ ] Return `(register_payload, 'register')` for normal register success.
- [ ] In `run_smoke`, use `auth_step` in `_require_fields(summary, auth_step, auth_payload, ['access_token'])`.
- [ ] Store the user id under `summary['checks'][auth_step]` so the summary reflects whether register or login authenticated the smoke user.
- [ ] Rerun the focused test and confirm GREEN.

### Task 3: Verify and commit

**Files:**
- No `BETA_TESTING.md` update required because it already documents `failed_step`, `MISSING_REQUIRED_FIELDS`, and `missing_fields`.

- [ ] Run related smoke script tests.
- [ ] Run full backend tests.
- [ ] Run frontend tests/build because the user requested relevant tests/build and no frontend changes are expected.
- [ ] Run `git diff --check` and `git diff --cached --check`.
- [ ] Commit intended files only.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest -q
cd /opt/WorldSim-Writer/frontend && npm run test -- --run
cd /opt/WorldSim-Writer/frontend && npm run build
cd /opt/WorldSim-Writer && git diff --check
cd /opt/WorldSim-Writer && git diff --cached --check
```
