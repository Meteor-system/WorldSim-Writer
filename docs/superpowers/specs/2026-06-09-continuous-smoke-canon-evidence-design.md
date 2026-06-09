# Continuous Smoke Canon Evidence Design

## Goal

Strengthen optional continuous two-chapter smoke diagnostics so beta testers can prove next-chapter prep sees the latest Story Bible/canon evidence before chapter 2 drafting.

## Current State

Backend and frontend now expose `truth_canon_version` and `truth_canon_excerpt` from `/worlds/{world_id}/next-chapter-prep`. Existing backend tests verify chapter 2 drafting uses latest canon, previous chapter summary, high-priority foreshadows, and stale draft approval rejection. Existing optional smoke verifies the two-chapter flow and reports world-version, previous-summary, foreshadow, stale-rejection, and approval-gate diagnostics.

The remaining gap is smoke evidence: `backend/scripts/e2e_smoke.py` does not require or summarize the new next-chapter prep canon fields. A beta smoke run can still pass without proving the prep endpoint exposed the current Story Bible snapshot.

## Selected Slice

Add display-only checks and JSON summary fields to the optional `E2E_CONTINUOUS_CHAPTERS=1` path:

- Require `truth_canon_version` and `truth_canon_excerpt` in the initial second-chapter prep response.
- Require the same fields in the fresh prep response after stale-canon update.
- Report whether the initial prep canon evidence matches `SECOND_CHAPTER_CANON` and whether the fresh prep canon evidence matches `STALE_DRAFT_CANON`.
- Report the prep canon versions alongside existing world-version checkpoints.

## Out of Scope

- No API route changes.
- No narrative generation or approval logic changes.
- No frontend changes.
- No new model calls or smoke steps.
- No change to the approval invariant that only user approval commits formal world-state changes.

## Test Strategy

Use TDD in `backend/tests/test_e2e_scripts.py`:

1. Update the fake next-chapter prep responses to include canon evidence.
2. Add assertions for new `checks.continuous_chapters` canon-evidence fields.
3. Run focused pytest and verify RED with missing summary keys.
4. Implement smoke requirements and summary fields in `backend/scripts/e2e_smoke.py`.
5. Update `BETA_TESTING.md` pass criteria.
6. Run focused, related, full backend tests, frontend build if frontend touched, diff checks, and commit.
