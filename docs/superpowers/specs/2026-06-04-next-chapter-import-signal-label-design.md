# Next Chapter Import Signal Label Design

## Goal

Make the next-chapter prep source signal for imported material read as a safe candidate-material reference instead of a generic imported-material label.

## Selected Small MVP Fix

The next-chapter prep panel renders source-signal chips above the suggested goal. The internal signal `import_material_reference` is mapped to `导入素材参考`, while nearby sections now use safer candidate-reference wording. The smallest useful fix is to map that signal to `候选素材参考`, so users see that imported material influenced the suggestion as reference material without implying formal canon mutation.

## Scope

- Frontend-only copy update in `frontend/src/world/NextChapterPrepPanel.tsx`.
- Update `frontend/src/world/NextChapterPrepPanel.test.tsx` to include the import source signal, expect `候选素材参考`, and reject the raw slug.
- Keep material titles, summaries, source titles, action buttons, execution context payloads, and canon behavior unchanged.

## Non-Goals

- No backend API changes.
- No database changes.
- No next-chapter prep algorithm changes.
- No import confirmation behavior changes.
- No automatic canon edits from imported candidate materials.
- No display of raw IDs, slugs, enums, or internal source fields.

## Safety Invariant

Imported materials remain candidate assets and writing references only. This task changes a source-signal label only and does not change formal canon mutation, world versioning, event history, or projection updates.

## Testing

Use TDD in `frontend/src/world/NextChapterPrepPanel.test.tsx`:

1. Add `import_material_reference` to the prep fixture source signals.
2. Expect the rendered chip `候选素材参考`.
3. Assert the raw slug `import_material_reference` is not exposed.
4. Preserve existing assertions that raw `asset_id`, `batch_id`, `inspiration`, and `正式 canon` are not exposed.
5. Preserve the `onUseContext` assertion that the material reference still reaches `material_references`.
6. Verify RED with the targeted next-chapter prep test before changing production copy.
7. Change the visible signal label in `NextChapterPrepPanel.tsx`.
8. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, and commit.

## Self-Review

- Scope is small and presentation-only.
- The fix improves Import Node P1 visibility in later-chapter prep source signals.
- The design does not create a new formal-canon mutation path.
