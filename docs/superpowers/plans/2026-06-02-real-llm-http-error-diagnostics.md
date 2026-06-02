# Real LLM HTTP Error Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Classify common upstream real-LLM HTTP failures into safe, actionable API details for smoke triage.

**Architecture:** Keep provider status inspection inside `backend/app/llm/client.py`, then allowlist safe `MODEL_*` runtime details at service boundaries. Do not expose arbitrary exception text.

**Tech Stack:** Python, httpx, FastAPI, pytest, Markdown docs.

---

### Task 1: Add failing LLM client classification tests

**Files:**
- Modify: `backend/tests/test_llm_client.py`

- [ ] Add `test_llm_client_reports_auth_failure_for_unauthorized_provider_response` using a fake `httpx.post` that returns `httpx.Response(401, request=...)`.
- [ ] Assert `LLMClient(settings).generate_chapter(...)` raises `RuntimeError` matching `MODEL_AUTH_FAILED`.
- [ ] Add `test_llm_client_reports_rate_limit_for_provider_429_response` using `httpx.Response(429, request=...)`.
- [ ] Assert it raises `RuntimeError` matching `MODEL_RATE_LIMITED`.
- [ ] Run both tests and confirm RED.

### Task 2: Add failing API boundary tests

**Files:**
- Modify: `backend/tests/test_narrative_approval.py`

- [ ] Add a fake LLM client that raises `RuntimeError('MODEL_AUTH_FAILED')`.
- [ ] Add `test_create_draft_preserves_safe_model_runtime_error_detail` and assert draft creation returns HTTP 502 with `detail == 'MODEL_AUTH_FAILED'`.
- [ ] Add a fake LLM client that raises `RuntimeError('provider secret text')`.
- [ ] Add `test_create_draft_masks_unknown_model_runtime_error_detail` and assert draft creation returns HTTP 502 with `detail == 'MODEL_REQUEST_FAILED'`.
- [ ] Run both tests and confirm RED for the safe pass-through case.

### Task 3: Add failing docs regression

**Files:**
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add `MODEL_AUTH_FAILED` and `MODEL_RATE_LIMITED` to the Beta playbook required terms.
- [ ] Run the focused docs regression and confirm RED.

### Task 4: Implement minimal diagnostics

**Files:**
- Modify: `backend/app/llm/client.py`
- Modify: `backend/app/narrative/service.py`
- Modify: `backend/app/world/story_arc.py`

- [ ] In `LLMClient._post_json()`, catch `httpx.HTTPStatusError` before generic `httpx.HTTPError`.
- [ ] Raise `RuntimeError('MODEL_AUTH_FAILED')` for status 401 or 403.
- [ ] Raise `RuntimeError('MODEL_RATE_LIMITED')` for status 429.
- [ ] Raise `RuntimeError('MODEL_REQUEST_FAILED')` for other HTTP statuses.
- [ ] Add a small allowlist helper or constant in each service module so `_map_model_error()` passes through only `MODEL_REQUEST_FAILED`, `MODEL_AUTH_FAILED`, and `MODEL_RATE_LIMITED` for `RuntimeError`.
- [ ] Keep unknown runtime messages masked as `MODEL_REQUEST_FAILED`.
- [ ] Rerun focused LLM and narrative tests and confirm GREEN.

### Task 5: Update Beta playbook wording

**Files:**
- Modify: `BETA_TESTING.md`

- [ ] Add one concise sentence in the real-LLM diagnostics paragraph explaining `MODEL_AUTH_FAILED` and `MODEL_RATE_LIMITED`.
- [ ] Rerun focused docs regression and confirm GREEN.

### Task 6: Verify and commit

**Files:**
- Backend and minimal docs only; no frontend changes expected.

- [ ] Run focused new tests.
- [ ] Run `tests/test_llm_client.py`, `tests/test_narrative_approval.py`, and `tests/test_event_docs.py`.
- [ ] Run full backend pytest.
- [ ] Run `git diff --check`.
- [ ] Stage intended files only; preserve `.hermes/plans/*` and `backend/worldsim-dev.db`.
- [ ] Run `git diff --cached --check`.
- [ ] Commit on the current feature branch.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_llm_client.py::test_llm_client_reports_auth_failure_for_unauthorized_provider_response tests/test_llm_client.py::test_llm_client_reports_rate_limit_for_provider_429_response -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_narrative_approval.py::test_create_draft_preserves_safe_model_runtime_error_detail tests/test_narrative_approval.py::test_create_draft_masks_unknown_model_runtime_error_detail -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py::test_beta_testing_playbook_documents_main_flow_smoke_and_reporting -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_llm_client.py tests/test_narrative_approval.py tests/test_event_docs.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest -q
cd /opt/WorldSim-Writer && git diff --check
cd /opt/WorldSim-Writer && git diff --cached --check
```
