# MVP20 World Pulse / Operational Overview 1.0 Design

## Product-route analysis

MVP14 through MVP19 completed a strong local long-form loop: custom world creation, world-bible management, timeline/event browsing, global search, narrative health, snapshots/export/compare, and Open Threads Board / Story Convergence. The updated `WorldSim-Writer.md` vision says the home workflow should answer “这个世界现在哪里需要处理” rather than just listing feature entrances.

The next MVP should therefore turn the existing scattered advisory signals into one top-level operational pulse. It should not introduce new canon writes, audience mechanics, or persisted arc state yet.

## Candidates and recommendation

### 1. World Pulse / Operational Overview 1.0 — recommended

Add a read-only `GET /worlds/{world_id}/pulse` endpoint plus a World page panel that summarizes current world status from existing signals: Narrative Health, Open Threads Board, Next Chapter Prep, approved chapter count, recent events, and archive/snapshot freshness. The pulse gives a concise answer to: “Should I continue writing, repair risks, converge open threads, or archive the current state?”

Why this is best:

- Directly implements the product vision’s `World Pulse` and homepage-first operational guidance.
- Reuses existing MVP17–MVP19 services without adding new persistence or model calls.
- Makes the growing Narrative Control Center easier to understand by placing one priority summary above detailed panels.
- Creates a future integration point for Arc Mode, Closure Plan, Sandbox operations, and Audience Steering mandates.

### 2. Arc Mode / Closure Plan 0.5

Add a read-only suggested arc mode derived from open threads and convergence pressure, with suggested closure focus.

Trade-off: valuable after MVP19, but persistent Arc Mode / Closure Plan is more useful when there is a clear top-level pulse to host it. A purely suggested arc mode can be included as one part of World Pulse without prematurely adding write state.

### 3. Sandbox Seed Library 1.0

Add multiple high-tension official world embryos and a starter selector.

Trade-off: improves cold start and sandbox feel, but the current product direction asks not to expand concepts endlessly. The long-form loop now benefits more from operational guidance than from additional templates.

### 4. Audience Steering minimal loop

Let authors record a manual audience intent and feed it into the next chapter.

Trade-off: the product spec explicitly marks Audience Steering as optional/future. It should not precede the author-owned canon governance and operational pulse layer.

## Recommendation

Implement **MVP20 World Pulse / Operational Overview 1.0**.

## Goals

- Add a read-only `GET /worlds/{world_id}/pulse` endpoint.
- Aggregate existing world operation signals into one deterministic summary.
- Return a top-level `pulse_status`: `stable`, `watch`, or `urgent`.
- Return current recommended `primary_mode`: `draft`, `repair`, `converge`, or `archive`.
- Return concise indicator cards for:
  - narrative health;
  - open threads;
  - next chapter readiness;
  - recent events;
  - archive/snapshot freshness.
- Return priority focus cards and next actions.
- Add frontend API types/helper.
- Add `WorldPulsePanel` above the Narrative Control Center detail panels.
- Keep this MVP advisory and read-only: no database writes, no EventLog creation, no `world_version` changes, no LLM calls, no migrations.

## Non-goals

- No persisted Arc Mode state.
- No persisted Closure Plan.
- No automatic foreshadow resolving or thread merging.
- No audience vote or mandate creation.
- No new world templates.
- No new database migrations.
- No changes to chapter generation prompts.

## Backend design

### Endpoint

```http
GET /worlds/{world_id}/pulse
```

Response model:

```python
WorldPulseResponse
```

Ownership is enforced via `require_owned_world()`.

### Source signals

The service reads only existing data:

1. **Narrative Health**
   - Uses `get_narrative_health(db, user, world_id)`.
   - `at_risk` health or high risks push pulse toward `urgent` and mode toward `repair`.

2. **Open Threads Board**
   - Uses `get_open_threads(db, user, world_id)`.
   - `must_close_count > 0` pushes mode toward `converge` unless repair is more urgent.
   - High total open threads or medium/high narrative entropy push pulse toward `watch` or `urgent`.

3. **Next Chapter Prep**
   - Uses `get_next_chapter_prep(db, user, world_id)`.
   - Provides next chapter number, suggested goal, recommended POV, and source signals.
   - If no urgent repair/convergence exists, next prep supports `draft` mode.

4. **Recent events and approved chapters**
   - Uses existing `EventLog` and `count_approved_chapters()` queries.
   - The pulse can distinguish first-chapter onboarding from ongoing operation.

5. **Snapshots/archive freshness**
   - Reads `WorldSnapshot` count and latest snapshot version if available.
   - If no snapshot exists, or the latest snapshot is behind the current `world_version`, add an archive reminder.
   - Snapshot freshness is advisory only; it does not create a snapshot.

### Response shape

```python
class WorldPulseIndicator(BaseModel):
    key: str
    label: str
    value: str
    status: str
    detail: str

class WorldPulseFocus(BaseModel):
    focus_key: str
    priority: str
    title: str
    detail: str
    suggested_action: str
    related_thread_id: str | None = None

class WorldPulseAction(BaseModel):
    action_key: str
    label: str
    detail: str
    target: str | None = None

class WorldPulseResponse(BaseModel):
    world_id: int
    world_version: int
    pulse_status: str
    primary_mode: str
    headline: str
    indicators: list[WorldPulseIndicator]
    focus: list[WorldPulseFocus]
    next_actions: list[WorldPulseAction]
    source_summary: dict
```

### Status and mode rules

`pulse_status`:

- `urgent` if Narrative Health is `at_risk`, or any open thread is `must_close`, or narrative entropy is `high`.
- `watch` if Narrative Health is `watch`, narrative entropy is `medium`, or there are no approved chapters yet.
- `stable` otherwise.

`primary_mode` priority:

1. `repair` when Narrative Health is `at_risk` or high health risks exist.
2. `converge` when must-close threads exist or narrative entropy is `high`.
3. `draft` when a next chapter goal is available and no higher priority mode applies.
4. `archive` when the world is stable but snapshot freshness is behind current world version.

The mode is advisory. It does not restrict user actions.

## Frontend design

### API

Add types:

- `WorldPulseIndicator`
- `WorldPulseFocus`
- `WorldPulseAction`
- `WorldPulseResponse`

Add helper:

```ts
getWorldPulse(worldId: number)
```

### UI

Create `frontend/src/world/WorldPulsePanel.tsx`.

Render:

- heading: `World Pulse`;
- headline text;
- status/mode badges;
- indicator cards for health, open threads, next chapter, recent events, and archive freshness;
- priority focus cards;
- next action cards;
- loading, error, and empty states.

Mount in `WorldPage` at the top of `Narrative Control Center`, above `NarrativeHealthPanel` and `OpenThreadsPanel`, so users first see the concise operational summary and can then inspect detailed panels.

## Testing strategy

### Backend TDD

Create `backend/tests/test_world_pulse.py` covering:

1. A new custom world returns a pulse with `watch` status, `draft` mode, onboarding/first-chapter action, and archive indicator.
2. Stored high critic/character-arc risk produces `urgent` status and `repair` mode.
3. High-pressure or must-close open threads produce a convergence focus and thread-related action.
4. Snapshot freshness is reflected without mutating state.
5. Endpoint is owner-scoped and rejects non-owner access with 403.

### Frontend TDD

- Add `getWorldPulse()` helper test to `frontend/src/api/client.test.ts`.
- Add `WorldPulsePanel.test.tsx` for summary/status/mode, indicators, focus cards, actions, empty/loading/error states.
- Update `WorldPage.test.tsx` to mock `getWorldPulse()`, assert it loads, and assert `World Pulse` appears above detail panels.

## Acceptance criteria

- World page shows `World Pulse` in the Narrative Control Center.
- Backend endpoint is owner-scoped and read-only.
- Pulse aggregates health, open threads, next prep, events, approved chapter count, and snapshot freshness.
- Pulse returns deterministic `pulse_status`, `primary_mode`, headline, indicators, focus cards, and next actions.
- No formal world-state changes occur.
- Backend targeted tests, frontend targeted tests, and frontend build pass.

## Risks and mitigations

- **Signal duplication with existing panels.** Keep World Pulse concise and link conceptually to detailed panels rather than duplicating every detail.
- **Heuristics may overstate urgency.** Use advisory labels and deterministic rules; do not claim literary truth.
- **Service composition could repeat queries.** MVP20 accepts small duplicate read cost for clarity; optimize only if profiling shows a real issue.
- **Scope creep into persisted Arc Mode.** This MVP returns suggested mode only and does not add write paths.

## Self-review

- No placeholders remain.
- Scope is one read-only operational overview.
- The design directly supports `WorldSim-Writer.md` World Pulse and Story Convergence guidance while avoiding new persistence complexity.
- Product invariant is preserved: advisory information does not commit formal world-state changes or event history.
