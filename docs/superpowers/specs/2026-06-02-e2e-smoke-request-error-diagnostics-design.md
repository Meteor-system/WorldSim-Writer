# E2E Smoke Request Error Diagnostics Design

## Goal

Make `backend/scripts/e2e_smoke.py` identify which smoke step failed when an HTTP request cannot be completed at all, such as when the backend is down or the connection is refused.

## Problem

The smoke script now records structured diagnostics for HTTP responses like 4xx/5xx, but the request itself is still evaluated before the step helper runs. If `client.get('/health')` or another request raises `httpx.RequestError`, the summary falls back to a generic top-level `error` without `failed_step`. That slows beta triage for the most common setup issue: the backend is not reachable.

## Scope

- Keep the existing smoke flow and success criteria unchanged.
- Change the step helper to execute the request callable itself.
- For request-level failures, return a summary with:
  - `ok: false`
  - `failed_step`
  - `error`
- Continue to include `status_code` and `response_body` only when an HTTP response exists.
- Do not include request headers, bearer tokens, API keys, or environment secrets.

## Non-goals

- Do not add live server checks beyond the existing `/health` call.
- Do not change backend API behavior.
- Do not add retry or polling behavior.
- Do not run a live smoke test in this iteration.

## Testing

Add a regression test in `backend/tests/test_e2e_scripts.py` where the first request raises `httpx.ConnectError`. The expected summary should be `ok: false`, `failed_step: "health"`, no `status_code`, no `response_body`, and an error string containing the connection failure message.
