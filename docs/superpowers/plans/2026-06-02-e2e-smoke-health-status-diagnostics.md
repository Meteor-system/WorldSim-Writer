# E2E Smoke Health Status Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Report successful health responses missing `status` as malformed health-step responses.

**Architecture:** Reuse `_require_paths` in `backend/scripts/e2e_smoke.py` and add `status` to the required health preflight paths.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing health missing-status test

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_requires_health_status_for_preflight`.
- [ ] Mock `/health` as `{'migration': {'up_to_date': True}, 'llm': {'mock': True}}`.
- [ ] Assert `summary['ok'] is False`, `failed_step == 'health'`, `error == 'MISSING_REQUIRED_FIELDS'`, and `missing_fields == ['status']`.
- [ ] Assert no auth request is made after malformed health.
- [ ] Run the focused test and confirm RED because health currently treats missing status as non-blocking.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_health_status_for_preflight -q
```

### Task 2: Require health status

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Change the health `_require_paths` call to require `['status', 'migration.up_to_date', 'llm.mock']`.
- [ ] Keep the final `health.get('status') == 'ok'` semantic pass criterion unchanged.
- [ ] Rerun the focused test and confirm GREEN.

### Task 3: Verify and commit

**Files:**
- No `BETA_TESTING.md` update required because it already documents health diagnostics and `MISSING_REQUIRED_FIELDS`.

- [ ] Run related smoke script tests.
- [ ] Run full backend tests.
- [ ] Run frontend tests/build because the user requested related tests/build and no frontend changes are expected.
- [ ] Run `git diff --check` and `git diff --cached --check`.
- [ ] Commit intended files only.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest -q
cd /opt/WorldSim-Writer/frontend && npm run test -- --run
cd /opt/WorldSim-Writer/frontend && npm run build
cd /opt/WorldSim-Writer && git diff --check
```
