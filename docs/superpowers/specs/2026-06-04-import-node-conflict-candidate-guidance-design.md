# Import Node Conflict Candidate Guidance Design

## Goal

Make Import Node conflict hints clearer for newcomers by explaining that conflicts are candidate-material review reminders, not automatic formal-canon edits.

## Selected Small MVP Fix

The Import Node preview currently labels conflict hints as `冲突提示`. The conflict text is readable, but the section heading is generic and does not restate the safety boundary at the exact moment users review possible overlap with formal settings.

Replace the conflict section heading and add one short safety note:

- `冲突提示` → `候选素材冲突提示`
- Add: `这些提示只帮助你审阅候选素材，不会自动合并或改写正式设定。`

This keeps the conflict audit easy to understand in the beginner loop and reduces the chance that users think imported material can silently become canon.

## Scope

- Frontend-only copy update in `frontend/src/world/WorldImportPanel.tsx`.
- Update `frontend/src/world/WorldImportPanel.test.tsx` to cover the new conflict heading and safety note.
- Preserve preview/confirm callbacks, request payloads, API fields, TypeScript type names, backend behavior, and persistence.
- Preserve existing hiding of raw IDs, enum slugs, and internal conflict category names.

## Non-Goals

- No backend API changes.
- No database changes.
- No import candidate persistence changes.
- No automatic canon edits from imported candidate materials.
- No changes to conflict detection logic.
- No broad Import Node layout redesign.

## Safety Invariant

Imported materials remain candidate-only writing references. Conflict hints are review guidance only. This task changes visible frontend copy only and does not change formal canon mutation, world versioning, event history, or projection updates.

## Testing

Use TDD in `frontend/src/world/WorldImportPanel.test.tsx`:

1. Update the preview-with-conflict test to expect `候选素材冲突提示` and the safety note.
2. Assert the old generic `冲突提示` heading is not visible by itself.
3. Preserve assertions that raw conflict category slugs and raw `canon` text are hidden.
4. Verify RED before changing production copy.
5. Change only the conflict heading and safety note in `WorldImportPanel.tsx`.
6. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, inline self-review, and commit.

## Self-Review

- Scope is small and user-facing.
- The fix improves conflict/audit readability in the import preview before confirmation.
- The design does not create or alter any canon mutation path.
