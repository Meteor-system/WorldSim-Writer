# MVP36 Tag View Reset Controls 1.0 Design

## Product-route analysis

MVP23 through MVP35 built a rich Tools Workspace tag workflow: users can create, edit, merge, delete with confirmation, search and sort the tag list, assign and bulk assign objects, tag search results, inspect selected tag details, filter/search/sort selected-tag objects, and preserve metadata-only tag invariants. As local controls accumulate, the next small usability gap is quickly returning tag list and tag detail views to their default state.

`WorldSim-Writer.md` names the Tools Workspace as the place for global search, multidimensional filtering, tags, batch editing, and data governance. MVP36 stays on that route by adding local reset controls for already-loaded tag views in `WorldTagsPanel`. It is frontend-only, deterministic, and does not affect canon or formal world state.

## Candidates and recommendation

### 1. Tag View Reset Controls 1.0 — recommended

Add explicit reset buttons for the tag list view and selected-tag object view. The tag-list reset clears tag search and restores default sort. The object-view reset restores all objects, clears object search, and restores default object sort.

Why this is best:

- It directly complements the new search/sort/filter controls from MVP30 through MVP35.
- It is small, frontend-only, and easy to cover with focused Vitest tests.
- It reduces user friction after filters produce narrow or empty views.
- It avoids backend or schema changes.

### 2. Persist last-used tag controls

Remember the user's last tag-list sort/filter choices locally.

Trade-off: useful later, but persistence semantics can surprise users and require storage decisions; reset controls are safer first.

### 3. Highlight matched tag/detail text

Emphasize search matches in tag names or object snippets.

Trade-off: useful, but requires more UI markup changes and is less important than clearing accumulated local controls.

## Recommendation

Implement **MVP36 Tag View Reset Controls 1.0**.

## Goals

- Add a local tag-list reset button when tags exist.
- `重置标签视图` clears tag-list search and restores tag-list sort to `默认排序`.
- Add a local selected-tag object reset button when tag detail is loaded.
- `重置对象视图` restores selected-tag object type filter to `all`, clears selected-tag object search, and restores object sort to `默认排序`.
- Preserve selected tag detail when resetting the tag list view if the selected tag remains visible after reset.
- Keep existing create, edit, merge, assign, bulk assign, unassign, tag-list search/sort, detail filter/search/sort, and delete confirmation behavior.
- Keep the feature frontend-only and metadata-only: no API schema changes, no canon mutation, no `world_version` increment, and no EventLog write.

## Non-goals

- No persisted preferences.
- No keyboard shortcuts.
- No global reset outside `WorldTagsPanel`.
- No backend API or schema changes.
- No canon mutation, no `world_version` increment, and no EventLog write.

## Frontend design

Update `WorldTagsPanel` only.

Tag-list reset:

```ts
function resetTagView() {
  setTagSearchQuery('');
  setTagSortMode('default');
}
```

Selected-tag object reset:

```ts
function resetDetailView() {
  setDetailObjectTypeFilter('all');
  setDetailSearchQuery('');
  setDetailSortMode('default');
}
```

UI:

- Render `重置标签视图` near the tag-list search/sort controls when `tags.length > 0`.
- Disable it only when no save/load operation currently disables the surrounding UI is not necessary; the control is local and safe.
- Render `重置对象视图` near the selected-tag object filter/search/sort controls when detail is loaded.
- Keep button styling consistent with existing `secondary-button` usage.

## Backend design

No backend changes are required. Reset controls only update local React state.

## Testing strategy

### Frontend TDD

Extend `frontend/src/world/WorldTagsPanel.test.tsx` with tests for:

1. Tag-list reset clears tag search and restores default tag sort/order.
2. Selected-tag object reset clears object type filter, detail search, and object sort.
3. Tag-list reset keeps selected detail visible when the reset makes the selected tag visible again.

The first test should fail before implementation because no `重置标签视图` button exists.

### Backend checks

No backend behavior is added. Final verification should still run `backend/tests/test_tags.py` and `backend/tests/test_world_search.py` because the feature sits in the tag/search toolchain.

## Acceptance criteria

- `WorldTagsPanel` shows `重置标签视图` when tags exist.
- Clicking `重置标签视图` clears `搜索标签` and restores `标签排序` to `默认排序`.
- `WorldTagsPanel` shows `重置对象视图` when selected tag detail is loaded.
- Clicking `重置对象视图` restores all object filter/search/sort controls to default.
- Reset actions are local-only and do not call write APIs.
- Existing targeted backend pytest, targeted frontend tests, and frontend build pass.

## Risks and mitigations

- **Unexpectedly clearing selected tag detail.** Resetting the tag list should only clear list controls; the existing hidden-selection effect can keep or restore visibility naturally.
- **Reset controls causing writes.** Implement as direct local `setState` calls only.
- **UI clutter.** Use compact secondary buttons near the relevant control groups.
- **Scope creep into persistence.** Do not save reset/default preferences in MVP36.

## Self-review

- No placeholders remain.
- Scope is limited to local view reset controls.
- The design adds no backend schema or write behavior.
- The design preserves all metadata-only tag invariants.

## Implementation status

Implemented on `feat/mvp36-tag-view-reset` using TDD. Frontend RED was observed for missing `重置标签视图` and `重置对象视图` buttons; GREEN passed after adding local reset handlers and reset buttons for tag-list and selected-tag object controls. Pre-merge verification passed with backend tag/search pytest, frontend targeted Vitest, and frontend production build. An initial frontend verification command was run from the backend directory and failed with missing `package.json`; it was rerun from `/opt/WorldSim-Writer/frontend` and passed.
