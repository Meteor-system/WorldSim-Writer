# World Status Event Log Design

## Brainstorming outcome

The highest-value small MVP improvement is to make archive/restore operations auditable. World status can already switch between `active` and `archived`, but the append-only event history does not record that lifecycle transition. Since archived/read-only behavior now affects many write paths, status changes should be visible in recent events and timeline reads.

## Scope

- Add a `world_status_changed` event whenever `PATCH /worlds/{world_id}/status` changes the persisted status.
- Include previous and next status in the event payload.
- Keep `world_version` unchanged; archiving/restoring changes bookshelf lifecycle state, not canon/projection state.
- Do not create an event when the requested status equals the current status.
- Preserve existing ownership and invalid-status behavior.

## Event contract

Event fields:

- `event_type`: `world_status_changed`
- `source_type`: `world_status`
- `payload`: `{ "previous_status": "active", "next_status": "archived" }`
- `world_version_before`: current `world.world_version`
- `world_version_after`: same current `world.world_version`

## Testing

- Backend test archives then restores a world and verifies two ordered events with stable world version.
- Backend test repeats the same status and verifies no duplicate event is created.
- Existing world route tests continue to cover ownership and invalid status.
