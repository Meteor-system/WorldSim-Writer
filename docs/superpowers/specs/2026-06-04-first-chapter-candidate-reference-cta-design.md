# First Chapter Candidate Reference CTA Design

## Goal

Make the first-chapter launchpad CTA visibly tell newcomers when candidate material references will enter the writing studio.

## Selected Small MVP Fix

The first-chapter launchpad already displays candidate material references and carries them into Studio execution context. The primary CTA still uses generic copy:

- `用此目标进入创作台`

When candidate material references are present, this hides the most important novice-loop value: imported material is ready to be used as a writing reference. The thin fix is to make the CTA explicit only in that state:

- `带候选素材参考进入创作台`

When no candidate material references are present, keep the existing generic CTA.

## Scope

- Frontend-only copy update in `frontend/src/world/WorldPage.tsx` inside `FirstChapterLaunchpad`.
- Update `frontend/src/world/WorldPage.test.tsx` to require the candidate-aware CTA when `materialReferences.length > 0`.
- Preserve the existing `onLaunchChapter(nextChapter)` call and context-building behavior.
- Keep all backend APIs, persistence, import candidate data, world projection, `world_version`, and event history unchanged.

## Non-Goals

- No backend API changes.
- No database changes.
- No changes to import candidate selection logic.
- No changes to story arc generation.
- No automatic canon edits from candidate material.
- No broad launchpad redesign.

## Safety Invariant

Imported materials remain candidate-only writing references. This task changes only visible CTA copy. Candidate material still reaches the Studio as execution context, and only explicit chapter approval can write formal world-state changes and event history.

## Testing

Use TDD in `frontend/src/world/WorldPage.test.tsx`:

1. Update the existing first-chapter launchpad reference test to expect `带候选素材参考进入创作台`.
2. Assert the generic `用此目标进入创作台` button is not visible in the candidate-reference state.
3. Click the candidate-aware CTA and verify the existing `onEnterStudio` payload still includes `material_references`.
4. Verify RED before changing production copy.
5. Change only the CTA label in `FirstChapterLaunchpad`.
6. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, inline self-review, and commit.

## Self-Review

- Scope is small and user-facing.
- The fix improves novice-loop discoverability without adding new behavior.
- The design does not create or alter any canon mutation path.
