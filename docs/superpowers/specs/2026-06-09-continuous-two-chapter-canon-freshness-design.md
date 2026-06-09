# Continuous Two-Chapter Canon Freshness Design

## Goal

Strengthen continuous two-chapter backend E2E coverage by proving chapter 2 uses a Story Bible/canon edit made after chapter 1 approval.

## Context

Commit `900b78a` already added strong continuous-chapter coverage in `backend/tests/test_narrative_pipeline.py::test_continuous_two_chapters_use_latest_context_and_stale_third_draft_is_blocked`. That test already proves chapter 2 can be generated and approved after chapter 1, chapter 2 sees the previous chapter summary and unresolved/advanced foreshadow context, and a stale later draft cannot be approved.

The remaining small gap is that the continuous two-chapter path only asserts the default canon is present in the chapter 2 prompt. A separate test proves manual Story Bible edits feed generation, but not in the chapter-1-to-chapter-2 continuous flow.

## Design

Keep the existing integration test and add one canon edit between chapter 1 approval and chapter 2 prep:

1. Approve chapter 1.
2. Update the world canon with a distinctive chapter-2 setup sentence.
3. Fetch next-chapter prep after the canon edit.
4. Generate chapter 2 with that prep.
5. Assert the captured chapter 2 prompt contains:
   - the updated canon text,
   - the latest world version after chapter 1 approval plus canon edit,
   - the previous chapter summary,
   - the still-unresolved/advanced foreshadow context,
   - the user-modified chapter 2 goal.
6. Keep existing assertions that chapter 2 approves successfully and a later stale draft approval returns `WORLD_VERSION_MISMATCH`, adjusting expected world versions for the canon edit.

## Scope

In scope:

- Test-only strengthening of `backend/tests/test_narrative_pipeline.py`.
- No production behavior changes unless the test exposes a real gap.
- No smoke-script real-LLM expansion in this step, because the requested behaviors are already best verified without paying for multiple real model calls.

Out of scope:

- Frontend changes.
- New API endpoints.
- Additional real LLM smoke calls.
- Broader refactors of narrative services or execution context shape.

## Test Strategy

Use TDD by first changing the existing continuous test expectations to require a post-chapter-1 canon edit in the chapter 2 prompt. Run that single test and confirm it fails because the edit has not yet been made in the flow. Then add the minimal test setup canon update and adjust expected versions. Run the focused test, related narrative tests, and full backend pytest before committing.
