# E2E Smoke Consistency Warning Evidence Design

## Context

The smoke script already calls `/chapters/{chapter_id}/approval-consistency`, derives `checks.approval_consistency.blocked`, and fails final `ok` when blocking consistency issues are present. `BETA_TESTING.md` tells testers to inspect the consistency summary/warnings when this gate blocks.

The current smoke summary keeps the consistency summary fields but drops the `consistency_warnings` array returned by the API. That means a failed real-LLM smoke can say consistency is blocked without preserving the specific warning category, severity, object, change index, or message needed for triage.

## Goal

Preserve approval-consistency warning details in the smoke JSON without changing backend approval behavior or exposing secrets.

## Approach

Add a `warnings` field under `checks.approval_consistency` populated from `consistency_warnings` when it is a list. Continue deriving `blocked` only from `consistency_summary.status == "blocked"` or `blocking_count > 0`; warning-only `needs_review` results stay non-blocking.

This is intentionally a smoke-reporting change only:

- No API response shape changes.
- No frontend changes.
- No approval/readiness behavior changes.
- No headers, tokens, API keys, request payloads, provider URLs, or model names are added to the smoke summary.

## Acceptance Criteria

- A smoke response with blocking consistency warnings includes `checks.approval_consistency.warnings` in the summary.
- The existing blocked consistency gate still makes `summary.ok` false.
- A warning-only consistency response can include warnings while remaining non-blocking.
- `BETA_TESTING.md` documents that consistency warning details are captured at `checks.approval_consistency.warnings`.
- Existing smoke diagnostics remain secret-safe.
