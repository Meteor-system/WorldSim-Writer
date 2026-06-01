# E2E Smoke Consistency Warning Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Preserve approval-consistency warning details in smoke JSON so blocked real-LLM smoke failures include actionable triage evidence.

**Architecture:** Reuse the existing approval-consistency smoke step and add a safe `warnings` list under `checks.approval_consistency`. Keep the final pass/fail gate based on the existing derived `blocked` boolean.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing smoke test for consistency warnings

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Extend `test_e2e_smoke_script_fails_when_approval_consistency_is_blocked` so the mocked approval-consistency response includes a warning object with `severity`, `category`, `object_type`, `object_id`, `change_index`, and `message`.
- [ ] Assert `summary['checks']['approval_consistency']['warnings']` equals that warning list.
- [ ] Run the focused test and confirm RED because the smoke summary currently drops `consistency_warnings`.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_fails_when_approval_consistency_is_blocked -q
```

Expected RED: `KeyError: 'warnings'` or equivalent missing-field assertion.

### Task 2: Store consistency warnings in smoke summary

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Read `consistency_warnings = consistency.get('consistency_warnings')`.
- [ ] Store `warnings: consistency_warnings if isinstance(consistency_warnings, list) else []` under `checks.approval_consistency`.
- [ ] Do not include request headers, bearer tokens, API keys, provider URLs, model names, or full request payloads.
- [ ] Do not change approval behavior or final `blocked` semantics.
- [ ] Rerun the focused test and confirm GREEN.

### Task 3: Document and verify

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add a docs assertion for `checks.approval_consistency.warnings`.
- [ ] Document that blocked consistency triage should inspect `checks.approval_consistency.warnings` for severity/category/message/object details.
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
