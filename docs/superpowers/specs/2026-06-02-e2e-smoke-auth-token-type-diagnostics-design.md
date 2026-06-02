# E2E Smoke Auth Token Type Diagnostics Design

## Goal

Make smoke authentication failures stop at the register/login step when a successful auth response returns a malformed `access_token` value.

## Problem

`backend/scripts/e2e_smoke.py` checks that auth responses contain `access_token`, then immediately interpolates the value into an `Authorization: Bearer ...` header. If an auth regression returns a non-string token such as `true`, an object, or a list, smoke can proceed into world creation with a malformed header and report a later failure. That makes beta reports less actionable because the broken API step was auth, not world creation.

## Brainstormed Options

1. Validate only `access_token` as a string before using it. This is the smallest fix and directly protects the header construction boundary.
2. Validate the full auth payload shape, including nested `user.id`. This gives more coverage but risks broadening scope beyond a blocking smoke failure.
3. Replace all scalar validators with a generic schema checker. This could reduce duplication later but is too much refactor for a small Beta-readiness round.

## Selected Design

Use option 1. Add a local helper in the smoke script that validates required top-level fields are non-empty strings. Call it immediately after the existing auth required-field check for register/login. On malformed tokens, set `failed_step` to the auth step, `error` to `INVALID_FIELD_TYPES`, and `invalid_fields` to `['access_token']`. Do not call `/worlds/from-template` after a malformed token.

## Scope Boundaries

- Do not change auth API behavior.
- Do not add product features or frontend changes.
- Do not change chapter approval or world-state mutation behavior.
- Do not validate optional `user` fields in this round.

## Test Strategy

- Add a failing smoke regression for a register response with boolean `access_token`.
- Add a failing smoke regression for a login fallback response with object `access_token`.
- Implement the minimal helper and auth call site.
- Run focused smoke tests, all smoke script tests, full backend pytest, and diff checks before committing.
