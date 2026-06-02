# E2E Smoke Auth User Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Return a structured smoke diagnostic when auth responses include a malformed optional `user` field.

**Architecture:** Reuse the smoke script's optional-object validation helper before reading `auth_payload.user.id`. Preserve the existing contract that `access_token` is required and `user` is optional.

**Tech Stack:** Python, httpx, pytest, Markdown, Git ignore rules.

---

## File map

- Modify `.gitignore` — ignore local `.hermes/plans/*.md` notes and `backend/worldsim-dev.db` while keeping them on disk.
- Modify `backend/tests/test_e2e_scripts.py` — add RED regression for non-object auth `user`.
- Modify `backend/scripts/e2e_smoke.py` — validate optional auth `user` before reading `user.id`.
- Modify `BETA_TESTING.md` — document auth user metadata diagnostics.
- Modify `backend/tests/test_event_docs.py` — require beta docs wording.
- Create `docs/superpowers/specs/2026-06-02-e2e-smoke-auth-user-contract-design.md` — design record.
- Create `docs/superpowers/plans/2026-06-02-e2e-smoke-auth-user-contract.md` — this implementation plan.

### Task 1: Preserve local untracked artifacts without committing them

**Files:**
- Modify: `.gitignore`

- [ ] Add `.hermes/plans/*.md` so local planning notes stay on disk but stop polluting status.
- [ ] Add `backend/worldsim-dev.db` so the local development database is never accidentally committed.
- [ ] Confirm `git status --short --branch` shows only intended tracked changes after the ignore update.

### Task 2: Add failing auth-user regression

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add a test where register returns `{'access_token': 'token', 'user': []}`.
- [ ] Assert the smoke stops at `register` with `INVALID_FIELD_TYPES` and `invalid_fields == ['user']`.
- [ ] Assert no world-creation request is made.
- [ ] Run the focused test and verify RED because the current smoke tries to read `.get()` from a list.

### Task 3: Implement optional auth user validation

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] After validating `access_token`, call `_require_optional_dict(summary, auth_step, auth_payload, 'user')`.
- [ ] Keep missing `user` allowed.
- [ ] Keep `checks[auth_step].user_id` populated from `user.id` when `user` is an object.
- [ ] Run the focused test and verify GREEN.

### Task 4: Document auth metadata diagnostics

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Update auth pass criteria to say auth evidence records optional user metadata.
- [ ] Update `INVALID_FIELD_TYPES` wording to include auth user metadata objects.
- [ ] Add docs coverage terms for `checks.register.user_id`, `checks.login.user_id`, and auth user metadata objects.
- [ ] Run docs coverage tests.

### Task 5: Verify and commit

**Files:**
- `.gitignore`, smoke script, smoke tests, beta docs, docs coverage test, and this task's spec/plan docs only.

- [ ] Run focused auth-user test.
- [ ] Run smoke-script tests.
- [ ] Run docs coverage.
- [ ] Run full backend tests.
- [ ] Run `git diff --check`.
- [ ] Stage intended files only; preserve `.hermes/plans/story-arc-collapse-nav-bugfix.md`, `.hermes/plans/story-arc-denser-collapse-followup.md`, and `backend/worldsim-dev.db` by leaving them ignored/untracked.
- [ ] Run `git diff --cached --check`.
- [ ] Commit on the current branch without pushing or merging.
