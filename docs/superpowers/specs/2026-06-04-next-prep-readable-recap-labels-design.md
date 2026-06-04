# Next Chapter Prep Readable Recap Labels Design

## Goal

Make the Next Chapter Prep world-ops recap easier for newcomers to read by replacing raw role/status/event labels with Chinese labels, while preserving imported material safety and canon-guard behavior.

## Selected Small MVP Fix

`NextChapterPrepPanel` is part of the newcomer loop and first-chapter preparation path. It already shows imported candidate materials as safe writing references, but the same panel still exposes raw backend-style labels such as `protagonist`, `advanced`, `urgency 4`, and `chapter_approved`. The highest-value small fix is to localize those recap labels so the preparation panel feels like a user-facing writing assistant rather than an internal debug view.

## Scope

- Frontend-only change in `frontend/src/world/NextChapterPrepPanel.tsx`.
- Use existing display label helpers from `frontend/src/world/displayLabels.ts`.
- Localize:
  - priority character role labels
  - priority foreshadow status labels
  - foreshadow urgency text
  - recent formal event labels and world version text
- Keep existing imported material reference cards and safety copy unchanged.
- Keep raw IDs, backend enum values, slugs, and source identifiers out of visible copy.

## Non-Goals

- No backend API changes.
- No database changes.
- No automatic canon edits from imported material.
- No changes to `buildExecutionContextFromPrep(prep)` or Studio handoff.
- No broad refactor of all world panels in this task.

## Safety Invariant

Imported candidates remain candidate/reference material. This task changes display labels only; it does not change world state, approval, formal events, or projection updates.

## Testing

Use TDD in `frontend/src/world/NextChapterPrepPanel.test.tsx`:

1. Update the main render test to expect Chinese labels for role, foreshadow status, urgency, and recent events.
2. Assert raw labels like `protagonist`, `advanced · urgency`, and `chapter_approved · 世界` are not visible.
3. Verify RED with the targeted Next Chapter Prep test.
4. Implement minimal display-label changes in `NextChapterPrepPanel.tsx`.
5. Verify GREEN, then run backend import safety tests, relevant frontend tests, frontend build, diff checks, and commit.

## Self-Review

- The scope is small and presentation-only.
- The fix improves the onboarding/first-chapter prep recap without changing data flow.
- The design preserves the import-candidate safety invariant.
