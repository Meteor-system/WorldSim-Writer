# E2E Smoke Health Status Diagnostics Design

## Context

The smoke script uses `/health` as the first beta preflight gate. Recent hardening requires nested `migration.up_to_date` and `llm.mock`, but `status` itself is still treated as optional until the final `summary.ok` calculation.

If `/health` returns a successful JSON object with migration and LLM fields but no `status`, smoke can continue into registration, world creation, drafting, and approval before finally reporting `ok: false`. That hides the real preflight contract issue and can create unnecessary `e2e-*` data.

## Goal

Fail smoke at the `health` step with `MISSING_REQUIRED_FIELDS` when a successful health response omits `status`.

## Approach

Use the existing `_require_paths` helper after the health API call succeeds. Require these health preflight paths:

- `status`
- `migration.up_to_date`
- `llm.mock`

This preserves existing behavior when `status` is present but not `ok`: final `summary.ok` remains false because `health.get('status') == 'ok'` is still part of the final gate.

This is a smoke diagnostics change only:

- No backend health response shape changes.
- No frontend changes.
- No users/worlds are created when the preflight contract is malformed.
- No secrets, headers, tokens, provider URLs, or model names are added to diagnostics.

## Acceptance Criteria

- A successful health response missing `status` produces `ok: false`, `failed_step: "health"`, `error: "MISSING_REQUIRED_FIELDS"`, and `missing_fields: ["status"]`.
- Smoke stops after `/health` when status is missing.
- Existing health mode/migration gates continue to work when status is present.
