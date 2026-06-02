# E2E Smoke Consistency Blocking Count Contract Design

## Context

The smoke script validates that `approval-consistency` returns a known `consistency_summary.status` and an integer `consistency_summary.blocking_count`. It then treats the consistency gate as blocked when status is `blocked` or the count is greater than zero.

## Problem

A negative `consistency_summary.blocking_count` is type-safe but semantically invalid. If a malformed real-LLM or backend response returns `status: "clear"` with `blocking_count: -1`, the smoke script currently treats the gate as unblocked and can proceed to formal approval with impossible consistency evidence.

## Decision

Require `consistency_summary.blocking_count` to be a non-negative integer before deriving `checks.approval_consistency.blocked`.

- Keep existing `MISSING_REQUIRED_FIELDS` behavior when the path is absent.
- Keep existing `INVALID_FIELD_TYPES` behavior for non-integers and booleans.
- Add `INVALID_FIELD_VALUES` for negative integers with `invalid_fields: ["consistency_summary.blocking_count"]`.
- Stop before formal approval when the value is negative.

## Scope

In scope:

- Add a focused smoke regression test for negative `blocking_count`.
- Add a minimal non-negative integer path validator in `backend/scripts/e2e_smoke.py`.
- Update beta docs and docs coverage to mention non-negative blocker counts.

Out of scope:

- Changing backend consistency response schemas.
- Changing warning categorization or blocker derivation beyond rejecting impossible negative values.
- Adding new endpoints or frontend behavior.

## Test strategy

Use TDD:

1. Add a failing test proving `blocking_count: -1` stops at `approval_consistency` before approval.
2. Implement the minimal validation.
3. Run focused smoke tests, smoke-script tests, docs coverage, and backend pytest.

## Self-review

- The design preserves the approval safety invariant by preventing formal approval after impossible pre-approval consistency evidence.
- The diagnostic style matches the existing `INVALID_FIELD_VALUES` pattern for supported-but-invalid values.
- The scope is limited to smoke diagnostics, tests, beta docs, and planning artifacts.
