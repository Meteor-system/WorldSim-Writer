# E2E Smoke Approve Status Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Report missing approval `status` as an explicit malformed success response instead of only ending with `ok: false`.

**Architecture:** Extend the approval required-field check in `backend/scripts/e2e_smoke.py`; add focused smoke-script coverage and a beta playbook pass criterion.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing approval-status diagnostic test

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_requires_approval_status_after_approval`.
- [ ] Mock a complete flow through pre-approval checks.
- [ ] Return approval payload `{'id': 20, 'approved_version': 2}` with no `status`.
- [ ] Assert `summary['ok'] is False`.
- [ ] Assert `summary['failed_step'] == 'approve'`.
- [ ] Assert `summary['error'] == 'MISSING_REQUIRED_FIELDS'`.
- [ ] Assert `summary['missing_fields'] == ['status']`.
- [ ] Assert no events or markdown export requests happen.
- [ ] Run the focused test and confirm RED because the script currently only requires `approved_version`.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_requires_approval_status_after_approval -q
```

### Task 2: Require approval status

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Change the approval required-field check to require `['status', 'approved_version']`.
- [ ] Rerun the focused approval-status test and confirm GREEN.
- [ ] Rerun all smoke-script tests.

### Task 3: Document beta pass criterion

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add `checks.approve.status` and `approved_version` to docs regression terms.
- [ ] Run the focused docs test and confirm RED if the playbook lacks either term.
- [ ] Update the mock-smoke pass criteria to require `checks.approve.status` is `approved` and preserve the existing world-version increment criterion.
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
