# E2E Smoke Preview Conflict Type Contract Design

## Context

The smoke script uses `GET /chapters/{chapter_id}/approval-preview` as the first pre-approval safety gate. It already stops when `version_conflict` is the JSON boolean `true`, and it validates that proposed character and foreshadow changes are lists of objects.

The remaining gap is the type contract for `version_conflict`. If a malformed success response returns a string such as `"true"` or `"false"`, the smoke currently treats it as not blocked because it only checks `preview.get('version_conflict') is True`. That can let the smoke continue through readiness, consistency, and formal approval after ambiguous version-conflict evidence. This matters for beta and real-LLM smoke triage because version conflict protects the core invariant that drafts generated from stale world state must not commit formal state.

## Decision

Harden the approval-preview smoke contract:

- Require `approval_preview.version_conflict` to be present.
- Require `approval_preview.version_conflict` to be a JSON boolean.
- Reuse the existing `MISSING_REQUIRED_FIELDS` diagnostic for absent `version_conflict`.
- Reuse the existing `INVALID_FIELD_TYPES` diagnostic for non-boolean `version_conflict`.
- Keep existing behavior for valid booleans:
  - `true` stops at `APPROVAL_PREVIEW_BLOCKED`.
  - `false` allows the smoke to continue if proposed changes are present.
- Document `version_conflict` as a boolean pre-approval signal in the beta playbook.

## Non-goals

- Do not change backend approval-preview API behavior.
- Do not change proposed-change validation beyond the existing list-of-object checks.
- Do not alter readiness, consistency, approval, overview, event, or export checks.
- Do not weaken the user-approval invariant from the product spec.

## Test strategy

Use strict inline TDD:

1. Add a failing smoke-script test for missing `version_conflict` in approval preview.
2. Add a failing smoke-script test for `version_conflict` returned as a string.
3. Implement minimal validation in `backend/scripts/e2e_smoke.py`.
4. Update `BETA_TESTING.md` and docs coverage terms.
5. Run focused tests, the smoke-script suite, docs coverage, full backend pytest, and diff checks before committing.

## Beta value

This improves pre-approval safety diagnostics by distinguishing malformed preview payloads from legitimate non-conflicting previews. It reduces the chance that a diagnostic smoke run performs a formal write after receiving ambiguous version-conflict evidence.
