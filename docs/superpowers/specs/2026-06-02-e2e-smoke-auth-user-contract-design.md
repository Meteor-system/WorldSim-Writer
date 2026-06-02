# E2E Smoke Auth User Contract Design

## Goal

Prevent the MVP/Beta smoke script from crashing when auth responses include a malformed optional `user` field.

## Context

The smoke script accepts both registration and fallback login responses. It requires `access_token` and records `checks.register.user_id` or `checks.login.user_id` from `user.id` when present. The `user` object is useful triage evidence but not required for authentication.

The current code assumes that, if `user` exists, it is an object. A successful auth response with `user` as a list, string, or number can therefore raise an attribute-access error after the access token has already passed validation. That weakens beta and real-smoke diagnostics by reporting a generic Python error instead of `INVALID_FIELD_TYPES`.

## Chosen approach

Use the existing optional-object validation helper for `auth_payload.user`:

- Missing `user` remains allowed.
- A dictionary `user` remains allowed and `user.id` is recorded as before.
- A present non-object `user` returns `INVALID_FIELD_TYPES` with `invalid_fields: ["user"]` at the auth step (`register` or `login`).

This keeps the auth contract small: the token is required, user metadata is optional but must be safely shaped when present.

## Scope

In scope:

- Add a focused regression test in `backend/tests/test_e2e_scripts.py`.
- Validate optional auth `user` in `backend/scripts/e2e_smoke.py` before reading `user.id`.
- Update `BETA_TESTING.md` and docs coverage terms.
- Include `.gitignore` status-policy entries that preserve local `.hermes` planning notes and `backend/worldsim-dev.db` without committing them.

Out of scope:

- Requiring auth `user` or `user.id`.
- Changing backend auth API behavior.
- Frontend auth behavior.

## Testing

Use TDD:

1. Add a test where registration returns a valid `access_token` but `user` is a list.
2. Verify RED: current smoke fails with a generic attribute error instead of `INVALID_FIELD_TYPES`.
3. Add minimal optional-object validation.
4. Verify focused test, smoke-script tests, docs coverage, and full backend pytest.
