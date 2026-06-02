# E2E Smoke Request Timeout Diagnostics Design

## Goal

Make smoke timeouts, especially real-LLM draft timeouts, fail with a stable diagnostic code instead of an opaque httpx exception string.

## Problem

`backend/scripts/e2e_smoke.py` currently catches `httpx.RequestError` and writes `str(exc)` into `summary['error']`. For provider-backed draft generation, client-side timeouts are a likely beta failure mode. Depending on the exception, `str(exc)` can be vague or empty, making the existing `timeout_seconds` evidence harder to connect to the documented `E2E_TIMEOUT_SECONDS` remediation path.

`BETA_TESTING.md` already tells testers to increase `E2E_TIMEOUT_SECONDS` when real-LLM draft generation times out, but the smoke JSON does not expose a stable timeout error code they can report.

## Brainstormed Options

1. Leave the script unchanged and rely on the raw exception string. This avoids code changes, but keeps real-LLM timeout reports inconsistent.
2. Add a timeout-specific branch only in the draft step. This targets the most common real-LLM timeout, but leaves health/auth/export timeout reports inconsistent.
3. Add a small shared request-error marker that maps any `httpx.TimeoutException` to `REQUEST_TIMEOUT` while preserving existing raw error strings for non-timeout request failures.

## Selected Design

Use option 3. Add a helper in `backend/scripts/e2e_smoke.py` that records request failures for a named step:

- `httpx.TimeoutException` becomes `error: "REQUEST_TIMEOUT"`.
- Other `httpx.RequestError` failures keep the existing `str(exc)` behavior.
- HTTP failures are unchanged and still include `status_code` plus a redacted `response_body`.

Use that helper in both `_step_json` and `_register_or_login` so preflight, auth, draft, approval, events, and export timeout diagnostics are consistent.

## Scope Boundaries

- Do not change backend timeout behavior or LLM client behavior.
- Do not repeat previous scalar/type/token/register-conflict diagnostics work.
- Do not change frontend behavior.
- Do not alter the approval/world-state mutation invariant.

## Test Strategy

- Add a failing smoke regression where the draft request raises `httpx.ReadTimeout` and assert the summary stops at `draft` with `error: "REQUEST_TIMEOUT"`.
- Add a failing auth regression where register raises `httpx.ConnectTimeout` and assert the summary stops at `register` with `error: "REQUEST_TIMEOUT"`.
- Keep the existing non-timeout request-error test passing to prove generic request failures still expose the original message.
- Update `BETA_TESTING.md` and the documentation coverage test to require `REQUEST_TIMEOUT`.
