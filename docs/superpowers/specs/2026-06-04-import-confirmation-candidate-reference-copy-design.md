# Import Confirmation Candidate Reference Copy Design

## Goal

Make the import confirmation state clearly say imported materials are candidate writing references for later creation.

## Selected Small MVP Fix

After confirming an import, the success state says `这些素材会作为创作参考出现在下一章准备区，不会自动改写正式设定。`. It is safe, but it does not explicitly say the materials remain candidates. The smallest useful fix is to change the sentence to `这些候选素材会作为写作参考出现在下一章准备区，不会自动改写正式设定。`.

## Scope

- Frontend-only copy update in `frontend/src/world/WorldImportPanel.tsx`.
- Update `frontend/src/world/WorldImportPanel.test.tsx` to expect the safer candidate-reference sentence and reject the older generic sentence.
- Keep import request payloads, preview/confirm behavior, asset counts, recent batch display, and canon behavior unchanged.

## Non-Goals

- No backend API changes.
- No database changes.
- No import parsing or classification changes.
- No next-chapter prep behavior changes.
- No automatic canon edits from imported candidate materials.
- No display of raw IDs, slugs, enums, or internal source fields.

## Safety Invariant

Imported materials remain candidate assets and writing references only. This task changes visible import-confirmation copy only and does not change formal canon mutation, world versioning, event history, or projection updates.

## Testing

Use TDD in `frontend/src/world/WorldImportPanel.test.tsx`:

1. Expect `这些候选素材会作为写作参考出现在下一章准备区，不会自动改写正式设定。` after confirming an import.
2. Assert the older sentence `这些素材会作为创作参考出现在下一章准备区，不会自动改写正式设定。` is not exposed.
3. Preserve existing assertions that batch IDs and raw enum/count labels are not exposed.
4. Verify RED with the targeted import confirmation test before changing production copy.
5. Change the visible success sentence in `WorldImportPanel.tsx`.
6. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, and commit.

## Self-Review

- Scope is small and presentation-only.
- The fix improves Import Node P1 handoff clarity immediately after users confirm imported candidates.
- The design does not create a new formal-canon mutation path.
