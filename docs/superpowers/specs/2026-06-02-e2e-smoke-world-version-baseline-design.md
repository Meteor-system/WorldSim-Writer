# E2E Smoke World Version Baseline Diagnostics Design

## Context

The smoke script proves the core MVP invariant that approval commits formal world-state changes by checking `checks.approve.world_version_incremented`. That check needs a known `world_version` baseline from world creation.

The current smoke script treats `world.world_version` as optional. If the create-world response lacks it, smoke continues, computes `expected_world_version_after` as `None`, and later reports `world_version_incremented: false`. That still fails, but it hides the true API contract problem: the baseline world version was missing before draft generation and approval.

## Goal

Fail smoke early with step-scoped diagnostics when create-world succeeds but does not include the baseline `world_version` required for the approval invariant check.

## Approach

Extend the existing `MISSING_REQUIRED_FIELDS` helper usage for `create_world` from requiring only `id` to requiring both `id` and `world_version`.

This keeps diagnostics consistent with the previous malformed-success handling:

- `failed_step`: `create_world`
- `error`: `MISSING_REQUIRED_FIELDS`
- `missing_fields`: the absent required field names

This is a smoke-script robustness change only:

- No backend API response shape changes.
- No frontend changes.
- No approval/world-state behavior changes.
- No secrets, headers, tokens, provider URLs, or model names are added to smoke diagnostics.

## Acceptance Criteria

- A create-world success response missing `world_version` produces `ok: false`, `failed_step: "create_world"`, `error: "MISSING_REQUIRED_FIELDS"`, and `missing_fields: ["world_version"]`.
- Smoke stops before chapter drafting when the baseline is missing.
- Existing malformed draft diagnostics continue to pass.
- `BETA_TESTING.md` continues to document the malformed-success diagnostic fields.
