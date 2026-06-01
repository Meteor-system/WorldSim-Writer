# E2E Smoke Health Contract Diagnostics Design

## Context

The smoke script uses `/health` to guard beta runs before creating users/worlds or making model calls. It relies on two health fields:

- `migration.up_to_date`, so smoke does not run against a stale schema.
- `llm.mock`, so mock and real-LLM smoke run against the intended backend mode.

Today, if either nested field is missing from a successful health response, smoke continues because the gate only checks explicit `False` / `True` mismatches. That can cause later steps to run despite incomplete preflight health information.

## Goal

Fail smoke at the `health` step with `MISSING_REQUIRED_FIELDS` when a successful health response omits the nested health fields required for preflight safety.

## Approach

Add a small nested-field validation helper for dotted health paths. After the health response succeeds and before mode/migration gates, require:

- `migration.up_to_date`
- `llm.mock`

If missing, return the existing malformed-success diagnostic shape:

- `failed_step: "health"`
- `error: "MISSING_REQUIRED_FIELDS"`
- `missing_fields: ["migration.up_to_date"]` or `["llm.mock"]`

This is a smoke diagnostics change only:

- No backend health response shape changes.
- No frontend changes.
- No model/provider settings are exposed.
- No users/worlds are created when health preflight is malformed.

## Acceptance Criteria

- A successful health response missing `llm.mock` produces `ok: false`, `failed_step: "health"`, `error: "MISSING_REQUIRED_FIELDS"`, and `missing_fields: ["llm.mock"]`.
- Smoke stops after `/health` when required health fields are missing.
- Existing mock/real LLM mismatch gates continue to work when `llm.mock` is present.
- Existing migration gate continues to work when `migration.up_to_date` is present.
