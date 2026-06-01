# E2E Smoke Failure Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Preserve structured, safe failure details in `scripts/e2e_smoke.py` summaries.

**Architecture:** Add small smoke-script helpers for step-scoped JSON requests and HTTP error serialization. Keep the flow sequential and success criteria unchanged.

**Tech Stack:** Python, httpx, pytest.

---

### Task 1: Add failing regression test

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add a test where `/worlds/{world_id}/chapters/draft` returns HTTP 502 with body `MODEL_REQUEST_FAILED`.
- [ ] Run the focused test and confirm it fails because the summary lacks structured failure context.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_returns_step_context_for_http_failure -q
```

Expected RED: assertion failure or raised HTTPStatusError showing structured diagnostics are not yet implemented.

### Task 2: Implement smoke diagnostics

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Add a bounded response text helper.
- [ ] Add a step-scoped request helper that stores `failed_step`, `error`, `status_code`, and `response_body` in the summary before re-raising.
- [ ] Replace direct `_json_response(client...)` calls in `run_smoke()` with the step helper.
- [ ] Keep success criteria unchanged.

### Task 3: Verify and commit

**Files:**
- Modified code/test/docs only.

- [ ] Run focused e2e script tests.
- [ ] Run relevant backend tests.
- [ ] Run `git diff --check`.
- [ ] Commit relevant files only.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py tests/test_event_docs.py -q
cd /opt/WorldSim-Writer && git diff --check
```
