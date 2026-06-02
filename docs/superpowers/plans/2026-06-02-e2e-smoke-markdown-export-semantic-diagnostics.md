# E2E Smoke Markdown Export Semantic Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Report well-formed but semantically invalid markdown export responses with a clear smoke diagnostic.

**Architecture:** Keep validation local to `backend/scripts/e2e_smoke.py`. After existing markdown export required-field and `files` shape checks, collect invalid archive evidence fields and fail the `markdown_export` step before the final `ok` gate.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing archive format/encoding regression

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_fails_when_markdown_export_archive_format_is_invalid` near existing markdown export tests.
- [ ] Mock the normal flow through events, then return:

```python
json_response({
    'archive_format': 'tar',
    'archive_encoding': 'plain',
    'archive_base64': 'UEs=',
    'files_are_inline': True,
    'files': [{'path': 'World.md', 'content': '# World'}],
})
```

- [ ] Assert:

```python
assert summary['ok'] is False
assert summary['failed_step'] == 'markdown_export'
assert summary['error'] == 'MARKDOWN_EXPORT_INVALID_ARCHIVE'
assert summary['invalid_fields'] == ['archive_format', 'archive_encoding']
```

- [ ] Run focused test and confirm RED.

### Task 2: Add failing missing World.md regression

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_fails_when_markdown_export_world_file_is_missing`.
- [ ] Return a valid archive response where `files` contains only `Characters.md`.
- [ ] Assert:

```python
assert summary['ok'] is False
assert summary['failed_step'] == 'markdown_export'
assert summary['error'] == 'MARKDOWN_EXPORT_INVALID_ARCHIVE'
assert summary['invalid_fields'] == ['files.World.md']
```

- [ ] Run focused test and confirm RED.

### Task 3: Add failing docs regression

**Files:**
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add `MARKDOWN_EXPORT_INVALID_ARCHIVE` and `files.World.md` to beta playbook required terms.
- [ ] Run focused docs test and confirm RED.

### Task 4: Implement semantic export diagnostics

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] After assigning `summary['checks']['markdown_export']`, add:

```python
invalid_export_fields = []
if export.get('archive_format') != 'zip':
    invalid_export_fields.append('archive_format')
if export.get('archive_encoding') != 'base64':
    invalid_export_fields.append('archive_encoding')
if export.get('files_are_inline') is not True:
    invalid_export_fields.append('files_are_inline')
if not export.get('archive_base64'):
    invalid_export_fields.append('archive_base64')
if not any(file.get('path') == 'World.md' for file in files):
    invalid_export_fields.append('files.World.md')
if invalid_export_fields:
    summary['failed_step'] = 'markdown_export'
    summary['error'] = 'MARKDOWN_EXPORT_INVALID_ARCHIVE'
    summary['invalid_fields'] = invalid_export_fields
    return summary
```

- [ ] Rerun focused smoke regressions and confirm GREEN.

### Task 5: Update beta playbook wording

**Files:**
- Modify: `BETA_TESTING.md`

- [ ] Extend markdown export pass criteria to mention `MARKDOWN_EXPORT_INVALID_ARCHIVE` and `invalid_fields`, including `files.World.md`.
- [ ] Rerun docs regression and confirm GREEN.

### Task 6: Verify and commit

**Files:**
- Backend/docs only; no frontend changes expected.

- [ ] Run focused markdown export semantic tests.
- [ ] Run all smoke script tests.
- [ ] Run docs regression tests.
- [ ] Run full backend tests.
- [ ] Run `git diff --check`.
- [ ] Stage intended files only; preserve `.hermes/plans/*` and `backend/worldsim-dev.db`.
- [ ] Run `git diff --cached --check`.
- [ ] Commit on the current feature branch.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest -q
cd /opt/WorldSim-Writer && git diff --check
cd /opt/WorldSim-Writer && git diff --cached --check
```