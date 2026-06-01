# E2E Smoke Health Contract Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Report successful health responses missing preflight fields as malformed health-step responses.

**Architecture:** Add a small dotted-path validation helper in `backend/scripts/e2e_smoke.py` and use it immediately after the health API call succeeds.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing health missing-field test

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_requires_health_llm_mode_for_preflight`.
- [ ] Mock `/health` as `{'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {}}`.
- [ ] Assert `summary['ok'] is False`, `failed_step == 'health'`, `error == 'MISSING_REQUIRED_FIELDS'`, and `missing_fields == ['llm.mock']`.
- [ ] Assert no auth request is made after malformed health.
- [ ] Run the focused test and confirm RED because health currently treats missing `llm.mock` as non-blocking.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_health_llm_mode_for_preflight -q
```

### Task 2: Require health preflight fields

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Add `_require_paths(summary: dict, step: str, payload: dict, paths: list[str]) -> bool`.
- [ ] It should split paths on `.` and require each nested key to exist in dictionaries.
- [ ] Reuse the existing `MISSING_REQUIRED_FIELDS` diagnostic fields.
- [ ] After health `_step_json` succeeds, require `['migration.up_to_date', 'llm.mock']`.
- [ ] Return the summary immediately when validation fails.
- [ ] Rerun the focused test and confirm GREEN.

### Task 3: Verify and commit

**Files:**
- No `BETA_TESTING.md` update required because it already documents `MISSING_REQUIRED_FIELDS`, `missing_fields`, migration, and LLM mode gates.

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
