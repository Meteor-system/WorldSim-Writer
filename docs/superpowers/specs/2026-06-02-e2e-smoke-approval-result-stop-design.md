# E2E Smoke Approval Result Stop Design

## Context

The beta smoke script verifies the MVP writing loop from health preflight through approval, event history, and markdown export. Recent hardening made the script stop early for unsafe pre-approval states. The next remaining diagnostic gap is after the approval call: if the approval response is a successful HTTP response but says the chapter was not approved, or if the returned world version does not advance from the draft baseline, the script currently records `ok: false` only at the end and can continue into later event/export checks.

## Goal

Make approval-result failures explicit and stop the smoke flow before later checks when formal approval did not clearly succeed.

## Selected approach

Add two approval-step hard stops in `backend/scripts/e2e_smoke.py` immediately after `checks.approve` is populated:

1. If `approved.status != "approved"`, set:
   - `failed_step: "approve"`
   - `error: "APPROVAL_STATUS_NOT_APPROVED"`
   - return the summary.
2. If `approved_version` does not equal the expected next world version, set:
   - `failed_step: "approve"`
   - `error: "WORLD_VERSION_NOT_INCREMENTED"`
   - return the summary.

This keeps all approval evidence in `checks.approve` while preventing later event/export diagnostics from obscuring the root failure.

## Scope

In scope:

- Smoke script diagnostics.
- Smoke-script regression tests.
- Beta playbook documentation and docs regression terms.
- Concise implementation plan.

Out of scope:

- Backend approval endpoint behavior changes.
- Frontend UI changes.
- Real model prompt changes.
- Cleanup script changes.

## Acceptance criteria

- A successful HTTP approval response with `status` other than `approved` stops at `approve` with `APPROVAL_STATUS_NOT_APPROVED`.
- A successful HTTP approval response with a non-incrementing `approved_version` stops at `approve` with `WORLD_VERSION_NOT_INCREMENTED`.
- In both cases, no events or markdown export requests are made.
- `BETA_TESTING.md` documents the new diagnostics.
- Relevant backend tests and full backend tests pass.
- `git diff --check` and `git diff --cached --check` pass.
