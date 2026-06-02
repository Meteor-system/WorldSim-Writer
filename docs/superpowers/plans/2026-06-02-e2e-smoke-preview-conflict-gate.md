# E2E Smoke Approval Preview Conflict Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Make approval-preview version conflicts an explicit smoke gate with documented beta triage guidance.

**Architecture:** Reuse the existing approval-preview smoke step and add a derived `blocked` boolean under `checks.approval_preview`. Keep final pass/fail behavior equivalent while making the reason visible in the JSON summary.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing preview-conflict smoke test

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add a test where approval preview returns `version_conflict: true`.
- [ ] Keep later readiness/consistency/approve/events/export responses successful to prove final `ok` depends on preview conflict.
- [ ] Assert `summary['ok'] is False`, `checks.approval_preview.version_conflict is True`, and `checks.approval_preview.blocked is True`.
- [ ] Run the focused test and confirm RED because `blocked` is currently missing.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_fails_when_approval_preview_has_version_conflict -q
```

Expected RED: missing test before creation, then `KeyError: 'blocked'` after the test is added.

### Task 2: Implement explicit preview conflict gate

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Compute `preview_blocked = preview.get('version_conflict') is True` after approval preview.
- [ ] Store `blocked: preview_blocked` under `checks.approval_preview`.
- [ ] Change final `summary.ok` from `preview.get('version_conflict') is False` to `not preview_blocked`.
- [ ] Do not change approval, readiness, or consistency behavior.
- [ ] Rerun the focused test and confirm GREEN.

### Task 3: Document and verify

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add a docs assertion for `checks.approval_preview.blocked`.
- [ ] Document the smoke pass criterion and recovery action: regenerate the draft against the current world version.
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
