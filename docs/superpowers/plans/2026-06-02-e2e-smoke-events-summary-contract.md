# E2E Smoke Events Summary Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Return a structured smoke diagnostic when the events response includes a malformed optional `summary` field.

**Architecture:** Add a small optional-object validation before reading `events.summary.event_type_counts`. Preserve the existing contract that `items` is required and `summary` is optional.

**Tech Stack:** Python, httpx, pytest, Markdown.

---

## File map

- Modify `backend/tests/test_e2e_scripts.py` — add RED regression for non-object events `summary`.
- Modify `backend/scripts/e2e_smoke.py` — validate optional events `summary` object before reading it.
- Modify `BETA_TESTING.md` — document event summary type diagnostics.
- Modify `backend/tests/test_event_docs.py` — require beta docs wording.
- Create `docs/superpowers/specs/2026-06-02-e2e-smoke-events-summary-contract-design.md` — design record.
- Create `docs/superpowers/plans/2026-06-02-e2e-smoke-events-summary-contract.md` — this implementation plan.

### Task 1: Add failing events-summary regression

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add a test where events returns `items: [{'event_type': 'world_version_increment'}]` and `summary: []`.
- [ ] Assert the smoke stops at `events` with `INVALID_FIELD_TYPES` and `invalid_fields == ['summary']`.
- [ ] Assert no markdown export request is made.
- [ ] Run the focused test and verify RED because the current smoke tries to read `.get()` from a list.

### Task 2: Implement optional summary object validation

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Add `_require_optional_dict(summary, step, payload, field)` near other validation helpers.
- [ ] Return `True` when the field is absent or a dict.
- [ ] Return `INVALID_FIELD_TYPES` when the field is present and not a dict.
- [ ] Use it for `events.summary` before reading `event_type_counts`.
- [ ] Run the focused test and verify GREEN.

### Task 3: Document event summary diagnostics

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Update event pass criteria to mention `items` and optional `events.summary.event_type_counts` evidence.
- [ ] Update `INVALID_FIELD_TYPES` wording to include events summary objects.
- [ ] Add docs coverage terms for `events.summary`, `event_type_counts`, and events summary objects.
- [ ] Run docs coverage tests.

### Task 4: Verify and commit

**Files:**
- Smoke script, smoke tests, beta docs, docs coverage test, and this task's spec/plan docs only.

- [ ] Run focused events-summary test.
- [ ] Run smoke-script tests.
- [ ] Run docs coverage.
- [ ] Run full backend tests.
- [ ] Run `git diff --check`.
- [ ] Stage intended files only; preserve `.hermes/plans/story-arc-collapse-nav-bugfix.md`, `.hermes/plans/story-arc-denser-collapse-followup.md`, and `backend/worldsim-dev.db`.
- [ ] Run `git diff --cached --check`.
- [ ] Commit on the current branch without pushing or merging.
