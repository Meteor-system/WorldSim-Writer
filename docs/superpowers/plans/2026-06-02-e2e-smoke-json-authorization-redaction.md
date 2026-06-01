# E2E Smoke JSON Authorization Redaction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Prevent smoke `response_body` diagnostics from exposing JSON-shaped bearer authorization fields.

**Architecture:** Keep redaction centralized in `backend/scripts/e2e_smoke.py` by extending `_REDACTION_PATTERNS`. Cover behavior with focused smoke-script tests and document the diagnostic contract in `BETA_TESTING.md`.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing JSON authorization redaction regression

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_redacts_json_authorization_response_body_details` near existing redaction tests.
- [ ] Return a 502 draft response body containing JSON-shaped authorization fields:

```python
sensitive_body = (
    '{"error":"MODEL_REQUEST_FAILED",'
    '"authorization":"Bearer json-secret-token",'
    '"Authorization":"Bearer second-json-secret"}'
)
```

- [ ] Assert the smoke fails at `draft`, includes `status_code == 502`, removes both raw tokens, and includes `[REDACTED_SECRET]`.
- [ ] Run the focused test and confirm RED.

### Task 2: Implement minimal redaction fix

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Add a JSON authorization regex to `_REDACTION_PATTERNS` near the existing plaintext authorization rule:

```python
(re.compile(r'("authorization"\s*:\s*"Bearer\s+)[^"]+(")', re.IGNORECASE), r'\1[REDACTED_SECRET]\2')
```

- [ ] Use the final implementation form that preserves valid JSON string boundaries and redacts only the token value.
- [ ] Rerun the focused test and confirm GREEN.

### Task 3: Update beta diagnostics docs

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add `Authorization` / bearer-header redaction wording to the real-LLM diagnostic paragraph.
- [ ] Add required docs terms for the new wording.
- [ ] Run the focused docs test and confirm RED before the playbook edit, then GREEN after the playbook edit.

### Task 4: Verify and commit

**Files:**
- Backend smoke script/tests/docs only; no frontend changes expected.

- [ ] Run focused JSON authorization redaction test.
- [ ] Run all smoke script tests.
- [ ] Run docs regression tests.
- [ ] Run full backend tests.
- [ ] Run `git diff --check`.
- [ ] Stage intended files only; preserve `.hermes/plans/*` and `backend/worldsim-dev.db`.
- [ ] Run `git diff --cached --check`.
- [ ] Commit on the current feature branch.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_redacts_json_authorization_response_body_details -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest -q
cd /opt/WorldSim-Writer && git diff --check
cd /opt/WorldSim-Writer && git diff --cached --check
```
