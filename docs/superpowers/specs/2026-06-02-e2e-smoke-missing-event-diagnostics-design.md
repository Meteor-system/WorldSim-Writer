# E2E Smoke Missing Event Diagnostics Design

## Context

The smoke script proves the main writing loop by approving a chapter, reading the world event log, and checking that a `chapter_approved` event is visible. Today, when the event list is well-formed but does not include `chapter_approved`, the final smoke summary only reports `ok: false` with `checks.events.chapter_approved_seen: false`. It does not set `failed_step` or an actionable `error`, which makes beta bug reports less useful.

## Goal

When approval succeeds but the event-log check does not find a `chapter_approved` event, the smoke script should stop with a specific diagnostic that identifies the failing step and reason.

## Selected Approach

After building `summary['checks']['events']`, add a guard:

- If `chapter_approved_seen` is false, set `failed_step` to `events`.
- Set `error` to `CHAPTER_APPROVED_EVENT_MISSING`.
- Return the summary immediately, before markdown export.

This preserves the smoke script's existing event response-shape validation and makes the event consistency failure as actionable as existing approval/export diagnostics.

## Alternatives Considered

1. Keep relying on final `ok: false`. This is minimal but fails the beta diagnostics goal because there is no `failed_step`/`error`.
2. Treat the absence as `MISSING_REQUIRED_FIELDS`. That would be misleading because the response shape is valid; the required business event is missing.
3. Add diagnostics for every final `ok` predicate at once. That may be valuable later, but it expands scope beyond one focused main-flow QA gap.

## Testing

Update `test_e2e_smoke_script_fails_when_expected_event_is_missing` so it expects:

- `failed_step == 'events'`
- `error == 'CHAPTER_APPROVED_EVENT_MISSING'`
- no markdown export request after the missing event is detected

Update `BETA_TESTING.md` and the docs regression test to document the new error code.

## Scope Boundaries

- No frontend changes.
- No database or API changes.
- No changes to chapter approval behavior.
- This only improves smoke-script diagnostics after approval when the event log does not contain the expected event.