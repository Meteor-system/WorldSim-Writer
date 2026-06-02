# Archived Backend World Bible Guard Design

## Goal

Prevent direct API mutations to World Bible data while a world is archived.

## Why this is the next small MVP

The frontend now consistently treats archived novels as paused/read-only: main writing actions, Narrative Control Center write actions, and World Bible manager edit controls are hidden until the user restores writing. However, frontend hiding is not an integrity boundary. A direct API caller can still attempt character, relation, or foreshadow mutations while a world is archived.

World Bible mutations increment `world_version` and write event history. Allowing those writes while archived weakens the product rule that archive is a reversible pause state. A small backend guard in the existing manual-edit governance path protects all current World Bible write endpoints with minimal duplication.

## Scope

### In scope

- Reject manual World Bible write operations when `world.status === 'archived'`.
- Apply the guard through `require_owned_world_for_update()` so existing character, relation, and foreshadow write paths share the behavior.
- Preserve read endpoints for archived worlds.
- Preserve `/worlds/{world_id}/status` so users can restore archived worlds.
- Add targeted backend regression tests for character, relation, and foreshadow write attempts.

### Out of scope

- Blocking snapshot/export/read-only timeline/search/tag reads.
- Changing archive status values or frontend behavior.
- Applying this to draft generation/approval in this slice.
- Adding database constraints.

## API behavior

For archived worlds, the following should return `409 Conflict` with detail `WORLD_ARCHIVED`:

- `POST /worlds/{world_id}/characters`
- `PUT /characters/{character_id}`
- `DELETE /characters/{character_id}`
- `POST /worlds/{world_id}/relations`
- `PUT /relations/{relation_id}`
- `DELETE /relations/{relation_id}`
- `POST /worlds/{world_id}/foreshadows`
- `PUT /foreshadows/{foreshadow_id}`
- `DELETE /foreshadows/{foreshadow_id}`

The following remain allowed:

- reading archived world overview and bible objects;
- restoring with `PATCH /worlds/{world_id}/status` to `active`.

## Implementation notes

- Update `backend/app/world/governance.py` in `require_owned_world_for_update()`:
  - keep existing not-found and owner checks;
  - after ownership passes, if `world.status == 'archived'`, raise `HTTPException(status_code=409, detail='WORLD_ARCHIVED')`.
- This function is already used by character, relation, and foreshadow create/update/delete services.
- No route-level duplication is needed.

## TDD plan

Add regression coverage:

1. `backend/tests/test_character_crud.py`
   - archive a world;
   - verify character create/update/delete return `409` + `WORLD_ARCHIVED`;
   - verify list/get still succeed.
2. `backend/tests/test_relation_crud.py`
   - archive a world;
   - verify relation create/update/delete return `409` + `WORLD_ARCHIVED`;
   - verify list/get still succeed.
3. `backend/tests/test_foreshadow_crud.py`
   - archive a world;
   - verify foreshadow create/update/delete return `409` + `WORLD_ARCHIVED`;
   - verify list/get still succeed.

Run the targeted backend tests to confirm RED, implement the guard, then rerun targeted tests to confirm GREEN.

## Acceptance criteria

- Archived World Bible write attempts are rejected at the backend.
- Read-only access remains available for archived worlds.
- Restore path remains available.
- Targeted backend tests, frontend build, relevant frontend tests/build, and `git diff --check` pass before commit.
