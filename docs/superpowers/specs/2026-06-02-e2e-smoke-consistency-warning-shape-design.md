# E2E Smoke Consistency Warning Shape Design

## Context

The smoke script checks approval consistency before formal chapter approval. It currently requires `consistency_summary.status`, but it treats a missing or malformed `consistency_warnings` field as an empty list. That can hide the very warning evidence beta testers need when real/local LLM smoke reaches the consistency gate.

Approval consistency is part of the pre-approval safety boundary. When a successful API response has the wrong shape, the smoke should stop at `failed_step: "approval_consistency"` with a malformed-response diagnostic rather than silently dropping warning details and continuing toward approval.

## Decision

Harden the approval-consistency smoke contract:

- Require `consistency_warnings` to be present in the approval-consistency response.
- Require `consistency_warnings` to be a list of objects before copying it into `checks.approval_consistency.warnings`.
- Reuse existing diagnostics:
  - `MISSING_REQUIRED_FIELDS` + `missing_fields` for absent `consistency_warnings`.
  - `INVALID_FIELD_TYPES` + `invalid_fields` for non-list or non-object warning collections.
- Preserve the existing consistency blocker behavior for valid responses whose `consistency_summary.status` or `blocking_count` indicates approval is unsafe.

## Non-goals

- Do not change backend approval-consistency API behavior.
- Do not validate every field inside each consistency warning in this fix.
- Do not change chapter approval, event, or export behavior.
- Do not weaken the invariant that generated drafts only commit formal world state/events after approval.

## Test strategy

Use strict TDD:

1. Add a failing smoke-script test for an approval-consistency response missing `consistency_warnings`.
2. Add a failing smoke-script test for `consistency_warnings` returned as a string.
3. Add a docs regression expectation that the beta playbook mentions approval consistency warning lists in malformed response diagnostics.
4. Implement minimal validation in `backend/scripts/e2e_smoke.py` using existing helper functions.
5. Verify focused tests pass, then run smoke-script tests, docs regression tests, and backend verification.

## Beta value

This improves real/local LLM smoke triage by ensuring consistency warning evidence is never silently discarded before approval. Beta testers get a precise malformed-response diagnostic instead of an empty warnings list that can mislead debugging.