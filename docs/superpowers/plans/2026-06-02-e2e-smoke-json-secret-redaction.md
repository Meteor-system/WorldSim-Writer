# E2E Smoke JSON Secret Redaction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Prevent smoke failure JSON from leaking JSON-shaped provider/request secrets.

**Architecture:** Keep redaction centralized in `backend/scripts/e2e_smoke.py` by extending the existing regex pattern list. Add focused tests in `backend/tests/test_e2e_scripts.py` and keep beta documentation aligned through `BETA_TESTING.md` plus `backend/tests/test_event_docs.py`.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing JSON-shaped redaction regression test

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_redacts_json_shaped_response_body_details` near the existing redaction test.
- [ ] Use a 502 draft response body containing JSON-shaped fields:

```python
sensitive_body = (
    '{"error":"MODEL_REQUEST_FAILED",'
    '"api_key":"sk-json-secret",'
    '"password":"json-pass",'
    '"llm_base_url":"https://provider.example/v1",'
    '"model":"secret-json-model",'
    '"messages":[{"role":"user","content":"secret JSON prompt"}]}'
)
```

- [ ] Assert the smoke summary fails at `draft` with `status_code == 502`.
- [ ] Assert the raw sensitive values are absent from `summary['response_body']`.
- [ ] Assert `[REDACTED_SECRET]`, `[REDACTED_URL]`, `[REDACTED_MODEL]`, and `[REDACTED_MESSAGES]` appear.
- [ ] Run the focused test and confirm RED because the current regexes do not catch all JSON-quoted forms.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_redacts_json_shaped_response_body_details -q
```

### Task 2: Implement minimal regex hardening

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Extend `_REDACTION_PATTERNS` with JSON-quoted alternatives for API key, password, LLM/base URL, model, and messages fields.
- [ ] Preserve existing plain-text redaction behavior.
- [ ] Keep `_response_body_snippet()` redacting before truncation.
- [ ] Rerun the focused test and confirm GREEN.
- [ ] Rerun the existing plain-text redaction test to confirm no regression.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_redacts_json_shaped_response_body_details -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_redacts_sensitive_response_body_details -q
```

### Task 3: Update beta diagnostics docs

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add a docs regression term such as `JSON-shaped` so the playbook continues to document this safety expectation.
- [ ] Run the focused docs test and confirm RED if the playbook lacks that term.
- [ ] Update the real-LLM diagnostics paragraph to say redaction covers JSON-shaped echoed provider/request fields.
- [ ] Rerun the focused docs test and confirm GREEN.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py::test_beta_testing_playbook_documents_main_flow_smoke_and_reporting -q
```

### Task 4: Verify and commit

**Files:**
- No frontend changes expected.

- [ ] Run `backend/tests/test_e2e_scripts.py`.
- [ ] Run `backend/tests/test_event_docs.py`.
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