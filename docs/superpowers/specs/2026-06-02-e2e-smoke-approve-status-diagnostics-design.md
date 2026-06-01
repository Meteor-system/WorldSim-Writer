# E2E Smoke Approve Status Diagnostics Design

## Problem

The smoke script uses `approved.get('status') == 'approved'` in the final success gate, but it only requires `approved_version` after calling `POST /chapters/{chapter_id}/approve`. If the backend returns a 2xx approval response missing `status`, the smoke can end with `ok: false` without the clearer `MISSING_REQUIRED_FIELDS` diagnostic that other malformed success responses get.

## Goal

Require the approval response to include both `status` and `approved_version` so malformed successful approval responses fail with explicit field-level diagnostics.

## Scope

In scope:

- Update `backend/scripts/e2e_smoke.py` to require `status` and `approved_version` after approval.
- Add a regression test for an approval response that includes `approved_version` but omits `status`.
- Update `BETA_TESTING.md` to include approval status evidence in pass criteria.

Out of scope:

- Changing backend approval endpoint behavior.
- Changing approval transaction semantics.
- Frontend changes.

## Design

Change the existing approval required-field check from:

```python
_require_fields(summary, 'approve', approved, ['approved_version'])
```

to:

```python
_require_fields(summary, 'approve', approved, ['status', 'approved_version'])
```

This preserves the existing malformed-response convention:

```json
{
  "failed_step": "approve",
  "error": "MISSING_REQUIRED_FIELDS",
  "missing_fields": ["status"]
}
```

## Test strategy

Use the existing `SequencedTransport` test style. Add a full pre-approval-success flow where approval returns `{'id': 20, 'approved_version': 2}`. Assert the smoke stops at approval with `MISSING_REQUIRED_FIELDS` and `missing_fields == ['status']`, and that no events/export requests are made.
