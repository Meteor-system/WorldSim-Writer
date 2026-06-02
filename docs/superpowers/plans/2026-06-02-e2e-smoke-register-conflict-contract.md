# E2E Smoke Register Conflict Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution for this plan. User constraints override subagent recommendations: no dynamic workflows, no subagents/agents/code-review subagent. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve precise register diagnostics unless `/auth/register` explicitly reports an existing smoke email.

**Architecture:** Tighten the smoke script's duplicate-email detector while keeping the existing `_step_json()` HTTP error handling for non-duplicate register failures. Use a focused regression to prove unrelated `400` responses stop at `register` and do not call `/auth/login`.

**Tech Stack:** Python, httpx, pytest, Markdown.

---

## File map

- Modify `backend/tests/test_e2e_scripts.py` — add RED regression for unrelated register `400`.
- Modify `backend/scripts/e2e_smoke.py` — narrow duplicate-email detection.
- Modify `BETA_TESTING.md` — document explicit duplicate-email fallback and register diagnostics.
- Modify `backend/tests/test_event_docs.py` — require the new beta docs wording.
- Create `docs/superpowers/specs/2026-06-02-e2e-smoke-register-conflict-contract-design.md` — design record.
- Create `docs/superpowers/plans/2026-06-02-e2e-smoke-register-conflict-contract.md` — this implementation plan.

### Task 1: Add failing register-400 regression

**Files:**
- Modify: `backend/tests/test_e2e_scripts.py`

- [ ] Add a test where `/auth/register` returns `400` with `{'detail': 'PASSWORD_POLICY_FAILED'}`.
- [ ] Assert the smoke stops at `failed_step == 'register'`.
- [ ] Assert `status_code == 400` and `response_body == '{"detail":"PASSWORD_POLICY_FAILED"}'`.
- [ ] Assert the request list is only `/health` and `/auth/register`.
- [ ] Run the focused test and verify RED because current code treats any register `400` as duplicate email and attempts `/auth/login`.

### Task 2: Tighten duplicate-email detection

**Files:**
- Modify: `backend/scripts/e2e_smoke.py`

- [ ] Parse register error JSON only when status is `400` or `409`.
- [ ] Return duplicate only when detail is `EMAIL_ALREADY_REGISTERED` or contains `already registered`.
- [ ] Preserve existing `409 EMAIL_ALREADY_REGISTERED` fallback.
- [ ] Preserve legacy `400 Email already registered` fallback used by existing tests.
- [ ] Run the focused test and verify GREEN.

### Task 3: Document fallback diagnostics

**Files:**
- Modify: `BETA_TESTING.md`
- Modify: `backend/tests/test_event_docs.py`

- [ ] Update auth pass criteria to mention `E2E_EMAIL` login fallback only for explicit duplicate-email register responses.
- [ ] Update failure diagnostics to say unrelated register failures remain `failed_step: "register"` with `status_code` and `response_body`.
- [ ] Add docs coverage terms for `EMAIL_ALREADY_REGISTERED`, `duplicate-email fallback`, and `failed_step: "register"`.
- [ ] Run docs coverage tests.

### Task 4: Verify and commit

**Files:**
- Smoke script, smoke tests, beta docs, docs coverage test, and this task's spec/plan docs only.

- [ ] Run focused register-conflict test.
- [ ] Run smoke-script tests.
- [ ] Run docs coverage.
- [ ] Run full backend tests.
- [ ] Run `git diff --check`.
- [ ] Stage intended files only.
- [ ] Run `git diff --cached --check`.
- [ ] Commit on the current branch without pushing or merging.
