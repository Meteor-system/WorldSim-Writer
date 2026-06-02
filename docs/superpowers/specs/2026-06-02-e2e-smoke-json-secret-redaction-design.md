# E2E Smoke JSON Secret Redaction Design

## Context

The smoke script already redacts several plain-text provider failure details before printing `response_body` in its JSON summary. Real/local OpenAI-compatible providers often return diagnostic bodies that echo JSON-shaped request fragments, for example `"api_key":"sk-..."`, `"password":"..."`, `"model":"..."`, `"base_url":"https://..."`, or `"messages":[...]`. The current redaction regexes mainly cover unquoted `key=value` or `key: value` fragments and can miss JSON-quoted forms.

## Decision

Harden `backend/scripts/e2e_smoke.py` response-body redaction to cover both plain-text and JSON-shaped sensitive fields without changing the smoke API flow or adding external dependencies.

The fix should remain intentionally small:

- Add regression coverage for JSON-shaped provider error text.
- Extend `_REDACTION_PATTERNS` so quoted JSON key/value pairs redact:
  - API keys and similar key fields.
  - Passwords.
  - LLM/base URLs.
  - Model names.
  - `messages` arrays.
- Preserve existing placeholders: `[REDACTED_SECRET]`, `[REDACTED_URL]`, `[REDACTED_MODEL]`, and `[REDACTED_MESSAGES]`.
- Keep redaction before truncation.
- Update beta playbook diagnostics to explicitly mention JSON-shaped echoed provider/request fields are redacted.

## Non-goals

- Do not parse arbitrary error bodies as JSON; provider errors may be partial text.
- Do not add a logging framework or secret scanner dependency.
- Do not change smoke success criteria, API calls, or world-state behavior.
- Do not expose bearer tokens, provider URLs, model names, API keys, passwords, or full request messages in smoke output.

## Test strategy

Use strict TDD in `backend/tests/test_e2e_scripts.py`:

1. Add a failing regression test where the draft endpoint returns HTTP 502 with JSON-shaped sensitive content.
2. Verify the current script leaks those values.
3. Implement minimal regex hardening.
4. Verify focused redaction tests pass.
5. Run all smoke script tests, docs regression tests, and full backend pytest.

## Beta value

This improves real/local LLM smoke diagnosability because beta testers can safely attach full smoke JSON to bug reports even when providers echo JSON-like request fragments in failure responses.