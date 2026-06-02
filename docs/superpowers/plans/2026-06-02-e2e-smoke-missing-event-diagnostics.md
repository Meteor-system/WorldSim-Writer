# E2E Smoke Missing Event Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Make the smoke script report a specific error when approved chapters are missing from the event log.

**Architecture:** Keep the change inside `backend/scripts/e2e_smoke.py`. After the existing event list shape checks and `chapter_approved_seen` calculation, add one explicit business-invariant guard that sets `failed_step`/`error` and returns before markdown export.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Tighten failing smoke regression

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Update `test_e2e_smoke_script_fails_when_expected_event_is_missing` to expect the smoke summary to stop at the event step:

```python
assert summary['failed_step'] == 'events'
assert summary['error'] == 'CHAPTER_APPROVED_EVENT_MISSING'
assert [request.url.path for request in transport.requests] == [
    '/health',
    '/auth/register',
    '/worlds/from-template',
    '/worlds/10/chapters/draft',
    '/chapters/20/approval-preview',
    '/chapters/20/approval-readiness',
    '/chapters/20/approval-consistency',
    '/chapters/20/approve',
    '/worlds/10/events',
]
```

- [ ] Run the focused test and confirm RED:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_fails_when_expected_event_is_missing -q
```

### Task 2: Add failing docs regression

**Files:**
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add `CHAPTER_APPROVED_EVENT_MISSING` and `checks.events.chapter_approved_seen` to the beta playbook required terms.
- [ ] Run the focused docs test and confirm RED:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py::test_beta_testing_playbook_documents_main_flow_smoke_and_reporting -q
```

### Task 3: Implement missing-event diagnostic

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] After assigning `summary['checks']['events']`, add:

```python
if not chapter_approved_seen:
    summary['failed_step'] = 'events'
    summary['error'] = 'CHAPTER_APPROVED_EVENT_MISSING'
    return summary
```

- [ ] Rerun the focused smoke regression and confirm GREEN.

### Task 4: Update beta playbook wording

**Files:**
- Modify: `BETA_TESTING.md`

- [ ] Extend the mock smoke pass criteria for `checks.events.chapter_approved_seen` to mention `CHAPTER_APPROVED_EVENT_MISSING`.
- [ ] Rerun docs regression and confirm GREEN.

### Task 5: Verify and commit

**Files:**
- Backend/docs only; no frontend changes expected.

- [ ] Run focused missing-event smoke test.
- [ ] Run all smoke script tests.
- [ ] Run docs regression tests.
- [ ] Run full backend tests.
- [ ] Run `git diff --check`.
- [ ] Stage intended files only; preserve `.hermes/plans/*` and `backend/worldsim-dev.db`.
- [ ] Run `git diff --cached --check`.
- [ ] Commit on the current feature branch.

Commands:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_event_docs.py -q
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest -q
cd /opt/WorldSim-Writer && git diff --check
cd /opt/WorldSim-Writer && git diff --cached --check
```