# Studio Candidate Reference Label Design

## Goal

Make imported candidate materials in Studio read as candidate writing references instead of ambiguous imported material references.

## Selected Small MVP Fix

The Studio execution context card already carries imported material references into chapter creation without changing formal canon. The card label still says `导入素材参考：1 条`, which is readable but less explicit about candidate status than the surrounding settlement copy. The smallest useful fix is to rename that visible count label to `候选素材参考：1 条`.

## Scope

- Frontend-only copy update in `frontend/src/studio/StudioPage.tsx`.
- Update `frontend/src/studio/StudioPage.test.tsx` to expect `候选素材参考：1 条` and reject the older ambiguous count label.
- Keep reference titles, summaries, source titles, execution context payloads, approval payloads, world overview refresh, and canon behavior unchanged.

## Non-Goals

- No backend API changes.
- No database changes.
- No changes to imported candidate asset persistence.
- No automatic canon edits from imported candidate materials.
- No display of raw IDs, slugs, enums, or internal source fields.

## Safety Invariant

Imported materials remain candidate assets and writing references only. This task changes a visible Studio label only and does not change formal canon mutation, world versioning, event history, or projection updates.

## Testing

Use TDD in `frontend/src/studio/StudioPage.test.tsx`:

1. Expect `候选素材参考：1 条` in the Studio execution context summary.
2. Assert `导入素材参考：1 条` is not exposed in that Studio summary path.
3. Preserve existing assertions that raw `asset_id`, `batch_id`, `inspiration`, and `正式 canon` are not exposed.
4. Verify RED with the targeted Studio execution-context test before changing production copy.
5. Change the visible count label in `StudioPage.tsx`.
6. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, and commit.

## Self-Review

- Scope is small and presentation-only.
- The fix improves Import Node P1 visibility by naming imported references as candidate material in Studio.
- The design does not create a new formal-canon mutation path.
