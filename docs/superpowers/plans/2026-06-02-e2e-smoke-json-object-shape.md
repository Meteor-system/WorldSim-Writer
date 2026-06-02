# E2E Smoke JSON Object Shape Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Report successful non-object JSON smoke responses with a specific redacted diagnostic.

**Architecture:** Keep the change inside `_step_json(...)` in `backend/scripts/e2e_smoke.py`. Treat a parsed non-dict JSON payload as a response-level shape error and return a structured failure summary before downstream field validators run.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing smoke regression

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_reports_non_object_json_response_body_for_success_response` near the invalid JSON diagnostics tests.
- [ ] Arrange a normal smoke flow through world creation, then return this draft response:

```python
httpx.Response(
    200,
    json=[
        'not an object',
        {'api_key': 'sk-array-secret', 'llm_base_url': 'https://provider.example/v1', 'model': 'secret-array-model'},
    ],
)
```

- [ ] Assert:

```python
assert summary['ok'] is False
assert summary['failed_step'] == 'draft'
assert summary['error'] == 'INVALID_JSON_RESPONSE_TYPE'
assert summary['status_code'] == 200
assert 'sk-array-secret' not in summary['response_body']
assert 'https://provider.example/v1' not in summary['response_body']
assert 'secret-array-model' not in summary['response_body']
assert '[REDACTED_SECRET]' in summary['response_body']
assert '[REDACTED_URL]' in summary['response_body']
assert '[REDACTED_MODEL]' in summary['response_body']
```

- [ ] Run the focused test and confirm RED:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_reports_non_object_json_response_body_for_success_response -q
```

### Task 2: Add failing docs regression

**Files:**
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add `INVALID_JSON_RESPONSE_TYPE` and `non-object JSON` to the beta playbook required terms.
- [ ] Run the focused docs test and confirm RED:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py::test_beta_testing_playbook_documents_main_flow_smoke_and_reporting -q
```

### Task 3: Implement diagnostic branch

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Replace the generic non-dict branch in `_step_json(...)` with:

```python
if not isinstance(payload, dict):
    summary['failed_step'] = step
    summary['error'] = 'INVALID_JSON_RESPONSE_TYPE'
    summary['status_code'] = response.status_code
    summary['response_body'] = _response_body_snippet(response)
    return {}
```

- [ ] Rerun the focused smoke regression and confirm GREEN.

### Task 4: Update beta playbook wording

**Files:**
- Modify: `BETA_TESTING.md`

- [ ] Extend the Real-LLM smoke diagnostics paragraph to mention `INVALID_JSON_RESPONSE_TYPE` for successful non-object JSON responses.
- [ ] Keep secret-redaction wording intact.
- [ ] Rerun docs regression tests and confirm GREEN.

### Task 5: Verify and commit

**Files:**
- Backend/docs only; no frontend changes expected.

- [ ] Run focused non-object JSON smoke test.
- [ ] Run all smoke script tests.
- [ ] Run docs regression tests.
- [ ] Run full backend tests.
- [ ] Run `git diff --check`.
- [ ] Stage intended files only; do not stage `.hermes/plans/*` or `backend/worldsim-dev.db`.
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