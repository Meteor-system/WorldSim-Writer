# E2E Smoke Consistency Count Shape Design

## Context

The smoke script gates formal chapter approval on the approval-consistency endpoint. It currently requires `consistency_summary.status`, but it does not require or type-check `consistency_summary.blocking_count` before comparing it with `0`. A malformed successful response can therefore either continue without count evidence or raise a Python `TypeError` instead of returning the safe JSON diagnostic format beta testers rely on.

Approval consistency is a pre-approval safety boundary. Response-shape failures should be localized to `failed_step: "approval_consistency"` and should not crash the smoke process or continue toward approval with incomplete blocker evidence.

## Decision

Harden the approval-consistency summary contract:

- Require `consistency_summary.blocking_count` before interpreting consistency blocker state.
- Require `consistency_summary.blocking_count` to be an integer.
- Use existing diagnostics:
  - `MISSING_REQUIRED_FIELDS` + `missing_fields` for absent `consistency_summary.blocking_count`.
  - `INVALID_FIELD_TYPES` + `invalid_fields` for non-integer `consistency_summary.blocking_count`.
- Preserve the existing `APPROVAL_CONSISTENCY_BLOCKED` gate for valid responses where status is `blocked` or `blocking_count > 0`.

## Non-goals

- Do not change backend approval-consistency API behavior.
- Do not validate all consistency summary counters in this fix.
- Do not change approval, events, export, or LLM behavior.
- Do not weaken the invariant that only user approval commits formal world state/events.

## Test strategy

Use strict TDD:

1. Add a failing smoke-script test for a consistency response missing `consistency_summary.blocking_count`.
2. Add a failing smoke-script test for `consistency_summary.blocking_count` returned as a string.
3. Add a docs regression expectation that the beta playbook mentions approval consistency blocker counts in malformed response diagnostics.
4. Implement minimal nested integer validation in `backend/scripts/e2e_smoke.py`.
5. Verify focused tests pass, then run smoke-script tests, docs regression tests, and backend verification.

## Beta value

This improves beta-blocking stability by keeping real/local LLM smoke failures in the structured JSON diagnostic path even when the consistency API returns malformed blocker-count data.