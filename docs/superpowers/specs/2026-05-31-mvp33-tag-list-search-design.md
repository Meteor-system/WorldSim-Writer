# MVP33 Tag List Search 1.0 Design

## Product-route analysis

MVP23 through MVP32 built a broad Tools Workspace tag workflow: users can create tags, assign and bulk assign objects, filter global search by tags, tag search results, show tag metadata in search, edit tags, merge tags, filter selected tag details, search inside selected tag details, and confirm destructive deletes. The next small usability gap is finding a tag itself when the tag list grows.

`WorldSim-Writer.md` names the Tools Workspace as the place for global search, multidimensional filtering, tags, batch editing, and data governance. MVP33 stays on that route by adding local text search over the tag list in `WorldTagsPanel`. It is frontend-only, reuses loaded tag summaries, and does not affect canon or formal world state.

## Candidates and recommendation

### 1. Tag List Search 1.0 — recommended

Add a local search input above the tag chips/cards. The query filters visible tags by tag name, slug, color, object type summary, and assignment count.

Why this is best:

- It complements MVP31, which searches inside a selected tag, by making the tag list itself navigable.
- It remains a small frontend-only slice with focused Vitest coverage.
- It avoids premature backend tag-list query parameters while local tag lists remain small.
- It improves daily Tools Workspace use without changing write behavior.

### 2. Tag list sort controls

Let users sort tags by name, count, or creation order.

Trade-off: useful, but search is more directly helpful once users know part of a tag name or category.

### 3. Tag delete undo

Offer a reversible tag deletion flow.

Trade-off: valuable, but undo needs backend restore semantics or re-creation decisions and is not as small as a local list filter.

## Recommendation

Implement **MVP33 Tag List Search 1.0**.

## Goals

- Add a local text search input for loaded tags in `WorldTagsPanel`.
- Filter visible tag cards by name, slug, color, object-type summary, and assignment count.
- Show a visible count: `显示 X / Y 个标签`.
- Preserve the existing no-tags empty state when there are no tags at all.
- Show a targeted empty state when the query matches no tags.
- Clear selected tag detail if the selected tag is hidden by the current tag-list search.
- Keep existing create, edit, merge, assign, bulk assign, unassign, detail filter/search, and delete confirmation behavior.
- Keep the feature frontend-only and metadata-only: no API schema changes, no canon mutation, no `world_version` increment, and no EventLog write.

## Non-goals

- No backend tag-list query parameters.
- No server-side pagination.
- No fuzzy ranking or highlighting.
- No saved tag views.
- No schema migration.
- No canon mutation, no `world_version` increment, and no EventLog write.

## Frontend design

Update `WorldTagsPanel` only.

State:

```ts
const [tagSearchQuery, setTagSearchQuery] = useState('');
```

Derived data:

```ts
const normalizedTagSearchQuery = tagSearchQuery.trim().toLowerCase();
const visibleTags = normalizedTagSearchQuery
  ? tags.filter((tag) => {
      const haystack = [
        tag.name,
        tag.slug,
        tag.color ?? '',
        String(tag.assignment_count),
        countText(tag),
      ].join(' ').toLowerCase();
      return haystack.includes(normalizedTagSearchQuery);
    })
  : tags;
```

Selection behavior:

- If a tag is selected and the query changes such that the selected tag is no longer visible, clear selected detail to avoid showing details for a hidden tag.
- Implement with a `useEffect` that depends on the selected tag id and `visibleTags`.

```ts
useEffect(() => {
  if (selectedTagId !== null && !visibleTags.some((tag) => tag.id === selectedTagId)) {
    setSelectedTagId(null);
    setDetail(null);
    setDeleteConfirming(false);
  }
}, [selectedTagId, visibleTags]);
```

UI:

- Render the search input when `tags.length > 0`.
- Label: `搜索标签`.
- Placeholder: `按名称、颜色、类型或数量搜索`.
- Helper text: `显示 {visibleTags.length} / {tags.length} 个标签`.
- Render tag cards from `visibleTags`.
- If `tags.length > 0` and `visibleTags.length === 0`, show `当前搜索没有匹配标签。`.

## Backend design

No backend changes are required. Existing `TagListResponse.tags` already includes the fields needed for local search:

- `name`
- `slug`
- `color`
- `assignment_count`
- `object_type_counts`

## Testing strategy

### Frontend TDD

Extend `frontend/src/world/WorldTagsPanel.test.tsx` with tests for:

1. Tag-list search filters visible tag cards by tag name.
2. Tag-list search can match object-type/count summary text.
3. A no-match query shows `当前搜索没有匹配标签。`.
4. Hiding the selected tag clears selected tag detail.

The first test should fail before implementation because no `搜索标签` input exists.

### Backend checks

No backend behavior is added. Final verification should still run `backend/tests/test_tags.py` and `backend/tests/test_world_search.py` because the feature sits in the tag/search toolchain.

## Acceptance criteria

- `WorldTagsPanel` shows a tag-list search input when tags exist.
- Typing a query updates visible tag cards without API calls.
- Search matches tag name, slug, color, object-type summary, and assignment count.
- The visible-count helper updates with the filtered result count.
- No-match queries show a targeted empty state.
- If the selected tag becomes hidden by the query, selected detail is cleared.
- Existing targeted backend pytest, targeted frontend tests, and frontend build pass.

## Risks and mitigations

- **Infinite render loop from derived arrays in `useEffect`.** Use a stable key from visible tag ids for the dependency rather than the raw array object.
- **Confusing selected hidden detail.** Clear selected detail when a query hides the selected tag.
- **Overbuilding search semantics.** Use simple case-insensitive substring matching only.
- **Scope creep into backend filtering.** Keep MVP33 local-only and defer server filtering until tag-list scale requires it.

## Self-review

- No placeholders remain.
- Scope is limited to local tag-list search.
- The design adds no backend schema or write behavior.
- The design preserves all metadata-only tag invariants.

## Implementation status

Implemented on `feat/mvp33-tag-list-search` using TDD. Frontend RED was observed for the missing `搜索标签` input and local tag-list filtering; GREEN passed after adding local tag search state, visible tag derivation, no-match empty state, visible counts, and selected-detail clearing when a query hides the selected tag. Pre-merge verification passed with backend tag/search pytest, frontend targeted Vitest, and frontend production build.
