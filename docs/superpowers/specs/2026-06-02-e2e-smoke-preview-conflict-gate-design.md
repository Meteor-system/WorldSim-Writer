# E2E Smoke Approval Preview Conflict Gate Design

## Context

The product invariant is that generated drafts only propose changes, while user approval commits formal world state. The smoke script already calls approval preview before approval and requires `preview.version_conflict is False` in final `summary.ok`.

However, the smoke JSON currently records only `checks.approval_preview.version_conflict`. It does not expose the preview conflict as a normalized `blocked` gate, unlike `checks.approval_readiness.blocked` and `checks.approval_consistency.blocked`. `BETA_TESTING.md` also does not document the preview conflict recovery path, even though a world-version mismatch is a beta-blocking approval issue.

## Goal

Make approval-preview version conflicts explicit and easy to triage in smoke output and beta docs.

## Approach

Add a derived `checks.approval_preview.blocked` boolean to the smoke summary. It is `true` only when `preview.version_conflict is True`. Keep the final `summary.ok` gate equivalent by checking `not preview_blocked` instead of directly checking `preview.version_conflict is False`.

Document that beta testers should regenerate the draft against the current world version if this gate blocks.

This is a smoke-reporting/documentation change only:

- No backend API response shape changes.
- No frontend changes.
- No approval behavior changes.
- No secrets or request headers are added to smoke diagnostics.

## Acceptance Criteria

- Smoke summary includes `checks.approval_preview.blocked`.
- Smoke `ok` is false when approval preview reports `version_conflict: true`.
- Existing non-conflict smoke flow still passes.
- `BETA_TESTING.md` documents `checks.approval_preview.blocked` and the recovery action.
