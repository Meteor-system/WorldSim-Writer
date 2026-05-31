# MVP38 Tag Filter Counts 1.0 Design

## Product-route analysis

MVP37 added a local `标签对象类型` selector so users can narrow the tag list by empty tags or tags that organize characters, foreshadows, chapters, and events. The selector works, but it does not preview how many tags each option will show. Users can choose `事件` without knowing that no event-tagged collections exist, which makes filtering feel like trial and error.

`WorldSim-Writer.md` names the Tools Workspace as the home for global search, multidimensional filtering, tags, batch editing, and data governance. MVP38 stays on that route by making the new tag-list filter self-explanatory with local counts derived from already-loaded tag summaries. It is frontend-only, deterministic, and does not affect canon or formal world state.

## Candidates and recommendation

### 1. Tag Filter Counts 1.0 — recommended

Show tag counts in the `标签对象类型` select options: total tags, empty tags, and number of tags that have at least one assignment for each object type. The option values stay unchanged, so MVP37 filtering behavior remains intact.

Why this is best:

- It directly improves the usability of the new MVP37 filter.
- It keeps filtering predictable by showing which options are empty before selection.
- It uses existing loaded tag summary data and needs no backend work.
- It is a very small TDD-verifiable UI change.

### 2. Disable zero-count filter options

Disable options like `事件` when no matching tags exist.

Trade-off: potentially useful later, but disabled controls can be confusing and make it harder to understand the full supported type set. Counts are clearer and less restrictive.

### 3. Add active filter summary chips

Show a compact summary of active tag-list search/type/sort controls.

Trade-off: useful after filtering, but counts improve the selection decision before filtering.

## Recommendation

Implement **MVP38 Tag Filter Counts 1.0**.

## Goals

- Add local counts to each `标签对象类型` option when tags exist.
- Count labels should describe the number of tags matching each filter option, not the total assignment count:
  - `全部标签 3` means three loaded tags total.
  - `无对象 1` means one loaded tag has no assignments.
  - `角色 1` means one loaded tag has at least one character assignment.
- Keep option values unchanged: `all`, `empty`, `character`, `foreshadow`, `chapter`, `event`.
- Keep MVP37 filter behavior unchanged.
- Keep counts derived from the full loaded tag list, not from currently searched/filtered visible tags.
- Keep existing tag-list search/sort/reset and selected-detail clearing behavior.
- Keep the feature frontend-only and metadata-only: no API schema changes, no canon mutation, no `world_version` increment, and no EventLog write.

## Non-goals

- No disabled filter options.
- No backend tag-list count endpoint.
- No persisted filter preference.
- No grouped tag-list sections.
- No schema migration.
- No canon mutation, no `world_version` increment, and no EventLog write.

## Frontend design

Update `WorldTagsPanel` only.

Add a helper near `countText()`:

```ts
function tagTypeFilterCount(tags: TagSummaryResponse[], value: string): number {
  if (value === 'all') return tags.length;
  if (value === 'empty') return tags.filter((tag) => tag.assignment_count === 0).length;
  return tags.filter((tag) => (tag.object_type_counts[value] ?? 0) > 0).length;
}
```

Update the `标签对象类型` select option labels:

```tsx
<option value="all">全部标签 {tagTypeFilterCount(tags, 'all')}</option>
<option value="empty">无对象 {tagTypeFilterCount(tags, 'empty')}</option>
{OBJECT_TYPES.map((item) => (
  <option key={item.value} value={item.value}>{item.label} {tagTypeFilterCount(tags, item.value)}</option>
))}
```

The existing `tagObjectTypeFilter` state and filtering derivation are unchanged.

## Backend design

No backend changes are required. Existing tag summaries already include:

- `assignment_count`
- `object_type_counts`

## Testing strategy

### Frontend TDD

Extend `frontend/src/world/WorldTagsPanel.test.tsx` with tests for:

1. Rendering tag-list type-filter option counts from `sortableListResponse`.
2. Keeping the counts based on all loaded tags while text search narrows the visible list.

The first test should fail before implementation because the options only show labels without counts.

### Backend checks

No backend behavior is added. Final verification should still run `backend/tests/test_tags.py` and `backend/tests/test_world_search.py` because the feature sits in the tag/search toolchain.

## Acceptance criteria

- `标签对象类型` options show counts for all tags, empty tags, and each object type.
- Counts represent matching tag count, not assignment totals.
- Counts remain based on all loaded tags while tag-list search narrows visible tags.
- Existing tag-list type filtering still works with unchanged option values.
- Existing targeted backend pytest, targeted frontend tests, and frontend build pass.

## Risks and mitigations

- **Counting assignments instead of tags.** Count tags whose `object_type_counts[type]` is greater than zero, not the numeric assignment total.
- **Breaking select values.** Only change visible labels; keep option values unchanged.
- **Recomputing too much.** The loaded tag list is small in the MVP, so simple derived counts are sufficient.
- **Scope creep into backend counts.** Keep MVP38 local-only and defer server-side aggregation until scale requires it.

## Self-review

- No placeholders remain.
- Scope is limited to local type-filter option counts.
- The design adds no backend schema or write behavior.
- The design preserves all metadata-only tag invariants.

## Implementation status

Implemented on `feat/mvp38-tag-filter-counts` using TDD. Frontend RED was observed for missing counts in `标签对象类型` options; GREEN passed after adding a local tag type filter count helper and count labels while keeping option values unchanged. Pre-merge verification passed with backend tag/search pytest, frontend targeted Vitest, and frontend production build. An initial frontend verification command was run from the backend directory and failed with missing `package.json`; it was rerun from `/opt/WorldSim-Writer/frontend` and passed.
