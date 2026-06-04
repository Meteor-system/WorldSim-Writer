# Character Arc Readable Audit Labels Design

## Goal

Make the Studio character arc report easier for newcomers to read by replacing raw backend labels and JSON state-change blobs with low-cognitive Chinese copy.

## Selected Small MVP Fix

The Studio character arc report is part of the chapter-writing and canon-guard loop. It explicitly tells the user that review suggestions do not automatically submit world-state changes, but the report still exposes internal values such as `protagonist`, `major`, `choice`, `uneasy_ally`, and a raw `JSON.stringify()` blob for proposed state changes. The smallest useful fix is to localize those visible labels and render proposed changes as readable audit lines.

## Scope

- Frontend-only change in `frontend/src/studio/CharacterArcPanel.tsx`.
- Update role, presence, arc stage, relation type, proposed state-change display, and same-surface safety copy.
- Keep the report safety invariant unchanged: suggestions are review hints only and do not submit formal world-state changes.
- Keep the existing CTA behavior for using a hint as the next chapter goal.
- Keep the existing risk and priority labels.

## Non-Goals

- No backend API changes.
- No database changes.
- No automatic canon edits from character arc suggestions.
- No broad Studio layout redesign.
- No changes to character arc report data shape.

## Safety Invariant

Character arc report output remains advisory. Displaying proposed changes readably must not change approval preview behavior, world versioning, formal events, projection updates, or imported-candidate handling.

## Testing

Use TDD in `frontend/src/studio/CharacterArcPanel.test.tsx`:

1. Update the report test to expect Chinese labels for role, presence, arc stage, relation type, and proposed state changes.
2. Assert raw labels and raw JSON snippets are not visible.
3. Verify RED with the targeted CharacterArcPanel test.
4. Implement minimal label helpers and readable proposed-change rendering.
5. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, and commit.

## Self-Review

- The scope is small and presentation-only.
- The fix improves a canon-guard writing review surface.
- The design does not create a new formal-canon mutation path.
