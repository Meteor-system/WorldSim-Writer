# E2E Smoke Approved Version Diagnostics Design

## Context

The smoke script proves the main writing loop by checking that chapter approval advances the world version from the create-world baseline. The approval response field `approved_version` is required to perform that check.

The smoke script already reports malformed successful responses for register, create-world, and draft. Approval still treats `approved_version` as optional and only records `world_version_incremented: false` if it is absent. That causes a vague invariant failure instead of identifying the malformed approval response at the approval step.

## Goal

Fail smoke at the `approve` step with `MISSING_REQUIRED_FIELDS` when a successful approval response omits `approved_version`.

## Approach

Reuse `_require_fields` before reading approval fields:

- After `_step_json(..., 'approve', ...)` succeeds, require `approved_version`.
- If missing, return the summary with `failed_step: "approve"`, `error: "MISSING_REQUIRED_FIELDS"`, and `missing_fields: ["approved_version"]`.
- Leave status validation as an `ok` criterion rather than a required field, because a non-approved status is already captured in `checks.approve.status` when `approved_version` is present.

This is a smoke diagnostics change only:

- No backend API response shape changes.
- No frontend changes.
- No approval/world-state behavior changes.
- No secrets, headers, tokens, provider URLs, or model names are added to diagnostics.

## Acceptance Criteria

- A successful approval response missing `approved_version` produces `ok: false`, `failed_step: "approve"`, `error: "MISSING_REQUIRED_FIELDS"`, and `missing_fields: ["approved_version"]`.
- Smoke stops before event/export checks when approval lacks the required version.
- Existing approval non-increment test still reports `checks.approve.world_version_incremented: false` when `approved_version` is present but wrong.
- Existing docs for `MISSING_REQUIRED_FIELDS` remain accurate.
