# Archived Tags Write Guard Design

## Target

Close the next archived-world read-only gap by rejecting tag catalog and tag-assignment writes while preserving tag reads.

## Background

Recent rounds made archived worlds read-only for world-bible, narrative core, and draft lifecycle writes. The tag subsystem remains a write surface: users can create, rename, merge, delete, assign, bulk-assign, and unassign tags on archived worlds. Tags are metadata and do not increment `world_version`, but they still mutate the archived world's stored organization state.

## Scope

When `world.status == 'archived'`, these endpoints must reject with `409 WORLD_ARCHIVED` after ownership is confirmed and before any tag/object mutation:

- `POST /worlds/{world_id}/tags`
- `PATCH /worlds/{world_id}/tags/{tag_id}`
- `POST /worlds/{world_id}/tags/{source_tag_id}/merge`
- `DELETE /worlds/{world_id}/tags/{tag_id}`
- `POST /worlds/{world_id}/tags/{tag_id}/objects`
- `POST /worlds/{world_id}/tags/{tag_id}/objects/bulk`
- `DELETE /worlds/{world_id}/tags/{tag_id}/objects/{object_type}/{object_id}`

These read-only endpoints remain available on archived worlds:

- `GET /worlds/{world_id}/tags`
- `GET /worlds/{world_id}/tags/{tag_id}`

## Approach

Add a small tag-service guard that calls `require_owned_world()` and rejects archived worlds before tag mutations. Keep list/detail reads unchanged. Use service-level enforcement so all current route callers get the same behavior and so tests can verify state remains unchanged after rejected write attempts.

## Error contract

Archived tag writes return:

```json
{"detail": "WORLD_ARCHIVED"}
```

with HTTP status `409 Conflict`.

## Tests

Add backend regression coverage in `backend/tests/test_tags.py`:

1. Create a world and initial tag/assignment while active.
2. Archive the world.
3. Assert create/update/merge/delete/assign/bulk-assign/unassign all return `409 WORLD_ARCHIVED`.
4. Assert list/detail reads still return `200`.
5. Assert existing tag names and assignment counts remain unchanged.

No frontend behavior is required for this backend guard round, but run the frontend build and existing WorldPage targeted tests for MVP smoke confidence.
