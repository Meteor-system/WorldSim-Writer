# MVP15 Timeline / Event Log Explorer 1.0 Design

## Goal

Make the formal world timeline visible and usable. Users should be able to inspect the event history that powers canon, filter by event type, understand world-version transitions, and see enough payload context to trust how the world changed over time.

## Current context

WorldSim-Writer now has a strong append-only history foundation:

- `EventLog` stores formal world events with `event_type`, `source_type`, `payload`, `world_version_before`, `world_version_after`, and `created_at`.
- `GET /worlds/{world_id}/events` already returns paginated events and supports `event_type` filtering.
- World overview shows only a short recent-event list.
- Markdown export includes a timeline, but the in-app UI has no full timeline explorer.
- MVP14 added `WORLD_CREATED`, so every world now has an initial provenance event.

MVP15 should expose the existing formal history rather than introduce a new event store or change the write model.

## Recommended approach

Extend the existing event-list API response with lightweight summary metadata and add a dedicated Timeline panel to the World overview. Keep the current endpoint path and data model so existing consumers remain compatible.

This is the best default because it uses existing EventLog persistence, avoids a parallel timeline subsystem, and gives immediate product value from events already written by approvals, manual bible edits, foreshadow management, world creation, and export history.

## Alternatives considered

### A. Add a separate `/timeline` endpoint

This would make the UI intent explicit, but it duplicates `/events` and creates two read paths for the same data. It is not necessary for MVP15.

### B. Build global search first

Search is valuable, but timeline visibility is the prerequisite for trust and debugging. The event explorer also provides reusable UI/data patterns for future search.

### C. Add rollback or branch-from-event

Rollback and branching are important future features, but they change formal state and need stricter governance. MVP15 remains read-only.

## Backend design

### API surface

Keep and enhance:

```http
GET /worlds/{world_id}/events?event_type=...&limit=...&offset=...
```

The response remains backward compatible with existing fields:

```json
{
  "items": [],
  "total": 12,
  "limit": 20,
  "offset": 0,
  "summary": {
    "total": 12,
    "event_type_counts": {
      "WORLD_CREATED": 1,
      "chapter_approved": 3,
      "foreshadow_change": 4
    },
    "latest_world_version": 5
  }
}
```

### Summary semantics

- `summary.total` counts all events for the owned world, not just the current filter.
- `summary.event_type_counts` groups all world events by `event_type`.
- `summary.latest_world_version` is the maximum `world_version_after` across events, or the current `world.world_version` when no events exist.
- Existing pagination and `event_type` filter apply only to `items` and `total` in the current filtered result.
- Ownership remains enforced by `require_owned_world()`.

## Frontend design

### Timeline panel

Add a `WorldTimelinePanel` under the Narrative Control Center area on the World overview tab.

The panel should:

- load the first page of events via `getWorldEvents(world.id, { limit: 20 })`;
- show summary counts by event type;
- expose filter buttons: `全部`, plus each event type from summary counts;
- reload items when a filter is selected;
- render each event with:
  - event type;
  - source type;
  - world version transition;
  - created timestamp;
  - a concise user-readable summary derived from known payload shapes;
- show a safe fallback JSON preview for unknown event payloads;
- show local loading/error states without blocking the rest of the World page.

### Event descriptions

MVP15 should support user-readable labels for known events:

- `WORLD_CREATED`: world title, genre, starter counts.
- `chapter_approved` / `CHAPTER_APPROVED`: chapter title/id and selected change summary if present.
- `character_change`: created/updated/deleted object and edit reason if present.
- `foreshadow_change`: created/updated/deleted object and edit reason if present.
- `world_version_increment`: target world version.

Unknown event types remain visible with the raw event type and compact payload preview.

## Compatibility expectations

- Existing `getWorldEvents()` callers continue to work because `summary` is additive.
- World overview recent events remain unchanged.
- Markdown export remains read-only and should continue to include event timeline data.
- Approval, consistency, foreshadow ledger, custom world creation, and sample world creation remain compatible.

## Testing strategy

Backend TDD:

- Add tests proving `/worlds/{world_id}/events` returns summary counts and latest world version.
- Add tests proving `event_type` filtering still filters `items`/filtered `total` while preserving all-world summary counts.
- Add tests proving non-owners cannot read event summary.

Frontend TDD:

- Add API helper/type test for `getWorldEvents()` summary response compatibility.
- Add `WorldTimelinePanel` tests for loading, summary counts, filter behavior, event descriptions, and error state.
- Update `WorldPage` tests to prove the timeline panel loads alongside the existing Narrative Control Center.

## Non-goals

MVP15 does not implement:

- rollback;
- event editing;
- branch world creation;
- full global search;
- tags;
- bulk event operations;
- event-log schema migrations;
- background indexing;
- push to remote git.

## Inline self-review

- Placeholder scan: no TBD/TODO placeholders remain.
- Scope check: this is a read-only event explorer over the existing EventLog model.
- Compatibility: the existing `/events` endpoint is enhanced additively, not replaced.
- Canon invariant: the explorer does not mutate formal world state; generated drafts still only propose changes until approval.
- Ambiguity resolved: `summary` describes all events in the world, while `items` and response `total` describe the current filter/page.
