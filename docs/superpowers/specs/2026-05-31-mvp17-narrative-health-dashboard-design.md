# MVP17 Narrative Health Dashboard 1.0 Design

## Roadmap Analysis

MVP16 made accumulated world material searchable. The next MVP should help authors decide what needs attention before continuing the next chapter. The codebase already has critic reports, character arc reports, foreshadow pressure, chapter history, next-chapter prep, timeline, and global search. These signals are useful, but they are scattered across panels and chapter-level views.

### Candidate 1 — Narrative Health Dashboard 1.0 (Recommended)

Add a read-only world-level health endpoint and panel that aggregates quality, continuity, character-arc, and foreshadow pressure signals into one dashboard.

Pros:
- Reuses existing reports and ledger data; no new model calls or persistence needed.
- Aligns with the product spec's `风险提示面板` and `质量仪表盘指标`.
- Gives users a quick answer to “is this world safe to continue writing?”

Trade-off:
- The first version is heuristic and advisory, not a literary truth engine.

### Candidate 2 — Export / Sync Log 1.0

Persist Markdown export attempts and expose a Sync Log panel.

Pros:
- Strengthens export auditability.
- Low-risk extension of existing Markdown export.

Trade-off:
- Less central than world-writing quality unless export is already a daily workflow.

### Candidate 3 — Tagging 1.0

Introduce tags for characters, foreshadows, chapters, and events, then integrate them into search.

Pros:
- Natural next step after global search.
- Helps large projects organize assets.

Trade-off:
- Requires new persistence and editing surfaces; better after the dashboard clarifies what needs organization.

## Recommendation

Build **MVP17 Narrative Health Dashboard 1.0**. It is the best next step because MVP16 improved findability, while MVP17 should improve decision-making. The system already generates quality and continuity signals; this MVP makes them visible at world level without adding risky write paths.

## Scope

### In Scope

- Add `GET /worlds/{world_id}/narrative-health`.
- The endpoint is owner-scoped and read-only.
- Aggregate existing data:
  - approved chapter count;
  - latest chapter with critic/character arc reports;
  - average critic score across stored reports;
  - high/medium critic issue counts;
  - high/medium character arc and relationship risk counts;
  - high-pressure foreshadows from the existing foreshadow ledger;
  - open foreshadow counts;
  - recent formal event count.
- Return:
  - `health_score` from 0 to 100;
  - `status`: `healthy`, `watch`, or `at_risk`;
  - metric cards;
  - prioritized risk list;
  - suggested next actions.
- Add frontend API typing/helper.
- Add `NarrativeHealthPanel` and mount it in the World page Narrative Control Center.

### Out of Scope

- New LLM calls.
- New database tables or migrations.
- Automatic rewriting, auto-fixing, rollback, or formal state mutation.
- Full literary scoring beyond existing stored critic reports.
- Cross-world portfolio health.

## Backend Design

Add schemas in `backend/app/narrative_control_center/schemas.py`:

- `NarrativeHealthMetric`
- `NarrativeHealthRisk`
- `NarrativeHealthResponse`

Add service in `backend/app/narrative_control_center/service.py`:

- `get_narrative_health(db, user, world_id)`.
- Ownership checked via `require_owned_world()`.
- Use existing `build_foreshadow_ledger(db, world)`.
- Scan chapters in the world for stored `critique_report` and `character_arc_report` JSON.
- Compute a deterministic score:
  - start at 100;
  - subtract for high/medium critic issues;
  - subtract for high/medium arc and relationship risks;
  - subtract for high-pressure foreshadows;
  - subtract for missing approved chapters only as a mild onboarding warning;
  - clamp to 0..100.
- Status rules:
  - `at_risk`: score < 60 or any high-risk item exists;
  - `watch`: score < 80 or medium-risk item exists;
  - `healthy`: otherwise.

Add route in `backend/app/narrative_control_center/router.py`:

- `GET /worlds/{world_id}/narrative-health`.

## Frontend Design

Add types in `frontend/src/api/types.ts`:

- `NarrativeHealthMetric`
- `NarrativeHealthRisk`
- `NarrativeHealthResponse`

Add helper in `frontend/src/api/client.ts`:

- `getNarrativeHealth(worldId)`.

Create `frontend/src/world/NarrativeHealthPanel.tsx`:

- Shows score and status.
- Shows metric cards.
- Shows prioritized risks with severity/source labels.
- Shows suggested next actions.
- Handles loading, error, and empty/no-risk states.

Mount in `WorldPage.tsx` inside Narrative Control Center, loaded alongside chapter history and next-chapter prep.

## Testing Strategy

### Backend

Add `backend/tests/test_narrative_health.py`:

1. Returns healthy baseline for a new custom world.
2. Aggregates critic and character arc risks from stored chapter reports.
3. Includes high-pressure foreshadow risk from the existing ledger.
4. Enforces owner scope with 403.

### Frontend

- Add `getNarrativeHealth()` API helper test.
- Add `NarrativeHealthPanel.test.tsx` for score, metrics, risks, and error state.
- Update `WorldPage.test.tsx` to mock and assert the panel loads.

## Acceptance Criteria

- The world page shows a Narrative Health panel.
- The endpoint is read-only and owner-scoped.
- The dashboard surfaces critic issues, character arc risks, and high-pressure foreshadows.
- The dashboard provides suggested next actions without mutating world state.
- Backend targeted tests, frontend targeted tests, and frontend build pass.

## Self-Review

- Placeholder scan: no placeholders remain.
- Scope check: one read-only dashboard; no new persistence or model calls.
- Consistency check: endpoint, types, helper, and panel names align.
- Product invariant: generated/advisory signals do not commit formal world-state changes.
