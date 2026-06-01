# E2E Smoke Malformed Success Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Make smoke report malformed successful API responses with step-scoped diagnostics instead of raw Python exceptions.

**Architecture:** Add a tiny required-field validation helper in `backend/scripts/e2e_smoke.py` and call it before dereferencing fields needed by later smoke steps. Keep HTTP/request error handling unchanged.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing malformed draft response test

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_reports_missing_required_fields_for_success_response`.
- [ ] Mock health/register/create-world success, then return a draft JSON object missing `chapter_id` but containing `draft_version`.
- [ ] Assert the summary contains `ok: false`, `failed_step: "draft"`, `error: "MISSING_REQUIRED_FIELDS"`, and `missing_fields: ["chapter_id"]`.
- [ ] Assert no later API requests are made after the malformed draft response.
- [ ] Run the focused test and confirm RED because the script currently raises a raw missing-key error or lacks the stable diagnostics.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_reports_missing_required_fields_for_success_response -q
```

### Task 2: Implement required-field diagnostics

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Add `_require_fields(summary: dict, step: str, payload: dict, fields: list[str]) -> bool`.
- [ ] If any field is absent, set `summary['failed_step'] = step`, `summary['error'] = 'MISSING_REQUIRED_FIELDS'`, and `summary['missing_fields'] = missing`.
- [ ] Return `False` when fields are missing and `True` otherwise.
- [ ] Call the helper before reading `auth_payload['access_token']`, `world['id']`, `draft['chapter_id']`, and `draft['draft_version']`.
- [ ] Return the summary immediately when validation fails.
- [ ] Rerun the focused test and confirm GREEN.

### Task 3: Document and verify

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add docs terms for `MISSING_REQUIRED_FIELDS` and `missing_fields`.
- [ ] Document that a malformed 2xx API response uses these fields for triage.
- [ ] Run related tests and full backend tests.
- [ ] Run frontend tests/build because the user requested tests/build and no frontend changes are expected.
- [ ] Run `git diff --check` and `git diff --cached --check`.
- [ ] Commit intended files only.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py tests/test_event_docs.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest -q
cd /opt/WorldSim-Writer/frontend && npm run test -- --run
cd /opt/WorldSim-Writer/frontend && npm run build
cd /opt/WorldSim-Writer && git diff --check
```
