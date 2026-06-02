# E2E Smoke Preview Conflict Type Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject malformed approval-preview `version_conflict` values before smoke proceeds to readiness, consistency, or formal approval.

**Architecture:** Add small validation in the existing approval-preview smoke block. Reuse existing diagnostic helpers and update beta documentation to make the boolean pre-approval contract explicit.

**Tech Stack:** Python, httpx, pytest, Markdown.

---

## File map

- Modify `backend/tests/test_e2e_scripts.py` — add RED regressions for missing and malformed `approval_preview.version_conflict`.
- Modify `backend/scripts/e2e_smoke.py` — require `version_conflict` and validate it is a JSON boolean before deriving `checks.approval_preview.blocked`.
- Modify `BETA_TESTING.md` — document `checks.approval_preview.version_conflict` as a boolean.
- Modify `backend/tests/test_event_docs.py` — require the new beta playbook terms.
- Create `docs/superpowers/specs/2026-06-02-e2e-smoke-preview-conflict-type-contract-design.md` — design record.
- Create `docs/superpowers/plans/2026-06-02-e2e-smoke-preview-conflict-type-contract.md` — this implementation plan.

### Task 1: Add failing preview conflict regressions

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add this test near the approval-preview smoke tests, after `test_e2e_smoke_script_fails_when_approval_preview_has_version_conflict`:

```python
def test_e2e_smoke_script_requires_preview_version_conflict_before_approval(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            json_response({'chapter_id': 20, 'draft_id': 30, 'draft_version': 1}),
            json_response({'character_changes': [{'character_id': 1}], 'foreshadow_changes': []}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['failed_step'] == 'approval_preview'
    assert summary['error'] == 'MISSING_REQUIRED_FIELDS'
    assert summary['missing_fields'] == ['version_conflict']
    assert [request.url.path for request in transport.requests] == [
        '/health',
        '/auth/register',
        '/worlds/from-template',
        '/worlds/10/chapters/draft',
        '/chapters/20/approval-preview',
    ]
```

- [ ] Add this test immediately after it:

```python
def test_e2e_smoke_script_requires_preview_version_conflict_to_be_boolean(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            json_response({'chapter_id': 20, 'draft_id': 30, 'draft_version': 1}),
            json_response({'version_conflict': 'false', 'character_changes': [{'character_id': 1}], 'foreshadow_changes': []}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['failed_step'] == 'approval_preview'
    assert summary['error'] == 'INVALID_FIELD_TYPES'
    assert summary['invalid_fields'] == ['version_conflict']
    assert [request.url.path for request in transport.requests] == [
        '/health',
        '/auth/register',
        '/worlds/from-template',
        '/worlds/10/chapters/draft',
        '/chapters/20/approval-preview',
    ]
```

- [ ] Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_preview_version_conflict_before_approval tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_preview_version_conflict_to_be_boolean -q
```

Expected RED: both tests fail because the current smoke script accepts absent/string `version_conflict` and proceeds past approval preview.

### Task 2: Implement preview conflict validation

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] In the approval-preview block, before proposed-change collection validation, add:

```python
if not _require_fields(summary, 'approval_preview', preview, ['version_conflict']):
    return summary
if not _require_bool_fields(summary, 'approval_preview', preview, ['version_conflict']):
    return summary
```

- [ ] Keep existing proposed-change validation and `preview_blocked = preview.get('version_conflict') is True` unchanged after this new type check.

- [ ] Run the focused tests again:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_preview_version_conflict_before_approval tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_preview_version_conflict_to_be_boolean -q
```

Expected GREEN.

### Task 3: Document beta preview conflict evidence

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Update the mock smoke approval-preview bullet to mention the direct boolean:

```markdown
- `checks.approval_preview.version_conflict` is a boolean and `checks.approval_preview.blocked` is `false`; if it is `true`, the smoke stops before formal approval with `failed_step: "approval_preview"` and `error: "APPROVAL_PREVIEW_BLOCKED"`, so regenerate the draft against the current world version and rerun smoke.
```

- [ ] Update the real-LLM diagnostic paragraph's `INVALID_FIELD_TYPES` examples to include `approval preview version-conflict booleans`.

- [ ] Add these terms to `required_terms` in `backend/tests/test_event_docs.py`:

```python
'checks.approval_preview.version_conflict',
'approval preview version-conflict booleans',
```

- [ ] Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py -q
```

Expected GREEN.

### Task 4: Verify and commit

**Files:**
- Backend smoke script, smoke tests, beta docs, docs coverage test, and this task's spec/plan docs only.

- [ ] Run focused preview-conflict tests:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_preview_version_conflict_before_approval tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_preview_version_conflict_to_be_boolean -q
```

- [ ] Run smoke-script tests:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py -q
```

- [ ] Run docs coverage:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py -q
```

- [ ] Run full backend tests if time permits:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest -q
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
git commit -m "fix: validate smoke preview conflict flag"
```
