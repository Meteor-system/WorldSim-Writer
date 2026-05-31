# MVP39 Tag View Summary 1.0 Design

## Product-route analysis

MVP33 through MVP38 added increasingly useful local tag-list controls: text search, sort, reset, object-type filtering, and option counts. The tag list now supports multidimensional filtering, but the resulting control state is spread across separate inputs. When a user combines search, object type, and sorting, there is no single readable summary of what view they are currently looking at.

`WorldSim-Writer.md` names the Tools Workspace as the home for global search, multidimensional filtering, tags, batch editing, and data governance. MVP39 stays on that route by adding a local tag view summary line in `WorldTagsPanel`. It is frontend-only, deterministic, and does not affect canon or formal world state.

## Candidates and recommendation

### 1. Tag View Summary 1.0 — recommended

Show a compact summary under the tag-list controls that reports the active search query, active object-type filter, active sort mode, and visible/total tag count. The summary updates as local controls change and returns to default wording when `重置标签视图` is clicked.

Why this is best:

- It makes the accumulated MVP33-MVP38 controls easier to understand at a glance.
- It improves confidence when search/filter combinations return a narrow or empty result.
- It is small, frontend-only, and covered by focused Vitest tests.
- It preserves all existing filtering, sorting, and reset behavior.

### 2. Active filter chips with per-chip removal

Render separate chips for search, type filter, and sort, each with a clear button.

Trade-off: useful later, but chip interactions add more UI and state handling. A summary line is simpler and safer.

### 3. Filter-specific empty state copy

Change the empty state text depending on whether search, type filter, or both caused no results.

Trade-off: helpful, but a persistent summary improves both empty and non-empty states.

## Recommendation

Implement **MVP39 Tag View Summary 1.0**.

## Goals

- Add a local tag-list view summary when tags exist.
- Summary should include:
  - visible/total tag count,
  - search state (`搜索「...」` or `未搜索`),
  - object-type filter state (`全部标签`, `无对象`, `角色`, `伏笔`, `章节`, `事件`),
  - sort state (`默认排序`, `名称 A-Z`, `对象数最多`, `最新创建`).
- Summary should update when tag search, object-type filter, or sort changes.
- `重置标签视图` should restore the summary to default state.
- Keep existing create, edit, merge, assign, bulk assign, unassign, delete confirmation, tag-list search/filter/sort/reset, and selected-detail controls.
- Keep the feature frontend-only and metadata-only: no API schema changes, no canon mutation, no `world_version` increment, and no EventLog write.

## Non-goals

- No per-chip clear controls.
- No persisted filter preference.
- No backend summary endpoint.
- No schema migration.
- No canon mutation, no `world_version` increment, and no EventLog write.

## Frontend design

Update `WorldTagsPanel` only.

Add helpers near the existing helper functions:

```ts
function tagTypeFilterLabel(value: string): string {
  if (value === 'all') return '全部标签';
  if (value === 'empty') return '无对象';
  return OBJECT_TYPES.find((item) => item.value === value)?.label ?? value;
}

function tagSortLabel(value: string): string {
  if (value === 'name') return '名称 A-Z';
  if (value === 'count') return '对象数最多';
  if (value === 'created') return '最新创建';
  return '默认排序';
}
```

Add derived summary text after `visibleTags`:

```ts
const tagViewSummary = [
  `显示 ${visibleTags.length} / ${tags.length} 个标签`,
  normalizedTagSearchQuery ? `搜索「${tagSearchQuery.trim()}」` : '未搜索',
  `类型：${tagTypeFilterLabel(tagObjectTypeFilter)}`,
  `排序：${tagSortLabel(tagSortMode)}`,
].join(' · ');
```

Render it below the tag-list controls while `tags.length > 0`:

```tsx
<p className="ink-muted text-xs" aria-label="标签视图摘要">{tagViewSummary}</p>
```

## Backend design

No backend changes are required.

## Testing strategy

### Frontend TDD

Extend `frontend/src/world/WorldTagsPanel.test.tsx` with tests for:

1. Updating the tag view summary when search, object-type filter, and sort controls change.
2. Resetting the tag view summary when `重置标签视图` is clicked.

The first test should fail before implementation because no `标签视图摘要` element exists.

### Backend checks

No backend behavior is added. Final verification should still run `backend/tests/test_tags.py` and `backend/tests/test_world_search.py` because the feature sits in the tag/search toolchain.

## Acceptance criteria

- `WorldTagsPanel` shows a `标签视图摘要` when tags exist.
- The summary reports visible/total count, search state, type filter state, and sort state.
- The summary updates as local tag-list controls change.
- `重置标签视图` restores the summary to the default no-search/all-tags/default-sort state.
- Existing targeted backend pytest, targeted frontend tests, and frontend build pass.

## Risks and mitigations

- **Duplicating count text confusingly.** Keep the existing count in the search card and add the summary as a concise combined state line.
- **Raw internal values leaking to users.** Use explicit label helpers for type and sort values.
- **Search whitespace mismatch.** Use the trimmed query in the summary.
- **Scope creep into chip controls.** Keep MVP39 read-only summary text; defer chip interactions.

## Self-review

- No placeholders remain.
- Scope is limited to local tag-list summary text.
- The design adds no backend schema or write behavior.
- The design preserves all metadata-only tag invariants.

## Implementation status

Implemented on `feat/mvp39-tag-view-summary` using TDD. Frontend RED was observed for the missing `标签视图摘要` element; GREEN passed after adding local label helpers, derived tag-view summary text, and summary UI below the tag-list controls. Pre-merge verification passed with backend tag/search pytest, frontend targeted Vitest, and frontend production build. An initial frontend verification command was run from the backend directory and failed with missing `package.json`; it was rerun from `/opt/WorldSim-Writer/frontend` and passed.
