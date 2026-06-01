# E2E Smoke Approval Result Stop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Stop smoke after a malformed or unsuccessful approval result so later event/export checks do not obscure the approval failure.

**Architecture:** Keep the existing single-file smoke script flow. Add approval result checks immediately after `checks.approve` is populated, using explicit error codes for non-approved status and non-incrementing world version.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing approval-status hard-stop test

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_stops_when_approval_status_is_not_approved`.
- [ ] Mock a complete flow through approval consistency.
- [ ] Return approval payload `{'id': 20, 'status': 'rejected', 'approved_version': 2}`.
- [ ] Assert `summary['ok'] is False`.
- [ ] Assert `summary['checks']['approve']['status'] == 'rejected'`.
- [ ] Assert `summary['failed_step'] == 'approve'`.
- [ ] Assert `summary['error'] == 'APPROVAL_STATUS_NOT_APPROVED'`.
- [ ] Assert no events or markdown export requests happen.
- [ ] Run the focused test and confirm RED because the script currently continues after the rejected approval status.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_stops_when_approval_status_is_not_approved -q
```

### Task 2: Add failing world-version hard-stop assertion

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Update `test_e2e_smoke_script_fails_when_approval_does_not_increment_world_version`.
- [ ] Keep its approval payload as `{'id': 20, 'status': 'approved', 'approved_version': 1}`.
- [ ] Assert `summary['failed_step'] == 'approve'`.
- [ ] Assert `summary['error'] == 'WORLD_VERSION_NOT_INCREMENTED'`.
- [ ] Assert no events or markdown export requests happen.
- [ ] Run the focused test and confirm RED because the script currently continues after a non-incrementing approval version.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_fails_when_approval_does_not_increment_world_version -q
```

### Task 3: Implement approval result hard stops

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] After `summary['checks']['approve'] = {...}`, add:

```python
        if approved.get('status') != 'approved':
            summary['failed_step'] = 'approve'
            summary['error'] = 'APPROVAL_STATUS_NOT_APPROVED'
            return summary
        if not world_version_incremented:
            summary['failed_step'] = 'approve'
            summary['error'] = 'WORLD_VERSION_NOT_INCREMENTED'
            return summary
```

- [ ] Rerun both focused tests and confirm GREEN.
- [ ] Rerun all smoke-script tests.

### Task 4: Document beta approval result diagnostics

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add docs regression terms:
  - `APPROVAL_STATUS_NOT_APPROVED`
  - `WORLD_VERSION_NOT_INCREMENTED`
- [ ] Run the focused docs test and confirm RED if the playbook lacks the new terms.
- [ ] Update the approval pass criteria in `BETA_TESTING.md` to mention the two approval-result errors and that they stop before later checks.
- [ ] Rerun the focused docs test and confirm GREEN.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py::test_beta_testing_playbook_documents_main_flow_smoke_and_reporting -q
```

### Task 5: Verify and commit

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
