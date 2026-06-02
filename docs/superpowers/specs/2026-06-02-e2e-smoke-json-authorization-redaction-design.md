# E2E Smoke JSON Authorization Redaction Design

## Goal

Make real/mock smoke failure diagnostics safe when an API gateway or model backend echoes JSON-shaped bearer authorization fields in an HTTP response body.

## Problem

`backend/scripts/e2e_smoke.py` already redacts several sensitive response-body shapes before printing `response_body` in smoke summaries, including plaintext `Authorization: Bearer ...`, JSON-shaped API keys/passwords/provider URLs/model names, and prompt messages. It does not explicitly redact JSON object fields such as `"authorization":"Bearer secret-token"` or `"Authorization":"Bearer secret-token"`.

Real LLM smoke failures are meant to be pasted into bug reports. If an upstream OpenAI-compatible gateway echoes request headers as JSON in an error body, the current redaction coverage can leak a smoke bearer token.

## Design

Keep the change local to the smoke script redaction boundary:

- Add a regular expression to `_REDACTION_PATTERNS` for JSON-shaped `authorization` fields whose value starts with `Bearer`.
- Preserve the header name and JSON string shape while replacing the token value with `[REDACTED_SECRET]`.
- Add a regression test that fails on the current code by returning a 502 draft response body containing both lowercase and uppercase JSON authorization fields.
- Keep existing plaintext authorization redaction behavior unchanged.
- Update `BETA_TESTING.md` so beta testers know authorization headers are included in the redacted evidence contract.

## Scope

In scope:

- Smoke script response-body redaction.
- Smoke script regression tests.
- Beta playbook wording and docs regression terms.

Out of scope:

- Backend authentication behavior.
- LLM client request construction.
- Frontend behavior.
- Any change to the chapter approval/state mutation invariant.

## Test Strategy

- Add a focused `test_e2e_smoke_script_redacts_json_authorization_response_body_details` test in `backend/tests/test_e2e_scripts.py`.
- Confirm it fails before implementation because the echoed token appears in `summary['response_body']`.
- Implement the minimal regex addition.
- Rerun the focused test, all smoke script tests, docs regression tests, and full backend pytest.
