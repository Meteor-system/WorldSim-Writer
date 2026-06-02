# E2E Smoke Consistency Blocking Count Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject negative approval-consistency blocker counts before smoke proceeds to formal approval.

**Architecture:** Add a small non-negative integer path validator to the smoke script and use it for `consistency_summary.blocking_count`. Preserve missing/type diagnostics and add an invalid-value diagnostic for negative integers.

**Tech Stack:** Python, httpx, pytest, Markdown.

---

## File map

- Modify `backend/tests/test_e2e_scripts.py` — add RED regression for negative `consistency_summary.blocking_count`.
- Modify `backend/scripts/e2e_smoke.py` — validate blocker count as a non-negative integer.
- Modify `BETA_TESTING.md` — document non-negative blocker-count pass criteria and diagnostics.
- Modify `backend/tests/test_event_docs.py` — require beta docs wording.
- Create `docs/superpowers/specs/2026-06-02-e2e-smoke-consistency-blocking-count-contract-design.md` — design record.
- Create `docs/superpowers/plans/2026-06-02-e2e-smoke-consistency-blocking-count-contract.md` — this implementation plan.

### Task 1: Add failing negative blocker-count regression

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add a test where `approval-consistency` returns `consistency_summary: {'status': 'clear', 'blocking_count': -1}`.
- [ ] Assert the smoke stops at `approval_consistency` with `INVALID_FIELD_VALUES`, `invalid_fields == ['consistency_summary.blocking_count']`, and no approval request is made.
- [ ] Run the focused test and verify RED because the current smoke script accepts negative blocker counts.

### Task 2: Implement non-negative count validation

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Add `_require_non_negative_int_path(summary, step, payload, path)` near `_require_int_path`.
- [ ] Preserve `MISSING_REQUIRED_FIELDS` for absent paths and `INVALID_FIELD_TYPES` for non-integers or booleans.
- [ ] Return `INVALID_FIELD_VALUES` for negative integers.
- [ ] Replace the approval-consistency `_require_int_path(... 'consistency_summary.blocking_count')` call with the non-negative validator.
- [ ] Run the focused test and verify GREEN.

### Task 3: Document non-negative blocker-count diagnostics

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Update the approval-consistency pass criterion to say blocker count is a non-negative integer.
- [ ] Update the real-LLM diagnostics sentence for `INVALID_FIELD_VALUES` to mention negative `consistency_summary.blocking_count`.
- [ ] Add docs coverage terms for non-negative consistency blocker counts.
- [ ] Run docs coverage tests.

### Task 4: Verify and commit

**Files:**
- Backend smoke script, smoke tests, beta docs, docs coverage test, and this task's spec/plan docs only.

- [ ] Run focused blocker-count test.
- [ ] Run smoke-script tests.
- [ ] Run docs coverage.
- [ ] Run full backend tests if time permits.
- [ ] Run `git diff --check`.
- [ ] Stage intended files only; preserve unrelated untracked files.
- [ ] Run `git diff --cached --check`.
- [ ] Commit on the current branch without pushing or merging.
