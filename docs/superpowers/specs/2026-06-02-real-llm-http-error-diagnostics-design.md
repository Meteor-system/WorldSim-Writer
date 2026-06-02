# Real LLM HTTP Error Diagnostics Design

## Goal

Make real-LLM smoke failures more actionable by distinguishing common provider HTTP failures without exposing secrets.

## Problem

`app.llm.client.LLMClient._post_json()` currently catches all `httpx.HTTPError` values and raises `RuntimeError('MODEL_REQUEST_FAILED')`. The narrative and story-arc service layers map runtime model errors back to the same generic API detail.

For Beta real-LLM smoke, two common setup failures need fast triage:

- Invalid or unauthorized provider credentials: HTTP 401/403.
- Provider or local gateway rate limiting: HTTP 429.

Both are currently reported as generic `MODEL_REQUEST_FAILED`, so testers must inspect backend logs or provider dashboards to decide whether to rotate credentials, disable mock mode, wait for quota, or debug networking.

## Design

Keep the change small and locally testable:

- In `backend/app/llm/client.py`, map upstream HTTP status codes to safe runtime error constants:
  - 401 or 403 -> `MODEL_AUTH_FAILED`
  - 429 -> `MODEL_RATE_LIMITED`
  - all other HTTP failures -> `MODEL_REQUEST_FAILED`
- In narrative and story-arc `_map_model_error()` helpers, pass through only allowlisted safe runtime model error constants. Unknown `RuntimeError` messages still map to `MODEL_REQUEST_FAILED` so arbitrary exception text cannot leak to API clients or smoke JSON.
- Update the Beta playbook real-LLM paragraph with a concise note for `MODEL_AUTH_FAILED` and `MODEL_RATE_LIMITED`.

## Scope

In scope:

- LLM client HTTP status classification.
- Narrative and story-arc safe runtime error pass-through.
- Tests for LLM client classification and API-layer mapping.
- Minimal Beta playbook wording.

Out of scope:

- Real external LLM calls.
- Provider-specific retry/backoff logic.
- Changes to the generated draft/approval state invariant.
- Frontend behavior.

## Test Strategy

- Add failing `backend/tests/test_llm_client.py` tests for 401 and 429 upstream responses.
- Add failing API-layer tests proving narrative draft generation returns `MODEL_AUTH_FAILED` for the safe runtime detail and still masks arbitrary runtime messages.
- Add a focused docs regression term only for the new actionable diagnostics.
- Implement minimal code.
- Run focused tests, all relevant LLM/narrative/docs tests, full backend pytest, and diff checks before committing.
