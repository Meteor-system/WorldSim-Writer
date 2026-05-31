# MVP35 Tag Detail Object Sort 1.0 Design

## Product-route analysis

MVP23 through MVP34 built a broad Tools Workspace tag workflow: users can create, edit, merge, delete with confirmation, search and sort tags, assign and bulk assign objects, tag search results, filter global search by tags, inspect selected tag details, filter selected tag objects by type, and search within selected tag details. The remaining local navigation gap is ordering the objects inside a selected tag detail after filtering and searching.

`WorldSim-Writer.md` names the Tools Workspace as the place for global search, multidimensional filtering, tags, batch editing, and data governance. MVP35 stays on that route by adding local sort controls for already-loaded selected-tag objects in `WorldTagsPanel`. It is frontend-only, deterministic, and does not affect canon or formal world state.

## Candidates and recommendation

### 1. Tag Detail Object Sort 1.0 — recommended

Add a local sort selector beside the selected-tag object search. Users can order visible tag objects by default API order, title, object type, or object id. Sorting composes with the existing type filter and detail text search.

Why this is best:

- It directly complements MVP30 type filtering and MVP31 detail text search.
- It mirrors MVP34 tag-list sorting at the next drill-down level.
- It remains a small frontend-only slice with focused Vitest coverage.
- It avoids backend query parameters while selected-tag object lists remain small.

### 2. Tag detail grouped sections by object type

Group selected-tag objects under type headings.

Trade-off: useful, but changes visual structure more heavily and can conflict with active type filters and future batch controls.

### 3. Tag detail copy object IDs

Add quick copy controls for object IDs in selected-tag detail rows.

Trade-off: helpful for power users, but sorting improves all users' scanning/navigation first.

## Recommendation

Implement **MVP35 Tag Detail Object Sort 1.0**.

## Goals

- Add a local selected-tag object sort control in `WorldTagsPanel` when tag detail is loaded.
- Support sort modes:
  - `默认排序` — preserve API/detail object order.
  - `标题 A-Z` — sort by object title, then object type, then object id.
  - `类型 A-Z` — sort by object type, then title, then object id.
  - `ID 从小到大` — sort by object id ascending, then object type.
- Compose sorting with existing selected-tag object filters: object type filter applies first, detail text search applies second, sort applies last.
- Show selected-tag object cards from the sorted filtered list.
- Preserve the existing visible count and empty state.
- Reset detail object sort to default when loading another tag.
- Keep existing create, edit, merge, assign, bulk assign, unassign, tag-list search/sort, detail filter/search, and delete confirmation behavior.
- Keep the feature frontend-only and metadata-only: no API schema changes, no canon mutation, no `world_version` increment, and no EventLog write.

## Non-goals

- No backend tag-detail query parameters.
- No server-side pagination.
- No persisted user sort preference.
- No grouping or section headers.
- No schema migration.
- No canon mutation, no `world_version` increment, and no EventLog write.

## Frontend design

Update `WorldTagsPanel` only.

State:

```ts
const [detailSortMode, setDetailSortMode] = useState('default');
```

Reset in `loadTag()`:

```ts
setDetailObjectTypeFilter('all');
setDetailSearchQuery('');
setDetailSortMode('default');
```

Derived data:

```ts
const normalizedDetailSearchQuery = detailSearchQuery.trim().toLowerCase();
const typeFilteredObjects = detail
  ? detailObjectTypeFilter === 'all'
    ? detail.objects
    : detail.objects.filter((item) => item.object_type === detailObjectTypeFilter)
  : [];
const searchedObjects = normalizedDetailSearchQuery
  ? typeFilteredObjects.filter((item) => {
      const haystack = [item.title, item.subtitle, item.snippet, item.object_type, String(item.object_id)].join(' ').toLowerCase();
      return haystack.includes(normalizedDetailSearchQuery);
    })
  : typeFilteredObjects;
const filteredObjects = [...searchedObjects].sort((left, right) => {
  if (detailSortMode === 'title') return left.title.localeCompare(right.title) || left.object_type.localeCompare(right.object_type) || left.object_id - right.object_id;
  if (detailSortMode === 'type') return left.object_type.localeCompare(right.object_type) || left.title.localeCompare(right.title) || left.object_id - right.object_id;
  if (detailSortMode === 'id') return left.object_id - right.object_id || left.object_type.localeCompare(right.object_type);
  return 0;
});
```

UI:

- Render sort control when tag detail is loaded, near `搜索当前标签对象`.
- Label: `对象排序`.
- Options:
  - `默认排序`
  - `标题 A-Z`
  - `类型 A-Z`
  - `ID 从小到大`

## Backend design

No backend changes are required. Existing selected-tag detail objects already include the fields needed for local sorting:

- `title`
- `object_type`
- `object_id`

## Testing strategy

### Frontend TDD

Extend `frontend/src/world/WorldTagsPanel.test.tsx` with tests for:

1. Sorting selected tag objects by title after loading a mixed detail response.
2. Sorting searched selected tag objects by object id.
3. Resetting selected-tag object sort when loading another tag.

The first test should fail before implementation because no `对象排序` select exists.

### Backend checks

No backend behavior is added. Final verification should still run `backend/tests/test_tags.py` and `backend/tests/test_world_search.py` because the feature sits in the tag/search toolchain.

## Acceptance criteria

- `WorldTagsPanel` shows an object sort selector when selected tag detail is loaded.
- Selecting `标题 A-Z` orders visible selected-tag objects by title.
- Selecting `ID 从小到大` orders visible selected-tag objects by object id.
- Sorting composes with selected-tag object type filters and text search.
- Loading a different tag resets selected-tag object sort to default.
- Existing targeted backend pytest, targeted frontend tests, and frontend build pass.

## Risks and mitigations

- **Accidentally mutating detail objects with `sort()`.** Sort a copied array, not `detail.objects` or filtered arrays in-place.
- **Confusing composition order.** Apply type filter first, detail text search second, sort last.
- **Locale surprises in Chinese titles.** Use simple `localeCompare`; this is sufficient for MVP local ordering and can be refined later.
- **Scope creep into backend filtering.** Keep MVP35 local-only and defer server sorting until tag-detail scale requires it.

## Self-review

- No placeholders remain.
- Scope is limited to local selected-tag object sorting.
- The design adds no backend schema or write behavior.
- The design preserves all metadata-only tag invariants.

## Implementation status

Implemented on `feat/mvp35-tag-detail-sort` using TDD. Frontend RED was observed for the missing `对象排序` select; GREEN passed after adding local selected-tag object sort state, reset-on-tag-load behavior, type-filter-plus-search-plus-sort derivation, and object sort UI. Pre-merge verification passed with backend tag/search pytest, frontend targeted Vitest, and frontend production build. An initial frontend verification command was run from the backend directory and failed with missing `package.json`; it was rerun from `/opt/WorldSim-Writer/frontend` and passed.
