# MVP12 Foreshadow Ledger 1.0 Design

## Summary

MVP12 upgrades foreshadows from a flat editable list into a managed Foreshadow Ledger. The ledger helps authors understand which foreshadows are planted, actively advanced, resolved, or expired; which ones are stale or high urgency; and which ones should be prioritized in next-chapter preparation.

The implementation builds on existing foreshadow CRUD, stale detection, timeline events, and Next Chapter Prep. It adds a shared backend ledger evaluator and a typed ledger endpoint so the frontend and narrative planning context use the same deterministic pressure model.

## Goals

- Let the user view a Foreshadow Ledger with lifecycle grouping by `planted`, `advanced`, `resolved`, and `expired`.
- Surface urgency and stale pressure for each foreshadow.
- Show author-facing pressure labels such as high urgency, stale, overdue, resolved, and expired.
- Include related character names and expected resolution window in ledger entries.
- Reuse ledger pressure in Next Chapter Prep so high urgency and stale foreshadows are prioritized.
- Preserve existing approval, consistency review, and selected-change approval behavior.
- Continue maintaining foreshadow lifecycle event history after approval.

## Non-goals

- No complex timeline editor.
- No graph visualization.
- No automatic all-book foreshadow network generation.
- No AI-driven automatic recovery strategy that directly mutates state.
- No Obsidian or Markdown export changes.
- No new database tables unless an existing requirement cannot be met through current models.

## Current baseline

The repository already has these building blocks:

- `Foreshadow` projection fields: `status`, `urgency_level`, `related_character_ids`, `expected_resolution_window`, and `source_chapter_id`.
- `ForeshadowEvent` timeline rows created on manual creation and status transition.
- `get_stale_foreshadows()` detecting planted foreshadows whose source chapter is at least three approved chapters behind.
- `ForeshadowManager` with CRUD, status advancement, stale warning, list and kanban views.
- `Next Chapter Prep` with priority foreshadows currently selected mainly by urgency and progression hints.
- Approval writes `ForeshadowEvent` rows through `apply_foreshadow_status_transition()` and records `foreshadow_change` EventLog entries.

MVP12 should not replace these. It should consolidate ledger pressure calculation into one reusable service and expose richer structured responses.

## Recommended approach

Use a backend shared Foreshadow Ledger evaluator.

### Approach A — Shared backend ledger evaluator and endpoint

Add a small deterministic evaluator in `app.foreshadow.service` that produces:

- ledger entries with enriched metadata,
- summary counts,
- status groups,
- pressure flags,
- recent timeline events.

Expose it through `GET /worlds/{world_id}/foreshadows/ledger`. Update Next Chapter Prep to reuse the same pressure ranking. Update the frontend ledger tab to consume the endpoint rather than reconstructing all ledger semantics client-side.

This is the recommended approach because it keeps pressure semantics authoritative, testable, and reusable by both UI and next-chapter context.

### Approach B — Frontend-only ledger enhancement

Keep backend endpoints unchanged and compute all grouping, stale, and urgency labels inside `ForeshadowManager`.

This is faster but duplicates logic and leaves Next Chapter Prep with a different pressure model.

### Approach C — New ledger table and audit model

Introduce a dedicated ledger aggregate table and more event types.

This is too heavy for MVP12. Current `Foreshadow` and `ForeshadowEvent` tables already support the acceptance scope.

## Data contract

### Ledger summary

```json
{
  "total": 4,
  "open_count": 2,
  "planted_count": 1,
  "advanced_count": 1,
  "resolved_count": 1,
  "expired_count": 1,
  "high_urgency_count": 2,
  "stale_count": 1,
  "overdue_count": 1
}
```

### Ledger entry

```json
{
  "foreshadow": {
    "id": 1,
    "source_chapter_id": 3,
    "title": "裂纹玉佩",
    "description": "玉佩出现裂纹。",
    "foreshadow_type": "plot",
    "status": "advanced",
    "urgency_level": 4,
    "related_character_ids": [1],
    "expected_resolution_window": "第2-4章"
  },
  "status_group": "advanced",
  "is_open": true,
  "is_high_urgency": true,
  "is_stale": false,
  "is_overdue": false,
  "chapters_since_planted": 0,
  "pressure_level": "high",
  "pressure_reasons": ["高紧迫度：4"],
  "related_characters": [
    { "id": 1, "name": "林砚", "role_type": "protagonist" }
  ],
  "recent_events": [
    {
      "event_type": "advanced",
      "chapter_id": 11,
      "chapter_title": "第一章 雨巷密谈",
      "note": "湿信推进玉佩线索",
      "created_at": "2026-05-31T00:00:00Z"
    }
  ]
}
```

### Ledger response

```json
{
  "world_id": 7,
  "world_version": 3,
  "summary": {},
  "groups": {
    "planted": [],
    "advanced": [],
    "resolved": [],
    "expired": []
  },
  "high_pressure": []
}
```

`high_pressure` includes open entries with `pressure_level` `high` or `critical`, sorted by pressure, urgency, stale age, and id.

## Pressure rules

The evaluator is deterministic and conservative:

- `is_open` is true for `planted` and `advanced`.
- `is_high_urgency` is true when `urgency_level >= 4` and the foreshadow is open.
- `is_stale` follows the existing stale policy: planted with a `source_chapter_id` and at least three approved chapters after that source chapter.
- `is_overdue` follows the existing critical stale policy: stale for at least six approved chapters.
- `pressure_level` is:
  - `critical` when overdue,
  - `high` when stale or high urgency,
  - `medium` when open but not high pressure,
  - `resolved` for resolved foreshadows,
  - `expired` for expired foreshadows.
- `pressure_reasons` are author-facing Chinese text explaining why the item needs attention.

## Backend design

### `app.foreshadow.schemas`

Add response models:

- `RelatedCharacterBrief`
- `ForeshadowLedgerSummary`
- `ForeshadowLedgerEntry`
- `ForeshadowLedgerResponse`

Keep `ForeshadowResponse`, `ForeshadowEventResponse`, and `StaleForeshadowResponse` unchanged for compatibility.

### `app.foreshadow.service`

Add shared helpers:

- `_chapters_since_source(db, world_id, source_chapter_id)`
- `_recent_foreshadow_events(db, foreshadow_id, limit=3)`
- `_ledger_entry(db, foreshadow, character_by_id)`
- `get_foreshadow_ledger(db, user, world_id)`
- `foreshadow_ledger_priority_entries(db, user, world_id)` or an internal helper reusable by Next Chapter Prep

The existing `get_stale_foreshadows()` should either reuse the same helper or remain compatible while matching the new stale rule.

### `app.foreshadow.router`

Add:

```python
@router.get('/worlds/{world_id}/foreshadows/ledger', response_model=ForeshadowLedgerResponse)
def ledger(...):
    ...
```

This endpoint is read-only and must not mutate `world_version` or write `EventLog` rows.

### `app.narrative_control_center.service`

Update `_priority_foreshadows()` to prefer ledger pressure semantics:

1. progression-hint related foreshadows still come first,
2. then open ledger high-pressure foreshadows,
3. reasons should mention high urgency, stale, or overdue where applicable,
4. keep existing response shape for `NextChapterPrepForeshadow` to preserve frontend compatibility.

Update fallback `suggested_goal` so stale/high-pressure foreshadows can seed the goal when no character hint or story arc summary exists.

### Approval event trajectory

No new mutation path is needed for approval. Existing approval already calls `apply_foreshadow_status_transition()` with `chapter_id` and `description_note`, then writes `foreshadow_change` EventLog rows. MVP12 tests should lock this behavior by verifying the ledger timeline includes approval-created foreshadow events.

## Frontend design

### `src/api/types.ts`

Add ledger response types mirroring backend response models:

- `RelatedCharacterBrief`
- `ForeshadowPressureLevel`
- `ForeshadowLedgerSummary`
- `ForeshadowLedgerEntry`
- `ForeshadowLedgerResponse`

### `src/api/client.ts`

Add:

```ts
export function getForeshadowLedger(worldId: number) {
  return apiRequest<ForeshadowLedgerResponse>(`/worlds/${worldId}/foreshadows/ledger`);
}
```

### `src/components/ForeshadowManager.tsx`

Load `getForeshadowLedger(worldId)` instead of combining flat foreshadows plus stale foreshadows for ledger display. The existing CRUD calls stay unchanged.

Display:

- summary counts from `ledger.summary`,
- status-group cards for planted/advanced/resolved/expired,
- per-entry pressure chips,
- related character names from `entry.related_characters`,
- expected resolution window,
- recent lifecycle events from `entry.recent_events`,
- high-pressure callout using `ledger.high_pressure`.

The manager can keep existing list/kanban view toggles and CRUD controls. After create/update/delete it reloads the ledger and calls `onChanged` as before.

### `src/world/NextChapterPrepPanel.tsx`

Keep the existing response shape but improve labels for priority foreshadow reasons. The panel should surface reason text that includes high urgency/stale/overdue when returned by the backend.

## Error handling

- Unauthorized and forbidden behavior follows existing dependencies and `require_owned_world`.
- Invalid status behavior is unchanged.
- Ledger endpoint returns empty groups and zero counts when the world has no foreshadows.
- Missing related character IDs are tolerated in display because older data may contain stale IDs; they are simply omitted from `related_characters`.
- Read-only ledger and next-chapter prep must not mutate world version or event logs.

## Testing plan

### Backend tests

Add tests to `backend/tests/test_foreshadow_crud.py`:

- ledger endpoint groups entries by lifecycle status and includes summary counts,
- ledger marks open urgency >= 4 as high pressure,
- ledger marks stale planted foreshadows as stale and critical overdue after six approved chapters,
- ledger includes related character names and recent timeline events,
- ledger endpoint does not mutate `world_version` or write events.

Add/update tests in `backend/tests/test_narrative_control_center.py`:

- Next Chapter Prep prioritizes stale/high-pressure ledger foreshadows with clear reasons,
- no mutation occurs when preparing next-chapter context.

Add/update tests in `backend/tests/test_narrative_approval.py` if needed:

- approval-created foreshadow timeline event remains visible through ledger recent events.

### Frontend tests

Update `frontend/src/api/client.test.ts`:

- `getForeshadowLedger()` calls `/worlds/{world_id}/foreshadows/ledger`.

Update `frontend/src/components/ForeshadowManager.test.tsx`:

- manager renders ledger summary and grouped entries from `getForeshadowLedger()`,
- high-pressure callout shows high urgency/stale/overdue items,
- related character names and recent events render,
- create/update/delete reload ledger and refresh world overview.

Update `frontend/src/world/NextChapterPrepPanel.test.tsx`:

- priority foreshadow reasons containing stale/high urgency are displayed.

Run targeted backend tests, targeted frontend tests, and frontend build.

## Compatibility

- No approval API shape changes.
- No approval selected-change semantics changes.
- No consistency review behavior changes.
- Existing CRUD endpoints remain available.
- Existing stale endpoint remains available for compatibility, even if the new UI primarily uses the ledger endpoint.
- `WorldOverview.foreshadows` remains unchanged.

## Inline self-review

- Placeholder scan: no TBD/TODO placeholders remain.
- Scope check: the design stays focused on ledger visibility, pressure ranking, next-chapter prep hints, and timeline continuity.
- Ambiguity check: stale and overdue thresholds are explicit and reuse current behavior: 3 and 6 approved chapters.
- Compatibility check: approval, consistency, selection, CRUD, and existing response shapes remain compatible.
