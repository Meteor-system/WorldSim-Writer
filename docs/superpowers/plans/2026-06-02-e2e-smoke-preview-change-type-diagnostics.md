# E2E Smoke Preview Change Type Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Stop smoke runs with a clear diagnostic when approval preview change collections are present but not lists of objects.

**Architecture:** Reuse the smoke script's existing `_require_list_of_dicts(...)` helper for approval preview `character_changes` and `foreshadow_changes` before computing proposed-change counts. Add focused tests and update beta playbook docs.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing approval-preview collection type tests

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_requires_preview_character_changes_to_be_list_of_objects` near the existing approval preview tests.
- [ ] Use the normal successful pre-approval setup, but return preview payload:

```python
{'version_conflict': False, 'character_changes': {'character_id': 1}, 'foreshadow_changes': []}
```

- [ ] Assert the smoke stops at `approval_preview` with `error == 'INVALID_FIELD_TYPES'` and `invalid_fields == ['character_changes']`.
- [ ] Assert the request path list stops after `/chapters/20/approval-preview`.
- [ ] Add `test_e2e_smoke_script_requires_preview_foreshadow_changes_to_be_list_of_objects` with preview payload:

```python
{'version_conflict': False, 'character_changes': [], 'foreshadow_changes': 'foreshadow-1'}
```

- [ ] Assert `invalid_fields == ['foreshadow_changes']` and the smoke stops after approval preview.
- [ ] Run both tests and confirm RED because the current smoke script counts malformed collections instead of diagnosing them.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest \
  tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_preview_character_changes_to_be_list_of_objects \
  tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_preview_foreshadow_changes_to_be_list_of_objects -q
```

### Task 2: Implement preview collection validation

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] After fetching `preview` and before computing `preview_blocked` or collection counts, call:

```python
if not _require_list_of_dicts(summary, 'approval_preview', preview, 'character_changes'):
    return summary
if not _require_list_of_dicts(summary, 'approval_preview', preview, 'foreshadow_changes'):
    return summary
```

- [ ] Keep the existing version conflict and no-proposed-change gates unchanged.
- [ ] Rerun the focused tests and confirm GREEN.
- [ ] Rerun the existing approval preview conflict/no-change tests to confirm no regression.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest \
  tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_preview_character_changes_to_be_list_of_objects \
  tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_preview_foreshadow_changes_to_be_list_of_objects -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest \
  tests/test_e2e_scripts.py::test_e2e_smoke_script_fails_when_approval_preview_has_version_conflict \
  tests/test_e2e_scripts.py::test_e2e_smoke_script_fails_when_approval_preview_has_no_proposed_changes -q
```

### Task 3: Update beta playbook wording

**Files:**
- Modify: `BETA_TESTING.md`

- [ ] Update the `INVALID_FIELD_TYPES` sentence to mention approval preview proposed-change collections as well as event/export collections.
- [ ] Run `backend/tests/test_event_docs.py` to confirm existing docs regression still passes.

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