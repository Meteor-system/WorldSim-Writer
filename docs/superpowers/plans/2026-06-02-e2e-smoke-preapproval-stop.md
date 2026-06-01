# E2E Smoke Pre-Approval Stop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent.

**Goal:** Stop smoke before formal approval when pre-approval gates are blocked or no projection changes are proposed.

**Architecture:** Add early-return gate checks to `backend/scripts/e2e_smoke.py` after approval preview, readiness, and consistency diagnostics are recorded. Preserve existing JSON diagnostic shape and document the new stop behavior in the beta playbook.

**Tech Stack:** Python, httpx, pytest, Markdown docs.

---

### Task 1: Add failing preview-stop regression tests

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Update `test_e2e_smoke_script_fails_when_approval_preview_has_version_conflict` to assert the smoke stops after `/chapters/{chapter_id}/approval-preview` and reports `APPROVAL_PREVIEW_BLOCKED`.
- [ ] Update `test_e2e_smoke_script_fails_when_approval_preview_has_no_proposed_changes` to assert the smoke stops after `/chapters/{chapter_id}/approval-preview` and reports `NO_PROPOSED_PROJECTION_CHANGES`.
- [ ] Run both focused tests and confirm RED because the script currently continues to readiness/consistency/approve.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_fails_when_approval_preview_has_version_conflict tests/test_e2e_scripts.py::test_e2e_smoke_script_fails_when_approval_preview_has_no_proposed_changes -q
```

### Task 2: Stop after blocked approval preview

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] After recording `summary['checks']['approval_preview']`, return immediately with `failed_step: "approval_preview"` and `error: "APPROVAL_PREVIEW_BLOCKED"` when `preview_blocked` is true.
- [ ] Return immediately with `failed_step: "approval_preview"` and `error: "NO_PROPOSED_PROJECTION_CHANGES"` when `proposed_change_count == 0`.
- [ ] Rerun the focused preview tests and confirm GREEN.

### Task 3: Add failing readiness/consistency stop tests

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Update `test_e2e_smoke_script_fails_when_approval_readiness_is_blocked` to assert no consistency/approve/events/export requests occur and error is `APPROVAL_READINESS_BLOCKED`.
- [ ] Update `test_e2e_smoke_script_fails_when_approval_consistency_is_blocked` to assert no approve/events/export requests occur and error is `APPROVAL_CONSISTENCY_BLOCKED`.
- [ ] Ensure the fixtures include one proposed preview change so they reach readiness/consistency after the new preview gate.
- [ ] Run both focused tests and confirm RED.

Command:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_e2e_scripts.py::test_e2e_smoke_script_fails_when_approval_readiness_is_blocked tests/test_e2e_scripts.py::test_e2e_smoke_script_fails_when_approval_consistency_is_blocked -q
```

### Task 4: Stop after blocked readiness/consistency

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] After recording readiness diagnostics, return with `failed_step: "approval_readiness"` and `error: "APPROVAL_READINESS_BLOCKED"` when `readiness_blocked` is true.
- [ ] After recording consistency diagnostics, return with `failed_step: "approval_consistency"` and `error: "APPROVAL_CONSISTENCY_BLOCKED"` when `consistency_blocked` is true.
- [ ] Rerun the focused readiness/consistency tests and confirm GREEN.

### Task 5: Document beta diagnostics

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Add the new error codes to the docs regression terms.
- [ ] Run the focused docs test and confirm RED.
- [ ] Update `BETA_TESTING.md` to say blocked approval preview/readiness/consistency and zero proposed projection changes stop before formal approval.
- [ ] Rerun the focused docs test and confirm GREEN.

### Task 6: Verify and commit

**Files:**
- No frontend changes expected.

- [ ] Run `backend/tests/test_e2e_scripts.py`.
- [ ] Run `backend/tests/test_event_docs.py`.
- [ ] Run full backend tests unless the user already provided fresh full-suite evidence for this exact post-change state.
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
