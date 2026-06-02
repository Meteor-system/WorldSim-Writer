# E2E Smoke LLM Mode Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Prevent misleading or costly smoke runs by verifying that the running backend LLM mode matches the requested smoke mode.

**Architecture:** Add a safe `llm.mock` boolean to `/health`, then have `scripts/e2e_smoke.py` compare it with its selected mode. Keep all checks on the existing health gate so mode mismatches fail before registration/world creation/model calls.

**Tech Stack:** Python, FastAPI, Pydantic settings, httpx, pytest, Markdown docs.

---

### Task 1: Add failing health and smoke tests

**Files:**
- Modify: `backend/tests/test_health.py`
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `/health` assertion for `llm: {mock: false}` in the existing health test.
- [ ] Add smoke test where mock smoke sees `health.llm.mock: false` and stops at health with `BACKEND_LLM_MOCK_DISABLED`.
- [ ] Add smoke test where `E2E_REAL_LLM=1` sees `health.llm.mock: true` and stops at health with `BACKEND_LLM_MOCK_ENABLED`.
- [ ] Run the focused tests and confirm RED.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_health.py::test_health_check_returns_ok_with_migration_status tests/test_e2e_scripts.py::test_e2e_smoke_script_stops_when_mock_smoke_targets_real_llm_backend tests/test_e2e_scripts.py::test_e2e_smoke_script_stops_when_real_llm_smoke_targets_mock_backend -q
```

Expected RED: `/health` lacks `llm`, and the new smoke tests continue past health or lack the expected mismatch errors.

### Task 2: Implement safe LLM mode health and smoke gates

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Return `{'llm': {'mock': settings.llm_mock}}` from `/health`.
- [ ] Record `checks.health.llm_mock` in the smoke summary.
- [ ] If mock smoke sees `llm_mock is False`, set `failed_step: 'health'`, `error: 'BACKEND_LLM_MOCK_DISABLED'`, and return.
- [ ] If real-LLM smoke sees `llm_mock is True`, set `failed_step: 'health'`, `error: 'BACKEND_LLM_MOCK_ENABLED'`, and return.
- [ ] Do not expose model names, URLs, API keys, headers, or tokens.

### Task 3: Document and verify

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add docs assertions for `llm_mock`, `BACKEND_LLM_MOCK_DISABLED`, and `BACKEND_LLM_MOCK_ENABLED`.
- [ ] Document the new smoke pass criteria and recovery steps.
- [ ] Run related tests and full backend tests.
- [ ] Run `git diff --check` and `git diff --cached --check`.
- [ ] Commit intended files only.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_health.py tests/test_e2e_scripts.py tests/test_event_docs.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest -q
cd /opt/WorldSim-Writer && git diff --check
```
