# MVP30 Tag Detail Filtering 1.0 Design

## Product-route analysis

MVP23 through MVP29 built a strong Tools Workspace tag workflow: users can create tags, assign and bulk assign objects, filter global search by tags, tag search results, see tag metadata in search, edit tag metadata, and merge duplicate tags. The next low-risk gap is day-to-day navigation inside a single busy tag. As tag collections grow, a selected tag detail panel can mix characters, foreshadows, chapters, and events in one long list with no local filter.

`WorldSim-Writer.md` names multidimensional filtering, batch editing, and资料治理 as Tools Workspace priorities. MVP30 keeps the scope small by adding object-type filtering inside `WorldTagsPanel` tag detail. This is a frontend-first vertical slice with no schema change and no canon write.

## Candidates and recommendation

### 1. Tag Detail Filtering 1.0 — recommended

Add a local object-type filter for the selected tag detail panel, with counts and an empty-state message for the current filter.

Why this is best:

- It improves the usability of tags after create/edit/merge made collections durable.
- It reuses existing `object_type_counts` metadata and loaded `objects` detail data.
- It has narrow TDD coverage in the existing `WorldTagsPanel` tests.
- It is metadata/view-only: no backend schema change, canon mutation, world version increment, or EventLog write.

### 2. Tag archive/soft delete

Hide tags without deleting assignments.

Trade-off: useful for cleanup, but needs new tag state semantics, backend filtering rules, and UI around archived tags.

### 3. Backend paginated tag detail

Add server-side pagination and object-type query parameters for tag detail.

Trade-off: valuable later, but current MVP fixture sizes are small. A local filter provides immediate value while keeping backend complexity low.

## Recommendation

Implement **MVP30 Tag Detail Filtering 1.0**.

## Goals

- Let users filter the selected tag’s assigned objects by object type: all, character, foreshadow, chapter, or event.
- Display per-type counts using the selected tag’s `object_type_counts` plus total assignment count.
- Reset the filter to `all` whenever a different tag detail loads.
- Show a targeted empty state when the current filter has no objects.
- Keep the feature view-only and metadata-only: no API write, no `world_version` increment, and no EventLog write.
- Preserve all existing tag creation, editing, merge, assignment, bulk assignment, unassignment, and deletion behavior.

## Non-goals

- No backend query parameters or pagination.
- No search-result UI changes.
- No bulk operations from the filtered subset.
- No object-title text search inside tag detail.
- No schema migration.
- No canon mutation, no `world_version` increment, and no EventLog write.

## Frontend design

Update `WorldTagsPanel` only.

State:

```ts
const [detailObjectTypeFilter, setDetailObjectTypeFilter] = useState('all');
```

When `loadTag()` successfully loads detail, reset:

```ts
setDetailObjectTypeFilter('all');
```

Derived data:

```ts
const filteredObjects = detail
  ? detailObjectTypeFilter === 'all'
    ? detail.objects
    : detail.objects.filter((item) => item.object_type === detailObjectTypeFilter)
  : [];
```

UI:

- Add a compact filter row inside the selected tag detail panel before the object list.
- Buttons:
  - `全部 (N)` from `detail.tag.assignment_count`
  - each known type with count from `detail.tag.object_type_counts[type] ?? 0`
- Highlight the active filter with the same ring pattern used by selected tags.
- Render the assignment list from `filteredObjects` instead of `detail.objects`.
- Empty states:
  - If `detail.objects.length === 0`, keep existing “这个标签还没有关联对象。” message.
  - If `detail.objects.length > 0` but `filteredObjects.length === 0`, show “当前筛选下没有对象。”

## Backend design

No backend changes are required. Existing `TagDetailResponse` already returns:

- `tag.assignment_count`
- `tag.object_type_counts`
- full `objects` list with `object_type`

## Testing strategy

### Frontend TDD

Extend `frontend/src/world/WorldTagsPanel.test.tsx` with tests for:

1. Filtering selected tag objects by type hides other types and shows only the selected type.
2. A selected type with zero objects shows “当前筛选下没有对象。”
3. Loading a different tag resets the filter back to all.

The first test should fail before implementation because no local filter UI exists.

### Backend checks

No new backend behavior is added. Final verification should still run `backend/tests/test_tags.py` and `backend/tests/test_world_search.py` because the feature is part of the tag/search toolchain and MVP29 touched backend tag merge behavior.

## Acceptance criteria

- `WorldTagsPanel` shows type filter buttons for the selected tag detail.
- Clicking a type filter updates only the visible assigned-object list.
- Counts are shown for all known object types and total assignments.
- A zero-result filter shows a targeted empty state.
- Loading a different tag resets the detail filter to all.
- Existing tag workflows continue to pass targeted tests.
- Targeted backend pytest, targeted frontend tests, and frontend build pass.

## Risks and mitigations

- **Stale filter after switching tags.** Reset `detailObjectTypeFilter` in `loadTag()` after every successful detail load.
- **Confusing empty states.** Keep the existing no-assignments message distinct from the no-results-for-filter message.
- **Scope creep into backend pagination.** Keep MVP30 local-only and defer server filtering until real list sizes justify it.
- **Breaking assignment/unassignment behavior.** Filter only render data; keep assignment and mutation handlers unchanged.

## Self-review

- No placeholders remain.
- Scope is limited to local view filtering inside tag detail.
- The design adds no backend schema or write behavior.
- The design preserves all metadata-only tag invariants.

## Implementation status

Implemented on `feat/mvp30-tag-detail-filter` using TDD. Frontend RED was observed for missing object-type filter controls; GREEN passed with targeted panel tests. Pre-merge verification passed with backend tag/search pytest, frontend targeted Vitest, and frontend production build.
