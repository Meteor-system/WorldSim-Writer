# E2E Smoke Health Type Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Reject malformed `/health` preflight boolean fields before smoke proceeds into auth/world/draft steps.

**Architecture:** Add a small nested boolean validation helper to `backend/scripts/e2e_smoke.py` and call it for `migration.up_to_date` and `llm.mock` immediately after required health paths are present. Reuse existing `INVALID_FIELD_TYPES` diagnostics and document the new health paths in beta testing guidance.

**Tech Stack:** Python, httpx, pytest.

---

### Task 1: Add failing health type regression

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_requires_health_flags_to_be_booleans` near the health preflight tests.
- [ ] Arrange `/health` to return:

```python
json_response({'status': 'ok', 'migration': {'up_to_date': 'false'}, 'llm': {'mock': 'true'}})
```

- [ ] Assert:

```python
assert summary['ok'] is False
assert summary['failed_step'] == 'health'
assert summary['error'] == 'INVALID_FIELD_TYPES'
assert summary['invalid_fields'] == ['migration.up_to_date', 'llm.mock']
assert [request.url.path for request in transport.requests] == ['/health']
```

- [ ] Run the focused test and confirm RED because the current smoke script accepts string health flags.

### Task 2: Implement nested boolean validation

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Add helper:

```python
def _require_bool_paths(summary: dict, step: str, payload: dict, paths: list[str]) -> bool:
    invalid = []
    for path in paths:
        current = payload
        for part in path.split('.'):
            current = current.get(part) if isinstance(current, dict) else None
        if not isinstance(current, bool):
            invalid.append(path)
    if not invalid:
        return True
    summary['failed_step'] = step
    summary['error'] = 'INVALID_FIELD_TYPES'
    summary['invalid_fields'] = invalid
    return False
```

- [ ] In `run_smoke()`, after `_require_paths(summary, 'health', health, ['status', 'migration.up_to_date', 'llm.mock'])`, call:

```python
if not _require_bool_paths(summary, 'health', health, ['migration.up_to_date', 'llm.mock']):
    return summary
```

- [ ] Rerun the focused test and confirm GREEN.

### Task 3: Document health type diagnostics

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] In the real-LLM diagnostic paragraph, extend the `INVALID_FIELD_TYPES` explanation to include health preflight boolean paths such as `migration.up_to_date` and `llm.mock`.
- [ ] Add `migration.up_to_date` and `llm.mock` to the beta docs coverage terms if not already explicit.
- [ ] Run `backend/tests/test_event_docs.py` and confirm GREEN.

### Task 4: Verify and commit

**Files:**
- Backend smoke script, smoke tests, beta docs, docs coverage test, and planning docs only.

- [ ] Run focused health type test.
- [ ] Run `backend/tests/test_e2e_scripts.py`.
- [ ] Run `backend/tests/test_event_docs.py`.
- [ ] Run full backend pytest if time permits; otherwise rely on the user-provided green baseline plus targeted smoke/docs tests.
- [ ] Run `git diff --check`.
- [ ] Stage intended files only; preserve `.hermes/plans/*` and `backend/worldsim-dev.db`.
- [ ] Run `git diff --cached --check`.
- [ ] Commit on the current feature branch.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_health_flags_to_be_booleans -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py -q
cd /opt/WorldSim-Writer && git diff --check
cd /opt/WorldSim-Writer && git diff --cached --check
```
