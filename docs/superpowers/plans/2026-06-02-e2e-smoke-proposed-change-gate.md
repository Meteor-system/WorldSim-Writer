# E2E Smoke Proposed Change Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Make smoke fail when a draft has zero visible proposed projection changes in approval preview.

**Architecture:** Extend the existing approval-preview smoke summary with `proposed_change_count` and include it in the final smoke `ok` gate. Document the new beta pass criterion.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing zero-proposed-change smoke test

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add `test_e2e_smoke_script_fails_when_approval_preview_has_no_proposed_changes`.
- [ ] Mock a complete otherwise-successful smoke flow.
- [ ] Return approval preview with `version_conflict: False`, `character_changes: []`, and `foreshadow_changes: []`.
- [ ] Assert `summary['ok'] is False`.
- [ ] Assert `summary['checks']['approval_preview']['proposed_change_count'] == 0`.
- [ ] Run the focused test and confirm RED because the summary currently lacks `proposed_change_count` and final `ok` does not require proposed changes.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_fails_when_approval_preview_has_no_proposed_changes -q
```

### Task 2: Gate smoke on proposed change count

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] In approval preview handling, calculate `character_change_count`, `foreshadow_change_count`, and `proposed_change_count`.
- [ ] Store all three counts in `summary['checks']['approval_preview']`.
- [ ] Include `proposed_change_count > 0` in the final `summary['ok']` gate.
- [ ] Update the existing successful smoke-flow fixture to include one proposed character change so it remains a valid happy path.
- [ ] Rerun the focused test and confirm GREEN.
- [ ] Rerun all smoke script tests and fix any fixtures whose expected successful path now needs a proposed change.

### Task 3: Document beta pass criterion

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add `checks.approval_preview.proposed_change_count` to the beta playbook docs regression terms.
- [ ] Run the focused docs test and confirm RED.
- [ ] Add a mock smoke pass-criteria bullet requiring `checks.approval_preview.proposed_change_count` to be greater than zero.
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
