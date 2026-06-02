# Archived Narrative Draft Lifecycle Guard Design

## Brainstorming

The previous backend guard blocks archived-world chapter creation, direct draft creation, approval, and rejection. Remaining narrative endpoints can still mutate chapter/draft review artifacts after archive: outline generation, pipeline writing, critique/report generation, manual draft edits, stashing, full revision, and paragraph revision.

Options considered:

1. **Frontend-only hiding** — insufficient because direct API calls bypass the UI.
2. **Router-level guards** — explicit but duplicates the same status check across many endpoints.
3. **Service-level guard in narrative mutation functions** — recommended. It keeps the rule close to state changes and preserves existing route shapes.

## Design

Archived worlds reject narrative draft lifecycle mutations with `409 WORLD_ARCHIVED` after ownership is confirmed and before any chapter/draft/report mutation occurs.

Guarded endpoints:

- `POST /chapters/{chapter_id}/outline`
- `POST /chapters/{chapter_id}/write`
- `POST /chapters/{chapter_id}/critique`
- `POST /chapters/{chapter_id}/critic-report`
- `POST /chapters/{chapter_id}/character-arc-report`
- `PUT /chapters/{chapter_id}/draft`
- `POST /chapters/{chapter_id}/draft/revise`
- `POST /chapters/{chapter_id}/draft/stash`
- `POST /chapters/{chapter_id}/draft/paragraph`

Read-only endpoints stay available, including stored report reads, draft diff/version reads, approval preview, and approval readiness.

## Backend approach

Reuse the existing `_ensure_world_is_active(world)` helper from `app.narrative.service` and add a small helper that loads the already-owned chapter's world:

```python
def _world_for_chapter(db: Session, chapter: Chapter) -> World:
    world = db.get(World, chapter.world_id)
    assert world is not None
    return world
```

Each mutating chapter service calls `_ensure_world_is_active(world)` before creating outlines, drafts, reports, or draft versions.

## Tests

Add targeted regression tests for representative mutation groups:

1. Pipeline chapter mutations reject outline/write/critique after archiving.
2. Draft lifecycle mutations reject edit/stash/paragraph/full revision after archiving.
3. Report generation rejects critic and character arc report writes after archiving while existing read endpoints remain untouched by this change.

## Non-goals

This does not change archive restore behavior, approval preview/readiness reads, draft diff/version reads, export/snapshot reads, or frontend copy.