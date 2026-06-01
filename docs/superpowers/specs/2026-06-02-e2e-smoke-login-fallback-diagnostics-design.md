# E2E Smoke Login Fallback Diagnostics Design

## Context

The smoke script first attempts `/auth/register`. When the generated or configured smoke email already exists, the backend returns `400`, and the script falls back to `/auth/login` so repeated smoke runs can reuse an account.

Current auth validation always reports missing `access_token` after auth as `failed_step: "register"`, even when the malformed successful response came from the fallback `/auth/login` call. That can mislead beta triage for repeated-email or manually configured `E2E_EMAIL` runs.

## Goal

When register falls back to login, malformed successful login responses should report `failed_step: "login"` with the existing `MISSING_REQUIRED_FIELDS` and `missing_fields` diagnostics.

## Approach

Return both the auth payload and the step that produced it from `_register_or_login`:

- `register` when `/auth/register` succeeds without fallback.
- `login` when `/auth/register` returns `400` and `/auth/login` is used.

Use that step when validating `access_token` and when storing the auth check summary. Preserve existing behavior for request/HTTP failures because `_step_json` already records the concrete failing step.

This is a smoke diagnostics change only:

- No backend auth behavior changes.
- No frontend changes.
- No tokens, headers, passwords, provider settings, or request payloads are added to diagnostics.
- The smoke flow and cleanup behavior remain unchanged.

## Acceptance Criteria

- If `/auth/register` returns `400` and fallback `/auth/login` returns a successful JSON object without `access_token`, smoke stops with `ok: false`, `failed_step: "login"`, `error: "MISSING_REQUIRED_FIELDS"`, and `missing_fields: ["access_token"]`.
- The smoke does not continue to world creation after malformed fallback login.
- Normal register success still stores the auth user check and continues the main flow.
