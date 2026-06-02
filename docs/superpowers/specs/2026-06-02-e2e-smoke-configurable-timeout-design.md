# E2E Smoke Configurable Timeout Design

## Context

The beta smoke script creates its own `httpx.Client` with a fixed 60-second timeout when no test client is injected. That is fine for mock smoke, but real-LLM chapter generation can legitimately take longer depending on provider latency, cold starts, or local model queues. A hard-coded timeout can turn an otherwise healthy real-LLM smoke into a false failure, and the current smoke summary does not tell testers what timeout was used.

## Goal

Let beta testers tune the smoke HTTP timeout without editing the script, and make the chosen timeout visible in the JSON summary.

## Selected approach

Add `E2E_TIMEOUT_SECONDS` support to `backend/scripts/e2e_smoke.py`:

- Default remains `60.0` seconds.
- `_timeout_seconds()` reads `E2E_TIMEOUT_SECONDS`.
- Blank or unset values use the default.
- Invalid, zero, or negative values fall back to the default to keep smoke executable.
- `run_smoke()` includes `timeout_seconds` in the summary.
- When the script owns the client, it passes `timeout=timeout_seconds` to `httpx.Client`.

Document the setting in `BETA_TESTING.md`, especially for real-LLM smoke. This is a small readiness improvement with no product-scope behavior changes.

## Scope

In scope:

- Smoke script timeout configuration.
- Unit-style smoke script tests for default, custom, and invalid timeout values.
- Beta playbook documentation and docs regression terms.
- Concise implementation plan.

Out of scope:

- Backend API timeout behavior.
- LLM client/provider timeout behavior inside the backend.
- Frontend changes.
- Retry logic or polling.

## Acceptance criteria

- Default smoke summary includes `timeout_seconds: 60.0`.
- `E2E_TIMEOUT_SECONDS=180` makes the internally-created `httpx.Client` use `timeout=180.0` and reports `timeout_seconds: 180.0`.
- Invalid values such as `0`, `-1`, or `abc` fall back to `60.0`.
- Existing injected-client tests remain unaffected.
- `BETA_TESTING.md` documents `E2E_TIMEOUT_SECONDS` for slow real-LLM providers.
- Relevant backend tests and full backend tests pass.
- `git diff --check` and `git diff --cached --check` pass.
