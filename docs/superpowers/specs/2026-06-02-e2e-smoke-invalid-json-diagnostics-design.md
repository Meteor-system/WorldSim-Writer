# E2E Smoke Invalid JSON Diagnostics Design

## Context

The smoke script records `status_code` and a redacted `response_body` for HTTP error responses, but successful HTTP responses with invalid JSON currently fall through the generic exception path. That produces an opaque JSON parser message without the HTTP status or safe body snippet beta testers need when a real/local LLM proxy returns HTML, plain text, or a malformed JSON envelope.

Real-LLM smoke diagnostics must stay safe to attach to bug reports. The existing response-body redaction should also apply to invalid successful JSON responses.

## Decision

Harden smoke JSON parsing diagnostics:

- When a step returns an HTTP 2xx response whose body cannot be parsed as JSON, stop at that step with `error: "INVALID_JSON_RESPONSE"`.
- Include `status_code` and redacted `response_body` for the malformed response.
- Preserve existing HTTP status error handling and required-field diagnostics.
- Use the same redaction path as HTTP failures so provider URLs, API keys, model names, passwords, bearer tokens, and prompt messages stay redacted.

## Non-goals

- Do not change backend API behavior.
- Do not add provider-specific parsing or retry behavior.
- Do not expose request payloads, bearer tokens, provider URLs, model names, API keys, or secrets.
- Do not change the approval/world-state invariant.

## Test strategy

Use strict TDD:

1. Add a failing smoke-script test where draft generation returns HTTP 200 with invalid JSON containing sensitive provider details.
2. Assert the smoke stops at `failed_step: "draft"` with `INVALID_JSON_RESPONSE`, `status_code: 200`, and a redacted `response_body`.
3. Add a docs regression expectation for `INVALID_JSON_RESPONSE`.
4. Implement minimal response parsing in `_step_json(...)` so invalid successful JSON responses keep response context.
5. Verify focused tests pass, then run smoke-script tests, docs tests, and backend verification.

## Beta value

This improves real/local LLM smoke readiness by turning malformed successful provider/proxy responses into structured, redacted diagnostics instead of opaque parser errors.