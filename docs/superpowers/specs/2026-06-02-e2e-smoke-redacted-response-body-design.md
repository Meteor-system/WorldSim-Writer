# E2E Smoke Redacted Response Body Design

## Context

The beta smoke script includes `response_body` snippets for HTTP failures so testers can attach useful evidence to bug reports. That is valuable for real-LLM smoke triage, but provider failures can echo sensitive configuration or request details. The current smoke script truncates response text but does not redact common secrets, provider URLs, model names, authorization headers, passwords, or request payload hints before printing the JSON summary.

## Goal

Keep smoke failure evidence useful while preventing response-body snippets from leaking real-LLM credentials or provider details.

## Selected approach

Add a small redaction pass inside `_response_body_snippet()` in `backend/scripts/e2e_smoke.py` before truncation. The redactor should cover common text and JSON-ish forms seen in HTTP error bodies:

- bearer authorization headers/tokens
- API key values (`api_key`, `LLM_API_KEY`, `OPENAI_API_KEY`)
- password values
- provider/base URL values and generic URLs
- model values (`model`, `LLM_MODEL`)
- message arrays/request payload echoes (`messages`)

Use simple regex substitutions with fixed placeholders such as `[REDACTED_SECRET]`, `[REDACTED_URL]`, `[REDACTED_MODEL]`, and `[REDACTED_MESSAGES]`. Keep the existing maximum snippet length.

## Scope

In scope:

- Smoke-script response body redaction.
- Regression tests proving sensitive substrings do not appear in `response_body`.
- Beta playbook documentation and docs regression terms.
- Concise implementation plan.

Out of scope:

- Backend error response behavior changes.
- LLM client changes.
- Frontend changes.
- Persisting or uploading smoke results.

## Acceptance criteria

- HTTP failure summaries still include `failed_step`, `status_code`, and `response_body`.
- `response_body` does not contain bearer tokens, API keys, passwords, provider URLs, model names, or echoed messages payloads from the test fixture.
- `response_body` contains redaction placeholders so testers know content was intentionally removed.
- Existing HTTP failure diagnostics still pass.
- `BETA_TESTING.md` documents that `response_body` is a short redacted snippet.
- Relevant backend tests and full backend tests pass.
- `git diff --check` and `git diff --cached --check` pass.
