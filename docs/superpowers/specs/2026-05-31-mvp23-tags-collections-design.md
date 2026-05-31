# MVP23 Tags / Collections 1.0 Design

## Product-route analysis

MVP19 through MVP22 added the first story-operations stack: Open Threads Board, World Pulse, Arc Mode / Closure Plan, and a Sandbox Seed Library for high-tension world embryos. A user can now create a rich world and see what needs attention next. The next low-risk gap is material governance: as worlds accumulate characters, foreshadows, approved chapters, and events, users need a lightweight way to group and retrieve story assets beyond full-text search.

`WorldSim-Writer.md` explicitly lists tags, collections, multi-dimensional filtering, and资料治理 as part of the Narrative Control Center / Tools Workspace direction. MVP23 should implement the smallest durable slice: owner-scoped tags that can be assigned to existing world objects and queried through a compact tag board. This complements search, timeline, history, and convergence tools without changing chapter-generation or canon-approval semantics.

## Candidates and recommendation

### 1. Tags / Collections 1.0 — recommended

Add a per-world tag system with a `tags` table and `object_tags` mapping table. Users can create tags, assign/unassign them to characters, foreshadows, approved chapters, and events, and view tag usage counts plus tagged objects.

Why this is best:

- Directly implements the product spec’s资料治理 / 标签系统 direction.
- Improves long-form manageability as worlds grow.
- Reuses existing ownership boundaries and object tables.
- Low product risk: explicit user action, no LLM calls, no automatic canon mutation.
- Small enough for one MVP if scoped to tags and tagged-object retrieval, not full collections/workflows.

### 2. Arc Transition Report 0.5

Add a read-only end-of-arc report summarizing closed/open issues and next-volume pressure.

Trade-off: useful, but current MVP worlds may not yet have enough chapter volume for this to provide more value than better organization.

### 3. Audience Steering 0.5

Let authors manually record audience intent and optionally inject it into next-chapter planning.

Trade-off: product spec marks this as optional/future. It should wait until author-side governance and organization are stronger.

## Recommendation

Implement **MVP23 Tags / Collections 1.0** with only durable object tags and a lightweight frontend tag board.

## Goals

- Add persistent per-world tags.
- Add persistent tag assignments for supported world object types.
- Support these object types in MVP23: `character`, `foreshadow`, `chapter`, `event`.
- Provide authenticated owner-scoped backend APIs to create/list/delete tags and assign/unassign tags.
- Provide a tag detail endpoint that returns tagged object summaries.
- Add frontend API helpers and types.
- Add a `WorldTagsPanel` under the Narrative Control Center so users can create tags, inspect counts, and view tagged items.
- Preserve existing world-state and chapter-approval invariants.

## Non-goals

- No AI-generated automatic tags.
- No marketplace or reusable public collections.
- No batch editing.
- No tag-based permission model.
- No full folder hierarchy.
- No tags on draft-only chapter versions.
- No changes to LLM prompts.
- No direct changes to chapter approval, world_version, or EventLog semantics.
- No migration of existing free-text fields into tags.

## Backend design

### Data model

Create a new domain package `app.tags`.

Add `Tag`:

- `id`: primary key.
- `world_id`: foreign key to `worlds.id`, cascade delete, indexed.
- `name`: user-facing tag name, required.
- `slug`: normalized tag identifier, unique per world.
- `color`: optional display color string.
- `created_at`: timestamp.
- Unique constraint: `(world_id, slug)`.

Add `ObjectTag`:

- `id`: primary key.
- `world_id`: foreign key to `worlds.id`, cascade delete, indexed.
- `tag_id`: foreign key to `tags.id`, cascade delete, indexed.
- `object_type`: string enum-like value: `character`, `foreshadow`, `chapter`, `event`.
- `object_id`: integer id in the target table.
- `created_at`: timestamp.
- Unique constraint: `(tag_id, object_type, object_id)`.
- Index: `(world_id, object_type, object_id)`.

This model keeps tags world-scoped and avoids adding columns to every domain table.

### Ownership and validation

All tag endpoints require `require_user()` and call `require_owned_world()` before reading or mutating tags.

Tag creation rules:

- Trim whitespace.
- Reject blank names with `TAG_NAME_REQUIRED`.
- Normalize slugs by lowercasing, trimming, replacing whitespace/underscore runs with `-`, and dropping characters outside letters, numbers, CJK, and hyphens.
- Reject names whose slug normalizes to blank with `TAG_NAME_REQUIRED`.
- Duplicate slug in the same world returns `TAG_ALREADY_EXISTS` with HTTP 409.
- Color is optional and stored as provided after trim, or `null` if blank.

Assignment rules:

- Tag must belong to the requested world.
- `object_type` must be one of `character`, `foreshadow`, `chapter`, `event`; unsupported types return `UNSUPPORTED_TAG_OBJECT_TYPE` with HTTP 422.
- Target object must exist and belong to the same world; otherwise return `TAG_OBJECT_NOT_FOUND` with HTTP 404.
- Duplicate assignments are idempotent: assigning an existing tag/object pair returns the existing assignment rather than erroring.
- Unassigning a missing assignment is idempotent and returns 204.

Deleting a tag deletes its assignments by cascade. Deleting a world deletes tags and assignments by cascade. Target object deletion does not need cross-table cascades in MVP23; tag detail should ignore orphaned assignments if any are encountered.

### Service functions

Add service functions in `backend/app/tags/service.py`:

```python
def list_tags(db: Session, user: User, world_id: int) -> dict

def create_tag(db: Session, user: User, world_id: int, data: TagCreateRequest) -> Tag

def delete_tag(db: Session, user: User, world_id: int, tag_id: int) -> None

def assign_tag(db: Session, user: User, world_id: int, tag_id: int, data: ObjectTagAssignRequest) -> ObjectTag

def unassign_tag(db: Session, user: User, world_id: int, tag_id: int, object_type: str, object_id: int) -> None

def get_tag_detail(db: Session, user: User, world_id: int, tag_id: int) -> dict
```

`list_tags()` returns counts by object type so the frontend can render a compact board without N+1 detail calls.

`get_tag_detail()` returns a list of tagged object summaries:

- `object_type`
- `object_id`
- `title`
- `subtitle`
- `snippet`
- `metadata`

Summary sources:

- Character: `name`, role/status, current goals.
- Foreshadow: `title`, status/urgency, description.
- Chapter: `title`, status/world version, chapter goal or approved excerpt.
- Event: `event_type`, source/world versions, payload snippet.

### API routes

Add `backend/app/tags/router.py` and include it from `app.api.router`.

Routes:

```http
GET    /worlds/{world_id}/tags
POST   /worlds/{world_id}/tags
GET    /worlds/{world_id}/tags/{tag_id}
DELETE /worlds/{world_id}/tags/{tag_id}
POST   /worlds/{world_id}/tags/{tag_id}/objects
DELETE /worlds/{world_id}/tags/{tag_id}/objects/{object_type}/{object_id}
```

All routes are authenticated and owner-scoped.

### Response shapes

```python
class TagCreateRequest(BaseModel):
    name: str
    color: str | None = None

class ObjectTagAssignRequest(BaseModel):
    object_type: str
    object_id: int

class TagResponse(BaseModel):
    id: int
    world_id: int
    name: str
    slug: str
    color: str | None
    created_at: datetime

class TagSummaryResponse(TagResponse):
    assignment_count: int
    object_type_counts: dict[str, int]

class TaggedObjectSummary(BaseModel):
    object_type: str
    object_id: int
    title: str
    subtitle: str
    snippet: str
    metadata: dict[str, Any]

class ObjectTagResponse(BaseModel):
    id: int
    world_id: int
    tag_id: int
    object_type: str
    object_id: int
    created_at: datetime

class TagListResponse(BaseModel):
    world_id: int
    tags: list[TagSummaryResponse]

class TagDetailResponse(BaseModel):
    tag: TagSummaryResponse
    objects: list[TaggedObjectSummary]
```

## Frontend design

### API

Add TypeScript types matching backend responses:

- `TagResponse`
- `TagSummaryResponse`
- `TaggedObjectSummary`
- `ObjectTagResponse`
- `TagListResponse`
- `TagDetailResponse`

Add helpers:

```ts
listWorldTags(worldId: number)
createWorldTag(worldId: number, data: { name: string; color?: string })
getWorldTag(worldId: number, tagId: number)
deleteWorldTag(worldId: number, tagId: number)
assignWorldTag(worldId: number, tagId: number, data: { object_type: string; object_id: number })
unassignWorldTag(worldId: number, tagId: number, objectType: string, objectId: number)
```

### WorldTagsPanel

Create `frontend/src/world/WorldTagsPanel.tsx`.

Props:

```ts
type Props = {
  worldId: number;
  onListTags: (worldId: number) => Promise<TagListResponse>;
  onCreateTag: (worldId: number, data: { name: string; color?: string }) => Promise<TagResponse>;
  onLoadTag: (worldId: number, tagId: number) => Promise<TagDetailResponse>;
  onAssignTag: (worldId: number, tagId: number, data: { object_type: string; object_id: number }) => Promise<ObjectTagResponse>;
  onUnassignTag: (worldId: number, tagId: number, objectType: string, objectId: number) => Promise<unknown>;
  onDeleteTag: (worldId: number, tagId: number) => Promise<unknown>;
};
```

Render:

- heading `Tags / Collections`;
- short guidance explaining tags are organizational metadata and do not change canon;
- create form with tag name and optional color;
- tag chips/cards showing assignment count and object-type counts;
- selecting a tag loads and displays tagged objects;
- assignment form for MVP23 with object type dropdown and object id number input;
- per-object `移除标签` action;
- tag delete action;
- loading, error, and empty states.

This intentionally uses object IDs for assignment in MVP23 to avoid coupling the first tag implementation to every manager UI. Later MVPs can add “tag this” buttons inside CharacterManager, ForeshadowManager, Chapter History, and Timeline.

### WorldPage integration

Add `WorldTagsPanel` to the Narrative Control Center area after Global Search and before Timeline/Archive. Pass API helpers directly from `WorldPage`.

This keeps tags accessible as a Tools Workspace surface while avoiding changes to core overview cards.

## Testing strategy

### Backend TDD

Create `backend/tests/test_tags.py` covering:

1. Tag creation/listing returns normalized slug and zero counts.
2. Duplicate tag names in the same world return `409 TAG_ALREADY_EXISTS`.
3. Assigning a tag to character, foreshadow, approved chapter, and event updates counts and detail summaries.
4. Assigning the same object twice is idempotent.
5. Assigning an object from another owner/world returns not found or forbidden via owner boundary.
6. Unsupported object type returns `422 UNSUPPORTED_TAG_OBJECT_TYPE`.
7. Deleting a tag removes it from the list.
8. Tag endpoints require login.

### Frontend TDD

- Add API helper tests to `frontend/src/api/client.test.ts`.
- Add `WorldTagsPanel.test.tsx` for create/list/select/assign/unassign/delete/error/empty states.
- Update `WorldPage.test.tsx` to mock tag helpers and assert the panel renders with the current world id.

## Acceptance criteria

- Users can create owner-scoped tags for a world.
- Users can assign tags to characters, foreshadows, approved chapters, and events by object id.
- Users can inspect tag counts and tagged object summaries.
- Users can unassign objects and delete tags.
- Tags are organizational metadata and do not increment `world_version` or write EventLog entries.
- Backend targeted tests, frontend targeted tests, and frontend build pass.

## Risks and mitigations

- **Schema scope creep.** Keep MVP23 to tags and object assignments; defer folders, bulk actions, manager-level buttons, and AI tagging.
- **Cross-table target validation complexity.** Support only four existing object types and centralize validation in one helper.
- **Orphaned assignments after target deletion.** Detail view filters missing targets; deeper cleanup can come later.
- **UI discoverability.** Put the first tag board inside Narrative Control Center and clearly state it is metadata, not canon.
- **World version confusion.** Do not increment `world_version` for tag metadata changes; tests should assert this.

## Self-review

- No placeholders remain.
- Scope is focused on durable tags and tagged-object retrieval, not full collection workflows.
- The design follows existing owner-scoped backend patterns.
- It preserves the core invariant: tags do not mutate formal story state and do not affect chapter approval or EventLog history.
