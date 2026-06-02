# E2E Smoke Collection Type Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Return structured smoke diagnostics when successful API responses contain collection fields with invalid types.

**Architecture:** Add one small validation helper to the existing smoke script and call it before iterating response collections. Preserve the existing `MISSING_REQUIRED_FIELDS` behavior for absent keys, and add `INVALID_FIELD_TYPES` only for present fields whose shape is unsafe to iterate.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing event-items type test

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_requires_event_items_to_be_list_of_objects`.
- [ ] Mock a successful flow through approval.
- [ ] Return events payload `{'items': {'event_type': 'chapter_approved'}}`.
- [ ] Assert `summary['ok'] is False`.
- [ ] Assert `summary['failed_step'] == 'events'`.
- [ ] Assert `summary['error'] == 'INVALID_FIELD_TYPES'`.
- [ ] Assert `summary['invalid_fields'] == ['items']`.
- [ ] Assert no markdown export request happens.
- [ ] Run the focused test and confirm RED because the script currently tries to iterate invalid event items.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_event_items_to_be_list_of_objects -q
```

### Task 2: Add failing markdown files type test

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_requires_markdown_export_files_to_be_list_of_objects`.
- [ ] Mock a successful flow through events.
- [ ] Return markdown export payload with required fields but `files` as a string.
- [ ] Assert `summary['ok'] is False`.
- [ ] Assert `summary['failed_step'] == 'markdown_export'`.
- [ ] Assert `summary['error'] == 'INVALID_FIELD_TYPES'`.
- [ ] Assert `summary['invalid_fields'] == ['files']`.
- [ ] Run the focused test and confirm RED because the script currently tries to iterate invalid file entries.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_markdown_export_files_to_be_list_of_objects -q
```

### Task 3: Implement collection type diagnostics

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Add helper near `_require_paths`:

```python
def _require_list_of_dicts(summary: dict, step: str, payload: dict, field: str) -> bool:
    value = payload.get(field)
    if isinstance(value, list) and all(isinstance(item, dict) for item in value):
        return True
    summary['failed_step'] = step
    summary['error'] = 'INVALID_FIELD_TYPES'
    summary['invalid_fields'] = [field]
    return False
```

- [ ] After events required-field validation, call `_require_list_of_dicts(summary, 'events', events, 'items')` and return if false.
- [ ] After markdown export required-field validation, call `_require_list_of_dicts(summary, 'markdown_export', export, 'files')` and return if false.
- [ ] Rerun the two focused tests and confirm GREEN.
- [ ] Rerun all smoke-script tests.

### Task 4: Document invalid field type diagnostics

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add docs regression terms:
  - `INVALID_FIELD_TYPES`
  - `invalid_fields`
- [ ] Run the focused docs test and confirm RED if the playbook lacks the new terms.
- [ ] Update the real-LLM diagnostics paragraph to explain that `INVALID_FIELD_TYPES` means a successful response had required fields with unsafe types.
- [ ] Rerun the focused docs test and confirm GREEN.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py::test_beta_testing_playbook_documents_main_flow_smoke_and_reporting -q
```

### Task 5: Verify and commit

**Files:**
- No frontend changes expected.

- [ ] Run `backend/tests/test_e2e_scripts.py`.
- [ ] Run `backend/tests/test_event_docs.py`.
- [ ] Run full backend tests.
- [ ] Skip frontend tests/build unless frontend files changed; state that no frontend files changed.
- [ ] Run `git diff --check` and `git diff --cached --check`.
- [ ] Commit intended files only.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest -q
cd /opt/WorldSim-Writer && git diff --check
cd /opt/WorldSim-Writer && git diff --cached --check
```
