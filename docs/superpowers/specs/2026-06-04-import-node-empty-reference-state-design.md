# Import Node Empty Reference State Design

## Goal

Make the Import Node empty history state useful for newcomers by explaining that imported materials become safe writing references, not automatic canon changes.

## Selected Small MVP Fix

`WorldImportPanel` already explains import safety in the header and after confirmation. But when a world has no import batches, the recent-import section only says `还没有导入批次。`. In the 3-minute newcomer loop, that empty state is a missed opportunity to explain what the first import will do. The smallest useful fix is to replace the terse empty state with a low-cognitive Chinese sentence that says imported material will first appear as candidate writing references for later prep/writing, and will not auto-edit formal settings.

## Scope

- Frontend-only copy update in `frontend/src/world/WorldImportPanel.tsx`.
- Update the empty recent-import history copy only.
- Update `WorldImportPanel` tests to expect the safe-reference empty state.
- Keep import preview, confirmation, batch listing, callbacks, payloads, and canon behavior unchanged.

## Non-Goals

- No backend API changes.
- No database changes.
- No new import-to-world-creation automation.
- No automatic canon edits from imported candidates.
- No broad Import Node layout redesign.

## Safety Invariant

Imported materials remain candidate assets and writing references only. This task changes empty-state copy only and does not change canon mutation, world versioning, event history, or projection updates.

## Testing

Use TDD in `frontend/src/world/WorldImportPanel.test.tsx`:

1. Add or update an empty-history test to expect the safe-reference empty state.
2. Assert the old terse empty state is not visible.
3. Verify RED with the targeted WorldImportPanel test.
4. Implement the minimal empty-state copy update.
5. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, and commit.

## Self-Review

- The scope is small and presentation-only.
- The fix targets Import Node P1 onboarding clarity.
- The design does not create a new formal-canon mutation path.
