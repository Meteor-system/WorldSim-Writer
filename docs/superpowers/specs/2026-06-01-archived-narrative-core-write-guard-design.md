# Archived Narrative Core Write Guard Design

## Brainstorming

Archived novels are now presented as paused/read-only in the bookshelf, Narrative Control Center, World Bible UI, and backend World Bible write APIs. The remaining high-value gap is the core narrative loop: direct API callers can still create chapter drafts or approve/reject existing drafts after a world has been archived.

Candidate approaches:

1. **Frontend-only hiding** — already mostly done, but insufficient because direct API calls can bypass it.
2. **Route-level checks in narrative router** — explicit but duplicates ownership/status logic across endpoints.
3. **Service-level guard near narrative mutations** — recommended. It keeps the invariant next to the transaction logic and covers current router/API callers without adding new infrastructure.

## Design

Archived worlds must reject core narrative write actions with `409 WORLD_ARCHIVED` while preserving read/review endpoints. This MVP guards:

- `POST /worlds/{world_id}/chapters`
- `POST /worlds/{world_id}/chapters/draft`
- `POST /chapters/{chapter_id}/approve`
- `POST /chapters/{chapter_id}/reject`

Read-only review endpoints such as approval preview/readiness remain available so users can inspect paused work.

## Backend behavior

Add a small narrative service helper that raises:

```python
HTTPException(status_code=status.HTTP_409_CONFLICT, detail='WORLD_ARCHIVED')
```

when a loaded world has `status == 'archived'`.

Apply it after ownership checks and before mutating narrative state. Approval keeps its existing row lock and ownership checks, then rejects archived worlds before draft/version/change application.

## Testing

Add a targeted regression test in `backend/tests/test_narrative_approval.py` that:

1. Creates a draft while active.
2. Archives the world.
3. Verifies new chapter session creation is rejected.
4. Verifies new draft creation is rejected.
5. Verifies approving the existing draft is rejected.
6. Verifies rejecting the existing draft is rejected.
7. Verifies approval preview/readiness still work.
8. Verifies the world version and chapter status did not change.

## Non-goals

This does not change archive/restore semantics, frontend UI, export/snapshot reads, or broader LLM report generation endpoints. Those can be hardened separately if needed.