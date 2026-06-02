# E2E Smoke Events Summary Contract Design

## Goal

Make the MVP/Beta smoke script report a structured diagnostic when the events endpoint returns a malformed optional `summary` field.

## Context

The smoke script verifies `/worlds/{world_id}/events` after approval. It already requires `items` to be a list of objects and checks for `chapter_approved` either in `items[*].event_type` or in `summary.event_type_counts`.

The current `summary` lookup assumes that, if present, `summary` is an object. If a successful HTTP response returns `summary` as a list or string, the smoke can fail with a generic Python error such as an attribute access failure instead of `INVALID_FIELD_TYPES`. That weakens beta triage evidence for real-LLM or deployed smoke runs.

## Chosen approach

Validate `events.summary` only when it is present:

- Missing `summary` remains allowed because `items` is the canonical evidence source.
- If `summary` is present and not an object, return `INVALID_FIELD_TYPES` with `invalid_fields: ["summary"]`.
- If `summary` is an object, keep the existing fallback check for `summary.event_type_counts`.

This is intentionally small and does not require `summary.event_type_counts`, because existing event responses can be validated from `items` alone.

## Scope

In scope:

- Add a regression test in `backend/tests/test_e2e_scripts.py`.
- Add a helper or inline check in `backend/scripts/e2e_smoke.py` for optional object fields.
- Update `BETA_TESTING.md` and docs coverage terms.

Out of scope:

- Changing the events endpoint response schema.
- Requiring `summary` or `summary.event_type_counts`.
- Adding new event types or frontend behavior.

## Testing

Use TDD:

1. Add a test where events returns valid `items` without `chapter_approved` plus `summary` as a list.
2. Verify RED: current smoke returns a generic failure instead of `INVALID_FIELD_TYPES`.
3. Implement minimal validation.
4. Verify focused test, full smoke-script tests, docs coverage, and full backend pytest.
