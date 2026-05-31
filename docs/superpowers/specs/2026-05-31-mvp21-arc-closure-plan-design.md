# MVP21 Arc Mode / Closure Plan 0.5 Design

## Product-route analysis

MVP19 made open narrative obligations visible through the Open Threads Board. MVP20 promoted those signals into a top-level World Pulse that tells the author whether the world should draft, repair, converge, or archive. The next smallest useful step is to turn the `converge` signal into a concrete chapter-planning surface: what phase is this story in, how much expansion is safe, and which obligations should the next chapter intentionally close, advance, defer, or preserve.

The updated `WorldSim-Writer.md` vision explicitly calls for Story Convergence, Narrative Entropy, Arc Mode, Closure Plan, Convergence Ratio, and Arc Transition Report. MVP21 should implement the advisory planning layer for Arc Mode and Closure Plan without adding persisted arc state yet.

## Candidates and recommendation

### 1. Arc Mode / Closure Plan 0.5 — recommended

Add a read-only `GET /worlds/{world_id}/arc-plan` endpoint plus a World page panel that derives an advisory arc mode and closure plan from existing signals: World Pulse, Open Threads Board, Narrative Health, Next Chapter Prep, approved chapter count, and story arc availability. The plan gives a concrete answer to: “For the next chapter, should I expand, organize, pressure, converge, payoff, or endgame — and which open threads should receive treatment?”

Why this is best:

- Directly follows MVP19 Open Threads and MVP20 World Pulse.
- Implements the product vision’s `Arc Mode` and `Closure Plan` concepts without premature persistence.
- Converts advisory warnings into actionable next-chapter planning guidance.
- Reuses existing deterministic services; no LLM calls, migrations, or world-state writes are required.
- Creates a future seam for persisted Closure Plan and Arc Transition Report.

### 2. Sandbox Seed Library 1.0

Add several high-tension official world embryos and a starter selector.

Trade-off: valuable for onboarding, but the current long-form loop now has enough world creation support. The stronger immediate gap is helping an existing world avoid endless expansion.

### 3. Audience Steering minimal loop

Let authors manually record audience intent and optionally feed it into next-chapter planning.

Trade-off: the product spec marks Audience Steering as optional/future. It should follow after author-owned arc/convergence planning is more explicit.

### 4. Tagging / Collections 1.0

Add user-defined labels for characters, foreshadows, chapters, and events.

Trade-off: useful for organization, but it introduces schema and editing complexity. Arc planning delivers more story-loop value with less persistence risk.

## Recommendation

Implement **MVP21 Arc Mode / Closure Plan 0.5**.

## Goals

- Add a read-only `GET /worlds/{world_id}/arc-plan` endpoint.
- Return an advisory `arc_mode`: `expand`, `organize`, `pressure`, `converge`, `payoff`, or `endgame`.
- Return a `mode_reason` explaining why that mode was selected.
- Return `expansion_budget`: `open`, `limited`, or `locked` to indicate whether the next chapter should add new threads.
- Return deterministic closure items derived from Open Threads Board.
- Classify closure items as `close`, `advance`, `merge`, `defer`, or `leave_open`.
- Return next-chapter guidance that can be shown above or near Next Chapter Prep.
- Add frontend API types/helper.
- Add `ArcPlanPanel` to the World page Narrative Control Center, near World Pulse and Open Threads.
- Keep this MVP advisory and read-only: no database writes, no EventLog creation, no `world_version` changes, no LLM calls, no migrations.

## Non-goals

- No persisted Arc Mode field.
- No persisted Closure Plan table.
- No Arc Transition Report persistence.
- No automatic foreshadow resolving, merging, or abandoning.
- No changes to chapter approval semantics.
- No changes to LLM prompts or chapter generation request payloads.
- No audience mandate support.
- No new world templates.

## Backend design

### Endpoint

```http
GET /worlds/{world_id}/arc-plan
```

Response model:

```python
ArcPlanResponse
```

Ownership is enforced via `require_owned_world()` before returning any data.

### Source signals

The service reads only existing advisory and projection data:

1. **World Pulse**
   - Uses `get_world_pulse(db, user, world_id)`.
   - `primary_mode = repair` pushes arc mode toward `organize` unless closure pressure is stronger.
   - `primary_mode = converge` pushes arc mode toward `converge`.
   - `pulse_status = urgent` limits or locks expansion.

2. **Open Threads Board**
   - Uses `get_open_threads(db, user, world_id)`.
   - `must_close` threads become `close` closure items.
   - `should_advance` threads become `advance` closure items.
   - Lower-priority threads become `defer` or `leave_open` items.
   - High entropy or many open threads locks expansion.

3. **Narrative Health**
   - Uses `get_narrative_health(db, user, world_id)`.
   - High-risk health makes expansion unsafe and adds repair-first guidance.

4. **Next Chapter Prep**
   - Uses `get_next_chapter_prep(db, user, world_id)`.
   - Provides suggested next chapter number, goal, and recommended POV.
   - Arc planning should complement, not replace, next prep.

5. **Approved chapter count and story arc availability**
   - Uses `count_approved_chapters()` and current `World.story_arc`.
   - Worlds with no approved chapters default to early `expand`/first-chapter guidance.
   - Worlds near the end of a ten-chapter story arc can move toward `payoff` or `endgame` when pressure supports it.

### Response shape

```python
class ArcPlanClosureItem(BaseModel):
    item_key: str
    thread_id: str | None = None
    treatment: str
    priority: str
    title: str
    rationale: str
    suggested_next_step: str
    related_character_ids: list[int]
    related_foreshadow_ids: list[int]

class ArcPlanGuidance(BaseModel):
    guidance_key: str
    label: str
    detail: str

class ArcPlanResponse(BaseModel):
    world_id: int
    world_version: int
    arc_mode: str
    mode_reason: str
    expansion_budget: str
    next_chapter_number: int
    recommended_goal: str
    closure_items: list[ArcPlanClosureItem]
    guidance: list[ArcPlanGuidance]
    source_summary: dict
```

### Arc mode rules

The service selects a single advisory mode in this priority order:

1. `organize`
   - Narrative Health is `at_risk`, or World Pulse primary mode is `repair`.
   - Meaning: repair coherence and reduce risk before adding major new branches.

2. `converge`
   - Open Threads Board has any `must_close` thread, or narrative entropy is `high`.
   - Meaning: next chapter should close/advance existing promises and avoid fresh sprawl.

3. `payoff`
   - Approved chapter count is at least 70% of the available story arc length and there are open threads to resolve.
   - Meaning: begin delivering promised reveals, reversals, and emotional returns.

4. `endgame`
   - Approved chapter count is at or beyond the available story arc length and open thread pressure remains.
   - Meaning: stop expanding; focus on terminal resolution and world-state lock-in.

5. `pressure`
   - There are `should_advance` threads or medium entropy, but no must-close/high-risk blocker.
   - Meaning: increase pressure on existing threads while allowing limited new setup.

6. `expand`
   - Default for new or low-pressure worlds.
   - Meaning: add conflict, clarify stakes, and establish reusable threads.

### Expansion budget rules

- `locked`: high health risk, any must-close thread, high entropy, or `endgame`.
- `limited`: medium entropy, `pressure`, `payoff`, or any should-advance threads.
- `open`: early/healthy `expand` mode with low entropy.

The budget is advisory only and does not block user actions.

### Closure item rules

Create up to eight closure items from the ordered Open Threads Board:

- `must_close` -> `treatment = close`.
- `should_advance` -> `treatment = advance`.
- `can_delay` with same related foreshadow or character as a higher-priority thread may become `merge`; otherwise `defer`.
- `can_leave_open` -> `leave_open`.

MVP21 does not write these treatments anywhere. The same source state will produce the same plan.

### Source summary

Return machine-readable inputs for the UI and tests:

- `pulse_status`
- `pulse_primary_mode`
- `health_status`
- `health_score`
- `open_thread_count`
- `must_close_count`
- `should_advance_count`
- `narrative_entropy_level`
- `approved_chapter_count`
- `story_arc_length`

## Frontend design

### API

Add types:

- `ArcPlanClosureItem`
- `ArcPlanGuidance`
- `ArcPlanResponse`

Add helper:

```ts
getArcPlan(worldId: number)
```

It calls:

```http
GET /worlds/{worldId}/arc-plan
```

### UI

Create `frontend/src/world/ArcPlanPanel.tsx`.

Render:

- heading: `Arc Mode / Closure Plan`;
- mode badge and expansion budget badge;
- mode reason;
- next chapter number and recommended goal;
- guidance cards;
- closure item cards showing treatment, priority, title, rationale, suggested next step, and related ids;
- loading, error, and empty states.

Mount in `WorldPage` inside the Narrative Control Center after `WorldPulsePanel` and before `NarrativeHealthPanel` / `OpenThreadsPanel`. This placement makes Arc Plan the bridge between the top-level pulse and detailed diagnostics.

## Testing strategy

### Backend TDD

Create `backend/tests/test_arc_plan.py` covering:

1. A new custom world returns `expand` mode, `open` or `limited` expansion budget, first/next chapter guidance, and closure items derived from initial open threads.
2. A high-risk approved chapter returns `organize` mode and `locked` expansion budget.
3. High-pressure or must-close open threads return `converge` mode with `close`/`advance` closure items.
4. A world late in its story arc with open threads returns `payoff` or `endgame` according to approved chapter count.
5. Endpoint is owner-scoped and rejects non-owner access with 403.

### Frontend TDD

- Add `getArcPlan()` helper test to `frontend/src/api/client.test.ts`.
- Add `ArcPlanPanel.test.tsx` for mode/budget, guidance, closure items, empty/loading/error states.
- Update `WorldPage.test.tsx` to mock `getArcPlan()`, assert it loads, and assert the panel appears near World Pulse.

## Acceptance criteria

- World page shows `Arc Mode / Closure Plan` in the Narrative Control Center.
- Backend endpoint is owner-scoped and read-only.
- Arc mode and expansion budget are deterministic from existing signals.
- Closure items are derived from Open Threads and include suggested treatment.
- No formal world-state changes occur.
- Backend targeted tests, frontend targeted tests, and frontend build pass.

## Risks and mitigations

- **Heuristics may feel too rigid.** Keep labels advisory and include `mode_reason` so the user can understand and override them.
- **Overlap with World Pulse and Open Threads.** Arc Plan should not duplicate every signal. It translates pulse/thread state into next-chapter policy and closure treatment.
- **Scope creep into persistence.** MVP21 intentionally avoids new tables and write APIs. Persisted Closure Plan can be a later MVP after users validate the advisory version.
- **Late-arc rules need story arc length.** Use current `World.story_arc` length only when available; otherwise fall back to open-thread pressure and approved chapter count.

## Self-review

- No placeholders remain.
- Scope is one read-only advisory planning surface.
- The design directly follows MVP19 Open Threads and MVP20 World Pulse.
- Product invariant is preserved: advisory arc planning does not commit formal world-state changes or event history.
