# MVP24 Tag-filtered Global Search 1.0 Design

## Product-route analysis

MVP23 added durable owner-scoped tags for characters, foreshadows, chapters, and events. The next low-risk step is to make those tags useful during retrieval: Global Search should filter results by selected tag names/slugs/ids so users can combine keyword search, object-type filters, and material organization.

`WorldSim-Writer.md` explicitly lists 全局搜索, 多维筛选, and 标签系统 in the Tools Workspace direction. MVP24 connects those already-implemented primitives without adding new canon writes, LLM calls, or schema-heavy workflow concepts.

## Candidates and recommendation

### 1. Tag-filtered Global Search 1.0 — recommended

Extend `GET /worlds/{world_id}/search` with a `tags` query parameter and add a frontend tag filter selector to `WorldSearchPanel`.

Why this is best:

- Builds directly on MVP23 instead of creating another isolated panel.
- Makes tags immediately valuable for long-form retrieval.
- Implements product-spec multi-dimensional filtering in a small, testable slice.
- Reuses existing tag persistence, ownership boundaries, and Global Search UI.
- Metadata-only: no world version changes and no EventLog writes.

### 2. Manager-level “tag this object” buttons

Add tag assignment controls inside Character, Foreshadow, Chapter History, and Timeline surfaces.

Trade-off: useful, but touches many UI managers and has more interaction risk. It should follow once tag-filtered retrieval is proven.

### 3. Bulk tag assignment 0.5

Allow applying one tag to multiple object IDs at once.

Trade-off: also mentioned in product spec, but bulk write UX and validation complexity are higher than read-side filtering.

## Recommendation

Implement **MVP24 Tag-filtered Global Search 1.0**.

## Goals

- Add `tags` filtering to backend world search.
- Accept tag filters by id, slug, or display name.
- Match objects assigned to at least one selected tag.
- Preserve existing keyword query and `object_types` behavior.
- Include matched tag metadata on search results for frontend display.
- Add frontend API support for the `tags` query parameter.
- Add a tag selector in `WorldSearchPanel` using existing `listWorldTags` data.
- Keep all behavior owner-scoped and metadata-only.

## Non-goals

- No automatic tag suggestion.
- No new tag assignment UI outside the existing `WorldTagsPanel`.
- No search pagination rewrite.
- No fuzzy tag matching beyond exact id/name/slug resolution.
- No AND/OR advanced query builder; MVP24 uses OR semantics across selected tags.
- No formal world-state mutation, no `world_version` increment, and no EventLog creation.
- No LLM prompt or generation changes.

## Backend design

### API

Extend the existing route:

```http
GET /worlds/{world_id}/search?q=<query>&object_types=character,event&tags=main,3,主线
```

Add optional query parameter:

- `tags`: comma-separated tag ids, slugs, or names.

Behavior:

- If `tags` is omitted or blank, search behavior remains unchanged.
- If `tags` is provided, returned results must be assigned to at least one resolved tag.
- Unknown tags resolve to an empty allowed-object set, producing no results.
- Object types not supported by tags are excluded when tag filtering is active.
- Existing keyword matching still applies; tags narrow the result set, they do not replace keyword search.

### Service changes

Modify `search_world()` in `backend/app/world/service.py`:

```python
def search_world(
    db: Session,
    user: User,
    world_id: int,
    query: str,
    object_types: str | None = None,
    limit: int = 20,
    tags: str | None = None,
) -> dict:
```

Add helpers:

- `_parse_tag_filters(tags: str | None) -> set[str]`
- `_load_tag_filter_assignments(db, world_id, tag_filters) -> tuple[set[tuple[str, int]], dict[tuple[str, int], list[dict]]] | None`
- `_result_allowed_by_tags(result, allowed_objects) -> bool`
- `_attach_tags(result, tag_metadata_by_object) -> dict`

Resolution rules:

- Numeric filter values match `Tag.id`.
- Non-numeric values match `Tag.slug` or `Tag.name` case-insensitively where possible.
- Only tags in the requested world are considered.

Result metadata:

Each result already has a `metadata` dictionary. When tag filtering is available, include:

```json
{
  "tags": [
    {"id": 3, "name": "主线", "slug": "主线", "color": "amber"}
  ]
}
```

This metadata may be present for matched tagged objects. It does not require a schema change because `metadata` is already flexible.

### Ownership and invariants

Search already calls `require_owned_world()`. Tag resolution must stay inside the same world id. Search remains read-only and must not commit.

## Frontend design

### API

Extend `searchWorld()` params in `frontend/src/api/client.ts`:

```ts
export function searchWorld(worldId: number, params: { q: string; object_types?: string[]; tags?: string[]; limit?: number })
```

When `params.tags` has values, append `tags=<comma-separated values>` to the query string.

### WorldSearchPanel

Extend props:

```ts
type Props = {
  worldId: number;
  onSearch: (worldId: number, params: { q: string; object_types?: string[]; tags?: string[]; limit?: number }) => Promise<WorldSearchResponse>;
  onListTags?: (worldId: number) => Promise<TagListResponse>;
};
```

Behavior:

- If `onListTags` is provided, load tags on mount.
- Render a small `标签筛选` section below object-type filters.
- Render one button per tag with name and assignment count.
- Toggling tags updates `selectedTags` using tag slugs when available, falling back to id strings.
- Submit search with `{ q, object_types, tags, limit: 20 }`.
- If tag loading fails, show a non-blocking message and keep keyword search usable.
- Display matched tag names from `result.metadata.tags` as chips on each result.

### WorldPage integration

Update `WorldPage.tsx` to pass `listWorldTags` into `WorldSearchPanel`:

```tsx
<WorldSearchPanel worldId={world.id} onSearch={searchWorld} onListTags={listWorldTags} />
```

This reuses the MVP23 tag API and does not remove `WorldTagsPanel`.

## Testing strategy

### Backend TDD

Extend `backend/tests/test_world_search.py` with tests for:

1. Search can filter by tag slug/name and returns only tagged matching objects.
2. Search can filter by tag id.
3. Unknown tag filter returns no results.
4. Tag filtering remains owner-scoped and cannot see another world’s tag/object assignments.

### Frontend TDD

- Extend `frontend/src/api/client.test.ts` for `searchWorld(..., { tags: [...] })` query-string behavior.
- Extend `frontend/src/world/WorldSearchPanel.test.tsx` to verify tag loading, toggling, and search params.
- Update `frontend/src/world/WorldPage.test.tsx` to assert `WorldSearchPanel` receives enough wiring indirectly by ensuring `listWorldTags` is called by the Global Search panel.

## Acceptance criteria

- Backend search supports `tags` filters by id, slug, or name.
- Tag filters narrow keyword/object-type search results to tagged objects.
- Search results include matched tag metadata in `metadata.tags`.
- Frontend Global Search can load and toggle tags and submit them to the search API.
- Existing Global Search behavior still works without tags.
- Tag-filtered search is read-only: no `world_version` increment and no EventLog writes.
- Targeted backend tests, frontend tests, and frontend build pass.

## Risks and mitigations

- **Tag filter ambiguity.** Resolve ids exactly and slugs/names within the current world only; duplicate display names are already prevented by slug uniqueness.
- **UI coupling to tags.** Make `onListTags` optional so standalone `WorldSearchPanel` tests and usages remain simple.
- **Overbuilding search language.** Use simple OR semantics across selected tags; defer advanced query builders.
- **Performance.** MVP scale is small; use indexed tag tables and existing result limiting. More advanced joins can come later if needed.

## Self-review

- No placeholders remain.
- Scope is read-side retrieval only.
- The design reuses MVP23 tags and MVP16 Global Search rather than adding a new domain.
- It preserves the core invariant: metadata filters do not mutate formal world state or chapter approval history.
