# MVP27 Search Tag Metadata 1.0 Design

## Product-route analysis

MVP23 created durable tags and object assignments. MVP24 let users filter Global Search by tags. MVP25 added bulk tag assignment. MVP26 let users apply an existing tag directly to visible search results. The remaining friction in that vertical workflow is visibility: after objects are tagged, ordinary Global Search results do not currently show tag metadata unless the search itself is tag-filtered.

`WorldSim-Writer.md` groups Global Search, multidimensional filtering, tags, and batch editing in the same Tools Workspace direction. MVP27 closes a small but important loop: search results should carry their existing tags by default, so users can see how objects are already organized while searching.

## Candidates and recommendation

### 1. Search Tag Metadata 1.0 — recommended

Attach existing tag metadata to Global Search results even when the request does not include a `tags` filter. The existing frontend result-chip rendering can then display tags without additional UI work.

Why this is best:

- Directly improves the MVP23 → MVP26 tag/search workflow.
- Low risk: read-only backend search enrichment, no schema change, no canon mutation.
- Complements MVP26 search-result tagging: users can immediately see collection state in later searches.
- Keeps the existing tag filter behavior intact.
- Small enough for strict TDD.

### 2. Per-result tag action buttons

Add an individual “tag this result” control on each search result.

Trade-off: useful, but broader UI complexity after MVP26’s visible-result bulk action.

### 3. Tag count badges in WorldTagsPanel

Improve collection visibility by adding richer count details to the tag panel.

Trade-off: valuable but less connected to search workflow than showing tags in search results.

## Recommendation

Implement **MVP27 Search Tag Metadata 1.0**.

## Goals

- Enrich every Global Search result with `metadata.tags` when that object has tag assignments.
- Preserve tag filtering by ID, slug, or name.
- Keep unknown tag filters returning no results.
- Keep search read-only and owner-scoped.
- Keep tag metadata limited to the current world.
- Reuse existing frontend tag chip rendering; only tests may need updates on the frontend.

## Non-goals

- No new tag assignment route.
- No new frontend production UI beyond existing tag chip rendering.
- No pagination or search index rewrite.
- No LLM prompt changes.
- No canon mutation, `world_version` increment, or EventLog write.

## Backend design

### Current behavior

`search_world()` loads tag assignment metadata only when a `tags` query parameter is supplied. `_append_search_result()` only attaches `metadata.tags` in tag-filtered searches.

### New behavior

Add a helper that loads all tag assignments for the current world:

```python
def _load_object_tag_metadata(db: Session, world_id: int) -> dict[tuple[str, int], list[dict]]:
```

Implementation outline:

1. Load all `ObjectTag` rows for the current world ordered by assignment ID.
2. Load the referenced `Tag` rows for the same world.
3. Build `metadata_by_object[(object_type, object_id)] = [tag metadata...]`.
4. Ignore any orphaned assignment whose tag is not found in the world.

Update `_append_search_result()` so it receives both:

- optional tag filter assignment data, for narrowing results,
- all object tag metadata, for enrichment.

Filtering still works first:

- If a tag filter exists and the object is not in the allowed set, skip the result.
- If the object is allowed, attach all known tags for that object.

For no tag filter:

- Attach `metadata.tags` when a result object has tags.
- Do not attach `tags` for objects without assignments.

## Frontend design

No production frontend change is required. `WorldSearchPanel` already renders tag chips from `result.metadata.tags` when present.

Add or adjust tests if needed to verify that unfiltered search responses containing `metadata.tags` still display tag chips.

## Testing strategy

### Backend TDD

Extend `backend/tests/test_world_search.py` with tests for:

1. Unfiltered search returns existing tag metadata on assigned results.
2. Tag metadata remains scoped to the current world.
3. Tag-filtered search still returns only matching objects and includes tag metadata.

The first test should fail before implementation because unfiltered search results currently omit `metadata.tags`.

### Frontend verification

Run existing `WorldSearchPanel` targeted tests to confirm the existing tag chip rendering still works.

## Acceptance criteria

- A normal `GET /worlds/{world_id}/search?q=...` response includes `metadata.tags` for matching objects with tags.
- Untagged matching results continue to work and do not need a `tags` key.
- Tag-filtered search still narrows results to matching tagged objects.
- Cross-world tag assignments never appear in another world’s results.
- Search remains read-only: no `world_version` increment and no EventLog write.
- Targeted backend tests, frontend tests, and frontend build pass.

## Risks and mitigations

- **Extra queries on search.** Load tag metadata with simple world-scoped queries; current MVP data size is small.
- **Metadata leakage across worlds.** Filter both `ObjectTag.world_id` and `Tag.world_id` by current world.
- **Changing filtered metadata semantics.** Existing tests assert the same tag metadata shape; keep the shape identical.
- **Frontend coupling.** Reuse existing `metadata.tags` rendering instead of adding new UI.

## Self-review

- No placeholders remain.
- Scope is limited to read-only search metadata enrichment.
- The design preserves existing tag filters and metadata-only invariants.
- No backend write paths are added.
