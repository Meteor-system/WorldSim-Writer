# E2E Smoke Pre-Approval Stop Design

## Problem

The smoke script records approval preview/readiness/consistency blockers, but it can continue through `POST /chapters/{chapter_id}/approve` even after a pre-approval gate has already proven the draft should not be approved. That weakens beta safety because a diagnostic smoke run should not attempt a formal write when its own checks say approval is unsafe or meaningless.

## Goal

Stop the smoke flow before `approve` when a pre-approval gate is blocked or when approval preview contains zero proposed projection changes.

## Scope

In scope:

- Approval preview `version_conflict` should stop the smoke before readiness/consistency/approve.
- Approval preview with zero character/foreshadow changes should stop before readiness/consistency/approve.
- Approval readiness blocked by status or blocking reasons should stop before consistency/approve.
- Approval consistency blocked by status or blocking count should stop before approve.
- The JSON summary should keep the existing `checks.*` diagnostics and add a concise `failed_step`/`error` for the stopping gate.
- `BETA_TESTING.md` should tell testers that blocked pre-approval checks stop before formal approval.

Out of scope:

- Backend approval endpoint behavior.
- Frontend behavior.
- LLM prompt changes.
- Changing the core invariant that only user approval commits formal world state/events.

## Design

`backend/scripts/e2e_smoke.py` will treat pre-approval gate failures as hard stops rather than final `ok: false` conditions after attempted approval.

Error codes:

- `APPROVAL_PREVIEW_BLOCKED` for preview version conflicts.
- `NO_PROPOSED_PROJECTION_CHANGES` for preview responses with zero proposed character/foreshadow changes.
- `APPROVAL_READINESS_BLOCKED` for readiness blockers.
- `APPROVAL_CONSISTENCY_BLOCKED` for consistency blockers.

The script will set `failed_step` to the gate that stopped the flow and `error` to the matching code, then return the summary without calling later endpoints.

## Test strategy

Use the existing `SequencedTransport` smoke-script tests to prove the script stops before later requests. Focused tests will assert the request path list ends at the failing pre-approval endpoint.
