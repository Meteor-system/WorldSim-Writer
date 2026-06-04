# Import Node Candidate Count Labels Design

## Goal

Make Import Node count summaries clearly describe candidate references, not formal canon, so newcomers understand imported material is usable as writing reference only.

## Selected Small MVP Fix

`WorldImportPanel` already shows imported assets as grouped candidate cards and says imported material will not auto-edit formal settings. However, the compact count summary still reads `正式设定 1 · 角色 1 · 灵感 1`. In a newcomer/import flow this can sound like the import already wrote formal world state. The smallest useful fix is to label those counts as candidate/reference buckets: `正式设定候选 1 · 角色候选 1 · 灵感候选 1`.

## Scope

- Frontend-only copy update in `frontend/src/world/WorldImportPanel.tsx`.
- Update all count summaries produced by `countText()`.
- Update `WorldImportPanel` tests to expect candidate labels and reject the old ambiguous count text.
- Keep import preview, confirmation, recent batch rendering, and callbacks unchanged.

## Non-Goals

- No backend API changes.
- No database changes.
- No new import-to-world-creation automation.
- No automatic canon edits from imported candidates.
- No broad Import Node layout redesign.

## Safety Invariant

Imported materials remain candidate assets and writing references only. This task changes display copy only and does not change canon mutation, world versioning, event history, or projection updates.

## Testing

Use TDD in `frontend/src/world/WorldImportPanel.test.tsx`:

1. Update preview/confirmation/recent-batch expectations to use `正式设定候选 1 · 角色候选 1 · 灵感候选 1`.
2. Assert the old ambiguous count `正式设定 1 · 角色 1 · 灵感 1` is not visible.
3. Verify RED with the targeted WorldImportPanel test.
4. Implement minimal `countText()` copy change.
5. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, and commit.

## Self-Review

- The scope is small and presentation-only.
- The fix targets Import Node P1 safety and newcomer comprehension.
- The design does not create a new formal-canon mutation path.
