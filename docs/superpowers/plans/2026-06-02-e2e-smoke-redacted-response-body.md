# E2E Smoke Redacted Response Body Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Redact sensitive real-LLM/provider details from smoke HTTP failure `response_body` snippets while preserving useful diagnostics.

**Architecture:** Keep smoke diagnostics local to `backend/scripts/e2e_smoke.py`. Add regex-based redaction inside `_response_body_snippet()` before truncating to `MAX_RESPONSE_BODY_CHARS`.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing response-body redaction test

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_redacts_sensitive_response_body_details` near the existing HTTP failure test.
- [ ] Use an HTTP 502 draft response body containing:
  - `Authorization: Bearer secret-token`
  - `api_key=sk-test-secret`
  - `password=secretpass`
  - `LLM_BASE_URL=https://provider.example/v1`
  - `LLM_MODEL=secret-model`
  - `messages=[{'role':'user','content':'secret prompt'}]`
- [ ] Assert `summary['failed_step'] == 'draft'` and `summary['status_code'] == 502`.
- [ ] Assert sensitive values are absent from `summary['response_body']`.
- [ ] Assert redaction placeholders such as `[REDACTED_SECRET]`, `[REDACTED_URL]`, `[REDACTED_MODEL]`, and `[REDACTED_MESSAGES]` are present.
- [ ] Run the focused test and confirm RED because the current script only truncates response text.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_redacts_sensitive_response_body_details -q
```

### Task 2: Implement response-body redaction

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Add `import re` near the existing imports.
- [ ] Add helper `_redact_response_body(text: str) -> str` near `_response_body_snippet()`.
- [ ] Redact common sensitive patterns before truncation:

```python
_REDACTION_PATTERNS = [
    (re.compile(r'Authorization\s*:\s*Bearer\s+[^\s,;]+', re.IGNORECASE), 'Authorization: Bearer [REDACTED_SECRET]'),
    (re.compile(r'((?:api[_-]?key|llm_api_key|openai_api_key)\s*[=:]\s*)[^\s,;&}]+', re.IGNORECASE), r'\1[REDACTED_SECRET]'),
    (re.compile(r'((?:password)\s*[=:]\s*)[^\s,;&}]+', re.IGNORECASE), r'\1[REDACTED_SECRET]'),
    (re.compile(r'((?:llm_base_url|base_url)\s*[=:]\s*)https?://[^\s,;&}]+', re.IGNORECASE), r'\1[REDACTED_URL]'),
    (re.compile(r'https?://[^\s,;&}]+', re.IGNORECASE), '[REDACTED_URL]'),
    (re.compile(r'((?:llm_model|model)\s*[=:]\s*)[^\s,;&}]+', re.IGNORECASE), r'\1[REDACTED_MODEL]'),
    (re.compile(r'messages\s*[=:]\s*\[[\s\S]*', re.IGNORECASE), 'messages=[REDACTED_MESSAGES]'),
]
```

- [ ] Update `_response_body_snippet()` to return `_redact_response_body(response.text)[:MAX_RESPONSE_BODY_CHARS]`.
- [ ] Rerun the focused test and confirm GREEN.
- [ ] Rerun the existing HTTP failure test to confirm non-secret diagnostics remain useful.

### Task 3: Document redacted response-body diagnostics

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add docs regression terms:
  - `redacted`
  - `REDACTED_SECRET`
- [ ] Run the focused docs test and confirm RED if the playbook lacks the new terms.
- [ ] Update the real-LLM diagnostics paragraph to say `response_body` is a short redacted snippet and that placeholders such as `[REDACTED_SECRET]` mean sensitive provider/request details were removed.
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
- [ ] Commit intended files only.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest -q
cd /opt/WorldSim-Writer && git diff --check
cd /opt/WorldSim-Writer && git diff --cached --check
```
