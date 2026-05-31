# MVP19 Open Threads Board / Story Convergence 1.0 Design

## Product-route analysis

MVP14 through MVP18 completed the practical long-form foundation: custom world creation, formal event timeline, global search, narrative health dashboard, world snapshots, Markdown archive export, and snapshot comparison. The updated product vision in `WorldSim-Writer.md` reframes the long-term target as a **可运营的故事世界沙盒** with a required brake system: Story Convergence, Narrative Entropy, Open Threads Board, Arc Mode, Closure Plan, and Convergence Ratio.

The next MVP should therefore avoid another broad tool surface and instead add the smallest useful convergence loop: make open narrative obligations visible and turn them into next-chapter guidance.

## Candidates and recommendation

### 1. Open Threads Board / Story Convergence 1.0 — recommended

Add a read-only endpoint and World page panel that aggregates open foreshadows, active character goals, progression hints, high-pressure risks, and recent event signals into a structured board of open story threads. Each thread is classified as `must_close`, `should_advance`, `can_delay`, or `can_leave_open`, and the endpoint returns a lightweight convergence ratio and suggested next actions.

Why this is best:

- Directly implements the new Story Convergence vision without adding risky mutations.
- Reuses existing data: foreshadow ledger, character current goals, character arc reports, narrative health risks, chapter history, and event logs.
- Helps authors answer: “What must be closed or advanced before I keep expanding?”
- Provides structure for future Closure Plan / Arc Mode without creating new tables yet.

### 2. World Pulse 1.0

Create a world-level pulse panel combining health, recent timeline, next chapter prep, and archive signals into one top-level operational status.

Trade-off: high UX value, but much of the underlying data already exists. It risks being a rearrangement rather than a new long-form writing capability.

### 3. Sandbox Seed Library 1.0

Add multiple high-tension official world embryos and an onboarding selector that can instantiate them.

Trade-off: strongly supports the sandbox cold-start vision, but MVP14 already created custom/sample world creation. More templates help onboarding, while Open Threads Board better completes the long-form closure loop.

## Recommendation

Implement **MVP19 Open Threads Board / Story Convergence 1.0**.

## Goals

- Add a read-only `GET /worlds/{world_id}/open-threads` endpoint.
- Aggregate existing world/story signals into structured open thread cards.
- Classify threads by closure priority and pressure.
- Compute a lightweight convergence summary:
  - open thread count;
  - must-close count;
  - should-advance count;
  - can-delay count;
  - can-leave-open count;
  - convergence ratio from resolved/expired vs open foreshadows;
  - narrative entropy level: `low | medium | high`.
- Add frontend API types/helper.
- Add `OpenThreadsPanel` to the World page Narrative Control Center.
- Keep this MVP read-only: no new tables, no formal state mutation, no LLM calls.

## Non-goals

- No persisted closure plans.
- No Arc Mode state machine writes.
- No automatic foreshadow resolving/expiring.
- No chapter-generation prompt changes.
- No audience steering.
- No branch world creation or restore.
- No new database migrations.

## Backend design

### Endpoint

```http
GET /worlds/{world_id}/open-threads
```

Response model:

```python
OpenThreadsResponse
```

Ownership is enforced with `require_owned_world()`.

### Thread sources

The service reads only existing data:

1. **Foreshadow ledger**
   - Open foreshadows (`planted`, `advanced`) become `foreshadow` threads.
   - `critical` or `high` pressure threads become `must_close` or `should_advance`.
   - Lower pressure open foreshadows become `can_delay`.
   - Resolved/expired foreshadows contribute to convergence ratio but do not become active thread cards.

2. **Character current goals**
   - Characters with `current_goals` become `character_goal` threads.
   - Protagonist/major characters become `should_advance`; other characters become `can_delay`.

3. **Latest character arc progression hints**
   - Hints from the latest approved chapter with high priority become `progression_hint` threads.
   - Hints with `can_seed_next_chapter_goal` become `should_advance` and can seed suggested actions.

4. **Narrative health high/medium risks**
   - High risks become `must_close` risk threads.
   - Medium risks become `should_advance` risk threads.

5. **Recent formal events**
   - Recent event count and latest world version are included in summary context, but events only become thread cards if their payload has an obvious `changed_objects` or manual edit reason that can be surfaced safely. MVP19 can keep events as summary context rather than exhaustive event threads.

### Response shape

```python
class OpenThreadItem(BaseModel):
    thread_id: str
    thread_type: str
    priority: str
    pressure_level: str
    title: str
    summary: str
    related_object_type: str | None
    related_object_id: int | None
    related_character_ids: list[int]
    related_foreshadow_ids: list[int]
    suggested_action: str
    can_seed_next_chapter_goal: bool

class OpenThreadsSummary(BaseModel):
    total_open_threads: int
    must_close_count: int
    should_advance_count: int
    can_delay_count: int
    can_leave_open_count: int
    convergence_ratio: float
    narrative_entropy_level: str
    recent_event_count: int

class OpenThreadsResponse(BaseModel):
    world_id: int
    world_version: int
    summary: OpenThreadsSummary
    threads: list[OpenThreadItem]
    suggested_next_actions: list[dict]
```

### Priority rules

- `must_close`:
  - overdue/critical foreshadows;
  - high narrative-health risks;
  - stale planted foreshadows that have waited many approved chapters.
- `should_advance`:
  - high-pressure foreshadows;
  - protagonist/major active goals;
  - high-priority progression hints;
  - medium narrative-health risks.
- `can_delay`:
  - lower-pressure open foreshadows;
  - non-core character goals.
- `can_leave_open`:
  - advisory only for MVP19; active cards rarely use this unless a thread is low pressure and explicitly non-blocking.

### Convergence ratio and entropy

- `convergence_ratio = resolved_or_expired_foreshadows / max(total_foreshadows, 1)`.
- `narrative_entropy_level`:
  - `high` if `must_close_count >= 2` or `total_open_threads >= 10`;
  - `medium` if `must_close_count >= 1` or `total_open_threads >= 5`;
  - `low` otherwise.

This is intentionally heuristic. It is not a literary truth score; it is an operational warning system.

## Frontend design

### API

Add types:

- `OpenThreadItem`
- `OpenThreadsSummary`
- `OpenThreadsResponse`

Add helper:

```ts
getOpenThreads(worldId: number)
```

### UI

Create `frontend/src/world/OpenThreadsPanel.tsx`.

Render:

- heading: `Open Threads Board`;
- summary cards:
  - open threads;
  - must close;
  - should advance;
  - convergence ratio;
  - entropy level;
- grouped/ordered thread cards with:
  - priority label;
  - pressure level;
  - title;
  - summary;
  - suggested action;
  - marker when it can seed the next chapter goal.
- loading/error/empty states.

Mount in `WorldPage` near Narrative Health and Next Chapter Prep. It remains advisory and does not mutate world state.

## Testing strategy

### Backend TDD

Create `backend/tests/test_open_threads.py` covering:

1. New world with starter character goals and open foreshadow returns open thread cards and summary counts.
2. High-pressure foreshadow is classified as `should_advance` or `must_close` and can seed next chapter guidance.
3. Stored critic/character arc high risk is surfaced as a `must_close` risk thread.
4. Endpoint is owner-scoped and rejects non-owner access with 403.

### Frontend TDD

- Add `getOpenThreads()` helper test to `frontend/src/api/client.test.ts`.
- Add `OpenThreadsPanel.test.tsx` for summary, thread rendering, empty/loading/error states.
- Update `WorldPage.test.tsx` to mock `getOpenThreads()` and assert the panel loads.

## Acceptance criteria

- World page shows an Open Threads Board.
- Backend endpoint is owner-scoped and read-only.
- Foreshadow pressure, character goals, progression hints, and health risks become structured thread cards.
- Response includes convergence ratio and narrative entropy level.
- The panel provides suggested next actions without mutating state.
- Backend targeted tests, frontend targeted tests, and frontend build pass.

## Risks and mitigations

- **Heuristics may feel imprecise.** Keep labels advisory and deterministic; do not overclaim literary correctness.
- **Thread duplication.** Use stable thread ids and avoid creating duplicate risk cards for the same source when possible.
- **Scope creep toward persisted closure planning.** MVP19 does not write closure plans; it only surfaces open obligations. Persisted Closure Plan can be a future MVP.

## Self-review

- No placeholders remain.
- Scope is one read-only convergence board.
- The design directly supports the new `WorldSim-Writer.md` Story Convergence vision while avoiding new persistence complexity.
- Product invariant is preserved: generated/advisory information does not commit formal world-state changes.
