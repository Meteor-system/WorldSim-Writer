# Archived Tags UI Read-Only Design

## Target

Make archived-world tag tooling read-only in the frontend so the UI matches the backend `WORLD_ARCHIVED` guard added in the previous round.

## Background

Backend tag writes now reject archived worlds, but the frontend still renders controls that invite the user to create, edit, merge, delete, assign, bulk-assign, and unassign tags. That creates a poor archived-world experience: the user sees write controls, clicks them, then gets backend errors. Archived worlds should be browsable without write affordances.

## Scope

When a world is archived:

- `WorldTagsPanel` still loads and displays tags.
- Tag list search/filter/sort remains available.
- Tag detail remains available.
- Object filtering/search/sort in the selected tag detail remains available.
- These controls are hidden:
  - create tag form
  - edit tag form
  - merge tag form
  - delete tag button and confirmation
  - single object assignment form
  - bulk object assignment form
  - per-object unassign button
- A clear read-only notice appears in Tags / Collections.
- `WorldSearchPanel` still searches and filters tags, but hides the search-results bulk tagging form.

Active worlds keep the existing write controls unchanged.

## Approach

Add a `readOnly?: boolean` prop to `WorldTagsPanel` and `WorldSearchPanel`. Pass `isArchivedWorld` from `WorldPage` to both panels. In the panels, conditionally render write controls only when `readOnly` is false. This mirrors the existing pattern used by character, relation, foreshadow, and Narrative Control Center UI.

No API shape changes are needed. Backend guards remain the source of truth; frontend read-only mode prevents avoidable failed calls.

## Tests

Add frontend TDD coverage:

1. `WorldTagsPanel` read-only mode shows the read-only notice, still lists tags and loads detail, and hides all tag write controls.
2. `WorldSearchPanel` read-only mode still searches and shows results, but hides the search-results bulk tagging form and never calls `onBulkAssignTag`.
3. Existing active-mode tests continue to verify write controls and callbacks.

Run targeted component tests, WorldPage tests, frontend build, backend tag tests for guard compatibility, and `git diff --check` before committing.
