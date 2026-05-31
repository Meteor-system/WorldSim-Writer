# MVP41 Tag Empty State Guidance 1.0 Design

## Product-route analysis

MVP37 through MVP40 made the tag workspace increasingly powerful: tag-list type filtering, filter counts, list summaries, and selected-tag object summaries. The remaining usability gap is the empty state. When a combined tag filter/search or selected-tag object filter/search returns nothing, the UI currently shows generic copy. Users can see the controls and summary, but the empty message itself does not explain which view state caused the empty result or what to do next.

`WorldSim-Writer.md` places global search, multidimensional filtering, tags, and data governance in the Tools Workspace. MVP41 continues that route with a frontend-only improvement that makes local filtering outcomes more explainable without changing metadata, canon, APIs, or persistence.

## Candidates and recommendation

### 1. Tag Empty State Guidance 1.0 — recommended

Replace the generic tag-list and selected-tag object filtered-empty copy with compact guidance derived from the active local view state. The guidance should name search/type constraints when present and suggest using the existing reset controls or adjusting filters.

Why this is best:

- It builds directly on MVP39 and MVP40 summaries.
- It improves a common confusing state: visible count is zero after combining filters/search.
- It is small, frontend-only, and covered by focused Vitest tests.
- It avoids adding more interactions before the current controls are fully understandable.

### 2. Empty-state reset buttons

Add dedicated reset buttons inside empty states.

Trade-off: useful, but existing reset buttons are already adjacent to controls. Adding duplicate actions increases interaction surface. Better copy is the safer next step.

### 3. Per-filter active chips

Show chips for active search/type/sort and allow clearing each one.

Trade-off: more powerful, but it adds new interaction logic. MVP41 should first make the current state more legible.

## Recommendation

Implement **MVP41 Tag Empty State Guidance 1.0**.

## Goals

- Replace tag-list filtered-empty copy with guidance that includes:
  - the active search query when present,
  - the active tag object-type filter when it is not `全部标签`,
  - reset/adjustment guidance.
- Replace selected-tag object filtered-empty copy with guidance that includes:
  - the active selected-tag object search query when present,
  - the active selected-tag object-type filter when it is not `全部对象`,
  - reset/adjustment guidance.
- Keep the no-data states unchanged:
  - no tags loaded still says to create a tag,
  - selected tag with zero assigned objects still says the tag has no associated objects.
- Keep existing summaries, filters, sorting, reset behavior, tag CRUD, assignment, merge, delete confirmation, and bulk assignment behavior.
- Keep the feature frontend-only and metadata-only: no API schema changes, no backend changes, no canon mutation, no `world_version` increment, and no EventLog write.

## Non-goals

- No new reset buttons inside empty states.
- No active filter chips.
- No persisted filter preferences.
- No backend empty-state metadata endpoint.
- No schema migration.
- No canon mutation, no `world_version` increment, and no EventLog write.

## Frontend design

Update `WorldTagsPanel` only.

Add a small formatter for view constraint labels:

```ts
function constraintText(parts: string[]): string {
  return parts.length > 0 ? parts.join('，') : '当前条件';
}
```

Add a tag-list empty guidance string after `tagViewSummary`:

```ts
const tagEmptyGuidance = [
  normalizedTagSearchQuery ? `搜索「${tagSearchQuery.trim()}」` : '',
  tagObjectTypeFilter !== 'all' ? `类型：${tagTypeFilterLabel(tagObjectTypeFilter)}` : '',
].filter(Boolean);
const tagFilteredEmptyText = `没有匹配${constraintText(tagEmptyGuidance)}的标签。请重置标签视图或调整搜索与类型筛选。`;
```

Add a selected-tag object empty guidance string after `detailViewSummary`:

```ts
const detailEmptyGuidance = [
  normalizedDetailSearchQuery ? `搜索「${detailSearchQuery.trim()}」` : '',
  detailObjectTypeFilter !== 'all' ? `类型：${objectTypeFilterLabel(detailObjectTypeFilter)}` : '',
].filter(Boolean);
const detailFilteredEmptyText = `没有匹配${constraintText(detailEmptyGuidance)}的对象。请重置对象视图或调整搜索与类型筛选。`;
```

Use the new text only for filtered-empty states:

```tsx
{tags.length > 0 && visibleTags.length === 0 && !error && <p className="ink-muted">{tagFilteredEmptyText}</p>}
```

```tsx
{detail.objects.length === 0 ? (
  <p className="ink-muted">这个标签还没有关联对象。</p>
) : filteredObjects.length === 0 ? (
  <p className="ink-muted">{detailFilteredEmptyText}</p>
) : (...)}
```

## Backend design

No backend changes are required.

## Testing strategy

### Frontend TDD

Extend `frontend/src/world/WorldTagsPanel.test.tsx` with tests for:

1. Tag-list filtered-empty guidance when a tag object-type filter has no matching tags.
2. Selected-tag object filtered-empty guidance when object type and detail search leave no matching objects.
3. No-data selected-tag copy remains unchanged when the selected tag has zero assigned objects.

The first two tests should fail before implementation because the UI still renders generic empty-state copy.

### Backend checks

No backend behavior is added. Final verification should still run `backend/tests/test_tags.py` and `backend/tests/test_world_search.py` because the feature sits in the tag/search toolchain.

## Acceptance criteria

- Tag-list filtered-empty copy names active search/type constraints and points users to reset or adjust filters.
- Selected-tag object filtered-empty copy names active search/type constraints and points users to reset or adjust filters.
- No-tags and no-associated-objects copy remains unchanged.
- Existing targeted backend pytest, targeted frontend tests, and frontend build pass.

## Risks and mitigations

- **Awkward empty guidance when no explicit constraints are active.** Use `当前条件` fallback, although the filtered-empty path is normally reached via search or filter constraints.
- **Raw internal values leaking to users.** Reuse existing label helpers for tag/object types.
- **Conflating no-data with filtered-empty.** Keep `tags.length === 0` and `detail.objects.length === 0` branches unchanged.
- **Scope creep into extra interactions.** Keep MVP41 copy-only; defer chips or in-empty-state actions.

## Self-review

- No placeholders remain.
- Scope is limited to local empty-state copy.
- The design adds no backend schema or write behavior.
- The design preserves all metadata-only tag invariants.

## Implementation status

Implemented on `feat/mvp41-tag-empty-guidance` using TDD. Frontend RED was observed for missing context-aware filtered-empty guidance in the tag list and selected-tag object view; GREEN passed after adding local constraint text derivation and replacing generic filtered-empty copy while preserving no-data empty states. Pre-merge verification passed with backend tag/search pytest, frontend targeted Vitest, and frontend production build. An initial targeted frontend verification command was run from the backend directory and failed with missing `package.json`; it was rerun from `/opt/WorldSim-Writer/frontend` and passed.
