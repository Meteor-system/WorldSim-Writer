# Next Chapter Candidate Reference Copy Design

## Goal

Make imported candidate materials in the later-chapter preparation panel read as safe candidate writing references.

## Selected Small MVP Fix

The next-chapter prep panel already carries imported material references into Studio without changing formal canon. Its dedicated reference section still uses the generic heading `导入素材参考` and the explanatory sentence `这些素材只是下一章写作参考，不会自动改写正式设定。`. The smallest useful fix is to rename that section heading to `候选素材写作参考` and make the safety sentence explicitly say these are candidate materials.

## Scope

- Frontend-only copy update in `frontend/src/world/NextChapterPrepPanel.tsx`.
- Update `frontend/src/world/NextChapterPrepPanel.test.tsx` to expect the safer heading and sentence.
- Update the `frontend/src/world/WorldPage.test.tsx` regression path that renders next-chapter prep after import confirmation to expect the same safer sentence.
- Keep material titles, summaries, source titles, action buttons, execution context payloads, and canon behavior unchanged.

## Non-Goals

- No backend API changes.
- No database changes.
- No next-chapter prep algorithm changes.
- No import confirmation behavior changes.
- No automatic canon edits from imported candidate materials.
- No display of raw IDs, slugs, enums, or internal source fields.

## Safety Invariant

Imported materials remain candidate assets and writing references only. This task changes visible later-chapter prep copy only and does not change formal canon mutation, world versioning, event history, or projection updates.

## Testing

Use TDD in `frontend/src/world/NextChapterPrepPanel.test.tsx`:

1. Expect `候选素材写作参考` in the material-reference section.
2. Expect `这些候选素材只是下一章写作参考，不会自动改写正式设定。`.
3. Preserve existing assertions that raw `asset_id`, `batch_id`, `inspiration`, and `正式 canon` are not exposed.
4. Preserve the `onUseContext` assertion that the material reference still reaches `material_references`.
5. Verify RED with the targeted next-chapter prep test before changing production copy.
6. Change the visible section heading and safety sentence in `NextChapterPrepPanel.tsx`.
7. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, and commit.

## Self-Review

- Scope is small and presentation-only.
- The fix improves Import Node P1 visibility in later-chapter creation.
- The design does not create a new formal-canon mutation path.
