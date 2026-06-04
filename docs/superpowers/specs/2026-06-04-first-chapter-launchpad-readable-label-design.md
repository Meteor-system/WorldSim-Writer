# First Chapter Launchpad Readable Label Design

## Goal

Make the first-chapter onboarding launchpad read as a low-cognitive Chinese surface for newcomers.

## Selected Small MVP Fix

The three-minute loop already shows Chinese steps and can carry imported candidate materials into the first chapter Studio context without changing canon. One visible newcomer-facing label still reads `First Chapter Launchpad`, which is inconsistent with the surrounding Chinese UI and can feel like an internal feature name. The smallest useful fix is to rename the visible label to `第一章启动台`.

## Scope

- Frontend-only copy update in `frontend/src/world/WorldPage.tsx`.
- Update tests in `frontend/src/world/WorldPage.test.tsx` to expect `第一章启动台` and reject `First Chapter Launchpad`.
- Keep story-arc generation, selected chapter context, imported material references, API calls, and canon behavior unchanged.

## Non-Goals

- No backend API changes.
- No database changes.
- No story-arc planner behavior changes.
- No Import Node payload or candidate asset behavior changes.
- No automatic canon edits from imported candidate materials.

## Safety Invariant

Imported materials remain candidate assets and writing references only. This task changes a visible onboarding label only and does not change canon mutation, world versioning, event history, or projection updates.

## Testing

Use TDD in `frontend/src/world/WorldPage.test.tsx`:

1. Replace first-chapter launchpad expectations with `第一章启动台`.
2. Add a regression assertion that the page does not expose `First Chapter Launchpad`.
3. Verify RED with a targeted WorldPage test before changing production copy.
4. Change the visible label in `WorldPage.tsx`.
5. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, and commit.

## Self-Review

- Scope is small and presentation-only.
- The fix improves the three-minute newcomer loop.
- The design does not create any new formal-canon mutation path.
