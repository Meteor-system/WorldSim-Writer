# MVP26 Search Result Tagging 0.5 Design

## Product-route analysis

MVP23 added durable tags and single-object assignments. MVP24 connected tags to Global Search as filters. MVP25 added bulk tag assignment once the user already knows object IDs. The next low-risk, high-value vertical slice is to connect Global Search results directly to bulk tagging so users can search a theme, inspect the visible matches, and apply a collection tag without manually copying IDs into the tag panel.

`WorldSim-Writer.md` lists Global Search, multidimensional filtering, tags, and batch editing under the same Tools Workspace direction. MVP26 implements the smallest frontend bridge across those already-built capabilities while preserving the metadata-only tag invariant.

## Candidates and recommendation

### 1. Search Result Tagging 0.5 — recommended

Add an optional bulk tagging action to `WorldSearchPanel`: after a search returns object results, the user can pick an existing tag and apply it to all visible results that have an object ID. The panel groups results by object type and calls the existing bulk tag endpoint once per object type.

Why this is best:

- Extends the MVP23 → MVP24 → MVP25 tag/search/bulk chain as a true workflow.
- High user value: search becomes an object collection builder, not just a lookup tool.
- Low risk: no schema migration, no new backend route, no LLM calls, no canon mutation.
- Reuses existing owner-scoped backend validation and idempotency from MVP25.
- Small enough for strict TDD in one development branch.

### 2. Search results always include tag metadata

Load and display all tags for search results even when no tag filter is active.

Trade-off: useful, but it touches backend search internals and does not close the workflow as much as direct result tagging.

### 3. Manager-level tag buttons

Add tag assignment controls to Character, Foreshadow, Chapter History, and Timeline panels.

Trade-off: useful but broader, touches many surfaces, and risks UI inconsistency.

## Recommendation

Implement **MVP26 Search Result Tagging 0.5**.

## Goals

- Add optional search-result bulk tagging to `WorldSearchPanel`.
- Reuse the tag list already loaded for tag filtering.
- Let users choose an existing tag as the target assignment tag.
- Apply the chosen tag to all visible search results with `object_id` values.
- Group selected visible results by `object_type` and call the existing bulk assignment helper for each group.
- Sum backend results into one compact success notice.
- Wire `bulkAssignWorldTag` into `WorldSearchPanel` from `WorldPage`.
- Keep behavior metadata-only: no world version increment, no EventLog write, no canon mutation.

## Non-goals

- No backend route changes.
- No new database schema or migration.
- No inline tag creation from search.
- No per-result checkbox selection in this version.
- No bulk unassign from search.
- No cross-world or cross-user tag operations.
- No automatic AI tag suggestions.

## Frontend design

### API usage

No new API helper is required. Reuse the existing MVP25 helper:

```ts
bulkAssignWorldTag(worldId: number, tagId: number, data: { object_type: string; object_ids: number[] })
```

### WorldSearchPanel props

Extend `WorldSearchPanel` with an optional prop:

```ts
onBulkAssignTag?: (worldId: number, tagId: number, data: { object_type: string; object_ids: number[] }) => Promise<ObjectTagBulkAssignResponse>;
```

The prop is optional so standalone tests and callers that only need search remain compatible.

### UI behavior

When all of these are true:

- `onBulkAssignTag` is provided,
- tag list has loaded at least one tag,
- a search response exists,
- visible results include at least one result with `object_id`,

show a compact panel labelled `搜索结果批量打标` with:

- a target tag `<select>` labelled `目标标签`,
- a button labelled `给搜索结果打标签`.

Submitting:

1. Require a selected target tag. If missing, show `请选择目标标签`.
2. Collect visible search results with non-null `object_id`.
3. Group IDs by `object_type`.
4. Deduplicate IDs within each object type while preserving visible order.
5. Call `onBulkAssignTag(worldId, targetTagId, { object_type, object_ids })` once per group.
6. Sum `assigned_count` and `already_assigned_count` from all responses.
7. Show `已为搜索结果打标：新增 X，已存在 Y。`
8. Reload tag filters through `onListTags` when available so assignment counts update.

If there are no taggable results, the panel stays hidden.

### WorldPage integration

Pass `bulkAssignWorldTag` into `WorldSearchPanel`:

```tsx
<WorldSearchPanel
  worldId={world.id}
  onSearch={searchWorld}
  onListTags={listWorldTags}
  onBulkAssignTag={bulkAssignWorldTag}
/>
```

## Backend design

No backend production changes are required. MVP25 already provides the owner-scoped, idempotent, metadata-only bulk endpoint. MVP26 relies on that contract and verifies it with existing backend tag/search targeted tests.

## Testing strategy

### Frontend TDD

Extend `frontend/src/world/WorldSearchPanel.test.tsx` with tests for:

1. After searching, selecting a target tag and clicking `给搜索结果打标签` groups visible results by type and calls `onBulkAssignTag` once per object type.
2. The panel displays the summed success notice.
3. The panel reloads tags after a successful bulk tagging operation.
4. The panel rejects submit without a target tag when no target tag is selected.

Extend `frontend/src/world/WorldPage.test.tsx` so the integration test verifies the search panel receives bulk tagging wiring by rendering the `搜索结果批量打标` surface after a search response.

### Backend verification

Run existing backend tag/search targeted tests to confirm the reused endpoint and search behavior remain green:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_tags.py tests/test_world_search.py -q
```

## Acceptance criteria

- Users can turn visible Global Search results into tag assignments without copying IDs manually.
- Mixed object-type search results are grouped into separate bulk API calls.
- Duplicate visible results of the same type/object are sent once per type group.
- Results without `object_id` are ignored rather than causing a bad request.
- Success notice summarizes new and already-existing assignments.
- Tag counts refresh after assignment.
- Existing search, tag filtering, and standalone panel behavior remain compatible.
- Targeted frontend tests, backend tests, and frontend build pass.

## Risks and mitigations

- **Accidental broad tagging.** Limit MVP26 to visible current results only and label the action as search-result tagging.
- **Mixed object types.** Group by object type and reuse the existing bulk endpoint per group.
- **Null object IDs.** Skip untaggable results.
- **UI clutter.** Show the panel only after search results exist and bulk tagging is wired.
- **Backend behavior drift.** Re-run tag/search backend tests even though MVP26 is frontend-focused.

## Self-review

- No placeholders remain.
- Scope is limited to connecting already-built search, tags, and bulk assignment capabilities.
- No backend schema or new route is required.
- The design preserves metadata-only tag behavior and the core invariant that only user-approved chapters mutate formal world state.
