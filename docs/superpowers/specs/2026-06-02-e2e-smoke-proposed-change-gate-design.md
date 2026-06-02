# E2E Smoke Proposed Change Gate Design

## Context

The smoke script is intended to prove the MVP writing loop includes draft generation, user approval, world-version advancement, event logging, export, and proposed world-state projection changes.

The current smoke summary records `approval_preview.character_changes` and `approval_preview.foreshadow_changes`, but the final `ok` gate does not require at least one proposed change. A backend or real-LLM response with no proposed character or foreshadow changes could still pass if approval increments the world version and emits `chapter_approved`.

That weakens beta confidence because a passing smoke run should demonstrate that the model generated at least one visible state-change proposal before approval.

## Goal

Fail smoke when the approval preview contains zero proposed character/foreshadow changes, and expose a clear `checks.approval_preview.proposed_change_count` value for beta reports.

## Approach

Update `backend/scripts/e2e_smoke.py` after approval preview succeeds:

- Count character changes.
- Count foreshadow changes.
- Add `proposed_change_count` to `summary['checks']['approval_preview']`.
- Include `proposed_change_count > 0` in the final `summary['ok']` gate.

Update tests:

- Add a regression test where every other smoke check succeeds but approval preview has no proposed changes; it should end with `ok: false` and `proposed_change_count == 0`.
- Update the successful smoke-flow fixture to include at least one proposed character change.
- Add a beta playbook docs regression term for `checks.approval_preview.proposed_change_count`.

Update `BETA_TESTING.md` mock smoke pass criteria to require `checks.approval_preview.proposed_change_count` greater than zero.

This is a smoke readiness change only:

- No backend generation/approval behavior changes.
- No frontend changes.
- No direct formal world-state writes are added outside approval.
- No secrets, tokens, headers, provider URLs, model names, or request payloads are added to diagnostics.

## Acceptance Criteria

- A smoke response with zero preview proposed changes reports `ok: false` while preserving the preview counts.
- The happy smoke unit test passes only when at least one preview proposed change is present.
- `BETA_TESTING.md` documents `checks.approval_preview.proposed_change_count` as a pass criterion.
