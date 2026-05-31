# MVP16 Global Search 1.0 Design

## Roadmap Analysis

After MVP15, the product has a stable local writing loop plus increasingly rich formal state surfaces: custom world creation, world bible management, foreshadow ledger, approval consistency/readiness, chapter history, Markdown export, and Timeline Explorer. The next MVP should improve navigation across that accumulated material without expanding the state model too aggressively.

### Candidate 1 — Global Search / Tools Workspace 1.0 (Recommended)

Add an owner-scoped world search endpoint and a frontend search panel that can find characters, foreshadows, approved chapters, and formal events from one place. This is high leverage because existing MVPs have created multiple data surfaces, but the user still needs to remember where an item lives.

Pros:
- Uses existing tables and APIs; no new infrastructure or search engine.
- Directly supports the spec's `资料治理与辅助工具` and `GET /worlds/{world_id}/search` direction.
- Helps long-running projects before they become unmanageable.

Trade-off:
- MVP should use simple database/application matching, not full-text indexing or tags yet.

### Candidate 2 — Literary Quality Dashboard 1.0

Build a world-level quality dashboard from existing critic and character-arc reports: recent scores, recurring issues, rhythm risks, and character arc stagnation signals.

Pros:
- Aligns with the Novel Quality Engine section.
- Reuses critic/arc report work already present in the app.

Trade-off:
- Stronger after there are more approved chapters and after search/navigation improves.

### Candidate 3 — Export / Sync Log 1.0

Persist Markdown export attempts as formal export logs and show a Sync Log panel.

Pros:
- Aligns with the Obsidian/export roadmap and auditability.
- Low risk because Markdown export already exists.

Trade-off:
- Less immediately useful than search unless exports become a repeated workflow.

## Recommendation

Build **MVP16 Global Search / Tools Workspace 1.0**. It is the best next step because MVP15 made formal history visible, and MVP16 should make all accumulated world material findable. This also creates a natural foundation for later tags, filters, batch tools, and repair workflows without committing to a complex search backend.

## Scope

### In Scope

- Add `GET /worlds/{world_id}/search`.
- Search is owner-scoped through `require_owned_world()`.
- Query parameter `q` searches across:
  - world metadata: title, genre template, truth canon;
  - characters: name, role type, status, destiny flag, current goals, public/hidden profile JSON;
  - foreshadows: title, description, type, status, expected resolution window, related character ids;
  - approved/reviewing chapters: title, chapter goal, approved content;
  - formal events: event type, source type, payload JSON.
- Optional `object_types` filter accepts comma-separated types: `world`, `character`, `foreshadow`, `chapter`, `event`.
- Limit results with `limit` query parameter, default 20, maximum 50.
- Return grouped counts by object type and flat ranked results.
- Frontend API helper and types.
- Frontend `WorldSearchPanel` mounted in the World page / Narrative Control Center area.
- Search panel supports query input, object-type chips, empty state, error state, and result cards with links described as text labels rather than router navigation.

### Out of Scope

- PostgreSQL full-text search, trigram indexes, vector search, or external search services.
- Tags and tag editing.
- Global cross-world search.
- Highlight spans and fuzzy ranking.
- Batch edit, repair tools, or object mutation from search results.
- Router/deep-link navigation.

## Backend Design

Add search schemas to `backend/app/world/schemas.py`:

- `WorldSearchResultResponse`
  - `object_type: str`
  - `object_id: int | None`
  - `title: str`
  - `subtitle: str`
  - `snippet: str`
  - `metadata: dict[str, Any]`
- `WorldSearchResponse`
  - `world_id: int`
  - `query: str`
  - `object_type_counts: dict[str, int]`
  - `results: list[WorldSearchResultResponse]`

Add service function in `backend/app/world/service.py`:

- `search_world(db, user, world_id, query, object_types=None, limit=20)`.
- Resolve ownership first with `require_owned_world()`.
- Strip the query; reject blank queries with HTTP 422 and `SEARCH_QUERY_REQUIRED`.
- Normalize matching by lowercasing text.
- Convert JSON fields with `json.dumps(..., ensure_ascii=False)`.
- Produce deterministic results in object-type order: world, characters, foreshadows, chapters, events; then database id order within each type.
- Count all matched rows after object-type filtering, then return up to `limit` results.

Add router handler in `backend/app/world/router.py`:

- `GET /worlds/{world_id}/search`
- Parameters:
  - `q: str`
  - `object_types: str | None`
  - `limit: int = Query(20, ge=1, le=50)`
- Response model: `WorldSearchResponse`.

## Frontend Design

Add types to `frontend/src/api/types.ts`:

- `WorldSearchResult`
- `WorldSearchResponse`

Add helper to `frontend/src/api/client.ts`:

- `searchWorld(worldId, { q, object_types, limit })`
- It builds query string with `q`, optional comma-separated object types, and limit.

Create `frontend/src/world/WorldSearchPanel.tsx`:

- Local state:
  - query string;
  - selected object types;
  - search response;
  - loading;
  - error;
  - hasSearched.
- Object type chips: all, characters, foreshadows, chapters, events.
- Submit only when trimmed query is non-empty.
- Render:
  - heading: `Global Search`;
  - helper copy: search across world bible, chapters, foreshadows, and events;
  - result summary: total returned and counts by type;
  - result cards with object type, title, subtitle, snippet;
  - localized empty and error messages.

Mount `WorldSearchPanel` in `WorldPage.tsx` alongside Timeline Explorer, passing `searchWorld`.

## Testing Strategy

### Backend TDD

Add `backend/tests/test_world_search.py`.

Required tests:

1. Search finds custom world character, foreshadow, and event matches in one response.
2. `object_types=character` filters results and counts to characters only.
3. Search is owner-scoped and returns 403 for another user.
4. Blank search query returns 422 with `SEARCH_QUERY_REQUIRED`.

### Frontend TDD

Add or update tests:

1. `frontend/src/api/client.test.ts` verifies `searchWorld()` URL construction.
2. New `frontend/src/world/WorldSearchPanel.test.tsx` verifies:
   - successful search renders counts and results;
   - object-type chip sends filtered search;
   - blank query does not call API;
   - API errors render localized alert.
3. Update `frontend/src/world/WorldPage.test.tsx` to mock and assert the panel is mounted.

### Verification Commands

Backend targeted:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_world_search.py tests/test_world_template.py -v'
```

Frontend targeted:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts src/world/WorldSearchPanel.test.tsx src/world/WorldPage.test.tsx
```

Frontend build:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

## Acceptance Criteria

- An authenticated owner can search within a world from one endpoint and one UI panel.
- Results include object type, id, title, subtitle, snippet, and metadata.
- Object type filters work on backend and frontend.
- Another user cannot search someone else's world.
- Blank queries are rejected before scanning data.
- No formal world-state changes occur during search.
- Existing MVP loop, Timeline Explorer, world creation, and frontend build remain green.

## Self-Review

- Placeholder scan: no placeholders or TBDs remain.
- Scope check: focused on read-only search; tags, indexing, router navigation, and mutation tools are explicitly out of scope.
- Consistency check: endpoint, schema names, frontend helper, and panel names align across backend/frontend sections.
- Product invariant check: search is read-only and does not affect formal world state or event history.
