# Foreshadow Ledger Enhancement Design

Date: 2026-05-29

## Goal

Enhance the existing foreshadow CRUD system into a lifecycle ledger that records when foreshadows are planted, advanced, resolved, or expired; prevents invalid lifecycle transitions; detects stale planted foreshadows; and gives the frontend both list and kanban views with lifecycle timelines.

This stays inside the current MVP writing loop invariant: generated drafts may propose foreshadow changes, but only user approval commits formal world-state changes and event history.

## Decisions

- Use a service-layer lifecycle rule set shared by manual CRUD updates and chapter approval.
- Add `expired` as a supported foreshadow status.
- Create a `ForeshadowEvent` on foreshadow creation, including the initial `planted` event by default.
- Implement the frontend kanban with native HTML5 drag/drop and no new dependencies.
- Keep `foreshadows.status` as `String(40)`; enforce allowed statuses in service code rather than adding a database enum.

## Backend Design

### Data Model

Add `ForeshadowEvent` in `backend/app/foreshadow/models.py` with table name `foreshadow_events`:

- `id`: primary key
- `foreshadow_id`: foreign key to `foreshadows.id`, `ondelete='CASCADE'`, indexed
- `chapter_id`: nullable foreign key to `chapters.id`, `ondelete='SET NULL'`, indexed
- `event_type`: string, one of `planted`, `advanced`, `resolved`, `expired`
- `note`: nullable text
- `created_at`: timezone-aware datetime, defaulting to current UTC time

Add relationships:

- `Foreshadow.events` with cascade delete-orphan
- `ForeshadowEvent.foreshadow`
- `ForeshadowEvent.chapter`

### Lifecycle Rules

Define foreshadow status constants and transition matrix in `backend/app/foreshadow/service.py`:

```python
FORESHADOW_STATUSES = {'planted', 'advanced', 'resolved', 'expired'}

VALID_STATUS_TRANSITIONS = {
    'planted': {'advanced', 'expired'},
    'advanced': {'resolved', 'expired'},
    'resolved': set(),
    'expired': set(),
}
```

Rules:

- Any unknown status returns HTTP 400 with detail `INVALID_STATUS`.
- A changed status outside the transition matrix returns HTTP 400 with detail `INVALID_STATUS_TRANSITION`.
- Updating a foreshadow without changing `status` does not create a lifecycle event.
- Creating a foreshadow creates one lifecycle event whose `event_type` matches the created status. The default created status is `planted`.
- Manual status updates create a lifecycle event with the new status.
- Chapter approval creates a lifecycle event for each approved proposed foreshadow status change.

### Services and APIs

Enhance `get_foreshadows` to accept an optional list of statuses. The router parses `GET /worlds/{world_id}/foreshadows?status=planted,advanced` by comma-splitting and passes the validated list to the service. Invalid status filters return HTTP 400 `INVALID_STATUS`.

Add `GET /foreshadows/{foreshadow_id}/timeline`:

- Requires ownership through the existing foreshadow ownership check.
- Returns events ordered by `created_at, id` ascending.
- Each event includes `event_type`, `chapter_id`, `chapter_title`, `note`, and `created_at`.

Add `GET /worlds/{world_id}/foreshadows/stale`:

- Requires world ownership.
- Considers only `status='planted'` foreshadows with a non-null `source_chapter_id`.
- Counts approved chapters in the same world whose `id` is greater than the source chapter id.
- Includes foreshadows with `chapters_since_planted >= 3`.
- Uses `alert_level='warning'` for 3-5 chapters and `alert_level='critical'` for 6 or more chapters.

### Chapter Approval Integration

In `backend/app/narrative/service.py`, `approve_chapter` will reuse the foreshadow lifecycle helper when applying proposed foreshadow status changes.

Behavior:

- Proposed foreshadow changes still must reference foreshadows in the same world.
- Proposed changes without a `status` remain invalid for approval, matching current behavior.
- `description_note` continues to append to `Foreshadow.description` as it does now.
- `description_note` is also saved as the `ForeshadowEvent.note`.
- If any proposed foreshadow status transition is invalid, approval fails and the transaction rolls back.

## Frontend Design

### Types and Client

Update `frontend/src/api/types.ts`:

- Add `ForeshadowStatus = 'planted' | 'advanced' | 'resolved' | 'expired'`.
- Use that union for foreshadow create/update/response status fields.
- Add `ForeshadowEvent` with `event_type`, `chapter_id`, `chapter_title`, `note`, and `created_at`.
- Add `StaleForeshadow` with `foreshadow`, `chapters_since_planted`, and `alert_level`.

Update `frontend/src/api/client.ts`:

- `getForeshadows(worldId, params?: { status?: ForeshadowStatus[] })`
- `getForeshadowTimeline(foreshadowId)`
- `getStaleForeshadows(worldId)`

### ForeshadowManager UI

Keep the current list view and add `viewMode: 'list' | 'kanban'` with a top-level toggle.

Status metadata becomes:

- `planted`: green
- `advanced`: amber
- `resolved`: stone/neutral
- `expired`: red (`bg-red-100 text-red-800` family)

The current quick status action should no longer cycle terminal states back to `planted`. It may use the next legal forward transition for common cases, while `expired` remains available through editing or kanban drop.

### Kanban View

Add four fixed columns:

```text
planted → advanced → resolved → expired
```

Each column shows a count and foreshadow cards for that status.

Use native HTML5 drag/drop:

- Cards are `draggable`.
- `onDragStart` stores the foreshadow id.
- Columns use `onDragOver` to allow dropping.
- `onDrop` calls `updateForeshadow(id, { status: targetStatus })`.
- On success, reload foreshadows and stale alerts.
- On backend rejection, show the existing error banner and do not apply a local optimistic state change.

The backend remains the source of truth for legal drag transitions.

### Timeline Component

Add a `ForeshadowTimeline` component, initially in `ForeshadowManager.tsx` unless the file becomes unwieldy.

Behavior:

- Each card has an expand/details control.
- The timeline loads on first expansion with `getForeshadowTimeline`.
- It displays event time, event type label, optional chapter title, and optional note.
- Loading and error states stay within the expanded detail area.

### Stale Alert

When `ForeshadowManager` loads, fetch foreshadows and stale foreshadows. The implementation may use `Promise.all` so the two requests load together.

If stale foreshadows exist, show a top warning banner:

```text
⚠️ 有 N 条伏笔已超过 X 章未推进，建议尽快处理
```

`X` is the minimum `chapters_since_planted` among stale items to avoid overstating the alert.

Clicking the banner switches to kanban view so the user can inspect the `planted` column.

## Migration Design

Add `backend/alembic/versions/0005_add_foreshadow_events.py` with:

- `revision = '0005_add_foreshadow_events'`
- `down_revision = '0004_add_state_consistency_foundation'`
- `op.create_table('foreshadow_events', ...)`
- indexes for `foreshadow_id`, `chapter_id`, and `(foreshadow_id, created_at)`
- downgrade that drops indexes then drops the table

No migration is needed for `foreshadows.status` because it is already a string column wide enough for `expired`.

## Testing Design

Add or update backend tests in `backend/tests/test_foreshadow_crud.py` and, if clearer, narrative approval tests for approval-path lifecycle events.

Required coverage:

1. `test_foreshadow_status_transitions`
   - legal `planted → advanced`
   - illegal `advanced → planted`
   - legal `advanced → resolved`
   - illegal terminal transition from `resolved`
   - legal `planted → expired`

2. `test_foreshadow_timeline`
   - creation writes the initial event
   - later transition appears after it
   - timeline response includes chapter fields and note fields

3. `test_foreshadow_filter_by_status`
   - single status filter
   - multi-status filter
   - invalid filter returns `INVALID_STATUS`

4. `test_foreshadow_stale_detection`
   - planted foreshadow with three approved later chapters returns `warning`
   - six approved later chapters returns `critical`

5. `test_foreshadow_event_created_on_transition`
   - a successful manual transition adds exactly one lifecycle event

6. Approval path event test
   - construct a chapter draft with a proposed foreshadow status change
   - approve the chapter
   - verify the foreshadow status changes and the lifecycle event includes the approved chapter id and note

## Verification

Run these commands before claiming completion:

```bash
cd /opt/WorldSim-Writer/backend && python -m pytest tests/ -x -v
cd /opt/WorldSim-Writer/frontend && npm run build
```

After implementation and verification, create a git commit containing all changes.
