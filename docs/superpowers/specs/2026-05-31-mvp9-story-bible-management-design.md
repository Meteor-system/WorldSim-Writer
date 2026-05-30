# MVP #9 Story Bible Management 1.0 Design

## Goal

Constrain and harden the existing World Bible management surface so writers can directly maintain formal Story Bible state for existing characters and character relations from WorldPage, while preserving the core writing-loop invariant: manual Story Bible edits update formal world projection, but never rewrite existing chapter drafts.

## Current state

WorldSim-Writer already has most of the underlying Story Bible management infrastructure:

- Backend character endpoints under `app.character.router`:
  - `POST /worlds/{world_id}/characters`
  - `GET /worlds/{world_id}/characters`
  - `GET /characters/{character_id}`
  - `PUT /characters/{character_id}`
  - `DELETE /characters/{character_id}`
- Backend relation endpoints under `app.character.relation_router`:
  - `POST /worlds/{world_id}/relations`
  - `GET /worlds/{world_id}/relations`
  - `GET /relations/{relation_id}`
  - `PUT /relations/{relation_id}`
  - `DELETE /relations/{relation_id}`
- Manual world governance in `app.world.governance.commit_manual_world_change()`:
  - increments `World.world_version`,
  - refreshes `current_characters`, `current_relations`, and `current_foreshadows`,
  - writes an object change event,
  - writes a `world_version_increment` event,
  - commits the formal world-state change.
- Frontend WorldPage tabs already expose `CharacterManager`, `RelationManager`, and `ForeshadowManager`.

MVP #9 is therefore not a greenfield implementation. It is a scope-constraining and acceptance-hardening pass over the existing management surface.

## Product decision

Use **strict MVP scope** for the user-facing UI:

- Existing characters can be edited.
- Characters cannot be created or deleted from the MVP #9 UI.
- Relations can be created and edited.
- Relations cannot be deleted from the MVP #9 UI.
- Existing backend create/delete endpoints remain in place for backward compatibility and historical tests, but they are not part of MVP #9 acceptance.

This keeps the MVP aligned with the requested non-goals while avoiding disruptive API removal.

## Invariants

1. A Story Bible edit is a formal world-state write.
2. Every successful character update or relation create/update increments `world_version` exactly once.
3. Every successful formal write records manual `EventLog` history.
4. Projection tables and cached projection JSON stay consistent after each write.
5. Existing reviewing drafts are not rewritten, re-versioned, approved, or rejected by Story Bible edits.
6. Existing approval readiness and approval preview continue to surface world-version mismatch when a draft was created against an older `source_world_version`.
7. Ownership boundaries apply to all read and write operations.
8. Cross-world relation endpoints reject character IDs that do not belong to the target relation world.

## Backend design

### Character update

MVP #9 uses the existing endpoint:

```http
PUT /characters/{character_id}
```

The backend schema may keep its broader `CharacterUpdate` shape, but MVP #9 UI only sends:

- `status`,
- `current_goals`,
- optional `edit_reason`.

The existing service flow remains the source of truth:

1. Load the character.
2. Ensure the current user owns the character's world.
3. Lock the world for update via `require_owned_world_for_update()`.
4. Capture `before` using `character_projection()`.
5. Apply the update.
6. Capture `after` using `character_projection()`.
7. Call `commit_manual_world_change()` with:
   - `object_type='character'`,
   - `action='updated'`,
   - `before`,
   - `after`,
   - optional `edit_reason`.

### Relation create

MVP #9 uses the existing endpoint:

```http
POST /worlds/{world_id}/relations
```

Allowed fields:

- `source_character_id`,
- `target_character_id`,
- `relation_type`,
- `intensity`,
- `visibility`,
- optional `edit_reason`.

The service must validate:

- source and target are not the same character,
- both character IDs exist,
- both character IDs belong to the requested world,
- the current user owns the world.

On success, the service writes formal governance via `commit_manual_world_change()` with `object_type='relation'` and `action='created'`.

### Relation update

MVP #9 uses the existing endpoint:

```http
PUT /relations/{relation_id}
```

The service must validate:

- relation exists,
- current user owns relation's world,
- updated source/target, if provided, remain non-self,
- updated source/target, if provided, still belong to the relation world.

On success, the service writes formal governance via `commit_manual_world_change()` with `object_type='relation'` and `action='updated'`.

### Event history

Keep the existing two-event manual edit model:

1. Object event:
   - `event_type='character_change'` or `event_type='relation_change'`,
   - `source_type='manual_edit'`,
   - payload includes `object_type`, `object_id`, `action`, `before`, `after`, and `edit_reason`.
2. Version event:
   - `event_type='world_version_increment'`,
   - `source_type='manual_edit'`,
   - payload includes the same commit group metadata and world-version transition.

MVP #9 does not introduce new event types.

## Frontend design

### WorldPage

WorldPage keeps the existing tabs:

- `世界概览`,
- `角色管理`,
- `关系管理`,
- `伏笔账本`.

The `角色管理` and `关系管理` tabs continue to pass `onChanged={loadWorld}`. Successful mutations reload both the manager-local list and the parent world overview, so world version, projection summaries, recent events, and narrative panels refresh.

### CharacterManager

MVP #9 presents CharacterManager as an update-only editor for existing characters.

Visible behavior:

- Render existing character cards.
- Show the governance warning that edits formally update world state and increase `world_version`.
- Provide an `编辑` action for each existing character.
- Hide `+ 新增角色`.
- Hide all delete controls.

Edit form fields:

- character name as read-only context,
- status,
- current goals as a delimiter-separated text input,
- optional edit reason.

Fields not exposed in MVP #9:

- name mutation,
- role type mutation,
- public profile JSON,
- hidden traits JSON,
- destiny flag mutation,
- create/delete controls.

Save behavior:

- Parse current goals by Chinese/English comma and dunhao delimiters.
- Send `updateCharacter(characterId, { status, current_goals, edit_reason })`.
- Show saving state while the request is in flight.
- On success, close the form, reload the character list, and call `onChanged`.
- On failure, keep the form open and render the error.

### RelationManager

MVP #9 presents RelationManager as create/update-only relation management.

Visible behavior:

- Render existing relation cards with character names.
- Show the governance warning.
- Show `+ 新增关系` when at least two characters exist.
- Provide `编辑` for existing relations.
- Hide relation delete controls.

Create/update form fields:

- source character,
- target character,
- relation type,
- intensity 1-5,
- visibility,
- optional edit reason.

Save behavior:

- Disable save if source and target are identical.
- For new relations, call `createRelation(worldId, payload)`.
- For existing relations, call `updateRelation(relationId, payload)`.
- Show saving state while the request is in flight.
- On success, close the form, reload relations, and call `onChanged`.
- On failure, keep the form open and render the error.

## Error handling

Backend errors remain explicit and stable:

- Missing world/character/relation: `404 NOT_FOUND`.
- Unauthorized owner boundary: `403 FORBIDDEN`.
- Same source and target relation: `400 INVALID_SELF_RELATION`.
- Related characters not found in the target world: `404 RELATED_CHARACTER_NOT_FOUND`.
- Pydantic validation errors remain `422`.

Frontend displays request errors in the relevant manager. Failed saves do not mutate local UI state optimistically.

## Testing plan

### Backend targeted tests

Add or extend backend tests for Story Bible management:

1. Updating a character changes status/current goals, increments `world_version`, refreshes projection, and writes manual events.
2. Non-owner character update is rejected.
3. Missing character update returns `404`.
4. Creating a relation increments `world_version`, refreshes projection, and writes manual events.
5. Updating a relation increments `world_version`, refreshes projection, and writes manual events.
6. Relation create/update rejects self-relations.
7. Relation create/update rejects cross-world character IDs.
8. Existing reviewing drafts are not mutated by manual Story Bible edits.
9. A draft created before a manual Story Bible edit reports world-version mismatch through approval readiness and approval preview.

### Frontend targeted tests

Update frontend tests for the narrowed UI scope:

1. CharacterManager renders existing characters and governance warning.
2. CharacterManager hides create/delete controls.
3. CharacterManager edits status/current goals and calls `updateCharacter` with the scoped payload.
4. CharacterManager shows saving state.
5. CharacterManager shows save errors without closing the form.
6. RelationManager renders existing relation cards and governance warning.
7. RelationManager hides delete controls.
8. RelationManager creates a relation and calls `onChanged`.
9. RelationManager updates a relation and calls `onChanged`.
10. RelationManager shows saving/error states.
11. RelationManager prevents self-relations.
12. WorldPage exposes the Story Bible tabs and refreshes overview through manager callbacks.

## Non-goals

- No character creation in the MVP #9 UI.
- No character deletion in the MVP #9 UI.
- No relation deletion in the MVP #9 UI.
- No backend endpoint removal for legacy create/delete behavior.
- No relation graph visualization.
- No AI-suggested Story Bible edits.
- No bulk edit.
- No complex JSON editor.
- No version tree.
- No automatic draft repair.
- No automatic chapter approval.
- No changes to formal chapter approval semantics.
- No dynamic workflows.
- No subagent execution.

## Self-review

- Placeholder scan: no TBD/TODO/fill-in-later placeholders remain.
- Internal consistency: backend and frontend scope both use update-only characters and create/update relations; create/delete backend compatibility is explicitly out of MVP #9 acceptance.
- Scope check: this is one implementation slice over existing Story Bible management and does not require decomposition.
- Ambiguity check: character UI field scope, relation UI field scope, event semantics, and draft non-mutation behavior are explicit.
