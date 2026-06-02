# E2E Smoke Consistency Status Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject malformed approval-consistency `consistency_summary.status` values before smoke proceeds to formal approval.

**Architecture:** Add a focused status-value validator to the smoke script for nested string paths. Reuse existing malformed-field diagnostics for type errors and add a clear invalid-value diagnostic for unsupported status strings, then document allowed consistency statuses in beta guidance.

**Tech Stack:** Python, httpx, pytest, Markdown.

---

## File map

- Modify `backend/tests/test_e2e_scripts.py` — add RED regressions for non-string and unsupported `consistency_summary.status`.
- Modify `backend/scripts/e2e_smoke.py` — validate consistency status type and allowed values before deriving `checks.approval_consistency.blocked`.
- Modify `BETA_TESTING.md` — document allowed consistency summary statuses and invalid-value diagnostics.
- Modify `backend/tests/test_event_docs.py` — require new beta playbook terms.
- Create `docs/superpowers/specs/2026-06-02-e2e-smoke-consistency-status-contract-design.md` — design record.
- Create `docs/superpowers/plans/2026-06-02-e2e-smoke-consistency-status-contract.md` — this implementation plan.

### Task 1: Add failing consistency status regressions

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add this test after `test_e2e_smoke_script_requires_consistency_summary_status_before_approval`:

```python
def test_e2e_smoke_script_requires_consistency_summary_status_to_be_string(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            json_response({'chapter_id': 20, 'draft_id': 30, 'draft_version': 1}),
            json_response({'version_conflict': False, 'character_changes': [{'character_id': 1}], 'foreshadow_changes': []}),
            json_response({'ready': True, 'status': 'ready', 'blocking_reasons': [], 'warnings': []}),
            json_response({'consistency_summary': {'status': 7, 'blocking_count': 0}, 'consistency_warnings': []}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['failed_step'] == 'approval_consistency'
    assert summary['error'] == 'INVALID_FIELD_TYPES'
    assert summary['invalid_fields'] == ['consistency_summary.status']
    assert [request.url.path for request in transport.requests] == [
        '/health',
        '/auth/register',
        '/worlds/from-template',
        '/worlds/10/chapters/draft',
        '/chapters/20/approval-preview',
        '/chapters/20/approval-readiness',
        '/chapters/20/approval-consistency',
    ]
```

- [ ] Add this test immediately after it:

```python
def test_e2e_smoke_script_requires_consistency_summary_status_to_be_known(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            json_response({'chapter_id': 20, 'draft_id': 30, 'draft_version': 1}),
            json_response({'version_conflict': False, 'character_changes': [{'character_id': 1}], 'foreshadow_changes': []}),
            json_response({'ready': True, 'status': 'ready', 'blocking_reasons': [], 'warnings': []}),
            json_response({'consistency_summary': {'status': 'unknown', 'blocking_count': 0}, 'consistency_warnings': []}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['failed_step'] == 'approval_consistency'
    assert summary['error'] == 'INVALID_FIELD_VALUES'
    assert summary['invalid_fields'] == ['consistency_summary.status']
    assert summary['allowed_values'] == {'consistency_summary.status': ['blocked', 'clear', 'needs_review']}
    assert [request.url.path for request in transport.requests] == [
        '/health',
        '/auth/register',
        '/worlds/from-template',
        '/worlds/10/chapters/draft',
        '/chapters/20/approval-preview',
        '/chapters/20/approval-readiness',
        '/chapters/20/approval-consistency',
    ]
```

- [ ] Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_consistency_summary_status_to_be_string tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_consistency_summary_status_to_be_known -q
```

Expected RED: both tests fail because the current smoke script does not validate consistency status type/value.

### Task 2: Implement consistency status validation

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Add helper near `_require_int_path`:

```python
def _require_string_path_in(summary: dict, step: str, payload: dict, path: str, allowed_values: set[str]) -> bool:
    current = payload
    for part in path.split('.'):
        if not isinstance(current, dict) or part not in current:
            summary['failed_step'] = step
            summary['error'] = 'MISSING_REQUIRED_FIELDS'
            summary['missing_fields'] = [path]
            return False
        current = current[part]
    if not isinstance(current, str) or not current:
        summary['failed_step'] = step
        summary['error'] = 'INVALID_FIELD_TYPES'
        summary['invalid_fields'] = [path]
        return False
    if current not in allowed_values:
        summary['failed_step'] = step
        summary['error'] = 'INVALID_FIELD_VALUES'
        summary['invalid_fields'] = [path]
        summary['allowed_values'] = {path: sorted(allowed_values)}
        return False
    return True
```

- [ ] Add module-level allowed values near constants:

```python
CONSISTENCY_STATUSES = {'clear', 'needs_review', 'blocked'}
```

- [ ] In the approval-consistency block, after `_require_paths(... ['consistency_summary.status'])`, call:

```python
if not _require_string_path_in(summary, 'approval_consistency', consistency, 'consistency_summary.status', CONSISTENCY_STATUSES):
    return summary
```

- [ ] Run focused tests again:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_consistency_summary_status_to_be_string tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_consistency_summary_status_to_be_known -q
```

Expected GREEN.

### Task 3: Document status-value diagnostics

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Update the approval-consistency pass criterion to say:

```markdown
- `checks.approval_consistency.status` from `consistency_summary.status` is one of `clear`, `needs_review`, or `blocked`, and `checks.approval_consistency.blocked` is `false`; if it is `true`, the smoke stops before formal approval with `error: "APPROVAL_CONSISTENCY_BLOCKED"`, so inspect `checks.approval_consistency.warnings` for severity/category/message/object details, adjust the proposed changes or regenerate the draft, and rerun smoke.
```

- [ ] In the real-LLM diagnostic paragraph, after the `INVALID_FIELD_TYPES` sentence, add that `INVALID_FIELD_VALUES` means a present field had an unsupported value and `allowed_values` lists accepted values such as `consistency_summary.status`.

- [ ] Add these terms to `required_terms` in `backend/tests/test_event_docs.py`:

```python
'clear',
'needs_review',
'blocked',
'INVALID_FIELD_VALUES',
'allowed_values',
```

- [ ] Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py -q
```

Expected GREEN.

### Task 4: Verify and commit

**Files:**
- Backend smoke script, smoke tests, beta docs, docs coverage test, and this task's spec/plan docs only.

- [ ] Run focused consistency-status tests.
- [ ] Run smoke-script tests.
- [ ] Run docs coverage.
- [ ] Run full backend tests if time permits.
- [ ] Run `git diff --check`.
- [ ] Stage intended files only; preserve unrelated untracked files.
- [ ] Run `git diff --cached --check`.
- [ ] Commit on the current branch without pushing or merging.
