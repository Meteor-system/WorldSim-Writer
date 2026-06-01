# E2E Smoke Preview Change Type Diagnostics Design

## Context

The smoke script already validates collection response shapes for event history and markdown export before iterating them. The approval preview step still counts `character_changes` and `foreshadow_changes` with `len(preview.get(...) or [])`. If a successful API response returns a string or object for either field, the smoke can compute a misleading proposed-change count instead of stopping with a clear malformed-response diagnostic.

Approval preview is the last checkpoint before readiness, consistency, and formal approval. For beta readiness, malformed proposed-change collections should stop at `failed_step: "approval_preview"` and identify the unsafe fields.

## Decision

Require approval preview `character_changes` and `foreshadow_changes` to be lists of objects before counting proposed changes.

The implementation will:

- Reuse `_require_list_of_dicts(...)` from `backend/scripts/e2e_smoke.py`.
- Validate both preview change collections immediately after the preview response and before `len(...)` counts.
- Return the existing `INVALID_FIELD_TYPES` diagnostic with `invalid_fields` pointing to the malformed field.
- Preserve existing behavior for empty lists, version conflicts, and no proposed projection changes.
- Update beta playbook wording so testers know approval preview collections are also covered by `INVALID_FIELD_TYPES`.

## Non-goals

- Do not change backend approval preview API schemas.
- Do not change smoke pass criteria or formal approval behavior.
- Do not inspect individual change object contents in this fix.
- Do not alter the writing-loop invariant: drafts may propose changes, only approval commits formal world state/events.

## Test strategy

Use strict TDD:

1. Add a focused failing test where `approval_preview.character_changes` is a dict.
2. Add a focused failing test where `approval_preview.foreshadow_changes` is a string.
3. Verify each test fails because the smoke currently continues past malformed preview collection fields.
4. Add minimal validation before preview counts.
5. Verify focused tests pass, then run all smoke-script tests and docs tests.

## Beta value

This improves main-flow QA and real/local LLM smoke diagnosability. Beta testers get a localized malformed-response diagnostic before the smoke attempts later approval checks, making preview-contract regressions easier to reproduce and report.