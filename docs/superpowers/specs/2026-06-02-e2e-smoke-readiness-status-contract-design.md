# E2E Smoke Readiness Status Contract Design

## Context

The smoke script already validates that approval readiness includes a boolean `ready` flag plus list-shaped `blocking_reasons` and `warnings`. The backend schema also constrains `approval-readiness.status` to `ready`, `needs_review`, or `blocked`, but the smoke script currently treats status as an unvalidated string-like field when computing whether it should stop before formal approval.

## Problem

If a real-LLM or backend regression returns a malformed readiness status such as an integer, empty string, or unsupported value, the smoke script can continue with ambiguous pre-approval safety evidence as long as `blocking_reasons` is empty. That weakens the beta safety gate whose purpose is to stop before formal approval when readiness evidence is malformed.

## Decision

Add a focused allowed-value check for `approval_readiness.status` in `backend/scripts/e2e_smoke.py`, mirroring the backend `ApprovalReadinessResponse` schema:

- Accept only `ready`, `needs_review`, and `blocked`.
- Report non-string or empty status as `INVALID_FIELD_TYPES` with `invalid_fields: ["status"]`.
- Report unsupported status strings as `INVALID_FIELD_VALUES` with `allowed_values: {"status": ["blocked", "needs_review", "ready"]}`.
- Run this validation before deriving `checks.approval_readiness.blocked` and before any formal approval request.

## Scope

In scope:

- Add smoke regression tests for non-string and unsupported readiness status.
- Add a small status constant and validation call in the smoke script.
- Update beta playbook diagnostics and docs coverage terms.

Out of scope:

- Changing backend readiness behavior or response schemas.
- Changing approval semantics.
- Adding new smoke endpoints or frontend behavior.

## Test strategy

Use TDD:

1. Add failing tests proving malformed readiness status stops at `approval_readiness` before consistency or approval.
2. Implement the minimal smoke validation.
3. Run focused smoke tests, docs coverage, full smoke-script tests, and backend pytest as needed.

## Self-review

- The design preserves the core invariant: generated drafts may propose changes, but only validated user approval commits formal world-state changes.
- No placeholders or broad refactors are included.
- The allowed values match `ApprovalReadinessResponse.status` in `backend/app/narrative/schemas.py`.
