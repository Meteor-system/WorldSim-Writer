# Recent Import Batch Candidate Reference Copy Design

## Goal

Make confirmed import batches read as candidate writing references when users review recent imported material.

## Selected Small MVP Fix

The recent import batch card currently labels its asset list as `可用创作参考` and ends with `这些素材只是写作参考，不会自动改写正式设定。`. This is safe, but it is less explicit than the rest of the Import Node P1 flow because it does not say the references are still candidate materials. The smallest useful fix is to change the list label to `候选素材写作参考` and the guardrail sentence to `这些候选素材只是写作参考，不会自动改写正式设定。`.

## Scope

- Frontend-only copy update in `frontend/src/world/WorldImportPanel.tsx`.
- Update `frontend/src/world/WorldImportPanel.test.tsx` to expect the clearer recent-batch candidate-reference copy and reject the older generic wording.
- Keep import request payloads, preview/confirm behavior, batch listing behavior, asset counts, and candidate asset labels unchanged.

## Non-Goals

- No backend API changes.
- No database changes.
- No import parsing or classification changes.
- No next-chapter prep behavior changes.
- No automatic canon edits from imported candidate materials.
- No display of raw IDs, slugs, enums, or internal source fields.

## Safety Invariant

Imported materials remain candidate assets and writing references only. This task changes visible recent-batch copy only and does not change formal canon mutation, world versioning, event history, or projection updates.

## Testing

Use TDD in `frontend/src/world/WorldImportPanel.test.tsx`:

1. Expect `候选素材写作参考` in the recent import batch card.
2. Expect `这些候选素材只是写作参考，不会自动改写正式设定。` in the recent import batch card.
3. Assert the older generic label `可用创作参考` and sentence `这些素材只是写作参考，不会自动改写正式设定。` are not exposed.
4. Preserve existing assertions that raw IDs, slugs, enums, and non-candidate labels are not exposed.
5. Verify RED with the targeted recent-batch test before changing production copy.
6. Change the visible recent-batch copy in `WorldImportPanel.tsx`.
7. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, inline self-review, and commit.

## Self-Review

- Scope is small and presentation-only.
- The fix improves Import Node P1 audit/history clarity after candidates have already been confirmed.
- The design does not create a new formal-canon mutation path.
