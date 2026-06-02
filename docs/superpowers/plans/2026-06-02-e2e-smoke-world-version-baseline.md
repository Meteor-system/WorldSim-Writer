# E2E Smoke World Version Baseline Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Fail smoke early when create-world lacks the baseline `world_version` needed to prove approval increments world state.

**Architecture:** Reuse the existing `_require_fields` helper in `backend/scripts/e2e_smoke.py` and tighten the create-world required fields from `['id']` to `['id', 'world_version']`.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing create-world baseline test

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_requires_world_version_baseline_for_create_world`.
- [ ] Mock health and register success, then create-world success with `id` but no `world_version`.
- [ ] Assert `summary['ok'] is False`, `failed_step == 'create_world'`, `error == 'MISSING_REQUIRED_FIELDS'`, and `missing_fields == ['world_version']`.
- [ ] Assert no draft request is made.
- [ ] Run the focused test and confirm RED because create-world currently only requires `id`.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_world_version_baseline_for_create_world -q
```

### Task 2: Tighten create-world required fields

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Change the create-world `_require_fields` call to require `['id', 'world_version']`.
- [ ] Keep `world_id = world['id']` and `initial_world_version = world.get('world_version')` unchanged after the validation.
- [ ] Do not change backend API behavior or approval behavior.
- [ ] Rerun the focused test and confirm GREEN.

### Task 3: Verify and commit

**Files:**
- No docs update required beyond this spec/plan because `BETA_TESTING.md` already documents `MISSING_REQUIRED_FIELDS` and `missing_fields`.

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
