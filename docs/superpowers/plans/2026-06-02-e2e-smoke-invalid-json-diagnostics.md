# E2E Smoke Invalid JSON Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Ensure successful HTTP responses with invalid JSON stop smoke with clear, redacted diagnostics.

**Architecture:** Refactor `_step_json(...)` in `backend/scripts/e2e_smoke.py` just enough to keep the `httpx.Response` object available while parsing JSON. Add a focused regression test in `backend/tests/test_e2e_scripts.py` and update beta playbook wording/docs tests for the new diagnostic code.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing invalid JSON smoke test

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_reports_invalid_json_response_body_for_success_response` near existing HTTP failure diagnostics tests.
- [ ] Use a successful flow through world creation, then return draft response:

```python
httpx.Response(
    200,
    text='not json api_key=sk-invalid-json LLM_BASE_URL=https://provider.example/v1 LLM_MODEL=secret-model',
)
```

- [ ] Assert:

```python
assert summary['ok'] is False
assert summary['failed_step'] == 'draft'
assert summary['error'] == 'INVALID_JSON_RESPONSE'
assert summary['status_code'] == 200
assert 'sk-invalid-json' not in summary['response_body']
assert 'https://provider.example/v1' not in summary['response_body']
assert 'secret-model' not in summary['response_body']
assert '[REDACTED_SECRET]' in summary['response_body']
assert '[REDACTED_URL]' in summary['response_body']
assert '[REDACTED_MODEL]' in summary['response_body']
```

- [ ] Run the focused test and confirm RED.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest \
  tests/test_e2e_scripts.py::test_e2e_smoke_script_reports_invalid_json_response_body_for_success_response -q
```

### Task 2: Add failing beta playbook docs test

**Files:**
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add `INVALID_JSON_RESPONSE` to the beta playbook required terms.
- [ ] Run the docs regression test and confirm RED until `BETA_TESTING.md` is updated.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py::test_beta_testing_playbook_documents_main_flow_smoke_and_reporting -q
```

### Task 3: Implement invalid JSON diagnostics

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Refactor `_step_json(...)` to call `request_call()` first, then `response.raise_for_status()`, then `response.json()`.
- [ ] Preserve existing `httpx.RequestError` and `httpx.HTTPStatusError` diagnostics.
- [ ] When `response.json()` raises, set:

```python
summary['failed_step'] = step
summary['error'] = 'INVALID_JSON_RESPONSE'
summary['status_code'] = response.status_code
summary['response_body'] = _response_body_snippet(response)
```

- [ ] Preserve the existing non-object response error behavior unless it needs the same response context during implementation.
- [ ] Rerun focused invalid JSON test and confirm GREEN.

### Task 4: Update beta playbook wording

**Files:**
- Modify: `BETA_TESTING.md`

- [ ] Mention `INVALID_JSON_RESPONSE` in the Real-LLM smoke diagnostics paragraph.
- [ ] Keep the secret-redaction wording intact.
- [ ] Run docs regression tests and confirm GREEN.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py -q
```

### Task 5: Verify and commit

**Files:**
- No frontend changes expected.

- [ ] Run focused invalid JSON test.
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