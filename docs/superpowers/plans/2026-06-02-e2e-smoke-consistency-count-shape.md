# E2E Smoke Consistency Count Shape Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Ensure malformed approval-consistency blocker counts stop smoke with clear diagnostics before formal approval.

**Architecture:** Add a small nested integer validation helper to `backend/scripts/e2e_smoke.py`, use it for `consistency_summary.blocking_count`, add focused smoke-script regression tests, and update beta playbook wording so testers can interpret malformed consistency blocker-count diagnostics.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing consistency blocker-count tests

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_requires_consistency_blocking_count_before_approval` near existing approval consistency tests.
- [ ] Use a successful flow through approval readiness, then return approval consistency payload:

```python
{'consistency_summary': {'status': 'clear'}, 'consistency_warnings': []}
```

- [ ] Assert smoke stops at `approval_consistency` with `error == 'MISSING_REQUIRED_FIELDS'` and `missing_fields == ['consistency_summary.blocking_count']`.
- [ ] Add `test_e2e_smoke_script_requires_consistency_blocking_count_to_be_int` with approval consistency payload:

```python
{'consistency_summary': {'status': 'clear', 'blocking_count': '0'}, 'consistency_warnings': []}
```

- [ ] Assert smoke stops at `approval_consistency` with `error == 'INVALID_FIELD_TYPES'` and `invalid_fields == ['consistency_summary.blocking_count']` instead of raising a Python exception.
- [ ] Run both focused tests and confirm RED.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest \
  tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_consistency_blocking_count_before_approval \
  tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_consistency_blocking_count_to_be_int -q
```

### Task 2: Add failing beta playbook docs test

**Files:**
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add `approval consistency blocker counts` to the beta playbook required terms.
- [ ] Run the docs regression test and confirm RED until `BETA_TESTING.md` is updated.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py::test_beta_testing_playbook_documents_main_flow_smoke_and_reporting -q
```

### Task 3: Implement consistency blocker-count validation

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Add a helper for nested integer fields:

```python
def _require_int_path(summary: dict, step: str, payload: dict, path: str) -> bool:
    current = payload
    for part in path.split('.'):
        if not isinstance(current, dict) or part not in current:
            summary['failed_step'] = step
            summary['error'] = 'MISSING_REQUIRED_FIELDS'
            summary['missing_fields'] = [path]
            return False
        current = current[part]
    if isinstance(current, int) and not isinstance(current, bool):
        return True
    summary['failed_step'] = step
    summary['error'] = 'INVALID_FIELD_TYPES'
    summary['invalid_fields'] = [path]
    return False
```

- [ ] After requiring `consistency_summary.status`, require `consistency_summary.blocking_count` as an integer:

```python
if not _require_int_path(summary, 'approval_consistency', consistency, 'consistency_summary.blocking_count'):
    return summary
```

- [ ] Keep existing blocked-consistency behavior after validation.
- [ ] Rerun focused smoke tests and confirm GREEN.
- [ ] Rerun the existing blocked-consistency test to confirm no regression.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest \
  tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_consistency_blocking_count_before_approval \
  tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_consistency_blocking_count_to_be_int -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_fails_when_approval_consistency_is_blocked -q
```

### Task 4: Update beta playbook wording

**Files:**
- Modify: `BETA_TESTING.md`

- [ ] Update the `INVALID_FIELD_TYPES` explanation to include approval consistency blocker counts.
- [ ] Run docs regression tests and confirm GREEN.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py -q
```

### Task 5: Verify and commit

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