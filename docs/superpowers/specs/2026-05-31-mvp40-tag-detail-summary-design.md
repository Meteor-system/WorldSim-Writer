# MVP40 Tag Detail View Summary 1.0 Design

## Product-route analysis

MVP30 through MVP36 added local selected-tag object controls: object-type filtering, detail text search, object sorting, and reset. MVP39 added a summary for the tag-list controls, making combined list state readable at a glance. The selected-tag detail panel now has the same accumulated-control problem: users can combine object type, object search, and object sort, but there is no single line explaining the current object view.

`WorldSim-Writer.md` names the Tools Workspace as the home for global search, multidimensional filtering, tags, batch editing, and data governance. MVP40 stays on that route by adding a local selected-tag object view summary in `WorldTagsPanel`. It is frontend-only, deterministic, and does not affect canon or formal world state.

## Candidates and recommendation

### 1. Tag Detail View Summary 1.0 — recommended

Show a compact summary near the selected-tag object controls that reports visible/total object count, active detail search query, active object-type filter, and active object sort mode. The summary updates as local detail controls change and returns to default wording when `重置对象视图` is clicked.

Why this is best:

- It mirrors MVP39 at the selected-tag detail level.
- It makes combined detail filters and sort easier to understand, especially when few or no objects remain visible.
- It is small, frontend-only, and covered by focused Vitest tests.
- It preserves all existing selected-tag detail behavior.

### 2. Detail active filter chips with per-chip removal

Render separate chips for object type, detail search, and sort, each with a clear button.

Trade-off: useful later, but it adds more interaction logic. A read-only summary line is smaller and safer.

### 3. Detail empty-state-specific copy

Change the empty state depending on whether type filter, search, or both caused no visible objects.

Trade-off: helpful, but a persistent summary improves both empty and non-empty detail views.

## Recommendation

Implement **MVP40 Tag Detail View Summary 1.0**.

## Goals

- Add a local selected-tag object view summary when tag detail is loaded.
- Summary should include:
  - visible/total object count,
  - detail search state (`搜索「...」` or `未搜索`),
  - object-type filter state (`全部对象`, `角色`, `伏笔`, `章节`, `事件`),
  - object sort state (`默认排序`, `标题 A-Z`, `类型 A-Z`, `ID 从小到大`).
- Summary should update when object type filter, detail search, or object sort changes.
- `重置对象视图` should restore the summary to default state.
- Keep existing create, edit, merge, assign, bulk assign, unassign, delete confirmation, tag-list controls, and selected-detail controls.
- Keep the feature frontend-only and metadata-only: no API schema changes, no canon mutation, no `world_version` increment, and no EventLog write.

## Non-goals

- No per-chip clear controls.
- No persisted detail filter preference.
- No backend summary endpoint.
- No schema migration.
- No canon mutation, no `world_version` increment, and no EventLog write.

## Frontend design

Update `WorldTagsPanel` only.

Add helpers near the existing label helpers:

```ts
function objectTypeFilterLabel(value: string): string {
  if (value === 'all') return '全部对象';
  return OBJECT_TYPES.find((item) => item.value === value)?.label ?? value;
}

function detailSortLabel(value: string): string {
  if (value === 'title') return '标题 A-Z';
  if (value === 'type') return '类型 A-Z';
  if (value === 'id') return 'ID 从小到大';
  return '默认排序';
}
```

Add derived summary text after `filteredObjects`:

```ts
const detailViewSummary = detail
  ? [
      `显示 ${filteredObjects.length} / ${detail.tag.assignment_count} 个对象`,
      normalizedDetailSearchQuery ? `搜索「${detailSearchQuery.trim()}」` : '未搜索',
      `类型：${objectTypeFilterLabel(detailObjectTypeFilter)}`,
      `排序：${detailSortLabel(detailSortMode)}`,
    ].join(' · ')
  : '';
```

Render it below the selected-tag object search/sort/reset controls while detail is loaded:

```tsx
<p className="ink-muted text-xs" aria-label="标签对象视图摘要">{detailViewSummary}</p>
```

## Backend design

No backend changes are required.

## Testing strategy

### Frontend TDD

Extend `frontend/src/world/WorldTagsPanel.test.tsx` with tests for:

1. Updating the selected-tag object view summary when type filter, detail search, and object sort controls change.
2. Resetting the selected-tag object view summary when `重置对象视图` is clicked.

The first test should fail before implementation because no `标签对象视图摘要` element exists.

### Backend checks

No backend behavior is added. Final verification should still run `backend/tests/test_tags.py` and `backend/tests/test_world_search.py` because the feature sits in the tag/search toolchain.

## Acceptance criteria

- `WorldTagsPanel` shows a `标签对象视图摘要` when selected tag detail is loaded.
- The summary reports visible/total object count, detail search state, object type filter state, and object sort state.
- The summary updates as local selected-tag object controls change.
- `重置对象视图` restores the summary to the default no-search/all-objects/default-sort state.
- Existing targeted backend pytest, targeted frontend tests, and frontend build pass.

## Risks and mitigations

- **Raw internal values leaking to users.** Use explicit label helpers for object type and detail sort values.
- **Summary showing when no detail is loaded.** Only render inside the existing `detail && (...)` block.
- **Search whitespace mismatch.** Use the trimmed detail search query in the summary.
- **Scope creep into chip controls.** Keep MVP40 read-only summary text; defer chip interactions.

## Self-review

- No placeholders remain.
- Scope is limited to local selected-tag object summary text.
- The design adds no backend schema or write behavior.
- The design preserves all metadata-only tag invariants.

## Implementation status

Implemented on `feat/mvp40-tag-detail-summary` using TDD. Frontend RED was observed for the missing `标签对象视图摘要` element; GREEN passed after adding local detail label helpers, derived selected-tag object-view summary text, and summary UI below the selected-tag object controls. Pre-merge verification passed with backend tag/search pytest, frontend targeted Vitest, and frontend production build. An initial frontend verification command was run from the backend directory and failed with missing `package.json`; it was rerun from `/opt/WorldSim-Writer/frontend` and passed.
