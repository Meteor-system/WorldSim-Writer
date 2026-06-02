# E2E Smoke Consistency Contract Design

## Problem

The smoke script calls approval consistency before approval, but if the response omits `consistency_summary.status`, the script currently treats the missing status as non-blocking and can continue to formal approval. That weakens the pre-approval safety gate and can hide malformed consistency responses during real-LLM or main-flow QA.

## Goal

Require approval consistency responses to include `consistency_summary.status` before smoke can continue to approval.

## Scope

In scope:

- Add a required-path check for `consistency_summary.status` in `backend/scripts/e2e_smoke.py` after the approval consistency call.
- Add a regression test proving smoke stops at `approval_consistency` when the nested status is missing.
- Document the contract in `BETA_TESTING.md` and docs regression coverage.

Out of scope:

- Changing backend consistency endpoint behavior.
- Changing consistency warning schemas.
- Frontend changes.

## Design

After the approval consistency response is parsed and before deriving `consistency_blocked`, call:

```python
_require_paths(summary, 'approval_consistency', consistency, ['consistency_summary.status'])
```

If the path is missing, smoke returns the existing malformed-success diagnostic:

```json
{
  "failed_step": "approval_consistency",
  "error": "MISSING_REQUIRED_FIELDS",
  "missing_fields": ["consistency_summary.status"]
}
```

This prevents the smoke from approving a draft when the consistency gate response is malformed.

## Test strategy

Add a full smoke-flow test through readiness where approval consistency returns `{'consistency_summary': {}, 'consistency_warnings': []}`. Assert the smoke stops at `approval_consistency`, reports `MISSING_REQUIRED_FIELDS`, lists `consistency_summary.status`, and does not call approve/events/export.
