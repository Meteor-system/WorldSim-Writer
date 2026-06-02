# E2E Smoke ID and Version Type Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Stop smoke at the exact API step when required scalar IDs or version fields are present but not integer values.

**Architecture:** Add one top-level integer-field validation helper in `backend/scripts/e2e_smoke.py`, then call it after existing required-field checks for world creation, draft creation, and approval. Preserve existing diagnostics vocabulary by using `INVALID_FIELD_TYPES` with `invalid_fields`.

**Tech Stack:** Python, httpx, pytest.

---

### Task 1: Add failing create-world scalar type regression

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_requires_create_world_id_and_world_version_to_be_int` near existing create-world validation tests.
- [ ] Return `json_response({'id': '10', 'world_version': True})` from `/worlds/from-template`.
- [ ] Assert:

```python
assert summary['ok'] is False
assert summary['failed_step'] == 'create_world'
assert summary['error'] == 'INVALID_FIELD_TYPES'
assert summary['invalid_fields'] == ['id', 'world_version']
assert [request.url.path for request in transport.requests] == [
    '/health',
    '/auth/register',
    '/worlds/from-template',
]
```

- [ ] Run the focused test and confirm RED.

### Task 2: Add failing draft scalar type regression

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_requires_draft_chapter_id_and_draft_version_to_be_int`.
- [ ] Return a normal world, then `json_response({'chapter_id': '20', 'draft_id': 30, 'draft_version': '1'})` from draft creation.
- [ ] Assert `failed_step == 'draft'`, `error == 'INVALID_FIELD_TYPES'`, and `invalid_fields == ['chapter_id', 'draft_version']`.
- [ ] Assert smoke does not call approval preview.
- [ ] Run the focused test and confirm RED.

### Task 3: Add failing approve scalar type regression

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_requires_approved_version_to_be_int`.
- [ ] Mock the normal flow through consistency, then return `json_response({'id': 20, 'status': 'approved', 'approved_version': '2'})`.
- [ ] Assert `failed_step == 'approve'`, `error == 'INVALID_FIELD_TYPES'`, and `invalid_fields == ['approved_version']`.
- [ ] Assert smoke does not call events or export.
- [ ] Run the focused test and confirm RED.

### Task 4: Implement scalar integer validation

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Add:

```python
def _require_int_fields(summary: dict, step: str, payload: dict, fields: list[str]) -> bool:
    invalid = [field for field in fields if not isinstance(payload.get(field), int) or isinstance(payload.get(field), bool)]
    if not invalid:
        return True
    summary['failed_step'] = step
    summary['error'] = 'INVALID_FIELD_TYPES'
    summary['invalid_fields'] = invalid
    return False
```

- [ ] Call it after create-world required fields for `['id', 'world_version']`.
- [ ] Call it after draft required fields for `['chapter_id', 'draft_version']`.
- [ ] Call it after approve required fields for `['approved_version']`.
- [ ] Rerun focused tests and confirm GREEN.

### Task 5: Verify and commit

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
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_create_world_id_and_world_version_to_be_int tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_draft_chapter_id_and_draft_version_to_be_int tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_approved_version_to_be_int -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest -q
cd /opt/WorldSim-Writer && git diff --check
cd /opt/WorldSim-Writer && git diff --cached --check
```
