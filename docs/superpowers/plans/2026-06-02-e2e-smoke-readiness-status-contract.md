# E2E Smoke Readiness Status Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject malformed approval-readiness `status` values before smoke proceeds to consistency checks or formal approval.

**Architecture:** Reuse the smoke script's existing allowed-value validator for string fields. Add a readiness-specific allowed-value constant and call it after requiring `ready`/`status`, before deriving the blocked flag.

**Tech Stack:** Python, httpx, pytest, Markdown.

---

## File map

- Modify `backend/tests/test_e2e_scripts.py` — add RED regressions for non-string and unsupported `approval_readiness.status`.
- Modify `backend/scripts/e2e_smoke.py` — validate readiness status type and allowed values before continuing.
- Modify `BETA_TESTING.md` — document allowed readiness statuses and invalid-value diagnostics.
- Modify `backend/tests/test_event_docs.py` — require the new beta playbook terms.
- Create `docs/superpowers/specs/2026-06-02-e2e-smoke-readiness-status-contract-design.md` — design record.
- Create `docs/superpowers/plans/2026-06-02-e2e-smoke-readiness-status-contract.md` — this implementation plan.

### Task 1: Add failing readiness status regressions

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add a test where readiness returns `status: 7` and assert the smoke stops at `approval_readiness` with `INVALID_FIELD_TYPES` and `invalid_fields == ['status']`.
- [ ] Add a test where readiness returns `status: 'unknown'` and assert the smoke stops at `approval_readiness` with `INVALID_FIELD_VALUES`, `invalid_fields == ['status']`, and `allowed_values == {'status': ['blocked', 'needs_review', 'ready']}`.
- [ ] Run the two focused tests and verify RED because the current smoke script does not validate readiness status type/value.

### Task 2: Implement readiness status validation

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Add `READINESS_STATUSES = {'ready', 'needs_review', 'blocked'}` near existing constants.
- [ ] In the approval-readiness block, after validating `ready` as a boolean, call `_require_string_path_in(summary, 'approval_readiness', readiness, 'status', READINESS_STATUSES)`.
- [ ] Run focused tests and verify GREEN.

### Task 3: Document status-value diagnostics

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Update the approval-readiness pass criterion to say `checks.approval_readiness.status` is one of `ready`, `needs_review`, or `blocked`.
- [ ] Update the real-LLM diagnostics sentence for `INVALID_FIELD_VALUES` to mention `approval_readiness.status` alongside `consistency_summary.status`.
- [ ] Add docs coverage terms for readiness status allowed values and invalid-value diagnostics.
- [ ] Run docs coverage tests.

### Task 4: Verify and commit

**Files:**
- Backend smoke script, smoke tests, beta docs, docs coverage test, and this task's spec/plan docs only.

- [ ] Run focused readiness-status tests.
- [ ] Run smoke-script tests.
- [ ] Run docs coverage.
- [ ] Run full backend tests if time permits.
- [ ] Run `git diff --check`.
- [ ] Stage intended files only; preserve unrelated untracked files.
- [ ] Run `git diff --cached --check`.
- [ ] Commit on the current branch without pushing or merging.
