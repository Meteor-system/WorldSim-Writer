# E2E Smoke Readiness Ready Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject malformed approval-readiness `ready` fields before smoke proceeds to formal approval.

**Architecture:** Add small smoke-script validation around the existing approval-readiness gate. Reuse existing `MISSING_REQUIRED_FIELDS` and `INVALID_FIELD_TYPES` diagnostics, then document the direct readiness boolean in the beta playbook.

**Tech Stack:** Python, httpx, pytest, Markdown.

---

## File map

- Modify `backend/tests/test_e2e_scripts.py` — add RED regression tests for missing and malformed `approval_readiness.ready`.
- Modify `backend/scripts/e2e_smoke.py` — require `ready` and validate it is a JSON boolean before recording readiness checks.
- Modify `BETA_TESTING.md` — document `checks.approval_readiness.ready` and the malformed readiness diagnostic.
- Modify `backend/tests/test_event_docs.py` — require the new beta playbook terms.
- Create `docs/superpowers/specs/2026-06-02-e2e-smoke-readiness-ready-contract-design.md` — design record.
- Create `docs/superpowers/plans/2026-06-02-e2e-smoke-readiness-ready-contract.md` — this implementation plan.

### Task 1: Add failing readiness ready regressions

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add this test near the approval-readiness response-shape tests, before `test_e2e_smoke_script_requires_readiness_blocking_reasons_to_be_list`:

```python
def test_e2e_smoke_script_requires_readiness_ready_before_approval(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            json_response({'chapter_id': 20, 'draft_id': 30, 'draft_version': 1}),
            json_response({'version_conflict': False, 'character_changes': [{'character_id': 1}], 'foreshadow_changes': []}),
            json_response({'status': 'ready', 'blocking_reasons': [], 'warnings': []}),
            json_response({'consistency_summary': {'status': 'clear', 'blocking_count': 0}, 'consistency_warnings': []}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['failed_step'] == 'approval_readiness'
    assert summary['error'] == 'MISSING_REQUIRED_FIELDS'
    assert summary['missing_fields'] == ['ready']
    assert [request.url.path for request in transport.requests] == [
        '/health',
        '/auth/register',
        '/worlds/from-template',
        '/worlds/10/chapters/draft',
        '/chapters/20/approval-preview',
        '/chapters/20/approval-readiness',
    ]
```

- [ ] Add this test immediately after it:

```python
def test_e2e_smoke_script_requires_readiness_ready_to_be_boolean(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            json_response({'chapter_id': 20, 'draft_id': 30, 'draft_version': 1}),
            json_response({'version_conflict': False, 'character_changes': [{'character_id': 1}], 'foreshadow_changes': []}),
            json_response({'ready': 'true', 'status': 'ready', 'blocking_reasons': [], 'warnings': []}),
            json_response({'consistency_summary': {'status': 'clear', 'blocking_count': 0}, 'consistency_warnings': []}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['failed_step'] == 'approval_readiness'
    assert summary['error'] == 'INVALID_FIELD_TYPES'
    assert summary['invalid_fields'] == ['ready']
    assert [request.url.path for request in transport.requests] == [
        '/health',
        '/auth/register',
        '/worlds/from-template',
        '/worlds/10/chapters/draft',
        '/chapters/20/approval-preview',
        '/chapters/20/approval-readiness',
    ]
```

- [ ] Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_readiness_ready_before_approval tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_readiness_ready_to_be_boolean -q
```

Expected RED: both tests fail because the current smoke script proceeds to approval-consistency.

### Task 2: Implement readiness ready validation

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] In the approval-readiness block, after requiring `status` and before list validation, add:

```python
if not _require_fields(summary, 'approval_readiness', readiness, ['ready', 'status']):
    return summary
if not _require_bool_fields(summary, 'approval_readiness', readiness, ['ready']):
    return summary
```

- [ ] Add a helper near `_require_int_fields`:

```python
def _require_bool_fields(summary: dict, step: str, payload: dict, fields: list[str]) -> bool:
    invalid = [field for field in fields if not isinstance(payload.get(field), bool)]
    if not invalid:
        return True
    summary['failed_step'] = step
    summary['error'] = 'INVALID_FIELD_TYPES'
    summary['invalid_fields'] = invalid
    return False
```

- [ ] Keep the existing summary assignment for `ready`:

```python
'ready': readiness.get('ready'),
```

- [ ] Run the focused tests again:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_readiness_ready_before_approval tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_readiness_ready_to_be_boolean -q
```

Expected GREEN.

### Task 3: Document beta readiness evidence

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Update the mock smoke approval-readiness bullet to mention the direct boolean:

```markdown
- `checks.approval_readiness.ready` is a boolean and `checks.approval_readiness.blocked` is `false`; if `blocked` is `true`, the smoke stops before formal approval with `error: "APPROVAL_READINESS_BLOCKED"`, so review `checks.approval_readiness.blocking_reasons`, regenerate or repair the draft as instructed, and rerun smoke.
```

- [ ] Update the real-LLM diagnostic paragraph's `INVALID_FIELD_TYPES` examples to include `approval readiness ready booleans`.

- [ ] Add these terms to `required_terms` in `backend/tests/test_event_docs.py`:

```python
'checks.approval_readiness.ready',
'approval readiness ready booleans',
```

- [ ] Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py -q
```

Expected GREEN.

### Task 4: Verify and commit

**Files:**
- Backend smoke script, smoke tests, beta docs, docs coverage test, and this task's spec/plan docs only.

- [ ] Run focused readiness-ready tests:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_readiness_ready_before_approval tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_readiness_ready_to_be_boolean -q
```

- [ ] Run smoke-script tests:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py -q
```

- [ ] Run docs coverage:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py -q
```

- [ ] Run relevant backend tests around approval readiness:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_narrative_approval.py tests/test_story_bible_management.py -q
```

- [ ] Run whitespace check:

```bash
cd /opt/WorldSim-Writer && git diff --check
```

- [ ] Stage intended files only, preserving old untracked `.hermes/plans/*` and `backend/worldsim-dev.db`.

- [ ] Run staged whitespace check:

```bash
cd /opt/WorldSim-Writer && git diff --cached --check
```

- [ ] Commit on the current branch without pushing or merging:

```bash
git commit -m "fix: validate smoke readiness ready flag"
```
