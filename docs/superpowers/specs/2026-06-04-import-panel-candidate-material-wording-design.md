# Import Panel Candidate Material Wording Design

## Goal

Make the import panel consistently describe imported references as candidate materials instead of technical candidate assets.

## Selected Small MVP Fix

The import panel already protects canon, but several visible strings still say `候选资产`, such as `候选资产池`, `需确认后才写入候选资产`, `确认写入候选资产`, and `候选资产 3 项`. `资产` is accurate internally, but it sounds more technical than the rest of the novice three-minute writing loop. The smallest useful fix is to replace user-facing `候选资产` wording with `候选素材` while leaving backend names, API payloads, types, and persistence unchanged.

## Scope

- Frontend-only copy update in `frontend/src/world/WorldImportPanel.tsx`.
- Update `frontend/src/world/WorldImportPanel.test.tsx` to expect `候选素材` in visible import-panel guidance, preview confirmation, confirmation button, and recent-batch badge.
- Preserve existing candidate pool labels such as `正式设定候选`, `角色候选`, and `灵感候选` because these are readable user labels, not raw enum values.
- Keep import request payloads, preview/confirm behavior, batch listing behavior, asset counts, and canon behavior unchanged.

## Non-Goals

- No backend API changes.
- No database changes.
- No import parsing or classification changes.
- No next-chapter prep behavior changes.
- No automatic canon edits from imported candidate materials.
- No display of raw IDs, slugs, enums, or internal source fields.

## Safety Invariant

Imported materials remain candidate-only writing references. This task changes visible copy only and does not change formal canon mutation, world versioning, event history, or projection updates.

## Testing

Use TDD in `frontend/src/world/WorldImportPanel.test.tsx`:

1. Expect the intro guardrail to say imported materials enter the `候选素材池`.
2. Expect the preview count copy to say confirmation writes `候选素材`.
3. Expect the confirm button to say `确认写入候选素材`.
4. Expect the recent batch badge to say `候选素材 3 项`.
5. Assert old `候选资产` wording is not exposed in the rendered panel states covered by the tests.
6. Verify RED before changing production copy.
7. Change only visible frontend strings in `WorldImportPanel.tsx`.
8. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, inline self-review, and commit.

## Self-Review

- Scope is small and presentation-only.
- The fix improves novice comprehension immediately around import preview, confirm, and recent import audit.
- The design keeps internal API/type names untouched and does not create a formal-canon mutation path.
