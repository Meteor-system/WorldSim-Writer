# Archived Story Arc Write Guard Design

## Target

Reject story arc generation writes for archived worlds while preserving archived-world reads and existing story arc display.

## Background

Archived worlds are intended to be paused/read-only. Recent rounds blocked world-bible writes, narrative core writes, draft lifecycle/report writes, and tag writes. One remaining persistent write surface is the story arc planner: `POST /worlds/{world_id}/story-arc` calls the model and overwrites `world.story_arc`.

`POST /worlds/{world_id}/suggest-goal` is not in this round because it does not persist data. If product policy later decides archived worlds should block all generation calls, that should be a separate, explicit UX/API round.

## Scope

When `world.status == 'archived'`, this endpoint must reject with `409 WORLD_ARCHIVED` after ownership is confirmed and before any model call or persistence:

- `POST /worlds/{world_id}/story-arc`

These reads remain available:

- `GET /worlds/{world_id}/overview` including existing `story_arc`
- Bookshelf/open-world reads for archived worlds

## Approach

Use the existing world update governance helper `require_owned_world_for_update()` in `app.world.story_arc.generate_story_arc()`. That helper locks the world row, enforces ownership, and rejects archived worlds with the established `WORLD_ARCHIVED` contract.

Keep `suggest_chapter_goal()` unchanged in this MVP because it only returns an ephemeral suggestion and does not mutate persisted world state.

## Error contract

Archived story arc writes return:

```json
{"detail": "WORLD_ARCHIVED"}
```

with HTTP status `409 Conflict`.

## Tests

Add backend regression coverage in `backend/tests/test_story_arc.py`:

1. Create a world and persist an initial story arc while active.
2. Archive the world.
3. Attempt to regenerate the story arc with a different fake model result.
4. Assert the endpoint returns `409 WORLD_ARCHIVED`.
5. Assert the stored `world.story_arc` remains unchanged.
6. Assert overview still reads the existing story arc for archived inspection.

Run targeted backend story arc tests, frontend build, WorldPage tests, and `git diff --check` before committing.
