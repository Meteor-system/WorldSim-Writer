# E2E Smoke Request Error Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Preserve `failed_step` diagnostics when smoke requests fail before an HTTP response exists.

**Architecture:** Convert the smoke step helper from accepting an already-created `httpx.Response` to accepting a zero-argument request callable. The helper executes the request, parses JSON responses, and records either HTTP response failures or request-level failures in the existing summary.

**Tech Stack:** Python, httpx, pytest.

---

### Task 1: Add failing request-error regression

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add a transport that raises `httpx.ConnectError`.
- [ ] Add a test asserting `run_smoke()` returns structured diagnostics for the `health` step.
- [ ] Run the focused test and confirm RED.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_returns_step_context_for_request_error -q
```

Expected RED: `httpx.ConnectError` escapes or the summary lacks `failed_step: "health"`.

### Task 2: Implement callable-based step helper

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Change `_step_json(summary, step, response)` to `_step_json(summary, step, request_call)`.
- [ ] Execute `response = request_call()` inside the helper.
- [ ] Catch `httpx.RequestError` separately and record `failed_step` plus `error` only.
- [ ] Update all call sites to pass `lambda: client.get(...)` or `lambda: client.post(...)`.
- [ ] Keep all existing HTTP response diagnostics unchanged.

### Task 3: Verify and commit

**Files:**
- Modified code/test/docs only.

- [ ] Run focused request-error test.
- [ ] Run all smoke script tests.
- [ ] Run docs tests.
- [ ] Run `git diff --check` and `git diff --cached --check` before commit.
- [ ] Commit relevant files only.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py tests/test_event_docs.py -q
cd /opt/WorldSim-Writer && git diff --check
```
