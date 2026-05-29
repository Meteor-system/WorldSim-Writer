# World-State Governance for Manual Edits — Design

## Summary

Manual world-state edits must follow the same governance guarantees as AI draft approval. Character, foreshadow, and relationship create/update/delete operations will become formal state mutations: they increment `world_version`, write `EventLog` records with before/after payloads, refresh current projections, and commit atomically. Manual requests may include an optional `edit_reason` for audit context.

This milestone keeps the current MVP architecture: FastAPI services mutate SQLAlchemy projection tables, `EventLog` records the audit trail, and current projection JSON fields support quick world overview rendering. It does not convert the system to full event sourcing.

## Goals

- Ensure every manual character create/update/delete increments `world_version`.
- Ensure every manual foreshadow create/update/delete increments `world_version`.
- Add post-creation character relationship CRUD with the same governance behavior.
- Add `current_relations` projection so relations participate in projection refreshes.
- Capture durable `EventLog` entries for all manual mutations with `before`, `after`, `action`, and optional `edit_reason`.
- Keep rejected chapter drafts non-mutating: no world version increment, no projection changes, no events.

## Non-goals

- Full event sourcing or replay-based projections.
- Rewriting chapter approval unless needed for shared helper compatibility.
- Preserving deleted foreshadow lifecycle rows in `foreshadow_events`; the durable deletion audit is the general `EventLog`.
- Complex relation graph visualization.

## Backend Architecture

Add a focused governance module under `backend/app/world/`, likely `governance.py`, that owns the common formal-state mutation workflow for manual edits.

The governance layer will:

1. Load and ownership-check the world, using a row lock where supported.
2. Record `version_before = world.world_version`.
3. Let the domain service perform a single validated mutation.
4. Capture object `before` and `after` snapshots with projection serializers.
5. Increment `world.world_version`.
6. Refresh all current projections:
   - `current_characters`
   - `current_foreshadows`
   - `current_relations`
7. Write object-change `EventLog` rows and a `world_version_increment` row.
8. Commit atomically and rollback on failure.

Domain services keep domain-specific validation:

- `character.service`: character ownership, character field mutation, and removing deleted character IDs from related foreshadows.
- `foreshadow.service`: status validation, lifecycle transition rules, source chapter validation, related-character validation, and `ForeshadowEvent` lifecycle rows.
- relationship service: source/target character validation, same-world ownership, no self-relations, relation field mutation.

The governance helper owns formal write semantics; services own business rules.

## Data Model

### World projections

Add `current_relations` to `World` as a JSONB list projection. Relation projection shape:

```json
{
  "id": 10,
  "source_character_id": 1,
  "target_character_id": 2,
  "relation_type": "mentor",
  "intensity": 4,
  "visibility": "private"
}
```

Update `refresh_world_projection()` to rebuild characters, foreshadows, and relations together.

### Migration

Add an Alembic migration after `0006_add_world_story_arc.py` that:

- Adds `worlds.current_relations` as JSONB, non-null, default `[]`.
- Backfills existing worlds from `character_relations` rows.
- Removes the server default afterward if that matches existing JSONB migration style.

### EventLog

No schema change is required. Manual events use:

```python
source_type = 'manual_edit'
```

Object-change events use these event types:

- `character_change`
- `foreshadow_change`
- `relation_change`

Each payload includes:

```json
{
  "commit_group_id": "manual-character-...",
  "object_type": "character|foreshadow|relation",
  "object_id": 123,
  "action": "created|updated|deleted",
  "before": null,
  "after": {},
  "edit_reason": "optional user text"
}
```

For deletes, `before` is populated and `after` is `null`.

Each governed mutation also writes a `world_version_increment` event with the same `source_type`, commit group, and version before/after.

### ForeshadowEvent alignment

`ForeshadowEvent` remains a lifecycle/timeline table:

- Create writes the initial status event.
- Status update writes the transition event.
- Delete is durably audited through `EventLog`, because `foreshadow_events.foreshadow_id` cascades on delete and would not preserve a deleted-row timeline entry.

No `ForeshadowEvent` schema change is included in this milestone.

### Request schemas

Add optional request-only `edit_reason` to:

- `CharacterCreate`
- `CharacterUpdate`
- `ForeshadowCreate`
- `ForeshadowUpdate`
- `CharacterRelationCreate`
- `CharacterRelationUpdate`

Response models do not echo `edit_reason`.

## API Contracts

### Character endpoints

Existing routes stay in place:

```http
POST /worlds/{world_id}/characters
GET /worlds/{world_id}/characters
GET /characters/{character_id}
PUT /characters/{character_id}
DELETE /characters/{character_id}?edit_reason=Duplicate%20entry
```

Create/update bodies accept optional `edit_reason`:

```json
{
  "name": "林七",
  "role_type": "supporting",
  "status": "active",
  "current_goals": ["保护青岚城"],
  "edit_reason": "Manual correction after outline review"
}
```

### Foreshadow endpoints

Existing routes stay in place:

```http
POST /worlds/{world_id}/foreshadows
GET /worlds/{world_id}/foreshadows
GET /foreshadows/{foreshadow_id}
GET /foreshadows/{foreshadow_id}/timeline
PUT /foreshadows/{foreshadow_id}
DELETE /foreshadows/{foreshadow_id}?edit_reason=No%20longer%20needed
```

Update bodies accept optional `edit_reason`:

```json
{
  "status": "advanced",
  "urgency_level": 5,
  "edit_reason": "Author manually advanced this after rereading chapter 3"
}
```

### Relationship endpoints

Add relation CRUD:

```http
POST /worlds/{world_id}/relations
GET /worlds/{world_id}/relations
GET /relations/{relation_id}
PUT /relations/{relation_id}
DELETE /relations/{relation_id}?edit_reason=Retconned
```

Create body:

```json
{
  "source_character_id": 1,
  "target_character_id": 2,
  "relation_type": "mentor",
  "intensity": 4,
  "visibility": "private",
  "edit_reason": "Clarify hidden alliance"
}
```

Update body:

```json
{
  "relation_type": "rival",
  "intensity": 5,
  "visibility": "public",
  "edit_reason": "Relationship became hostile after chapter approval"
}
```

Response body:

```json
{
  "id": 10,
  "source_character_id": 1,
  "target_character_id": 2,
  "relation_type": "mentor",
  "intensity": 4,
  "visibility": "private"
}
```

### Validation and errors

Follow existing API style:

- `401 UNAUTHORIZED`
- `403 FORBIDDEN`
- `404 NOT_FOUND`
- `404 RELATED_CHARACTER_NOT_FOUND` for relation endpoints referencing missing or foreign characters
- `400 INVALID_SELF_RELATION` when source and target match
- `400 INVALID_STATUS` and `400 INVALID_STATUS_TRANSITION` for foreshadow rules
- `422` for schema validation

Relation validation:

- source and target characters must exist in the same owned world
- source and target cannot be the same character
- `relation_type` must be non-blank
- `intensity` is constrained to `1..5`

No new event endpoint is needed. Existing world overview and event listing endpoints surface manual events.

## Frontend Changes

### Shared edit reason UX

Add optional `edit_reason` support to manual mutation forms and delete confirmations.

Suggested label: `修改原因（可选）`

Suggested placeholder: `例如：修正设定、同步章节结果、删除重复条目`

The field is optional and should not block quick edits.

### CharacterManager

Update `frontend/src/components/CharacterManager.tsx` to:

- include `edit_reason` in form state
- send it on create/update when non-blank
- collect optional delete reason before confirmed deletion
- continue calling `onChanged` after mutations so `WorldPage` reloads version/events/projections

### ForeshadowManager

Update `frontend/src/components/ForeshadowManager.tsx` to:

- include `edit_reason` in create/update modal
- collect optional delete reason before confirmed deletion
- keep quick status actions fast; status button and drag/drop may omit `edit_reason`
- continue calling `onChanged` after mutations

The foreshadow timeline UI remains unchanged; durable manual audit is visible through world events.

### RelationManager

Add `frontend/src/components/RelationManager.tsx` with:

- list existing relations
- create relation
- edit relation
- delete relation
- optional edit reason on create/update/delete
- source/target character name rendering using loaded `WorldOverview.characters`

Minimal card display:

```text
林砚 → 沈微霜
关系：mentor
强度：4
可见性：private
[编辑] [删除]
```

Form fields:

- source character
- target character
- relation type
- intensity
- visibility
- edit reason optional

### WorldPage

Add a relations tab:

```ts
overview | characters | relations | foreshadows
```

Update event descriptions for:

- `relation_change`
- manual `character_change` and `foreshadow_change` payloads using `action`
- backward compatibility with current chapter approval payloads, where `change` may contain model-proposed fields

### API client and types

Update `frontend/src/api/types.ts`:

- add `edit_reason?: string` to character and foreshadow create/update types
- add `CharacterRelation`, `CharacterRelationCreate`, and `CharacterRelationUpdate`
- type `WorldOverview.relations` as `CharacterRelation[]`
- add `current_relations: CharacterRelation[]`

Update `frontend/src/api/client.ts` with relation CRUD helpers and optional `edit_reason` query support for delete calls.

## Test Strategy

### Backend tests first

Use TDD for implementation. Add failing tests before implementation code.

#### Character governance

Extend `backend/tests/test_character_crud.py` or add a dedicated governance test file to prove:

- create increments `world_version`
- update increments `world_version`
- delete increments `world_version`
- `current_characters` is refreshed after each operation
- delete refreshes foreshadow projections when related character IDs are removed
- `EventLog` records include `source_type`, `event_type`, `action`, `before`, `after`, `edit_reason`, and correct version before/after

#### Foreshadow governance

Extend `backend/tests/test_foreshadow_crud.py` to prove:

- create/update/delete increment `world_version`
- `current_foreshadows` is refreshed
- general `EventLog` is written for create/update/delete
- `ForeshadowEvent` remains aligned for create and status updates
- deletion audit is retained in general `EventLog`

#### Relationship governance

Add relation CRUD tests proving:

- create/update/delete increment `world_version`
- `current_relations` is refreshed
- relation events contain before/after payloads and optional edit reason
- invalid source/target IDs are rejected
- cross-world source/target characters are rejected
- self-relations are rejected
- owner boundaries mirror existing character/foreshadow behavior

#### Rejected draft invariant

Keep and strengthen existing tests proving rejected drafts:

- do not increment `world_version`
- write no `EventLog`
- do not mutate characters, foreshadows, relations, or current projections

### Migration and model tests

Update state consistency/model tests to assert:

- `World.current_relations` defaults to `[]`
- world creation seeds starter relations into both `character_relations` rows and `current_relations`
- overview returns `relations` and `current_relations`

### Frontend verification

Minimum frontend verification:

```bash
npm run build
```

If lightweight, add Vitest coverage for relation form payloads and optional edit reason handling. The required milestone proof remains backend-heavy.

### Verification commands

Run targeted backend tests first:

```bash
pytest tests/test_character_crud.py tests/test_foreshadow_crud.py tests/test_state_consistency.py -v
```

Then run full backend suite:

```bash
pytest -v
```

Then run frontend build:

```bash
npm run build
```

## Open Decisions Resolved

- Relationship CRUD follows the exact same governance as character and foreshadow CRUD.
- Add `current_relations` instead of treating relations as unprojected secondary data.
- Keep `edit_reason` optional.
- Use general `EventLog` as the durable deletion audit for foreshadows.
- Keep quick foreshadow status actions fast by allowing omitted edit reasons.
