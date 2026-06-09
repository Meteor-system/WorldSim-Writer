# Continuous Smoke Approval Gate Diagnostics Design

## Goal

Make optional two-chapter smoke output more useful for beta triage by reporting the second chapter approval gate evidence that is already checked internally.

## Current State

Backend coverage already verifies the core continuous chapter invariant: chapter 2 can be generated after chapter 1 approval, it uses updated Story Bible/canon, previous chapter summary, current world version, changed character state/goals, unresolved foreshadow context, and a user-edited goal. It also verifies stale later drafts cannot be approved after `world_version` changes.

The optional smoke path in `backend/scripts/e2e_smoke.py` also performs second-chapter approval preview, readiness, consistency, approval, and overview checks. However, `checks.continuous_chapters` currently reports context freshness and approval success without surfacing the approval-gate diagnostics for the fresh second chapter. Beta testers can see that chapter 2 was approved, but cannot distinguish whether preview/readiness/consistency gates were clean or merely passed without details.

## Selected Slice

Add display-only JSON diagnostics to the existing optional continuous smoke summary:

1. Report the fresh second-chapter approval preview gate:
   - `second_preview_version_conflict`
   - `second_proposed_change_count`
2. Report approval readiness gate:
   - `second_readiness_status`
   - `second_readiness_blocked`
3. Report approval consistency gate:
   - `second_consistency_status`
   - `second_consistency_blocked`
4. Update `BETA_TESTING.md` so beta testers know these fields should show no conflict/blocking and at least one proposed change.

## Out of Scope

- No backend API changes.
- No changes to narrative generation or approval logic.
- No frontend changes.
- No new smoke steps or model calls.
- No changes to the invariant that only approval commits formal world-state changes.

## Test Strategy

Use TDD in `backend/tests/test_e2e_scripts.py`:

1. Add failing assertions to `test_e2e_smoke_script_optionally_checks_continuous_second_chapter_and_stale_draft` for the new `checks.continuous_chapters` fields.
2. Run the focused test and confirm RED because the fields are missing.
3. Add the fields to the existing `summary['checks']['continuous_chapters']` block in `backend/scripts/e2e_smoke.py` using values already computed in the optional continuous path.
4. Update `BETA_TESTING.md` continuous-smoke pass criteria.
5. Run focused script test, all e2e script tests, relevant backend tests, and diff checks before committing.
