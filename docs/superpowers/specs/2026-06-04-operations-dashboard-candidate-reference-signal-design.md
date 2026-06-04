# Operations Dashboard Candidate Reference Signal Design

## Goal

Make imported candidate material safely visible in the World Operations Dashboard so users see it during later operations review before continuing the next chapter.

## Selected Small MVP Fix

The first-chapter launchpad and next-chapter prep panel already show candidate material references. The World Operations Dashboard, which is the first operations-review surface on the overview page, still summarizes only formal world progress, approved chapters, event history, and foreshadow counts.

Add one operations metric when next-chapter prep contains candidate material references:

- `候选素材参考：N 条`
- Safety note: `只作为下一章写作参考，不会自动写入正式设定。`

This makes imported candidate materials visible in the operations review loop without treating them as canon or formal world history.

## Scope

- Frontend-only dashboard copy update in `frontend/src/world/WorldPage.tsx`.
- Pass `nextPrep?.material_references ?? []` into `WorldOperationsDashboard`.
- Update `frontend/src/world/WorldPage.test.tsx` to cover the dashboard signal and safety note.
- Preserve existing dashboard actions, Studio launch behavior, NextChapterPrep behavior, API fields, backend behavior, and persistence.
- Hide raw IDs, enum slugs, and internal terms.

## Non-Goals

- No backend API changes.
- No database changes.
- No import candidate persistence changes.
- No automatic canon edits from imported candidate materials.
- No changes to next-chapter prep generation or material-reference selection.
- No broad dashboard redesign.

## Safety Invariant

Imported materials remain candidate-only writing references. The dashboard signal only reports that candidate references are available for next-chapter writing. It does not change formal canon mutation, world versioning, event history, or projection updates.

## Testing

Use TDD in `frontend/src/world/WorldPage.test.tsx`:

1. Add/extend an operations dashboard test to mock next-chapter prep with one candidate material reference.
2. Expect `候选素材参考：1 条` and the safety note inside the dashboard.
3. Assert raw terms such as `asset_id`, `batch_id`, and `inspiration` are not visible.
4. Verify RED before changing production copy.
5. Change only the dashboard props/rendering and pass existing next-prep material references.
6. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, inline self-review, and commit.

## Self-Review

- Scope is small and user-facing.
- The fix improves later operations review visibility.
- The design does not create or alter any canon mutation path.
