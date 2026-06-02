# E2E Smoke JSON Object Shape Diagnostics Design

## Context

The backend smoke script already reports structured diagnostics for HTTP errors, malformed successful JSON, missing fields, and invalid field types. One remaining diagnostics gap is a successful API response that contains valid JSON but not a JSON object, such as a list or string. `_step_json(...)` currently raises a generic `Expected JSON object response` error for this case, which loses the HTTP status and redacted body snippet that beta testers need for triage.

## Goal

When any smoke step receives a successful HTTP response whose JSON payload is valid but not an object, the smoke summary should stop at that step with a specific, safe diagnostic that includes the HTTP status and a redacted response snippet.

## Selected Approach

Add a response-level validation branch inside `_step_json(...)` after `response.json()` succeeds:

- If the parsed payload is not a `dict`, set `failed_step` to the current step.
- Set `error` to `INVALID_JSON_RESPONSE_TYPE`.
- Set `status_code` to the response status code.
- Set `response_body` to `_response_body_snippet(response)`, preserving existing secret redaction.
- Return `{}` and let the existing `_has_failed(...)` checks stop the smoke before any formal approval step.

This keeps the change local to `backend/scripts/e2e_smoke.py` and preserves the writing-loop invariant: diagnostics stop before approval when pre-approval response evidence is malformed.

## Alternatives Considered

1. Reuse `INVALID_JSON_RESPONSE` for valid non-object JSON. This is simpler but conflates malformed JSON syntax with wrong top-level response shape.
2. Let field validators handle non-object payloads. This would require each caller to guard against non-dicts and would spread response-shape handling across the script.
3. Keep the generic exception. This is least disruptive but leaves beta testers without status/body context.

## Testing

Add a regression test where the draft endpoint returns HTTP 200 with a JSON array containing secret-shaped values. The expected smoke summary should be:

- `ok: false`
- `failed_step: "draft"`
- `error: "INVALID_JSON_RESPONSE_TYPE"`
- `status_code: 200`
- `response_body` present and redacted

Update the beta playbook docs regression so `BETA_TESTING.md` documents the new diagnostic code.

## Scope Boundaries

- No frontend changes.
- No API contract changes.
- No changes to real draft generation or approval behavior.
- No changes to existing malformed JSON handling.