# E2E Smoke Runbook Payload Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add self-triaging runbook metadata to the smoke JSON so mock and real-LLM beta smoke failures are easier to fix and clean up.

**Architecture:** Keep `backend/scripts/e2e_smoke.py` as the only production-code touchpoint. Add small pure helpers for runbook metadata, cleanup command generation, and failure-to-next-action mapping, then call them from `run_smoke()` before returning. Update README and beta playbook text to describe the new JSON fields without changing API behavior.

**Tech Stack:** Python 3.13, httpx, pytest, FastAPI smoke script, Markdown docs.

---

## File Structure

- Modify `backend/scripts/e2e_smoke.py`: add helper functions and include `runbook`, dynamic `cleanup_command`, and `next_action` in summaries.
- Modify `backend/tests/test_e2e_scripts.py`: add focused regression tests using existing `SequencedTransport` style.
- Modify `README.md`: mention `runbook` and `next_action` in smoke instructions.
- Modify `BETA_TESTING.md`: document how testers should use `runbook`, `next_action`, and cleanup dry-run/confirm.

---

### Task 1: Add failing tests for runbook metadata and dynamic cleanup command

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`
- Test: `backend/tests/test_e2e_scripts.py`

- [ ] **Step 1: Add the failing test**

Append this test after `test_e2e_smoke_script_runs_api_flow_and_returns_json_summary`:

```python
def test_e2e_smoke_script_includes_runbook_metadata_and_dynamic_cleanup_command(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test/')
    monkeypatch.delenv('E2E_REAL_LLM', raising=False)
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            json_response({'chapter_id': 20, 'draft_id': 30, 'draft_version': 1}),
            json_response({'version_conflict': False, 'character_changes': [{'character_id': 1}], 'foreshadow_changes': []}),
            json_response({'ready': True, 'status': 'ready', 'blocking_reasons': [], 'warnings': []}),
            json_response({'consistency_summary': {'status': 'clear', 'blocking_count': 0}, 'consistency_warnings': []}),
            json_response({'id': 20, 'status': 'approved', 'approved_version': 2}),
            overview_response(),
            json_response({'items': [{'event_type': 'chapter_approved'}], 'summary': {'event_type_counts': {'chapter_approved': 1}}}),
            json_response({'archive_format': 'zip', 'archive_encoding': 'base64', 'archive_base64': 'UEs=', 'files_are_inline': True, 'files': [{'path': 'World.md', 'content': '# World'}]}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is True
    assert summary['runbook']['required_backend_env'] == ['LLM_MOCK=true']
    assert summary['runbook']['client_env'] == ['BASE_URL=https://worldsim.test', 'E2E_REAL_LLM unset or false']
    assert 'E2E_TIMEOUT_SECONDS=<seconds> for slow backends' in summary['runbook']['optional_client_env']
    assert summary['cleanup_command'] == f"cd {module.BACKEND_DIR} && PYTHONIOENCODING=utf-8 {module.sys.executable} scripts/cleanup_e2e_data.py --confirm"
    assert 'next_action' not in summary
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_includes_runbook_metadata_and_dynamic_cleanup_command -q
```

Expected: FAIL with `KeyError: 'runbook'` or missing dynamic cleanup fields.

---

### Task 2: Add failing tests for common next_action triage

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`
- Test: `backend/tests/test_e2e_scripts.py`

- [ ] **Step 1: Update existing mode mismatch tests**

Add these assertions to the existing mock/real mismatch tests:

```python
assert summary['next_action'] == 'Restart the backend with LLM_MOCK=true, then rerun mock smoke.'
```

inside `test_e2e_smoke_script_stops_when_mock_smoke_targets_real_llm_backend`, and:

```python
assert summary['runbook']['required_backend_env'] == ['LLM_MOCK=false', 'LLM_BASE_URL=<provider-url>', 'LLM_API_KEY=<secret>', 'LLM_MODEL=<model>']
assert summary['next_action'] == 'Restart the backend with real LLM_* settings and LLM_MOCK=false, then rerun with E2E_REAL_LLM=1.'
```

inside `test_e2e_smoke_script_stops_when_real_llm_smoke_targets_mock_backend`.

- [ ] **Step 2: Add a real-provider failure triage test**

Append this test near HTTP failure tests:

```python
def test_e2e_smoke_script_adds_next_action_for_real_llm_provider_auth_failure(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    monkeypatch.setenv('E2E_REAL_LLM', '1')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': False}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            httpx.Response(502, text='MODEL_AUTH_FAILED api_key=sk-secret LLM_BASE_URL=https://provider.example/v1'),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['mode'] == 'real-llm'
    assert summary['failed_step'] == 'draft'
    assert summary['response_body'] == 'MODEL_AUTH_FAILED api_key=[REDACTED_SECRET] LLM_BASE_URL=[REDACTED_URL]'
    assert summary['next_action'] == 'Check LLM_API_KEY permissions and provider access, restart the backend, then rerun real-LLM smoke.'
```

- [ ] **Step 3: Run tests to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_stops_when_mock_smoke_targets_real_llm_backend tests/test_e2e_scripts.py::test_e2e_smoke_script_stops_when_real_llm_smoke_targets_mock_backend tests/test_e2e_scripts.py::test_e2e_smoke_script_adds_next_action_for_real_llm_provider_auth_failure -q
```

Expected: FAIL because `next_action` and `runbook` do not exist yet.

---

### Task 3: Implement runbook and triage helpers

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`
- Test: `backend/tests/test_e2e_scripts.py`

- [ ] **Step 1: Add imports and constants**

Change the import block from:

```python
import json
import os
import re
```

to:

```python
import json
import os
import re
import shlex
import sys
```

Add after constants:

```python
BACKEND_DIR = Path(__file__).resolve().parents[1]
```

- [ ] **Step 2: Add helper functions**

Add after `_timeout_seconds()`:

```python
def _cleanup_command() -> str:
    return (
        f'cd {shlex.quote(str(BACKEND_DIR))} && '
        f'PYTHONIOENCODING=utf-8 {shlex.quote(sys.executable)} scripts/cleanup_e2e_data.py --confirm'
    )


def _runbook(mode: str, base_url: str) -> dict:
    if mode == 'real-llm':
        required_backend_env = ['LLM_MOCK=false', 'LLM_BASE_URL=<provider-url>', 'LLM_API_KEY=<secret>', 'LLM_MODEL=<model>']
        client_env = [f'BASE_URL={base_url}', 'E2E_REAL_LLM=1']
    else:
        required_backend_env = ['LLM_MOCK=true']
        client_env = [f'BASE_URL={base_url}', 'E2E_REAL_LLM unset or false']
    return {
        'required_backend_env': required_backend_env,
        'client_env': client_env,
        'optional_client_env': ['E2E_TIMEOUT_SECONDS=<seconds> for slow backends'],
        'cleanup': 'Run cleanup_command after smoke runs to remove e2e-* users and worlds.',
    }


def _next_action(summary: dict) -> str | None:
    error = summary.get('error')
    response_body = summary.get('response_body') or ''
    if error == 'BACKEND_LLM_MOCK_DISABLED':
        return 'Restart the backend with LLM_MOCK=true, then rerun mock smoke.'
    if error == 'BACKEND_LLM_MOCK_ENABLED':
        return 'Restart the backend with real LLM_* settings and LLM_MOCK=false, then rerun with E2E_REAL_LLM=1.'
    if error == 'MIGRATION_NOT_UP_TO_DATE':
        return 'Run alembic upgrade head from backend/, restart the backend, then rerun smoke.'
    if error == 'REQUEST_TIMEOUT':
        return 'Increase E2E_TIMEOUT_SECONDS for the smoke client or inspect backend/provider latency, then rerun smoke.'
    if 'MODEL_AUTH_FAILED' in response_body:
        return 'Check LLM_API_KEY permissions and provider access, restart the backend, then rerun real-LLM smoke.'
    if 'MODEL_RATE_LIMITED' in response_body:
        return 'Wait for provider quota or queue capacity, then rerun real-LLM smoke.'
    if summary.get('failed_step') == 'register':
        return 'Inspect register status_code/response_body; only explicit duplicate-email errors should fall back to login.'
    return None


def _finalize_summary(summary: dict) -> dict:
    action = _next_action(summary)
    if action:
        summary['next_action'] = action
    return summary
```

- [ ] **Step 3: Initialize summary with helpers**

In `run_smoke()`, replace hard-coded cleanup command with:

```python
        'cleanup_command': _cleanup_command(),
        'runbook': _runbook(mode, base_url),
```

- [ ] **Step 4: Finalize before every return**

For each `return summary` inside `run_smoke()`, return `_finalize_summary(summary)` instead. Leave the `finally` block unchanged.

In `main()`, after the `except` summary is built, add:

```python
    if 'runbook' not in summary:
        summary['runbook'] = _runbook(summary.get('mode', 'mock'), summary.get('base_url', _base_url()))
        summary['cleanup_command'] = _cleanup_command()
    summary = _finalize_summary(summary)
```

- [ ] **Step 5: Run focused tests to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_includes_runbook_metadata_and_dynamic_cleanup_command tests/test_e2e_scripts.py::test_e2e_smoke_script_stops_when_mock_smoke_targets_real_llm_backend tests/test_e2e_scripts.py::test_e2e_smoke_script_stops_when_real_llm_smoke_targets_mock_backend tests/test_e2e_scripts.py::test_e2e_smoke_script_adds_next_action_for_real_llm_provider_auth_failure -q
```

Expected: PASS.

---

### Task 4: Update run docs

**Files:**
- Modify: `README.md`
- Modify: `BETA_TESTING.md`

- [ ] **Step 1: Update README smoke paragraph**

Replace the real-LLM smoke paragraph with wording that says both modes print `runbook`, `cleanup_command`, and `next_action` when applicable.

- [ ] **Step 2: Update Beta playbook**

Add to smoke pass/fail criteria:

```markdown
- The JSON includes `runbook` with mode-specific backend/client environment hints and a `cleanup_command` for removing generated `e2e-*` data.
- On common failures, `next_action` gives the first safe triage step; follow it before rerunning smoke.
```

Clarify cleanup:

```markdown
Run without `--confirm` first for a dry-run summary; add `--confirm` only after the matched `e2e-*` accounts look correct.
```

---

### Task 5: Verify and commit

**Files:**
- Verify all modified files.

- [ ] **Step 1: Run related tests**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_e2e_scripts.py tests/test_e2e_cleanup.py -q
```

Expected: PASS.

- [ ] **Step 2: Run docs-safe diff check**

Run:

```bash
cd /opt/WorldSim-Writer && git diff --check
```

Expected: no output and exit 0.

- [ ] **Step 3: Commit only**

Run:

```bash
cd /opt/WorldSim-Writer && git status --short
git add backend/scripts/e2e_smoke.py backend/tests/test_e2e_scripts.py README.md BETA_TESTING.md docs/superpowers/specs/2026-06-09-e2e-smoke-runbook-payload-design.md docs/superpowers/plans/2026-06-09-e2e-smoke-runbook-payload.md
git diff --cached --check
git commit -m "feat: add smoke runbook diagnostics"
```

Expected: commit succeeds. Do not push or merge.
