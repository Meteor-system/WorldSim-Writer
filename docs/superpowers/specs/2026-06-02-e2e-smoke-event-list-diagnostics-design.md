# E2E Smoke Event List Diagnostics Design

## Context

`BETA_TESTING.md` requires smoke to confirm `checks.events.chapter_approved_seen` after approval. The smoke script currently calls `/worlds/{world_id}/events` and reads `events.get('items', [])` plus summary counts.

If the events endpoint returns a successful JSON object without `items`, smoke silently treats the event list as empty and reports `chapter_approved_seen: false`. That still fails final `ok`, but it hides an API contract problem: the event list response was malformed before the event assertion could run.

## Goal

Fail smoke at the `events` step with `MISSING_REQUIRED_FIELDS` when a successful events response omits the `items` list needed for the event-presence check.

## Approach

Reuse `_require_fields` after the events API call succeeds and before reading event types. Require `items` to be present. Continue treating `summary` as optional because the script can prove `chapter_approved` from the `items` list alone.

This is a smoke diagnostics change only:

- No backend API response shape changes.
- No frontend changes.
- No event/approval behavior changes.
- No secrets, headers, tokens, provider URLs, or model names are added to diagnostics.

## Acceptance Criteria

- A successful events response missing `items` produces `ok: false`, `failed_step: "events"`, `error: "MISSING_REQUIRED_FIELDS"`, and `missing_fields: ["items"]`.
- Existing event-missing semantic test still reports `checks.events.chapter_approved_seen: false` when `items` is present but lacks `chapter_approved`.
- Existing docs for `MISSING_REQUIRED_FIELDS` and `missing_fields` remain accurate.
