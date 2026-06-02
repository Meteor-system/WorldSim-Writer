# E2E Smoke Readiness Response Shape Design

## Context

The smoke script gates formal approval on the approval-readiness endpoint. It currently records `status`, `blocking_reasons`, and `warnings`, but it does not require `status` to be present and does not validate that `blocking_reasons` and `warnings` are lists. A malformed successful response can therefore either continue with incomplete readiness evidence or treat a string/dict as blocking data without a clear malformed-response diagnostic.

Approval readiness is part of the main writing-loop safety boundary before formal approval. For beta readiness and real/local LLM smoke triage, response-shape failures should be localized to `failed_step: "approval_readiness"`.

## Decision

Harden the approval-readiness smoke contract:

- Require `approval_readiness.status` before interpreting readiness.
- Require `approval_readiness.blocking_reasons` to be a list.
- Require `approval_readiness.warnings` to be a list.
- Use existing diagnostics:
  - `MISSING_REQUIRED_FIELDS` + `missing_fields` for absent `status`.
  - `INVALID_FIELD_TYPES` + `invalid_fields` for non-list readiness collections.
- Preserve the existing `APPROVAL_READINESS_BLOCKED` gate for valid readiness responses whose status or blocking reasons indicate approval is unsafe.

## Non-goals

- Do not change backend readiness API behavior.
- Do not inspect the contents of readiness warning/reason items in this fix.
- Do not alter approval, consistency, event, or export smoke flow.
- Do not weaken the invariant that only approval commits formal world state/events.

## Test strategy

Use strict TDD:

1. Add a failing test for a readiness response missing `status`.
2. Add a failing test for `blocking_reasons` returned as a string.
3. Add a failing test for `warnings` returned as a string.
4. Implement a small `_require_list(...)` helper or equivalent validation in `backend/scripts/e2e_smoke.py`.
5. Verify focused tests pass, then run smoke-script tests, docs regression tests, and full backend pytest.

## Beta value

This improves beta triage by distinguishing malformed readiness responses from legitimate readiness blockers, reducing false debugging trails during mock and real/local LLM smoke runs.