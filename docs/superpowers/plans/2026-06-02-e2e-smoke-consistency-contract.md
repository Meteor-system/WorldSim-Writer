# E2E Smoke Consistency Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Prevent smoke from approving drafts when approval consistency returns a malformed success response without `consistency_summary.status`.

**Architecture:** Add a nested required-path check in `backend/scripts/e2e_smoke.py` before consistency blocking is interpreted. Cover with smoke-script tests and beta playbook docs.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing consistency-contract test

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_requires_consistency_summary_status_before_approval`.
- [ ] Mock a complete flow through approval readiness.
- [ ] Return consistency payload `{'consistency_summary': {}, 'consistency_warnings': []}`.
- [ ] Assert `summary['ok'] is False`.
- [ ] Assert `summary['failed_step'] == 'approval_consistency'`.
- [ ] Assert `summary['error'] == 'MISSING_REQUIRED_FIELDS'`.
- [ ] Assert `summary['missing_fields'] == ['consistency_summary.status']`.
- [ ] Assert no approve/events/export requests happen.
- [ ] Run the focused test and confirm RED because the script currently approves after a malformed consistency response.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_consistency_summary_status_before_approval -q
```

### Task 2: Require consistency summary status

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] After the consistency response is received and before `consistency_summary = ...`, call `_require_paths(summary, 'approval_consistency', consistency, ['consistency_summary.status'])`.
- [ ] Return immediately if the path check fails.
- [ ] Rerun the focused consistency-contract test and confirm GREEN.
- [ ] Rerun all smoke-script tests.

### Task 3: Document beta consistency contract

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add `consistency_summary.status` to docs regression terms.
- [ ] Run the focused docs test and confirm RED if the playbook lacks the term.
- [ ] Update the consistency pass criterion to require `checks.approval_consistency.status` to be present and non-blocking.
- [ ] Rerun the focused docs test and confirm GREEN.

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
