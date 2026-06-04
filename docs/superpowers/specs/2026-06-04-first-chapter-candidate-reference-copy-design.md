# First Chapter Candidate Reference Copy Design

## Goal

Make imported candidate materials in the newcomer first-chapter launchpad read as safe candidate writing references.

## Selected Small MVP Fix

The first-chapter launchpad already passes imported material references into Studio without changing formal canon. Its visible count still says `已准备 1 条导入素材参考。`, which is readable but less explicit than the safer candidate-reference wording now used in Studio. The smallest useful fix is to rename that count sentence to `已准备 1 条候选素材写作参考。`.

## Scope

- Frontend-only copy update in `frontend/src/world/WorldPage.tsx`.
- Update `frontend/src/world/WorldPage.test.tsx` to expect the safer count sentence and reject the older ambiguous sentence.
- Keep material titles, summaries, source titles, Studio launch context payloads, and canon behavior unchanged.

## Non-Goals

- No backend API changes.
- No database changes.
- No import confirmation behavior changes.
- No story arc generation behavior changes.
- No automatic canon edits from imported candidate materials.
- No display of raw IDs, slugs, enums, or internal source fields.

## Safety Invariant

Imported materials remain candidate assets and writing references only. This task changes visible newcomer-loop copy only and does not change formal canon mutation, world versioning, event history, or projection updates.

## Testing

Use TDD in `frontend/src/world/WorldPage.test.tsx`:

1. Expect `已准备 1 条候选素材写作参考。` in the first-chapter launchpad import-reference section.
2. Assert `已准备 1 条导入素材参考。` is not exposed in that path.
3. Preserve existing assertions that raw `asset_id`, `batch_id`, `inspiration`, and `正式 canon` are not exposed.
4. Preserve the `onEnterStudio` assertion that the material reference still reaches `executionContext.material_references`.
5. Verify RED with the targeted first-chapter launchpad test before changing production copy.
6. Change the visible count sentence in `WorldPage.tsx`.
7. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, and commit.

## Self-Review

- Scope is small and presentation-only.
- The fix improves Import Node P1 visibility in the newcomer creation loop.
- The design does not create a new formal-canon mutation path.
