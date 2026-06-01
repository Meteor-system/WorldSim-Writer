# E2E Smoke Approval Consistency Blocker Gate Design

## Context

The smoke script already calls `/chapters/{chapter_id}/approval-consistency` and records the returned `consistency_summary`, but final smoke `ok` does not require the consistency result to be unblocked. The backend approval path blocks consistency failures, but smoke should still make the consistency gate explicit in its JSON summary and pass criteria.

This is especially useful for beta triage and real-LLM smoke: testers should see whether a failure is caused by model-proposed state changes that violate approval consistency, not only by a later `approve` HTTP failure.

## Decision

Add a derived boolean to the smoke summary:

```json
"checks": {
  "approval_consistency": {
    "status": "blocked",
    "blocking_count": 1,
    "blocked": true
  }
}
```

`blocked` is true when either:

- `consistency_summary.status == "blocked"`, or
- `consistency_summary.blocking_count > 0`.

Final smoke `ok` must require `checks.approval_consistency.blocked` to be false. `status: "needs_review"` and warning-only consistency results remain non-blocking for smoke.

## Testing

Use TDD:

1. Add a smoke-script regression test where approval consistency returns a blocked summary while later mocked responses appear successful.
2. Confirm RED because smoke currently returns `ok: true` or lacks `blocked`.
3. Implement the derived boolean and final `ok` gate.
4. Update `BETA_TESTING.md` and the docs regression test to document `checks.approval_consistency.blocked`.

## Scope boundaries

- Do not change backend approval consistency behavior.
- Do not make warning-only consistency results fail smoke.
- Do not add external services or dependencies.
