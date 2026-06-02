# E2E Smoke Readiness Response Shape Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Ensure malformed approval-readiness success responses stop smoke with clear diagnostics before formal approval.

**Architecture:** Add minimal list-shape validation to `backend/scripts/e2e_smoke.py`, reuse existing missing-field diagnostics for readiness status, and add focused regression tests in `backend/tests/test_e2e_scripts.py`. Update beta playbook wording so testers can distinguish malformed readiness response shapes from legitimate readiness blockers.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing readiness response-shape tests

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_requires_readiness_status_before_approval` near existing approval readiness tests.
- [ ] Use a successful flow through approval preview, then return readiness payload:

```python
{'ready': True, 'blocking_reasons': [], 'warnings': []}
```

- [ ] Assert smoke stops at `approval_readiness` with `error == 'MISSING_REQUIRED_FIELDS'` and `missing_fields == ['status']`.
- [ ] Add `test_e2e_smoke_script_requires_readiness_blocking_reasons_to_be_list` with readiness payload:

```python
{'ready': False, 'status': 'blocked', 'blocking_reasons': 'version conflict', 'warnings': []}
```

- [ ] Assert smoke stops at `approval_readiness` with `error == 'INVALID_FIELD_TYPES'` and `invalid_fields == ['blocking_reasons']`.
- [ ] Add `test_e2e_smoke_script_requires_readiness_warnings_to_be_list` with readiness payload:

```python
{'ready': True, 'status': 'ready', 'blocking_reasons': [], 'warnings': 'warning text'}
```

- [ ] Assert `invalid_fields == ['warnings']` and the request path list stops after `/chapters/20/approval-readiness`.
- [ ] Run all three focused tests and confirm RED.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest \
  tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_readiness_status_before_approval \
  tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_readiness_blocking_reasons_to_be_list \
  tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_readiness_warnings_to_be_list -q
```

### Task 2: Implement readiness response-shape validation

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Add a small helper:

```python
def _require_list(summary: dict, step: str, payload: dict, field: str) -> bool:
    value = payload.get(field)
    if isinstance(value, list):
        return True
    summary['failed_step'] = step
    summary['error'] = 'INVALID_FIELD_TYPES'
    summary['invalid_fields'] = [field]
    return False
```

- [ ] After loading `readiness`, require `status`:

```python
if not _require_fields(summary, 'approval_readiness', readiness, ['status']):
    return summary
```

- [ ] Validate list fields before using them:

```python
if not _require_list(summary, 'approval_readiness', readiness, 'blocking_reasons'):
    return summary
if not _require_list(summary, 'approval_readiness', readiness, 'warnings'):
    return summary
```

- [ ] Keep existing readiness blocker logic after validation.
- [ ] Rerun focused tests and confirm GREEN.
- [ ] Rerun the existing blocked-readiness test to confirm no regression.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest \
  tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_readiness_status_before_approval \
  tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_readiness_blocking_reasons_to_be_list \
  tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_readiness_warnings_to_be_list -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_fails_when_approval_readiness_is_blocked -q
```

### Task 3: Update beta playbook wording

**Files:**
- Modify: `BETA_TESTING.md`

- [ ] Update the `INVALID_FIELD_TYPES` explanation to include approval readiness reason/warning lists.
- [ ] Run docs regression tests.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py -q
```

### Task 4: Verify and commit

**Files:**
- No frontend changes expected.

- [ ] Run all smoke script tests.
- [ ] Run docs regression tests.
- [ ] Run full backend tests.
- [ ] Skip frontend tests/build unless frontend files changed; state that no frontend files changed.
- [ ] Run `git diff --check` and `git diff --cached --check`.
- [ ] Commit intended files only; do not stage `.hermes/plans/*` or `backend/worldsim-dev.db`.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest -q
cd /opt/WorldSim-Writer && git diff --check
cd /opt/WorldSim-Writer && git diff --cached --check
```