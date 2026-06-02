# E2E Smoke Collection Type Diagnostics Design

## Context

The beta smoke script checks required response fields before continuing through the MVP writing loop, but some fields are later treated as collections of JSON objects. In particular, `events.items` is iterated as event dictionaries and `markdown_export.files` is iterated as file dictionaries. If a successful API response contains those keys with the wrong type, the smoke can raise an internal Python exception instead of returning a safe JSON diagnostic.

This matters for beta and real-LLM readiness because smoke output is the evidence testers attach to bug reports. Malformed successful responses should be reported through the same structured summary shape as missing fields, without exposing request secrets or crashing before the JSON summary is printed.

## Goal

Make malformed collection fields return explicit smoke diagnostics instead of uncaught iteration errors.

## Selected approach

Add a small helper to `backend/scripts/e2e_smoke.py`:

- `_require_list_of_dicts(summary, step, payload, field)`
- It verifies that `payload[field]` is a list and every item is a dict.
- If invalid, it sets:
  - `failed_step` to the current step
  - `error` to `INVALID_FIELD_TYPES`
  - `invalid_fields` to `[field]`
  - returns `False`

Use it before iterating:

- `events.items`
- `markdown_export.files`

Keep required-field checks unchanged so missing keys still report `MISSING_REQUIRED_FIELDS` with `missing_fields`.

## Scope

In scope:

- Smoke script collection type validation.
- Smoke-script regression tests for malformed `events.items` and `markdown_export.files`.
- Beta playbook documentation and docs regression terms.
- Concise implementation plan.

Out of scope:

- Backend API schema changes.
- Frontend changes.
- Changes to approval, projection, or world-state mutation semantics.

## Acceptance criteria

- If `events.items` exists but is not a list of objects, smoke returns `failed_step: "events"`, `error: "INVALID_FIELD_TYPES"`, and `invalid_fields: ["items"]`.
- If `markdown_export.files` exists but is not a list of objects, smoke returns `failed_step: "markdown_export"`, `error: "INVALID_FIELD_TYPES"`, and `invalid_fields: ["files"]`.
- Missing fields still use the existing `MISSING_REQUIRED_FIELDS` diagnostics.
- `BETA_TESTING.md` documents the new diagnostic fields.
- Relevant backend tests and full backend tests pass.
- `git diff --check` and `git diff --cached --check` pass.
