# Continuous Smoke Context Diagnostics Design

## Goal

Make optional two-chapter smoke output more useful for MVP/Beta triage without changing backend API behavior.

## Current State

The backend already covers the core continuous chapter invariant: after chapter 1 approval, chapter 2 can be drafted from latest Story Bible/canon, previous chapter summary, current character/foreshadow projection, and frozen execution context; stale world-version drafts are rejected with `WORLD_VERSION_MISMATCH`. The optional `E2E_CONTINUOUS_CHAPTERS=1` smoke path already edits canon, fetches next-chapter prep, drafts a second chapter, verifies stale approval rejection, regenerates, and approves chapter 2.

The remaining small gap is diagnostic detail. The smoke summary currently reports that previous chapter summary and priority foreshadows are present, but it does not expose enough echoed second/fresh execution-context evidence to quickly tell whether the draft was generated with the intended goal, source version, previous summary, and priority foreshadow context.

## Selected Slice

Enhance `scripts/e2e_smoke.py` continuous-mode summary only:

1. Keep the existing optional smoke flow and API calls unchanged.
2. Add summary fields under `checks.continuous_chapters` for:
   - the initial canon edit world version,
   - second draft source world version,
   - whether the second draft echoed the requested goal,
   - whether the second draft echoed previous chapter summary,
   - the second draft priority foreshadow count,
   - stale setup world version,
   - fresh prep world version,
   - whether the fresh draft echoed the regenerated goal,
   - whether the fresh draft echoed previous chapter summary,
   - the fresh draft priority foreshadow count,
   - expected post-second-approval world version.
3. Add/update script tests first so the new fields fail before implementation.
4. Update beta runbook text if it names continuous smoke pass criteria.

## Out of Scope

- No backend service behavior change unless the diagnostics test reveals a real bug.
- No frontend change.
- No new smoke API endpoints.
- No dynamic workflows or subagents.

## Test Strategy

Use TDD in `backend/tests/test_e2e_scripts.py`:

1. Add assertions to the existing continuous smoke script test for the new diagnostic fields.
2. Run the focused test and confirm it fails because the summary lacks those fields.
3. Implement minimal summary additions in `backend/scripts/e2e_smoke.py`.
4. Re-run the focused test, related script tests, full backend tests, and `git diff --check` before commit.
