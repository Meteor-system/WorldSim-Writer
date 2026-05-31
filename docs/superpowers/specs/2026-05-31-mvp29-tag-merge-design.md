# MVP29 Tag Merge 1.0 Design

## Product-route analysis

MVP23 through MVP28 built the core Tools Workspace tag lifecycle: create tags, assign/unassign objects, bulk assign, filter search by tags, tag search results, display tag metadata, and edit tag names/colors. Once tags are durable organization handles, the next maintenance gap is cleanup: users can accidentally create overlapping tags and currently must delete one manually, losing or tediously recreating assignments.

`WorldSim-Writer.md` names tags, multidimensional filtering, batch editing, and资料治理 as part of the Tools Workspace direction. MVP29 keeps that direction small and safe by adding metadata-only tag merging: move all assignments from one tag into another tag, deduplicate overlaps, then delete the emptied source tag.

## Candidates and recommendation

### 1. Tag Merge 1.0 — recommended

Add a backend merge endpoint and a selected-tag UI action that lets users merge the current tag into another tag in the same world.

Why this is best:

- It completes the next natural cleanup step after tag editing.
- It prevents assignment loss when users consolidate duplicate or overlapping collections.
- It reuses existing tag/object schemas and uniqueness constraints without a migration.
- It is metadata-only: no canon mutation, no `world_version` increment, and no EventLog write.
- It has crisp TDD boundaries in both backend service behavior and frontend interaction.

### 2. Tag archive/soft delete

Hide tags without deleting assignments.

Trade-off: useful later, but requires new state semantics or columns and more filter UI.

### 3. Search tag bulk cleanup panel

Let users manage tags from search results in a richer batch panel.

Trade-off: valuable, but broader because it spans search, selection state, and bulk operations. Tag merge is a smaller primitive first.

## Recommendation

Implement **MVP29 Tag Merge 1.0**.

## Goals

- Allow owners to merge a source tag into a different target tag within the same world.
- Move source tag assignments to the target tag.
- Deduplicate objects that are already assigned to the target tag.
- Delete the source tag after a successful merge.
- Return a structured merge summary for UI feedback.
- Keep tag merging metadata-only: no `world_version` increment and no EventLog write.
- Keep world ownership boundaries identical to existing tag endpoints.
- Add frontend controls in `WorldTagsPanel` to merge the currently selected tag into another tag.

## Non-goals

- No multi-tag merge in one request.
- No undo or soft-delete archive.
- No automatic duplicate-name detection or AI cleanup suggestions.
- No search-result UI changes.
- No schema migration.
- No canon mutation, no `world_version` increment, and no EventLog write.

## Backend design

### API

Add:

```http
POST /worlds/{world_id}/tags/{source_tag_id}/merge
```

Request body:

```json
{
  "target_tag_id": 12
}
```

Response body:

```json
{
  "world_id": 7,
  "source_tag_id": 3,
  "target_tag_id": 12,
  "moved_count": 2,
  "already_assigned_count": 1,
  "deleted_source_tag": true
}
```

### Service behavior

Add `TagMergeRequest` and `TagMergeResponse` in `backend/app/tags/schemas.py` and `merge_tag()` in `backend/app/tags/service.py`.

`merge_tag()` should:

1. Require owned world using `require_owned_world()`.
2. Require both source and target tags belong to the world with `_require_tag()`.
3. Reject self-merge with `422 TAG_MERGE_TARGET_REQUIRED`.
4. Load all `ObjectTag` rows for the source tag.
5. For each source assignment:
   - If the target already has the same `(object_type, object_id)`, delete the source assignment and count it as `already_assigned`.
   - Otherwise, update the assignment's `tag_id` to the target tag and count it as `moved`.
6. Delete the source tag.
7. Commit once and return the merge summary.

Assignments keep their `world_id`, `object_type`, `object_id`, and `created_at`. Only the owning `tag_id` changes for moved rows.

### Invariants

- Merging must not increment `world.world_version`.
- Merging must not append an EventLog row.
- Merging a tag into itself must be rejected before writes.
- Merging must preserve unique target assignments.
- Other users must receive the existing ownership failure behavior for another user's world.

## Frontend design

Update `WorldTagsPanel` and API wiring.

Props:

```ts
onMergeTag: (worldId: number, sourceTagId: number, data: { target_tag_id: number }) => Promise<TagMergeResponse>;
```

State:

- `mergeTargetTagId`
- `mergeNotice`

When a tag detail loads:

- Set merge target to the first available tag whose id is not the selected tag.
- Clear merge notice.

UI:

- In the selected tag detail panel, add a compact “合并标签” form if at least one other tag exists.
- The form contains a select of other tags and a “合并当前标签” button.
- After successful merge:
  - reload tag list,
  - load the target tag detail,
  - show a short success notice,
  - keep the target tag active.
- If no other tags exist, show a muted message that another tag is needed before merge.

`WorldPage` wires `mergeWorldTag` from the API client into `WorldTagsPanel`.

## Testing strategy

### Backend TDD

Extend `backend/tests/test_tags.py` with tests for:

1. Merging moves unique assignments, deduplicates target overlaps, deletes the source tag, and returns counts.
2. Self-merge returns `422 TAG_MERGE_TARGET_REQUIRED` and preserves the source tag.
3. Merging does not increment world version or create an EventLog.

The first test should fail before implementation because the merge route does not exist.

### Frontend TDD

Extend `frontend/src/world/WorldTagsPanel.test.tsx` with tests for:

1. Merging the selected tag into another tag calls `onMergeTag`, reloads list, loads target detail, and shows the merge summary.
2. The panel explains that another tag is required when only one tag exists.

Update API client tests for the new `mergeWorldTag` helper and update `WorldPage` tests/mocks for the new prop wiring.

## Acceptance criteria

- `POST /worlds/{world_id}/tags/{source_tag_id}/merge` merges into a different target tag.
- Unique source assignments are moved to the target tag.
- Overlapping source assignments are deduplicated without violating `uq_object_tags_tag_object`.
- The source tag is deleted after a successful merge.
- Self-merge is rejected with `422 TAG_MERGE_TARGET_REQUIRED`.
- Merging is metadata-only: no world version increment and no EventLog write.
- `WorldTagsPanel` lets users merge the selected tag and switches to the target tag after success.
- Targeted backend pytest, targeted frontend tests, and frontend build pass.

## Risks and mitigations

- **Unique constraint collisions.** Check target assignments before retargeting source rows; delete overlapping source rows first.
- **Accidental assignment loss.** Only delete source assignments that already exist on the target; move all others.
- **Self-merge destructive behavior.** Reject source equal to target before touching rows.
- **Frontend stale selection.** Reload the list and load the target detail after merge.
- **Scope creep into archive/undo.** Keep MVP29 to immediate one-way merge only.

## Self-review

- No placeholders remain.
- Scope is limited to one-way metadata-only tag merge.
- The design preserves tag assignments and existing ownership boundaries.
- The design adds no new database schema and no canon-affecting writes.

## Implementation status

Implemented on `feat/mvp29-tag-merge` and verified with targeted backend pytest, targeted frontend Vitest, and frontend production build before merge.
