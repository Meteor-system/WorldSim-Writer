# MVP34 Tag List Sort 1.0 Design

## Product-route analysis

MVP23 through MVP33 built a usable Tools Workspace tag workflow: users can create tags, assign and bulk assign objects, filter global search by tags, tag search results, show tag metadata in search, edit tags, merge tags, filter/search selected tag details, confirm destructive deletes, and search the tag list itself. The next small navigation gap is ordering a growing tag list after finding/filtering became possible.

`WorldSim-Writer.md` names the Tools Workspace as the place for global search, multidimensional filtering, tags, batch editing, and data governance. MVP34 stays on that route by adding local sort controls for already-loaded tag summaries in `WorldTagsPanel`. It is frontend-only, deterministic, and does not affect canon or formal world state.

## Candidates and recommendation

### 1. Tag List Sort 1.0 — recommended

Add a local sort selector above tag cards. Users can order visible tags by default load order, name, assignment count, or creation time. Sorting composes with MVP33 tag-list search.

Why this is best:

- It directly complements MVP33 search: search narrows the list, sort controls ordering within the narrowed list.
- It remains a small frontend-only slice with focused Vitest coverage.
- It avoids premature backend sorting/pagination while local tag lists remain small.
- It improves daily Tools Workspace navigation without changing write behavior.

### 2. Tag color filter

Let users filter tags by color.

Trade-off: useful once colors carry strong semantics, but current data has no formal color taxonomy and search already matches color text.

### 3. Tag duplicate warning

Warn before creating a tag with a near-duplicate name.

Trade-off: valuable, but duplicate semantics are better enforced by backend slug/name constraints and error messages; a local sort is smaller and less ambiguous.

## Recommendation

Implement **MVP34 Tag List Sort 1.0**.

## Goals

- Add a local tag-list sort control in `WorldTagsPanel` when tags exist.
- Support sort modes:
  - `默认排序` — preserve backend/load order.
  - `名称 A-Z` — sort by tag name, then id.
  - `对象数最多` — sort by assignment count descending, then name, then id.
  - `最新创建` — sort by `created_at` descending, then id descending.
- Compose sorting with MVP33 tag-list search: search filters first, then sorting orders visible results.
- Show tag cards from the sorted visible list.
- Preserve the existing visible count and no-match state.
- Preserve selected-detail clearing if the selected tag is hidden by search.
- Keep existing create, edit, merge, assign, bulk assign, unassign, detail filter/search, delete confirmation, and tag-list search behavior.
- Keep the feature frontend-only and metadata-only: no API schema changes, no canon mutation, no `world_version` increment, and no EventLog write.

## Non-goals

- No backend query parameters for sorting.
- No server-side pagination.
- No persisted user sort preference.
- No drag-and-drop manual tag ordering.
- No schema migration.
- No canon mutation, no `world_version` increment, and no EventLog write.

## Frontend design

Update `WorldTagsPanel` only.

State:

```ts
const [tagSortMode, setTagSortMode] = useState('default');
```

Derived data:

```ts
const normalizedTagSearchQuery = tagSearchQuery.trim().toLowerCase();
const searchedTags = normalizedTagSearchQuery
  ? tags.filter((tag) => {
      const haystack = [tag.name, tag.slug, tag.color ?? '', String(tag.assignment_count), countText(tag)].join(' ').toLowerCase();
      return haystack.includes(normalizedTagSearchQuery);
    })
  : tags;
const visibleTags = [...searchedTags].sort((left, right) => {
  if (tagSortMode === 'name') return left.name.localeCompare(right.name) || left.id - right.id;
  if (tagSortMode === 'count') return right.assignment_count - left.assignment_count || left.name.localeCompare(right.name) || left.id - right.id;
  if (tagSortMode === 'created') return right.created_at.localeCompare(left.created_at) || right.id - left.id;
  return 0;
});
const visibleTagIdsKey = visibleTags.map((tag) => tag.id).join(',');
```

Selection behavior:

- Continue clearing selected detail only when a search query hides the selected tag.
- Sorting must not clear selected detail because the selected tag remains visible.
- Existing `visibleTags`-based effect remains valid because sorting changes the order but not membership.

UI:

- Render a sort `<select>` when `tags.length > 0`.
- Label: `标签排序`.
- Options:
  - `默认排序`
  - `名称 A-Z`
  - `对象数最多`
  - `最新创建`
- Render tag cards from `visibleTags`.

## Backend design

No backend changes are required. Existing `TagListResponse.tags` already includes the fields needed for local sorting:

- `name`
- `assignment_count`
- `created_at`
- `id`

## Testing strategy

### Frontend TDD

Extend `frontend/src/world/WorldTagsPanel.test.tsx` with tests for:

1. Sorting visible tags by assignment count descending.
2. Sorting visible tags by name after applying tag-list search.
3. Confirming that changing sort order does not clear the currently selected tag detail.

The first test should fail before implementation because no `标签排序` select exists.

### Backend checks

No backend behavior is added. Final verification should still run `backend/tests/test_tags.py` and `backend/tests/test_world_search.py` because the feature sits in the tag/search toolchain.

## Acceptance criteria

- `WorldTagsPanel` shows a tag-list sort selector when tags exist.
- Selecting `对象数最多` orders visible tag cards by assignment count descending.
- Selecting `名称 A-Z` orders visible tag cards by name ascending.
- Sort controls compose with tag-list search.
- Sorting alone does not call write APIs and does not clear selected detail.
- Existing targeted backend pytest, targeted frontend tests, and frontend build pass.

## Risks and mitigations

- **Accidentally mutating React state with `sort()`.** Sort a copied array, not `tags` directly.
- **Selection flicker from ordering changes.** The selected-detail clearing effect checks membership, so sorting should not clear detail.
- **Locale surprises in Chinese sorting.** Use simple `localeCompare`; this is sufficient for MVP local ordering and can be refined later.
- **Scope creep into backend pagination.** Keep MVP34 local-only and defer server sorting until tag-list scale requires it.

## Self-review

- No placeholders remain.
- Scope is limited to local tag-list sorting.
- The design adds no backend schema or write behavior.
- The design preserves all metadata-only tag invariants.

## Implementation status

Implemented on `feat/mvp34-tag-list-sort` using TDD. Frontend RED was observed for the missing `标签排序` select; GREEN passed after adding local sort state, search-then-sort visible tag derivation, count/name/created/default sort modes, and sort UI. Pre-merge verification passed with backend tag/search pytest, frontend targeted Vitest, and frontend production build. An initial frontend verification command was run from the backend directory and failed with missing `package.json`; it was rerun from `/opt/WorldSim-Writer/frontend` and passed.
