# E2E Smoke Failure Diagnostics Design

## Goal

Make `backend/scripts/e2e_smoke.py` more useful for beta triage when the main-flow smoke fails, especially in real-LLM mode.

## Problem

The smoke script prints a JSON summary, but unexpected HTTP failures currently escape the flow and are collapsed by `main()` into a top-level `error` string. That loses the failing step name, HTTP status code, and safe response body. Beta testers then have to infer whether the failure happened during health, auth, world creation, draft generation, approval, event listing, or export.

## Scope

- Keep the existing smoke flow and success criteria unchanged.
- Add structured failure context to the returned summary when an API step fails.
- Include:
  - `failed_step`
  - `error`
  - `status_code` when the failure came from an HTTP response
  - `response_body` with a short safe text snippet when available
- Do not log request headers, bearer tokens, API keys, or backend environment secrets.
- Keep cleanup guidance in the summary.

## Non-goals

- Do not add new API endpoints.
- Do not change backend LLM behavior.
- Do not run a live smoke test against a server in this iteration.
- Do not alter frontend behavior.

## Testing

Add a regression test in `backend/tests/test_e2e_scripts.py` where draft generation returns an HTTP 502 body such as `MODEL_REQUEST_FAILED`. The expected summary should be `ok: false`, preserve prior successful checks, and include `failed_step: "draft"`, `status_code: 502`, and the response body text.
