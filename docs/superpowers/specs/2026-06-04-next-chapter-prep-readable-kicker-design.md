# Next Chapter Prep Readable Kicker Design

## Goal

Make the next-chapter writing reference surface read as low-cognitive Chinese UI.

## Selected Small MVP Fix

The next-chapter preparation panel already shows imported candidate materials as writing references and explicitly says they do not change formal settings. Its small visible kicker still reads `Next Chapter Prep`, which feels like an internal English feature label inside an otherwise Chinese chapter-writing flow. The smallest useful fix is to rename that kicker to `下一章写作准备`.

## Scope

- Frontend-only copy update in `frontend/src/world/NextChapterPrepPanel.tsx`.
- Update `frontend/src/world/NextChapterPrepPanel.test.tsx` to expect `下一章写作准备` and reject `Next Chapter Prep`.
- Keep callbacks, generated execution context, imported material references, API payloads, and canon behavior unchanged.

## Non-Goals

- No backend API changes.
- No database changes.
- No changes to next-chapter recommendation logic.
- No changes to imported candidate asset selection or persistence.
- No automatic canon edits from imported candidate materials.

## Safety Invariant

Imported materials remain candidate assets and writing references only. This task changes a visible label only and does not change canon mutation, world versioning, event history, or projection updates.

## Testing

Use TDD in `frontend/src/world/NextChapterPrepPanel.test.tsx`:

1. Expect `下一章写作准备` on the panel.
2. Assert `Next Chapter Prep` is not exposed.
3. Verify RED with the targeted panel test before changing production copy.
4. Change the visible kicker in `NextChapterPrepPanel.tsx`.
5. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, and commit.

## Self-Review

- Scope is small and presentation-only.
- The fix improves the chapter-writing reference flow.
- The design does not create a new formal-canon mutation path.
