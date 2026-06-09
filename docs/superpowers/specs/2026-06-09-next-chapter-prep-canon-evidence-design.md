# Next Chapter Prep Canon Evidence Design

## Goal

Make the next-chapter prep evidence clearer for beta testers by showing which current Story Bible/canon snapshot will feed chapter 2+ creation.

## Current State

The next-chapter prep API already returns the current `world_version`, previous chapter summary, priority characters, priority foreshadows, progression hints, recent events, and candidate material references. Backend tests already cover that chapter generation uses the latest Story Bible/canon, and optional smoke diagnostics cover two-chapter continuity gates.

The remaining beta-readiness gap is evidence visibility: the next-chapter prep panel does not show the current Story Bible/canon snapshot even though the backend generation prompt uses `world.truth_canon`. A tester can see previous chapter and unresolved foreshadows, but cannot confirm from the prep UI/API that the next chapter is grounded in the latest formal Story Bible text.

## Selected Slice

Add two display-only fields to `/worlds/{world_id}/next-chapter-prep`:

- `truth_canon_version`: the current formal Story Bible/canon version.
- `truth_canon_excerpt`: a short excerpt from the current formal Story Bible/canon.

Render those fields in `NextChapterPrepPanel` as "当前 Story Bible" evidence near the suggested goal and source signals.

## Constraints

- Additive API response only; do not remove or rename existing fields.
- Do not change narrative generation, approval, model calls, or world-state mutation behavior.
- Preserve the invariant that formal world-state changes only happen on approval or explicit manual edits.
- Keep candidate material copy clear that imported material remains writing reference and does not auto-write formal canon.

## Test Strategy

Use TDD:

1. Backend RED: add assertions to `test_next_chapter_prep_uses_high_priority_character_arc_progression_hint` for `truth_canon_version` and `truth_canon_excerpt`; verify the focused pytest fails because the fields are missing.
2. Backend GREEN: add fields to `NextChapterPrepResponse` and `get_next_chapter_prep` using the current `World` row.
3. Frontend RED: add panel expectations for Story Bible version/excerpt; verify the focused Vitest fails because the UI does not render them.
4. Frontend GREEN: extend `NextChapterPrepResponse` type and render the evidence in `NextChapterPrepPanel`.
5. Run focused and related tests, frontend build, diff checks, then commit.
