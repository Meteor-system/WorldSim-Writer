# MVP31 Tag Detail Text Search 1.0 Design

## Product-route analysis

MVP23 through MVP30 built the core Tools Workspace tag workflow: create tags, assign and bulk assign objects, filter global search by tags, tag search results, show tag metadata in search, edit tag metadata, merge duplicate tags, and locally filter a selected tag detail by object type. The next small usability gap is finding a specific item inside a busy tag after narrowing by type.

`WorldSim-Writer.md` calls out the Tools Workspace as the home for global search, multidimensional filtering, tags, batch editing, and data governance. MVP31 stays inside that route by adding local text search to selected tag details. It reuses already-loaded tag detail data, so it does not need backend query parameters, schema changes, canon writes, world-version changes, or EventLog entries.

## Candidates and recommendation

### 1. Tag Detail Text Search 1.0 — recommended

Add a local search box inside the selected tag detail panel. The query filters assigned objects by title, subtitle, snippet, object type, and object id, and combines with MVP30's object-type filter.

Why this is best:

- It compounds the value of MVP30 by letting users narrow busy tag details by both type and text.
- It is a small frontend-only slice with focused Vitest coverage.
- It keeps metadata/tag operations view-only and does not affect canon state.
- It avoids premature backend pagination until real tag-detail scale demands server-side filtering.

### 2. Tag archive/soft delete

Hide old tags without deleting assignments.

Trade-off: useful cleanup primitive, but it needs backend state semantics, list filtering rules, and UI for archived tags.

### 3. Backend tag-detail query filtering

Add `object_type` and `q` query parameters to the tag detail endpoint.

Trade-off: more scalable later, but unnecessary for the current MVP-sized local detail list and would require backend/API changes for the same visible outcome.

## Recommendation

Implement **MVP31 Tag Detail Text Search 1.0**.

## Goals

- Add a local text search input in the selected tag detail panel.
- Filter assigned objects by title, subtitle, snippet, object type, and object id.
- Combine text search with the existing object-type filter.
- Show a clear count of visible matches versus total assigned objects.
- Reset the search query whenever a different tag detail loads.
- Preserve existing empty-state behavior for no assignments and no matches.
- Keep the feature frontend-only and view-only: no API write, no `world_version` increment, and no EventLog write.

## Non-goals

- No backend search endpoint changes.
- No server-side tag-detail pagination.
- No fuzzy ranking or highlighting.
- No saved searches.
- No search-result page changes.
- No schema migration.
- No canon mutation, no `world_version` increment, and no EventLog write.

## Frontend design

Update `WorldTagsPanel` only.

State:

```ts
const [detailSearchQuery, setDetailSearchQuery] = useState('');
```

When `loadTag()` successfully loads detail, reset:

```ts
setDetailSearchQuery('');
```

Derived data:

```ts
const normalizedDetailSearchQuery = detailSearchQuery.trim().toLowerCase();
const typeFilteredObjects = detail
  ? detailObjectTypeFilter === 'all'
    ? detail.objects
    : detail.objects.filter((item) => item.object_type === detailObjectTypeFilter)
  : [];
const filteredObjects = normalizedDetailSearchQuery
  ? typeFilteredObjects.filter((item) => {
      const haystack = [item.title, item.subtitle, item.snippet, item.object_type, String(item.object_id)].join(' ').toLowerCase();
      return haystack.includes(normalizedDetailSearchQuery);
    })
  : typeFilteredObjects;
```

UI:

- Add a compact search input below the object-type filter row and before assignment forms.
- Label it `搜索当前标签对象`.
- Placeholder: `按标题、摘要、类型或 ID 搜索`.
- Show helper text: `显示 X / Y 个对象` where `X` is `filteredObjects.length` and `Y` is `detail.tag.assignment_count`.
- Render the assignment list from `filteredObjects`.
- Keep the existing no-assignment message when `detail.objects.length === 0`.
- Reuse `当前筛选下没有对象。` when either the selected object type or search query has zero matches.

## Backend design

No backend changes are required. Existing `TagDetailResponse` already includes enough data for local search:

- `objects[].title`
- `objects[].subtitle`
- `objects[].snippet`
- `objects[].object_type`
- `objects[].object_id`
- `tag.assignment_count`

## Testing strategy

### Frontend TDD

Extend `frontend/src/world/WorldTagsPanel.test.tsx` with tests for:

1. Text search filters selected tag objects by title/snippet and hides non-matching objects.
2. Text search combines with the existing object-type filter.
3. Loading another tag resets the text search query.

The first test should fail before implementation because no local detail search input exists.

### Backend checks

No backend behavior is added. Final verification should still run `backend/tests/test_tags.py` and `backend/tests/test_world_search.py` because the feature sits in the tag/search toolchain and recent MVPs changed tag behavior.

## Acceptance criteria

- `WorldTagsPanel` shows a text search input for the selected tag detail.
- Typing a query updates only the visible assigned-object list.
- Search matches title, subtitle, snippet, object type, and object id.
- Search combines with object-type filtering.
- Loading a different tag resets the detail search query.
- Zero-result searches show the existing targeted empty state.
- Existing tag workflows continue to pass targeted tests.
- Targeted backend pytest, targeted frontend tests, and frontend build pass.

## Risks and mitigations

- **Stale search after switching tags.** Reset `detailSearchQuery` in `loadTag()` after every successful detail load.
- **Confusing interaction with type filters.** Apply object-type filtering first, then text search, and show visible/total counts.
- **Overbuilding search semantics.** Use simple case-insensitive substring matching only; defer fuzzy ranking and highlighting.
- **Breaking assignment/unassignment behavior.** Filter only render data; keep mutation handlers unchanged.

## Self-review

- No placeholders remain.
- Scope is limited to local view search inside tag detail.
- The design adds no backend schema or write behavior.
- The design preserves all metadata-only tag invariants.

## Implementation status

Implemented on `feat/mvp31-tag-detail-search` using TDD. Frontend RED was observed for the missing `搜索当前标签对象` input and search result count; GREEN passed after adding local search state, case-insensitive text matching, visible counts, and reset-on-tag-load behavior. Pre-merge verification passed with backend tag/search pytest, frontend targeted Vitest, and frontend production build.
