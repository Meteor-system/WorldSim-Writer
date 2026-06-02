# E2E Smoke Consistency Warning Shape Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Ensure malformed approval-consistency warning collections stop smoke with clear diagnostics before formal approval.

**Architecture:** Add minimal response-shape validation to `backend/scripts/e2e_smoke.py` using existing required-field and list-of-dicts helpers. Add focused regression tests in `backend/tests/test_e2e_scripts.py` and update beta playbook wording so testers can distinguish malformed consistency warning collections from legitimate consistency blockers.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing consistency warning shape tests

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_requires_consistency_warnings_before_approval` near existing approval consistency tests.
- [ ] Use a successful flow through approval readiness, then return approval consistency payload:

```python
{'consistency_summary': {'status': 'clear'}}
```

- [ ] Assert smoke stops at `approval_consistency` with `error == 'MISSING_REQUIRED_FIELDS'` and `missing_fields == ['consistency_warnings']`.
- [ ] Add `test_e2e_smoke_script_requires_consistency_warnings_to_be_list_of_objects` with approval consistency payload:

```python
{'consistency_summary': {'status': 'clear'}, 'consistency_warnings': 'warning text'}
```

- [ ] Assert smoke stops at `approval_consistency` with `error == 'INVALID_FIELD_TYPES'` and `invalid_fields == ['consistency_warnings']`.
- [ ] Run both focused tests and confirm RED.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest \
  tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_consistency_warnings_before_approval \
  tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_consistency_warnings_to_be_list_of_objects -q
```

### Task 2: Add failing beta playbook docs test

**Files:**
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add `approval consistency warning lists` to the beta playbook required terms.
- [ ] Run the docs regression test and confirm RED until `BETA_TESTING.md` is updated.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py::test_beta_testing_playbook_documents_main_flow_smoke_and_reporting -q
```

### Task 3: Implement consistency warning validation

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] After requiring `consistency_summary.status`, require `consistency_warnings`:

```python
if not _require_fields(summary, 'approval_consistency', consistency, ['consistency_warnings']):
    return summary
```

- [ ] Validate the warning collection before using it:

```python
if not _require_list_of_dicts(summary, 'approval_consistency', consistency, 'consistency_warnings'):
    return summary
```

- [ ] Replace the old fallback assignment with the validated list:

```python
consistency_warnings = consistency.get('consistency_warnings') or []
```

- [ ] Rerun focused smoke tests and confirm GREEN.
- [ ] Rerun the existing blocked-consistency test to confirm no regression.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest \
  tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_consistency_warnings_before_approval \
  tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_consistency_warnings_to_be_list_of_objects -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_fails_when_approval_consistency_is_blocked -q
```

### Task 4: Update beta playbook wording

**Files:**
- Modify: `BETA_TESTING.md`

- [ ] Update the `INVALID_FIELD_TYPES` explanation to include approval consistency warning lists.
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
- [ ] Run relevant backend tests; run full backend tests if the targeted suite is green and time allows.
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