# MVP25 Bulk Tag Assignment 0.5 Design

## Product-route analysis

MVP23 added durable tags and single-object assignments. MVP24 connected tags to Global Search. The next small high-value step is bulk tag assignment: users should be able to paste multiple object IDs and apply one tag to them in one operation.

`WorldSim-Writer.md` explicitly lists 批量编辑能力 under 资料治理与辅助工具, including batch tagging. MVP25 implements the smallest safe version of that idea by reusing the existing tag domain, supported object types, and metadata-only invariants.

## Candidates and recommendation

### 1. Bulk Tag Assignment 0.5 — recommended

Add a bulk assignment endpoint for a single tag and one object type, accepting multiple object IDs. Add a compact bulk input in `WorldTagsPanel`.

Why this is best:

- Directly follows MVP23/MVP24 and makes tags practical for larger worlds.
- Implements a product-spec gap: 批量编辑能力.
- Low risk: no schema migration, no LLM calls, no formal canon mutation.
- Reuses existing owner boundary and target validation.
- Small enough for one TDD cycle.

### 2. Manager-level tag buttons

Add “tag this” controls inside Character, Foreshadow, Chapter History, and Timeline views.

Trade-off: useful but touches many surfaces and increases UI coupling.

### 3. Repair tools 0.5

Add orphan tag cleanup or invalid foreshadow repair tools.

Trade-off: valuable later, but current user-facing benefit is lower than bulk tagging.

## Recommendation

Implement **MVP25 Bulk Tag Assignment 0.5**.

## Goals

- Add backend bulk assignment for one tag, one object type, many object IDs.
- Keep duplicate assignments idempotent.
- Validate all target object IDs belong to the same world before writing new assignments.
- Return a compact summary of assigned, already-existing, and requested IDs.
- Add frontend API helper and types.
- Add bulk object ID input to `WorldTagsPanel`.
- Preserve tags as metadata-only: no `world_version` increments and no EventLog writes.

## Non-goals

- No bulk unassign.
- No cross-object-type bulk request in one call.
- No automatic lookup/search picker for object IDs.
- No manager-level tag controls.
- No batch creation of tags.
- No formal world-state mutation, no chapter approval changes, no EventLog writes.

## Backend design

### API

Add a new route:

```http
POST /worlds/{world_id}/tags/{tag_id}/objects/bulk
```

Request:

```json
{
  "object_type": "character",
  "object_ids": [1, 2, 3]
}
```

Response:

```json
{
  "world_id": 7,
  "tag_id": 3,
  "object_type": "character",
  "requested_count": 3,
  "assigned_count": 2,
  "already_assigned_count": 1,
  "assigned_object_ids": [2, 3],
  "already_assigned_object_ids": [1]
}
```

### Validation rules

- Route requires login.
- World must be owned by current user via `require_owned_world()`.
- Tag must belong to the requested world.
- `object_type` must be one of `character`, `foreshadow`, `chapter`, `event`.
- `object_ids` must contain 1 to 100 positive integer IDs.
- Deduplicate repeated IDs while preserving first-seen order.
- All target IDs must exist in the same world before writing any new assignment.
- If any target is invalid, return `404 TAG_OBJECT_NOT_FOUND` and do not create partial assignments.
- Existing assignments count as already assigned and do not error.

### Service design

Add schemas:

```python
class ObjectTagBulkAssignRequest(BaseModel):
    object_type: str
    object_ids: list[int]

class ObjectTagBulkAssignResponse(BaseModel):
    world_id: int
    tag_id: int
    object_type: str
    requested_count: int
    assigned_count: int
    already_assigned_count: int
    assigned_object_ids: list[int]
    already_assigned_object_ids: list[int]
```

Add service function:

```python
def bulk_assign_tag(db: Session, user: User, world_id: int, tag_id: int, data: ObjectTagBulkAssignRequest) -> dict:
```

Implementation outline:

1. Resolve owned world.
2. Resolve tag within world.
3. Validate object type.
4. Deduplicate IDs.
5. Validate every target via existing `_target_object()` before adding assignments.
6. Load existing `ObjectTag` rows for this tag/type/id set.
7. Create missing assignments.
8. Commit once.
9. Return counts and ID lists.

This keeps the write atomic for the batch.

## Frontend design

### API

Add type:

```ts
export type ObjectTagBulkAssignResponse = {
  world_id: number;
  tag_id: number;
  object_type: string;
  requested_count: number;
  assigned_count: number;
  already_assigned_count: number;
  assigned_object_ids: number[];
  already_assigned_object_ids: number[];
};
```

Add helper:

```ts
bulkAssignWorldTag(worldId: number, tagId: number, data: { object_type: string; object_ids: number[] })
```

### WorldTagsPanel

Extend props:

```ts
onBulkAssignTag?: (worldId: number, tagId: number, data: { object_type: string; object_ids: number[] }) => Promise<ObjectTagBulkAssignResponse>;
```

UI behavior:

- Show a `批量对象 ID` textarea when a tag is selected and `onBulkAssignTag` is provided.
- Parse comma, whitespace, newline, and Chinese comma separators.
- Reject blank/invalid/non-positive IDs with `请输入有效对象 ID 列表`.
- Submit one object type plus parsed IDs to bulk helper.
- Show a success message like `批量打标完成：新增 2，已存在 1。`
- Reload tag list and selected detail after success.

`onBulkAssignTag` is optional so existing tests and simple usages stay compatible.

### WorldPage integration

Import and pass `bulkAssignWorldTag` to `WorldTagsPanel`.

## Testing strategy

### Backend TDD

Extend `backend/tests/test_tags.py` with tests for:

1. Bulk assigning repeated object IDs deduplicates, creates missing assignments, and reports already-existing IDs.
2. Bulk assignment validates all targets before writing partial assignments.
3. Bulk assignment does not increment world version or create EventLog entries.
4. Bulk endpoint requires login.

### Frontend TDD

- Extend `frontend/src/api/client.test.ts` for the bulk endpoint helper.
- Extend `frontend/src/world/WorldTagsPanel.test.tsx` for parsing multiple IDs, calling `onBulkAssignTag`, displaying summary, and rejecting invalid lists.
- Update `frontend/src/world/WorldPage.test.tsx` mocks/imports so `WorldTagsPanel` receives the bulk helper.

## Acceptance criteria

- Users can bulk assign one tag to multiple objects of the same supported type.
- Duplicate IDs in the request are deduplicated.
- Existing assignments are idempotent and reported separately.
- Invalid targets fail the whole batch without partial writes.
- Frontend panel supports pasted ID lists and displays a completion summary.
- Existing single-object tag assignment still works.
- Tags remain metadata-only; no `world_version` or EventLog changes.
- Targeted backend tests, frontend tests, and frontend build pass.

## Risks and mitigations

- **Partial writes.** Validate all targets before adding any missing assignments and commit once.
- **Large payloads.** Limit `object_ids` to 100.
- **UI clutter.** Keep bulk input inside selected tag detail and only show it when the bulk prop is wired.
- **Ambiguous separators.** Parse common separators in the frontend and send clean integer arrays.

## Self-review

- No placeholders remain.
- Scope is limited to metadata-only bulk tag assignment.
- The design reuses existing MVP23 tag validation and MVP24 retrieval improvements.
- It preserves the core invariant: tag metadata changes do not mutate canon or chapter approval history.
