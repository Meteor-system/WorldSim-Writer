# Import Node Readable Record Copy Design

## Goal

Make the Import Node recent-record surface use low-cognitive candidate-material wording instead of internal batch terminology.

## Selected Small MVP Fix

`WorldImportPanel` already hides raw IDs and explains imported materials as `候选素材`. One visible wording gap remains in the recent import area:

- section heading: `最近导入批次`
- fallback load error: `导入批次加载失败`

`批次` is an internal/audit concept. It is not as helpful for newcomers as a candidate-material record label. The smallest useful fix is to rename this visible surface to candidate material records:

- `最近候选素材记录`
- `导入记录加载失败`

This keeps all API fields, list data, import confirmation, and audit behavior unchanged.

## Scope

- Frontend-only copy update in `frontend/src/world/WorldImportPanel.tsx`.
- Update `frontend/src/world/WorldImportPanel.test.tsx` to expect the readable heading and fallback error copy.
- Keep recent record cards, source titles, candidate counts, material reference cards, callbacks, payloads, and backend behavior unchanged.

## Non-Goals

- No backend API changes.
- No database changes.
- No import persistence changes.
- No import batch model rename in TypeScript types or API payloads.
- No automatic canon edits from imported candidate materials.
- No broad Import Node redesign.

## Safety Invariant

Imported materials remain candidate-only writing references. This task changes visible frontend copy only and does not change formal canon mutation, world versioning, event history, or projection updates.

## Testing

Use TDD in `frontend/src/world/WorldImportPanel.test.tsx`:

1. Update the recent import record test to expect `最近候选素材记录`.
2. Assert `最近导入批次` is not visible.
3. Add a fallback load-error test where `onListBatches` rejects with a non-Error value.
4. Expect `导入记录加载失败` and assert `导入批次加载失败` is not visible.
5. Preserve existing assertions that raw IDs, slugs, enums, `候选资产`, and generic old reference copy are not exposed.
6. Verify RED before changing production copy.
7. Change only the visible heading and fallback error string in `WorldImportPanel.tsx`.
8. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, inline self-review, and commit.

## Self-Review

- Scope is small and presentation-only.
- The fix improves newcomer readability on the Import Node audit surface.
- The design does not create or alter any canon mutation path.
