# Studio Proposed Change Localization Design

## Goal

Remove author-facing internal enum values and raw ID fallbacks from the Studio draft review panel while preserving API contracts and approval behavior.

## Current State

`frontend/src/studio/StudioPage.tsx` already uses Chinese copy in most of the Studio flow and labels foreshadow status in the sidebar with `labelStatus()`. The lower "世界状态变化" panel still renders raw proposed-change values directly:

- Character proposed status appears as `({c.status})`.
- Foreshadow proposed status appears as `({f.status})`, e.g. `(advanced)`.
- Missing lookup fallbacks render `角色#<id>` or `伏笔#<id>`, exposing raw IDs.

The approval preview checkboxes already use names/titles from the API and the approval submission uses selected change indexes. This slice must not change the payload sent to `approveChapter` or the invariant that world state changes only after approval.

## Selected Slice

Update only the Studio proposed-change display:

1. Localize proposed status values with existing `labelStatus()`.
2. Replace raw ID fallback strings with soft labels: `未命名角色` and `未命名伏笔`.
3. Add a short explanatory line that proposed changes are suggestions and only the checked approval items are written after clicking the formal approval button.
4. Keep API types, selection indexes, and approval requests unchanged.

## Out of Scope

- No backend changes.
- No broad Studio copy rewrite.
- No changes to approval logic or selected-change behavior.
- No changes to API response shapes.

## Test Strategy

Use TDD in `frontend/src/studio/StudioPage.test.tsx`:

1. Add a failing assertion to the existing draft review test that the proposed change panel shows localized status text and does not expose `(advanced)`, `(planted)`, `角色#`, or `伏笔#`.
2. Run the targeted Studio test and confirm RED.
3. Implement the smallest `StudioPage.tsx` display change.
4. Re-run the targeted Studio test, then frontend test/build gates and `git diff --check` before committing.
