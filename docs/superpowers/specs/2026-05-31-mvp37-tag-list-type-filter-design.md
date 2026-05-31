# MVP37 Tag List Type Filter 1.0 Design

## Product-route analysis

MVP23 through MVP36 built a broad Tools Workspace tag workflow: users can create, edit, merge, delete with confirmation, search and sort the tag list, assign and bulk assign objects, tag search results, inspect selected tag details, filter/search/sort selected-tag objects, and reset accumulated local tag views. The remaining tag-list navigation gap is direct multidimensional filtering by the kind of object a tag currently organizes.

`WorldSim-Writer.md` names the Tools Workspace as the home for global search, multidimensional filtering, tags, batch editing, and data governance. MVP37 stays on that route by adding a local tag-list object-type filter in `WorldTagsPanel`. It is frontend-only, deterministic, and does not affect canon or formal world state.

## Candidates and recommendation

### 1. Tag List Type Filter 1.0 — recommended

Add a local `标签对象类型` selector beside the tag-list search/sort controls. Users can show all tags, only empty tags, or only tags with at least one character, foreshadow, chapter, or event assignment. The filter composes with existing tag-list search, sort, reset, and selected-detail clearing behavior.

Why this is best:

- It directly implements the Tools Workspace's multidimensional filtering direction at the tag-list level.
- It complements MVP33-MVP36 tag search/sort/reset controls without adding backend complexity.
- Existing tag summary responses already expose `object_type_counts`, so no API or schema change is needed.
- It is small and easy to verify with focused Vitest coverage.

### 2. Tag list active-filter chips

Show compact chips for active tag-list search/sort/filter state.

Trade-off: useful after filters exist, but the object-type filter itself is a more fundamental navigation capability.

### 3. Persist tag-list filter preference

Remember the last selected tag-list object-type filter locally.

Trade-off: persistence semantics can surprise users and require storage decisions; the safer first step is an explicit local filter with reset support.

## Recommendation

Implement **MVP37 Tag List Type Filter 1.0**.

## Goals

- Add a local tag-list object-type filter control when tags exist.
- Support filter modes:
  - `全部标签` — no type filtering.
  - `无对象` — tags with `assignment_count === 0`.
  - `角色` — tags with `object_type_counts.character > 0`.
  - `伏笔` — tags with `object_type_counts.foreshadow > 0`.
  - `章节` — tags with `object_type_counts.chapter > 0`.
  - `事件` — tags with `object_type_counts.event > 0`.
- Compose tag-list controls in a deterministic order: object-type filter first, text search second, sort last.
- Keep the visible tag count as `visible / total` after all local filters.
- Clear selected tag detail when the selected tag is hidden by the type filter, using the existing visible-tag effect.
- Extend `重置标签视图` to restore `标签对象类型` to `全部标签` in addition to clearing search and restoring default sort.
- Keep existing create, edit, merge, assign, bulk assign, unassign, delete confirmation, tag-list search/sort/reset, and selected-detail controls.
- Keep the feature frontend-only and metadata-only: no API schema changes, no canon mutation, no `world_version` increment, and no EventLog write.

## Non-goals

- No backend tag-list query parameters.
- No persisted filter preference.
- No grouped tag-list sections.
- No schema migration.
- No canon mutation, no `world_version` increment, and no EventLog write.

## Frontend design

Update `WorldTagsPanel` only.

State:

```ts
const [tagObjectTypeFilter, setTagObjectTypeFilter] = useState('all');
```

Derived tag list:

```ts
const typeFilteredTags = tagObjectTypeFilter === 'all'
  ? tags
  : tags.filter((tag) => {
      if (tagObjectTypeFilter === 'empty') return tag.assignment_count === 0;
      return (tag.object_type_counts[tagObjectTypeFilter] ?? 0) > 0;
    });
const normalizedTagSearchQuery = tagSearchQuery.trim().toLowerCase();
const searchedTags = normalizedTagSearchQuery
  ? typeFilteredTags.filter((tag) => {
      const haystack = [tag.name, tag.slug, tag.color ?? '', String(tag.assignment_count), countText(tag)].join(' ').toLowerCase();
      return haystack.includes(normalizedTagSearchQuery);
    })
  : typeFilteredTags;
```

Reset:

```ts
function resetTagView() {
  setTagSearchQuery('');
  setTagObjectTypeFilter('all');
  setTagSortMode('default');
}
```

UI:

- Render a select labeled `标签对象类型` near `搜索标签` and `标签排序` when tags exist.
- Options: `全部标签`, `无对象`, `角色`, `伏笔`, `章节`, `事件`.
- Keep the existing `重置标签视图` button in the same control row.
- Use the existing `OBJECT_TYPES` list for the object-type options.

## Backend design

No backend changes are required. Existing tag summaries already include:

- `assignment_count`
- `object_type_counts`

## Testing strategy

### Frontend TDD

Extend `frontend/src/world/WorldTagsPanel.test.tsx` with tests for:

1. Filtering visible tags by assigned object type.
2. Filtering visible tags to empty tags and resetting the type filter with `重置标签视图`.
3. Clearing selected tag detail when the selected tag is hidden by the tag-list object-type filter.

The first test should fail before implementation because no `标签对象类型` select exists.

### Backend checks

No backend behavior is added. Final verification should still run `backend/tests/test_tags.py` and `backend/tests/test_world_search.py` because the feature sits in the tag/search toolchain.

## Acceptance criteria

- `WorldTagsPanel` shows `标签对象类型` when tags exist.
- Selecting `伏笔` shows only tags with foreshadow assignments.
- Selecting `无对象` shows only tags without assignments.
- Tag-list type filtering composes with existing tag-list search and sort.
- `重置标签视图` restores `标签对象类型` to `全部标签`.
- If the type filter hides the selected tag, selected tag detail is cleared.
- Existing targeted backend pytest, targeted frontend tests, and frontend build pass.

## Risks and mitigations

- **Unexpected selected-detail persistence.** Reuse the existing `visibleTags`-based effect so any hidden selected tag clears detail consistently.
- **Filter/search composition ambiguity.** Apply type filter first, text search second, sort last, and document that order.
- **UI clutter.** Add one compact select to the existing tag-list control grid and keep reset nearby.
- **Scope creep into backend filtering.** Keep MVP37 local-only and defer server filtering until tag-list scale requires it.

## Self-review

- No placeholders remain.
- Scope is limited to local tag-list object-type filtering.
- The design adds no backend schema or write behavior.
- The design preserves all metadata-only tag invariants.

## Implementation status

Implemented on `feat/mvp37-tag-list-type-filter` using TDD. Frontend RED was observed for the missing `标签对象类型` select; GREEN passed after adding local tag-list object-type filter state, type-filter-plus-search-plus-sort derivation, reset integration, and filter UI. Pre-merge verification passed with backend tag/search pytest, frontend targeted Vitest, and frontend production build. An initial frontend verification command was run from the backend directory and failed with missing `package.json`; it was rerun from `/opt/WorldSim-Writer/frontend` and passed.
