# Beta Auth Fallback Playbook Design

## Context

The smoke script supports repeated runs by attempting `/auth/register` first, then falling back to `/auth/login` when registration returns `400` for an existing smoke email.

Recent diagnostics now preserve that distinction: a fresh smoke account records `checks.register`, while a reused smoke account can record `checks.login`. Malformed fallback-login responses also report `failed_step: "login"`.

`BETA_TESTING.md` currently says checks include register/login, but it does not document the concrete `checks.register` / `checks.login` summary keys or the repeated-email fallback path. That can confuse beta testers who pin `E2E_EMAIL` or rerun smoke before cleanup.

## Goal

Document how to interpret smoke auth results for both fresh registration and fallback login.

## Approach

Update `BETA_TESTING.md` mock smoke pass criteria and diagnostic guidance:

- Note that auth evidence appears as either `checks.register` or `checks.login`.
- Explain that `checks.login` is expected when `E2E_EMAIL` points at an existing smoke account or a previous run reused the email before cleanup.
- Explain that `failed_step: "login"` with `MISSING_REQUIRED_FIELDS` means the fallback login response was malformed, not that world creation or drafting failed.

Add a regression assertion in `backend/tests/test_event_docs.py` so the playbook keeps these terms documented.

This is documentation/readiness only:

- No backend behavior changes.
- No frontend behavior changes.
- No secrets, tokens, headers, passwords, or provider settings are added to docs.

## Acceptance Criteria

- `BETA_TESTING.md` mentions `checks.register`, `checks.login`, and `E2E_EMAIL`.
- The beta playbook explains that fallback login is expected for reused smoke accounts.
- Documentation regression tests fail before the doc update and pass after it.
