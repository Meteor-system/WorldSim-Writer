# E2E Smoke Register Conflict Login Fallback Design

## Goal

Make smoke reuse of an existing `E2E_EMAIL` match the current backend auth contract by falling back to login when registration returns `409 EMAIL_ALREADY_REGISTERED`.

## Problem

`backend/scripts/e2e_smoke.py` currently falls back from register to login only when `/auth/register` returns HTTP `400`. The backend now returns HTTP `409 Conflict` with `detail: "EMAIL_ALREADY_REGISTERED"` for duplicate emails. As a result, beta testers who rerun smoke with the same `E2E_EMAIL` can get a register failure even though the intended smoke behavior is to log in and continue.

This contradicts `BETA_TESTING.md`, which says auth evidence can appear as `checks.login` when `E2E_EMAIL` reuses an existing smoke account.

## Brainstormed Options

1. Fall back on any register `409`. This is simple, but could mask unrelated conflict responses if the register endpoint gains more conflict cases later.
2. Fall back only on `409` with `detail == "EMAIL_ALREADY_REGISTERED"`. This matches the current backend contract and avoids masking other errors.
3. Fall back on both legacy `400` and current `409` duplicate-email responses. This preserves compatibility with any older local backend while fixing the current app behavior.

## Selected Design

Use option 3. Add a small helper in the smoke script that recognizes duplicate-email register responses by status/detail:

- legacy-compatible `400`
- current `409` with `detail == "EMAIL_ALREADY_REGISTERED"`

Only those responses trigger the login fallback. Other register HTTP failures should continue to be reported as register failures through existing `_step_json` diagnostics.

## Scope Boundaries

- Do not change backend auth behavior.
- Do not repeat token/type diagnostics work from prior rounds.
- Do not add frontend behavior.
- Do not change the chapter approval or world-state mutation invariant.

## Test Strategy

- Add a failing smoke regression where register returns `409 EMAIL_ALREADY_REGISTERED`, login succeeds, and smoke continues through the main flow.
- Add a regression proving unrelated register `409` failures do not fall back to login.
- Implement the minimal helper and update `_register_or_login`.
- Run focused smoke tests, all smoke script tests, full backend pytest, and diff checks before committing.
