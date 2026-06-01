# E2E Smoke Approval Readiness Blocker Gate Design

## Context

The smoke script already calls `/chapters/{chapter_id}/approval-readiness` and records `ready`, `status`, `blocking_reasons`, and `warnings`. However, the final `ok` calculation does not require the readiness result to be unblocked. That means a faulty or mocked API sequence could report `ok: true` even when approval readiness reported blocking reasons before approval.

The product invariant is that generated drafts can propose changes, but only safe user approval commits formal world-state changes. The readiness endpoint is part of that safety surface: `status: "blocked"` and non-empty `blocking_reasons` mean the draft should not be considered a clean main-flow pass.

## Decision

Keep warnings non-blocking for smoke because current happy-path smoke can legitimately return `status: "needs_review"` with warnings for missing optional reports. Add a derived boolean to smoke summary:

```json
"checks": {
  "approval_readiness": {
    "ready": false,
    "status": "needs_review",
    "blocking_reasons": [],
    "warnings": ["..."],
    "blocked": false
  }
}
```

Fail final smoke `ok` when approval readiness is blocked:

- `readiness.status == "blocked"`, or
- `blocking_reasons` is non-empty.

Do not stop immediately after readiness. Continuing through approval/export preserves diagnostic context for beta reports, but `ok` must be `false` if readiness was blocked.

## Testing

Use TDD:

1. Add a smoke-script regression test where approval readiness returns `status: "blocked"` and a blocking reason, while later mocked API responses appear successful.
2. Confirm the new test fails because smoke currently returns `ok: true`.
3. Add `blocked` to `checks.approval_readiness` and include `not readiness_blocked` in final `summary.ok`.
4. Update `BETA_TESTING.md` and the docs regression test to document `checks.approval_readiness.blocked`.

## Scope boundaries

- Do not change backend approval behavior.
- Do not make `needs_review` warnings fail smoke.
- Do not add external services or new dependencies.
