# MVP32 Tag Delete Confirmation 1.0 Design

## Product-route analysis

MVP23 through MVP31 expanded the Tools Workspace tag workflow from creation and assignment through editing, merging, filtering, and local search. Tags now carry useful organization work, and deleting a tag removes that metadata and its assignments. The current UI exposes `删除当前标签` as a one-click action in the selected tag detail panel. That is too easy to trigger accidentally as tag collections become more valuable.

`WorldSim-Writer.md` emphasizes data governance, repair tools, and safe user-approved state changes. MVP32 adds a small safety guard for destructive tag metadata actions without changing backend behavior. It is narrower and higher priority than adding another navigation filter because it reduces accidental metadata loss while preserving the existing metadata-only tag invariant.

## Candidates and recommendation

### 1. Tag Delete Confirmation 1.0 — recommended

Add a two-step confirmation UI before deleting a selected tag. The first click arms a warning. The user can then confirm or cancel.

Why this is best:

- It protects accumulated tag assignments from accidental deletion.
- It is a small frontend-only change with focused Vitest coverage.
- It does not alter backend delete semantics or persistence.
- It complements MVP29 tag merge by making deletion feel like a deliberate cleanup action.

### 2. Tag list text filtering

Add search over tag names/colors in the tag list.

Trade-off: useful for larger tag sets, but MVP31 already improved local search in selected tag detail. Delete safety addresses a more destructive workflow risk.

### 3. Tag assignment undo notice

After unassigning an object, show a short-lived undo prompt.

Trade-off: valuable, but it needs a reversible API sequence and edge-case decisions around reassign failures.

## Recommendation

Implement **MVP32 Tag Delete Confirmation 1.0**.

## Goals

- Prevent one-click deletion of selected tags.
- Show a confirmation warning that includes the selected tag name and assignment count.
- Provide explicit `确认删除标签` and `取消删除` actions.
- Only call `onDeleteTag` after confirmation.
- Reset pending delete confirmation when loading another tag.
- Preserve all existing tag workflows, including create, edit, merge, assign, bulk assign, unassign, object-type filter, and text search.
- Keep the feature frontend-only and metadata-only: no API schema changes, no canon mutation, no `world_version` increment, and no EventLog write.

## Non-goals

- No backend changes.
- No soft-delete/archive semantics.
- No undo implementation.
- No extra confirmation for unassigning individual objects.
- No schema migration.
- No canon mutation, no `world_version` increment, and no EventLog write.

## Frontend design

Update `WorldTagsPanel` only.

State:

```ts
const [deleteConfirming, setDeleteConfirming] = useState(false);
```

When `loadTag()` successfully loads detail, reset:

```ts
setDeleteConfirming(false);
```

When deletion succeeds, also reset confirmation while clearing the selected tag detail:

```ts
setDeleteConfirming(false);
```

UI:

- Keep the existing `删除当前标签` button.
- Change its click behavior to only set `deleteConfirming` to `true`.
- When `deleteConfirming` is true, render a compact warning panel near the selected tag header:
  - Text: `确认删除标签「{detail.tag.name}」？这会移除 {detail.tag.assignment_count} 个对象关联。`
  - Button: `确认删除标签` calls the existing delete handler.
  - Button: `取消删除` sets `deleteConfirming` to `false`.

Existing delete handler:

- Continues calling `onDeleteTag(worldId, selectedTagId)`.
- Clears selection/detail after success.
- Reloads tags.
- Does not mutate canon or event state in the frontend.

## Backend design

No backend changes are required. Existing delete behavior and authorization remain the source of truth. MVP32 only changes when the frontend calls the existing delete prop.

## Testing strategy

### Frontend TDD

Extend `frontend/src/world/WorldTagsPanel.test.tsx` with tests for:

1. First delete click shows a confirmation and does not call `onDeleteTag`.
2. Confirming deletion calls `onDeleteTag` with the selected tag id.
3. Cancelling deletion hides the confirmation and does not call `onDeleteTag`.
4. Loading a different tag resets a pending delete confirmation.

The first test should fail before implementation because the current delete button calls `onDeleteTag` immediately and no confirmation UI exists.

### Backend checks

No backend behavior is added. Final verification should still run `backend/tests/test_tags.py` and `backend/tests/test_world_search.py` because the feature protects the tag/search toolchain.

## Acceptance criteria

- Clicking `删除当前标签` does not immediately call `onDeleteTag`.
- The confirmation warning includes the selected tag name and assignment count.
- Clicking `确认删除标签` calls `onDeleteTag` and keeps existing successful delete behavior.
- Clicking `取消删除` hides the warning without calling `onDeleteTag`.
- Loading another tag clears a pending delete confirmation.
- Existing targeted backend pytest, targeted frontend tests, and frontend build pass.

## Risks and mitigations

- **Breaking existing delete test expectations.** Update tests to match the safer two-step behavior and add explicit confirm coverage.
- **Stale confirmation after switching tags.** Reset `deleteConfirming` in `loadTag()`.
- **Extra UI clutter.** Render the warning only after the user clicks delete.
- **Scope creep into archive/undo.** Keep MVP32 to frontend confirmation only.

## Self-review

- No placeholders remain.
- Scope is limited to frontend confirmation before an existing delete action.
- The design adds no backend schema or write behavior.
- The design preserves all metadata-only tag invariants.

## Implementation status

Implemented on `feat/mvp32-tag-delete-confirmation` using TDD. Frontend RED was observed because `删除当前标签` called `onDeleteTag` immediately and no confirmation warning existed; GREEN passed after adding local confirmation state, confirm/cancel actions, and reset-on-tag-load behavior. Pre-merge verification passed with backend tag/search pytest, frontend targeted Vitest, and frontend production build.
