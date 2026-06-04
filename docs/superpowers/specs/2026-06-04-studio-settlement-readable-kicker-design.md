# Studio Settlement Readable Kicker Design

## Goal

Make the Studio approval settlement audit fully readable in low-cognitive Chinese UI.

## Selected Small MVP Fix

The Studio settlement panel is the place where users confirm a chapter has entered formal story history while imported materials remain writing references. Its heading is Chinese (`世界推进结算`), but the small kicker above it still reads `Canon Settlement`. The smallest useful fix is to rename the visible kicker to `正史结算`.

## Scope

- Frontend-only copy update in `frontend/src/studio/StudioPage.tsx`.
- Update `frontend/src/studio/StudioPage.test.tsx` to expect `正史结算` and reject `Canon Settlement`.
- Keep approval API calls, selected change indexes, imported material settlement copy, world overview refresh, and canon behavior unchanged.

## Non-Goals

- No backend API changes.
- No database changes.
- No approval transaction changes.
- No changes to imported candidate asset behavior.
- No automatic canon edits from imported candidate materials.

## Safety Invariant

Imported materials remain candidate assets and writing references only. This task changes a visible label only and does not change canon mutation, world versioning, event history, or projection updates.

## Testing

Use TDD in `frontend/src/studio/StudioPage.test.tsx`:

1. Expect `正史结算` after approval settlement.
2. Assert `Canon Settlement` is not exposed.
3. Verify RED with the targeted Studio settlement test before changing production copy.
4. Change the visible kicker in `StudioPage.tsx`.
5. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, and commit.

## Self-Review

- Scope is small and presentation-only.
- The fix improves canon-audit readability at the approval settlement point.
- The design does not create a new formal-canon mutation path.
