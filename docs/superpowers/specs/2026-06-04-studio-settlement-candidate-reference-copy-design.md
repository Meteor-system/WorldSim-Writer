# Studio Settlement Candidate Reference Copy Design

## Goal

Make imported materials visibly safe in the Studio approval settlement audit.

## Selected Small MVP Fix

After a draft is approved, the Studio settlement panel summarizes whether the chapter used imported material references. The current sentence says `本章参考了 1 条导入素材：雨夜审讯。`, which is understandable but does not explicitly remind the user that the material remained a candidate writing reference rather than formal canon. The smallest useful fix is to change that settlement sentence to `本章使用 1 条候选素材作为写作参考：雨夜审讯。`.

## Scope

- Frontend-only copy update in `frontend/src/studio/StudioPage.tsx`.
- Update `frontend/src/studio/StudioPage.test.tsx` to expect the safer settlement sentence and reject the older ambiguous sentence.
- Keep approval API calls, selected change indexes, world overview refresh, event history, and material reference title extraction unchanged.

## Non-Goals

- No backend API changes.
- No database changes.
- No changes to Import Node persistence.
- No changes to approval transaction behavior.
- No automatic canon edits from imported candidate materials.

## Safety Invariant

Imported materials remain candidate assets and writing references only. This task changes one settlement sentence and does not change canon mutation, world versioning, event history, or projection updates.

## Testing

Use TDD in `frontend/src/studio/StudioPage.test.tsx`:

1. Expect `本章使用 1 条候选素材作为写作参考：雨夜审讯。` after approval settlement.
2. Assert the old sentence `本章参考了 1 条导入素材：雨夜审讯。` is not exposed.
3. Verify RED with the targeted Studio settlement test before changing production copy.
4. Change `materialReferenceSentence()` in `StudioPage.tsx`.
5. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, and commit.

## Self-Review

- Scope is small and presentation-only.
- The fix improves canon-safety readability at the approval audit point.
- The design does not create a new formal-canon mutation path.
