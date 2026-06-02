# E2E Smoke Readiness Ready Contract Design

## Context

The smoke script gates formal approval on `GET /chapters/{chapter_id}/approval-readiness`. It currently requires `status`, `blocking_reasons`, and `warnings`, then treats a response as blocked when `status == "blocked"` or `blocking_reasons` is non-empty. The backend schema exposes a direct `ready: bool` field, and the beta playbook already asks testers to inspect approval readiness before approval.

A malformed successful readiness response can return `ready` as a string, number, or object while still returning `status: "ready"` and empty blockers. In that case the smoke script can proceed to formal approval without proving the direct readiness contract is safe to consume. This is a small but important main-flow QA gap because readiness is one of the last pre-approval safety boundaries.

## Decision

Harden the approval-readiness smoke contract:

- Require `approval_readiness.ready` to be present before interpreting readiness.
- Require `approval_readiness.ready` to be a JSON boolean.
- Continue to allow `ready: false` with `status: "needs_review"` and no blockers to pass smoke, because non-blocking warnings are review evidence rather than formal write blockers.
- Reuse existing diagnostics:
  - `MISSING_REQUIRED_FIELDS` + `missing_fields: ["ready"]` for absent readiness evidence.
  - `INVALID_FIELD_TYPES` + `invalid_fields: ["ready"]` for non-boolean readiness evidence.
- Add `checks.approval_readiness.ready` to beta playbook pass criteria so testers know the direct boolean contract is part of smoke evidence.

## Non-goals

- Do not change backend approval-readiness API behavior.
- Do not require `ready` to be `true` for smoke success when `status` is `needs_review` and there are warnings only.
- Do not alter consistency, approval, event, overview, or export smoke behavior.
- Do not weaken the invariant that only user approval commits formal world state/events.

## Test strategy

Use strict inline TDD:

1. Add a failing smoke-script test for readiness missing `ready`.
2. Add a failing smoke-script test for readiness returning `ready` as a non-boolean string.
3. Implement minimal validation in `backend/scripts/e2e_smoke.py`.
4. Update `BETA_TESTING.md` and docs coverage terms.
5. Run focused tests, smoke-script tests, docs tests, relevant backend tests, and whitespace checks before committing.

## Beta value

This makes mock and real-LLM smoke safer at the approval boundary. It separates malformed readiness payloads from legitimate warning-only readiness states, making beta failures easier to triage and reducing the risk that a diagnostic smoke run approves a draft after receiving ambiguous readiness evidence.
