# Next Chapter Prep Candidate CTA Design

## Goal

Make imported candidate material visibly available at the next-chapter action point by naming it in the Studio launch CTA when candidate references are present.

## Selected Small MVP Fix

The next-chapter preparation panel already shows `候选素材写作参考` and passes `material_references` into the Studio launch context. However, the primary CTA remains generic: `进入创作台并使用此目标`. Newcomers may miss that candidate material will travel with the next-chapter context.

Change the primary CTA only when candidate references exist:

- With candidate references: `带下一章候选素材参考进入创作台`
- Without candidate references: keep `进入创作台并使用此目标`

This mirrors the first-chapter launchpad CTA pattern and keeps candidate material visible without implying canon mutation.

## Scope

- Frontend-only CTA copy update in `frontend/src/world/NextChapterPrepPanel.tsx`.
- Update `frontend/src/world/NextChapterPrepPanel.test.tsx` to cover the conditional CTA copy.
- Preserve `buildExecutionContextFromPrep`, callback payloads, API fields, backend behavior, and persistence.
- Preserve existing raw ID/enum/slug hiding assertions.

## Non-Goals

- No backend API changes.
- No database changes.
- No import candidate persistence changes.
- No automatic canon edits from imported candidate materials.
- No changes to next-chapter prep ranking or selection logic.
- No broad layout redesign.

## Safety Invariant

Imported materials remain candidate-only writing references. The CTA only communicates that candidate references will accompany the Studio context. It does not change formal canon mutation, world versioning, event history, or projection updates.

## Testing

Use TDD in `frontend/src/world/NextChapterPrepPanel.test.tsx`:

1. Update the existing prep test to expect `带下一章候选素材参考进入创作台` when `material_references` exist.
2. Assert the generic CTA is not visible in that referenced-material state.
3. Add or preserve a no-reference case that keeps `进入创作台并使用此目标`.
4. Verify RED before changing production copy.
5. Change only the CTA label logic in `NextChapterPrepPanel.tsx`.
6. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, inline self-review, and commit.

## Self-Review

- Scope is small and user-facing.
- The fix improves the beginner next-chapter loop at the exact action point.
- The design does not create or alter any canon mutation path.
