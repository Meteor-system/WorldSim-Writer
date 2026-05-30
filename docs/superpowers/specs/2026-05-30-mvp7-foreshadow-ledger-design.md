# MVP #7 Foreshadow Ledger 1.0 Design

## Goal

Upgrade the MVP #6 foreshadow editor into a Foreshadow Ledger governance surface. Writers can systematically inspect unresolved foreshadows, identify stale or overdue risks, filter the ledger, advance or drop lifecycle state, and keep the world overview fresh after every formal write.

## Current state

The backend already provides authenticated foreshadow CRUD and governance behavior:

- `GET /worlds/{world_id}/foreshadows` with optional comma-separated `status` filtering.
- `GET /worlds/{world_id}/foreshadows/stale` for stale detection.
- `GET /foreshadows/{foreshadow_id}/timeline` for lifecycle events.
- `POST /worlds/{world_id}/foreshadows`, `PUT /foreshadows/{foreshadow_id}`, and `DELETE /foreshadows/{foreshadow_id}`.
- Manual create/update/delete operations increment `world_version`, refresh projection state, and write event history.

The frontend already has `ForeshadowManager`, list and kanban views, create/edit/delete, status advance, stale warning, timeline expansion, and `onChanged` refresh callbacks.

## Product decision

MVP #7 will not introduce a new backend status enum. It will keep the existing persisted statuses and provide an equivalent UI lifecycle mapping:

| Ledger lifecycle label | Persisted status |
| --- | --- |
| 已埋设 / Seeded | `planted` |
| 活跃推进 / Active | `advanced` |
| 已收束 / Resolved | `resolved` |
| 已放弃 / Dropped | `expired` |

`planned` is not a new persisted state in this MVP. A foreshadow with no source chapter is shown as `未绑定来源章节` rather than stored as `planned`.

## Recommended architecture

Use a light frontend extraction around the existing manager instead of adding a new backend aggregate endpoint.

- Keep `frontend/src/components/ForeshadowManager.tsx` as the WorldPage tab component and owner of load/mutation state.
- Add focused ledger UI logic inside the manager or a small local component/helper if it improves readability.
- Reuse existing client functions: `getForeshadows`, `getStaleForeshadows`, `updateForeshadow`, `createForeshadow`, `deleteForeshadow`, and `getForeshadowTimeline`.
- Reuse backend stale detection and status transition validation.
- Add tests before production changes.

This keeps scope aligned with the current MVP and avoids duplicating backend projection logic.

## Ledger behavior

### Summary strip

The ledger shows operational counts near the top:

- total foreshadows,
- unresolved foreshadows (`planted` + `advanced`),
- stale foreshadows from `/stale`,
- overdue foreshadows (`alert_level === 'critical'`),
- high urgency foreshadows (`urgency_level >= 4`).

### Filters

The ledger supports these filters:

- `全部` — all loaded foreshadows,
- `未收束` — `planted` and `advanced`,
- `Stale` — items returned by `/stale`,
- `Overdue` — stale items whose alert level is `critical`,
- `已收束` — `resolved`,
- `已放弃` — `expired`.

Filtering is frontend-only for stale/overdue because those are derived from `/stale`. Status-only views may still rely on the full loaded list for MVP simplicity.

### Ledger item details

Each card should make governance state visible:

- title and description,
- lifecycle label and persisted status,
- source chapter id or `未绑定来源章节`,
- expected resolution window or `未设定收束窗口`,
- related character names,
- urgency label,
- stale or overdue badge when applicable,
- timeline expansion,
- edit and delete actions,
- lifecycle actions.

### Lifecycle actions

Use existing `updateForeshadow` status updates:

- `planted -> advanced` as the normal advance action,
- `advanced -> resolved` as the normal advance action,
- `planted -> expired` as a drop action,
- `advanced -> expired` as a drop action,
- terminal states (`resolved`, `expired`) disable lifecycle advance/drop actions.

Every successful status update reloads the ledger data and calls `onChanged` so the world overview and narrative panels can refresh.

## Backend design

No new production backend endpoint is required for the recommended MVP.

Existing backend modules remain the source of truth:

- `backend/app/foreshadow/router.py`,
- `backend/app/foreshadow/service.py`,
- `backend/app/foreshadow/schemas.py`,
- `backend/app/foreshadow/models.py`,
- `backend/app/world/governance.py`,
- `backend/app/world/service.py` projection helpers,
- `backend/app/event/*` event history.

Backend work should be limited to tests unless frontend needs reveal a missing contract. Status transitions and `world_version` increments already exist and should not be weakened.

## Frontend design

### `ForeshadowManager`

The manager becomes the Foreshadow Ledger tab:

- Keep create/edit/delete forms from MVP #6.
- Keep the existing governance warning that edits formally update world state and increment `world_version`.
- Add summary strip and filter controls above the card grid.
- Add stale/overdue/high-urgency indicators on cards.
- Add a `放弃伏笔` action for unresolved items, implemented as `updateForeshadow(id, { status: 'expired' })`.
- Keep the existing status advance action but label it as a lifecycle action.
- Keep list and kanban views. Filters apply to the visible item collection in both views.

### `WorldPage`

`WorldPage` keeps the existing `伏笔账本` tab and continues passing `onChanged={loadWorld}`. The tab should still expose World Bible Editor create/edit/delete behavior while adding ledger governance.

## Error handling

- Initial load failures still render the existing component-level error.
- Stale endpoint failures should not block basic foreshadow listing if a simple fallback is feasible during implementation; otherwise the existing load error is acceptable for MVP.
- Mutation failures render existing `paper-error` messages.
- Terminal lifecycle actions are disabled rather than sending invalid transitions.
- Invalid backend status transition errors are surfaced as request errors and do not mutate local UI state.

## Testing plan

### Backend targeted tests

Run the existing foreshadow CRUD tests as the backend acceptance baseline:

- status filtering,
- stale detection,
- valid and invalid transitions,
- timeline event creation,
- create/update/delete world-version increments,
- ownership and validation.

Add backend tests only if implementation changes backend behavior.

### Frontend TDD focus

Add or extend tests in `frontend/src/components/ForeshadowManager.test.tsx` for:

- rendering ledger summary counts,
- filtering unresolved, stale, overdue, resolved, and dropped views,
- showing source chapter, expected resolution window, urgency, stale, and overdue risk metadata,
- advancing lifecycle with existing `updateForeshadow`,
- dropping unresolved foreshadows via `updateForeshadow(id, { status: 'expired' })`,
- refreshing local ledger data and calling `onChanged` after writes.

Extend `frontend/src/world/WorldPage.test.tsx` if needed to ensure the `伏笔账本` tab exposes the ledger and preserves the world-version governance warning.

## Non-goals

- No new LLM calls.
- No automatic foreshadow generation.
- No automatic foreshadow repair.
- No batch editing.
- No rollback or branch-world support.
- No Obsidian export work in this MVP.
- No complex graph visualization.
- No chapter approval behavior changes.
- No new complex permission model.
- No dynamic workflows.
- No subagent execution.
