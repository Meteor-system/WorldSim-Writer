# E2E Smoke Consistency Status Contract Design

## Context

The smoke script calls `POST /chapters/{chapter_id}/approval-consistency` before formal approval. The backend schema constrains `consistency_summary.status` to one of `clear`, `needs_review`, or `blocked`, and `blocking_count > 0` is a formal approval blocker.

The smoke script currently verifies that `consistency_summary.status` exists and that `consistency_summary.blocking_count` is an integer, but it does not validate the status value. A malformed success payload such as `status: "unknown"` with `blocking_count: 0` can be treated as non-blocking and proceed to formal approval. That weakens real/mock smoke diagnostics because invalid consistency evidence should be localized to `failed_step: "approval_consistency"`, not allowed to pass silently.

## Decision

Harden the approval-consistency smoke contract:

- Require `consistency_summary.status` to be a string in the allowed set: `clear`, `needs_review`, or `blocked`.
- Reuse existing diagnostics:
  - `INVALID_FIELD_TYPES` with `invalid_fields: ["consistency_summary.status"]` for non-string status values.
  - `INVALID_FIELD_VALUES` with `invalid_fields: ["consistency_summary.status"]` for unsupported status strings.
- Keep existing blocking behavior:
  - `blocked` or `blocking_count > 0` stops smoke with `APPROVAL_CONSISTENCY_BLOCKED`.
  - `clear` and `needs_review` with `blocking_count == 0` may proceed, preserving warning-only review evidence.
- Document the allowed consistency statuses in the beta playbook.

## Non-goals

- Do not change backend consistency API behavior.
- Do not validate the full warning object schema beyond the existing list-of-dicts check.
- Do not alter approval, overview, event, export, or LLM behavior.
- Do not weaken the invariant that only approved chapters commit formal world state.

## Test strategy

Use strict inline TDD:

1. Add a failing smoke-script test for a non-string `consistency_summary.status`.
2. Add a failing smoke-script test for an unsupported string status.
3. Implement small path string/set validation in `backend/scripts/e2e_smoke.py`.
4. Update beta playbook diagnostics and docs coverage terms.
5. Run focused tests, smoke-script tests, docs coverage, relevant/full backend tests, and diff checks before committing.

## Beta value

This makes the last pre-approval consistency gate more trustworthy. It prevents real/mock smoke from approving a chapter after receiving malformed consistency status evidence, and it gives beta testers a precise diagnostic when the consistency endpoint contract drifts.
