# MVP #6 World Bible Editor 1.0 Design

## Goal

Make the existing world-state CRUD capabilities usable from the frontend as a World Bible Editor. Writers can create, edit, and delete characters, character relations, and foreshadows from the World page. Every write operation refreshes the world overview and clearly warns that the edit is a formal world-state change that increments `world_version`.

## Current state

The backend already has authenticated CRUD for characters, relations, and foreshadows, including world ownership checks, projection refresh, event logging, and `world_version` increments. The frontend already has initial manager components and World page tabs. MVP #6 should harden and complete that path rather than introduce a new backend subsystem.

## Recommended approach

Use incremental hardening of the current managers:

- Keep `frontend/src/components/CharacterManager.tsx`.
- Keep `frontend/src/components/RelationManager.tsx`.
- Keep `frontend/src/components/ForeshadowManager.tsx`.
- Keep `frontend/src/world/WorldPage.tsx` tabs.
- Add consistent governance copy warning that edits formally update world state and increment `world_version`.
- Add TDD coverage for create, edit, delete, refresh callbacks, and key safety affordances.

This keeps the MVP scoped, avoids component migration churn, and reuses existing backend CRUD.

## Backend design

No new core backend endpoints are required.

Existing modules remain the source of truth:

- `backend/app/character/*`
- `backend/app/relation/*`
- `backend/app/foreshadow/*`
- `backend/app/world/service.py`
- `backend/app/event/*`

Backend tests already cover CRUD ownership, validation, event writing, projection refresh, and world-version increments. Add backend tests only if implementation exposes a missing requirement.

## Frontend design

### World page

`frontend/src/world/WorldPage.tsx` remains the entry point. The tab set represents the World Bible Editor:

- 世界概览
- 角色管理
- 关系管理
- 伏笔账本

The manager tabs call `loadWorld` through `onChanged` after successful mutations so the latest overview, projections, recent events, and Narrative Control Center inputs are refreshed.

### Governance warning

Each manager displays the same clear warning near the top:

> 这些编辑会正式写入世界状态，并使 world_version 增长。

This is informational only. It does not block edits.

### Character manager

`CharacterManager` supports:

- list characters,
- create character,
- edit character,
- delete character with optional reason,
- call `onChanged` after each successful mutation.

Fields remain MVP-level: name, role type, status, destiny flag, current goals, edit reason.

### Relation manager

`RelationManager` supports:

- list relations,
- create relation,
- edit relation,
- delete relation with optional reason,
- prevent same source and target character,
- call `onChanged` after each successful mutation.

Fields remain MVP-level: source character, target character, relation type, intensity, visibility, edit reason.

### Foreshadow manager

`ForeshadowManager` supports:

- list foreshadows,
- create foreshadow,
- edit foreshadow,
- delete foreshadow with optional reason,
- advance status where allowed,
- drag/drop status update in kanban view,
- stale warning and timeline display,
- call `onChanged` after each successful mutation.

Fields remain MVP-level: title, description, type, status, urgency, related characters, expected resolution window, edit reason.

## Error handling

- Load failures render existing component-level errors.
- Create/edit/delete failures render existing `paper-error` messages.
- Invalid relation source/target selection disables submit and shows an error.
- Manager forms stay lightweight and local; failed requests do not mutate local state beyond error display.

## Testing plan

### Frontend TDD focus

Add or extend tests for:

- `CharacterManager`: renders warning and existing characters; create/edit/delete call the correct API and `onChanged`.
- `RelationManager`: renders warning; create/edit/delete call the correct API and `onChanged`; same source/target is prevented.
- `ForeshadowManager`: renders warning and cards; create/edit/delete/status advance call the correct API and `onChanged`; stale warning renders.
- `WorldPage`: management tabs expose the World Bible Editor sections and existing overview flow remains intact.

### Backend verification

Run existing backend CRUD test files and full backend tests. No backend production changes are expected unless tests uncover a gap.

## Non-goals

- No batch editing.
- No branch world.
- No rollback.
- No automatic repair.
- No new LLM call.
- No complex permissions beyond existing ownership checks.
- No chapter approval behavior changes.
- No dynamic workflows.
- No subagent execution.
