# Studio Clear Stale Candidate Context Design

## Goal

When a user approves a chapter and clicks `继续下一章`, clear the old Studio launch execution context so candidate material from the approved chapter does not silently carry into the next chapter session.

## Selected Small MVP Fix

Studio can be launched from next-chapter preparation with candidate material references. Those references are useful for the current chapter, but after approval the `继续下一章` button should start a fresh chapter session based on the updated world.

The next session should:

- show the normal `创建章节` button unless a new next-chapter prep context is provided;
- create a manual execution context from the updated world if the user types a new goal directly;
- use the updated `world_version` and next chapter number;
- send `material_references: []` for this new manual context;
- avoid showing stale candidate titles from the approved chapter.

## Scope

- Frontend-only state handling in `frontend/src/studio/StudioPage.tsx`.
- Add a Studio regression test that starts from a launch context with candidate material, approves, continues, then creates the next chapter.
- Preserve backend/API/database/import behavior and approval payload shape.
- Preserve the invariant that candidate material is writing/reference context only and never auto-mutates formal canon, world projections, world version, or event history.

## Non-Goals

- No backend API changes.
- No database changes.
- No import candidate persistence changes.
- No new LLM prompt behavior.
- No broad Studio layout redesign.

## Testing

Use TDD in `frontend/src/studio/StudioPage.test.tsx`:

1. Start Studio with a next-chapter execution context containing candidate material.
2. Create, outline, draft, approve, and continue to the next chapter.
3. Expect stale candidate reference UI to disappear and the create button to return to `创建章节`.
4. Create a new chapter and verify the submitted execution context is manual, based on the updated world version, and has empty `material_references`.
5. Assert raw/internal terms such as `asset_id`, `batch_id`, `inspiration`, and `正式 canon` remain hidden.
