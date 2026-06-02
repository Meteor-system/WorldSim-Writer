# E2E Smoke Register Conflict Contract Design

## Goal

Make smoke auth fallback diagnostics precise when `/auth/register` fails, so Beta testers do not lose the original register error behind an unnecessary login attempt.

## Context

The smoke script supports rerunning with `E2E_EMAIL`: if registration reports that the smoke email already exists, it falls back to `/auth/login` and continues. Current duplicate detection is too broad for status `400`: any `400` register response is treated as duplicate-email evidence, even if the backend is reporting an unrelated validation or policy failure.

## Decision

Keep login fallback only for explicit duplicate-email signals:

- `409` with JSON object detail `EMAIL_ALREADY_REGISTERED`.
- Legacy `400` with string detail `EMAIL_ALREADY_REGISTERED` or text containing `already registered`.

All other register failures must remain register failures. The smoke should stop at `failed_step: "register"` through the existing `_step_json()` HTTP error path, preserving `status_code` and redacted `response_body` for triage.

## Scope

- Add a focused regression for an unrelated `400` register failure.
- Tighten `_is_duplicate_email_register_response()`.
- Document duplicate-email fallback behavior in `BETA_TESTING.md`.
- Extend docs coverage terms so future docs edits retain the diagnostic contract.

## Non-goals

- Change backend auth API behavior.
- Add new smoke CLI flags.
- Change login fallback credentials or cleanup behavior.
