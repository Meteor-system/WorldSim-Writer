# MVP28 Tag Editing 1.0 Design

## Product-route analysis

MVP23 through MVP27 built a coherent Tools Workspace path around tags and search: users can create tags, assign them to objects, filter search by tags, bulk assign tags, tag visible search results, and see existing tags in ordinary search results. The next low-risk gap is maintenance. Once tags become durable collection handles, users need to correct a tag name or visual color without deleting and recreating assignments.

`WorldSim-Writer.md` names tags, multidimensional filtering, and batch editing as part of the资料工具台 / Tools Workspace direction. MVP28 keeps that vertical slice small by adding metadata-only tag editing: rename an existing tag and change or clear its color while preserving object assignments.

## Candidates and recommendation

### 1. Tag Editing 1.0 — recommended

Add a `PATCH /worlds/{world_id}/tags/{tag_id}` endpoint and frontend controls in `WorldTagsPanel` to edit the selected tag’s name and color.

Why this is best:

- It completes the basic tag lifecycle after create, assign, list, detail, unassign, and delete.
- It preserves existing assignments, so users do not lose collections when correcting names.
- It is metadata-only and low risk: no schema migration, canon mutation, world version increment, or event log write.
- It fits strict TDD with narrow backend and frontend tests.

### 2. Tag merge

Let users merge one tag into another and move all assignments.

Trade-off: valuable for cleanup, but broader because it needs conflict handling, assignment dedupe semantics, and a more dangerous destructive UI.

### 3. Tag count badges in search filters

Improve search filter display with richer object-type counts per tag.

Trade-off: useful but less fundamental than being able to correct an existing tag itself.

## Recommendation

Implement **MVP28 Tag Editing 1.0**.

## Goals

- Allow owners to update an existing tag’s name.
- Recompute the tag slug from the updated name.
- Allow owners to set a trimmed color value or clear color with a blank value.
- Preserve all existing object assignments for the edited tag.
- Reject duplicate tag names within the same world using the existing slug uniqueness rule.
- Keep tag editing metadata-only: no `world_version` increment and no EventLog write.
- Keep world ownership boundaries identical to existing tag endpoints.
- Add frontend controls to edit the currently selected tag from `WorldTagsPanel`.

## Non-goals

- No tag merge or bulk rename.
- No color palette component; MVP accepts a plain string like existing create-tag UI.
- No new database columns or migrations.
- No tag assignment changes during editing.
- No canon mutation, no `world_version` increment, and no EventLog write.
- No search-result UI changes beyond benefitting from updated tag metadata returned by existing endpoints.

## Backend design

### API

Add:

```http
PATCH /worlds/{world_id}/tags/{tag_id}
```

Request body:

```json
{
  "name": "主线压力",
  "color": "amber"
}
```

Both fields are optional, but at least one should be accepted by the service if present. The same payload model can support partial updates:

- `name`: optional non-blank string. When present, trim it and recompute `slug` via existing `_slugify()`.
- `color`: optional nullable string. When present, trim it; blank becomes `null`.

Response: existing `TagResponse`.

### Service behavior

Add `TagUpdateRequest` in `backend/app/tags/schemas.py` and `update_tag()` in `backend/app/tags/service.py`.

`update_tag()` should:

1. Require owned world using `require_owned_world()`.
2. Require the tag belongs to the world with `_require_tag()`.
3. If `name` was provided, trim it, recompute slug, and update both `name` and `slug`.
4. If `color` was provided, normalize it using the same trim/blank-to-null behavior as creation.
5. Commit and refresh the tag.
6. Convert slug uniqueness conflicts into `409 TAG_ALREADY_EXISTS`, matching create behavior.

Assignments remain untouched because they reference `tag_id`.

### Invariants

- Editing a tag must not increment `world.world_version`.
- Editing a tag must not append an EventLog row.
- Other users must receive the existing ownership failure behavior for another user’s world.
- Duplicate names in the same world must be rejected.

## Frontend design

Update `WorldTagsPanel` only.

Props:

```ts
onUpdateTag: (worldId: number, tagId: number, data: { name?: string; color?: string | null }) => Promise<TagResponse>;
```

State:

- `editTagName`
- `editTagColor`
- `editNotice`

When a tag detail loads, initialize the edit fields from `detail.tag.name` and `detail.tag.color ?? ''`.

UI:

- In the selected tag detail panel, add a compact “编辑标签” form.
- The name field is required on submit after trimming.
- The color field is optional; blank submits `color: null` so the backend clears it.
- After successful update:
  - reload tag list,
  - reload selected tag detail,
  - show a short success notice,
  - keep selected tag active.

`WorldPage` wires `updateWorldTag` from the API client into `WorldTagsPanel`.

## Testing strategy

### Backend TDD

Extend `backend/tests/test_tags.py` with tests for:

1. Updating tag name and color preserves assignments and updates slug.
2. Updating tag to a duplicate name in the same world returns `409 TAG_ALREADY_EXISTS`.
3. Updating a tag does not increment world version or create an EventLog.

The first test should fail before implementation because the `PATCH` route does not exist.

### Frontend TDD

Extend `frontend/src/world/WorldTagsPanel.test.tsx` with tests for:

1. Editing the selected tag submits trimmed name and cleared color, then reloads list and detail.
2. Blank edit tag name is rejected before calling `onUpdateTag`.

Update API client tests if a nearby client test pattern exists; otherwise the targeted component test plus TypeScript build verifies frontend wiring.

## Acceptance criteria

- `PATCH /worlds/{world_id}/tags/{tag_id}` updates tag name, slug, and color.
- Existing object assignments remain attached after editing.
- Duplicate tag names in the same world return `409 TAG_ALREADY_EXISTS`.
- Editing a tag is metadata-only: no world version increment and no EventLog write.
- `WorldTagsPanel` lets users edit the selected tag and refreshes visible metadata after success.
- Frontend `WorldPage` passes the real API update function into the panel.
- Targeted backend pytest, targeted frontend tests, and frontend build pass.

## Risks and mitigations

- **Accidental destructive cleanup.** Do not touch `ObjectTag` rows in `update_tag()`.
- **Duplicate slug conflicts.** Reuse `_slugify()` and convert `IntegrityError` to the existing `TAG_ALREADY_EXISTS` error.
- **Blank color ambiguity.** Make blank color explicitly clear to `null`; preserve existing color only if `color` is omitted.
- **Frontend stale selected tag.** Reload both list and selected detail after a successful update.
- **Scope creep into merge/palette UX.** Keep MVP28 to plain edit fields only.

## Self-review

- No placeholders remain.
- Scope is limited to metadata-only tag editing.
- The design preserves tag assignments and existing ownership boundaries.
- The design adds no new database schema and no canon-affecting writes.
