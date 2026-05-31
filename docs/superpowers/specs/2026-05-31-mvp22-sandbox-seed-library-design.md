# MVP22 Sandbox Seed Library 1.0 Design

## Product-route analysis

MVP19 through MVP21 completed the first story-convergence stack: Open Threads Board, World Pulse, and Arc Mode / Closure Plan. The long-form loop can now diagnose what an existing world needs next. The highest-value low-risk gap is onboarding into that loop: `WorldSim-Writer.md` says templates should become high-tension **世界胚胎**, and new users should be able to start from a compelling seed rather than a generic field form.

MVP22 should therefore add a small official Sandbox Seed Library that instantiates high-tension world embryos through the existing world-creation pipeline. This improves first-session value without adding LLM calls, migrations, marketplace complexity, or new canon mutation semantics.

## Candidates and recommendation

### 1. Sandbox Seed Library 1.0 — recommended

Add a static backend seed catalog plus frontend seed selector. Each seed includes key, label, genre, hook, tension profile, and a full `WorldCreateRequest` payload. Users can browse seeds, preview why they are high-tension, apply one to the existing custom world form, or create directly from an official seed endpoint.

Why this is best:

- Directly implements the product vision’s “世界胚胎” and cold-start guidance.
- Reuses the existing `create_world_from_template()` path and validation.
- Produces worlds immediately compatible with World Pulse, Open Threads, Arc Plan, Foreshadow Ledger, Timeline, Search, and Studio.
- Low technical risk: static catalog, no database migrations, no LLM calls, no marketplace or plugins.
- Complements MVP19–MVP21 by giving the convergence system richer seed worlds to analyze.

### 2. Arc Transition Report 0.5

Add a read-only report that summarizes closed/open questions at the end of a story-arc segment.

Trade-off: it builds on MVP21, but is most useful after more generated/approved chapter history exists. It is less helpful for a new user entering the product.

### 3. Audience Steering minimal loop

Let authors manually record audience intent and optionally feed it into next-chapter planning.

Trade-off: still future/optional in the product spec and depends on stronger author-side control surfaces first.

### 4. Tags / Collections 1.0

Add user tags to organize characters, foreshadows, chapters, and events.

Trade-off: useful, but it requires schema and mutation UX. Seed Library delivers onboarding value with less persistence risk.

## Recommendation

Implement **MVP22 Sandbox Seed Library 1.0**.

## Goals

- Add a static official seed catalog on the backend.
- Add `GET /worlds/seeds` to list seed summaries.
- Add `GET /worlds/seeds/{seed_key}` to return a seed detail including the full creation payload.
- Add `POST /worlds/from-seed/{seed_key}` to instantiate a seed through the existing creation path.
- Add frontend API types/helpers for listing, loading, and creating from seeds.
- Add seed cards to `WorldCreationForm` so users can apply a seed to the existing editable form.
- Keep the existing custom form and built-in sample shortcut.
- Keep created worlds fully compatible with current MVP flows.

## Non-goals

- No template marketplace.
- No user-created reusable templates.
- No dynamic AI seed generation.
- No seed persistence table.
- No migrations.
- No LLM calls.
- No multi-world switching changes.
- No changes to the formal approval/canon update invariant.

## Backend design

### Static catalog

Create `backend/app/world/seed_library.py` containing `WORLD_SEEDS`, a list of seed dictionaries. Each seed has:

- `key`: stable machine key;
- `label`: display name;
- `genre_template`: genre identifier;
- `hook`: one-sentence high-tension pitch;
- `tension_profile`: list of pressure tags;
- `starter_summary`: counts and short asset names;
- `payload`: a complete `WorldCreateRequest`-compatible dict.

Initial seeds:

1. `forgotten-sun-city`
   - A city where everyone forgot the sun ever existed.
   - Genre: fantasy / weird mystery.
2. `dead-god-oracle`
   - A dead god whose church still receives daily prophecies.
   - Genre: dark fantasy.
3. `generation-ship-myth`
   - A generation ship where no one believes outside space exists.
   - Genre: sci-fi.
4. `assigned-death-kingdom`
   - A kingdom where every child receives a state-assigned future cause of death.
   - Genre: political fantasy.
5. `world-bug-sect`
   - A cultivation sect whose protagonist is the world bug itself.
   - Genre: xianxia / meta mystery.

### Service functions

Add:

```python
def list_world_seeds() -> list[dict]
def get_world_seed(seed_key: str) -> dict
def create_world_from_seed(db: Session, user: User, seed_key: str) -> World
```

Rules:

- Unknown seed returns `404 SEED_NOT_FOUND`.
- `create_world_from_seed()` validates the seed payload with `WorldCreateRequest.model_validate()`.
- Creation delegates to `create_world_from_template()` so EventLog, projections, ForeshadowEvent, validation, and world_version behavior remain identical.

### API routes

Add static routes before dynamic `/{world_id}` routes:

```http
GET /worlds/seeds
GET /worlds/seeds/{seed_key}
POST /worlds/from-seed/{seed_key}
```

`GET /worlds/seeds` and `GET /worlds/seeds/{seed_key}` require auth like other world endpoints. This keeps the API simple and consistent with the app’s current authenticated workflow.

### Response shapes

```python
class WorldSeedSummary(BaseModel):
    key: str
    label: str
    genre_template: str
    hook: str
    tension_profile: list[str]
    starter_summary: dict

class WorldSeedDetail(WorldSeedSummary):
    payload: WorldCreateRequest

class WorldSeedListResponse(BaseModel):
    seeds: list[WorldSeedSummary]
```

## Frontend design

### API

Add types:

- `WorldSeedSummary`
- `WorldSeedDetail`
- `WorldSeedListResponse`

Add helpers:

```ts
listWorldSeeds()
getWorldSeed(seedKey: string)
createWorldFromSeed(seedKey: string)
```

### UI

Create `frontend/src/world/SeedLibraryPanel.tsx`.

Props:

```ts
type Props = {
  seeds: WorldSeedSummary[];
  selectedSeedKey: string | null;
  loading?: boolean;
  error?: string;
  onApplySeed: (seedKey: string) => void;
  onCreateSeed: (seedKey: string) => void;
};
```

Render:

- heading `Sandbox Seed Library`;
- seed cards with label, genre, hook, tension tags, starter summary;
- `套用到表单` action;
- `直接创建此胚胎` action;
- loading, error, and empty states.

### WorldCreationForm integration

`WorldCreationForm` should:

- accept seed props from `WorldPage`;
- show `SeedLibraryPanel` above genre preset cards;
- when applying a seed, call `getWorldSeed(seedKey)`, set the form to `seed.payload`, and visually mark the selected seed;
- when creating a seed directly, call `onCreateSeed(seedKey)` from `WorldPage`;
- keep custom editing available after applying a seed.

### WorldPage integration

`WorldPage` should:

- load seed summaries when no world exists;
- pass summaries/loading/error into `WorldCreationForm`;
- implement direct seed creation via `createWorldFromSeed(seedKey)`, then load overview and Narrative Control Center;
- keep existing sample and custom creation paths unchanged.

## Testing strategy

### Backend TDD

Create/update `backend/tests/test_world_seed_library.py` covering:

1. `GET /worlds/seeds` returns at least five official seeds and summary metadata.
2. `GET /worlds/seeds/{seed_key}` returns a full creation payload for a known seed.
3. `POST /worlds/from-seed/{seed_key}` creates a world with `WORLD_CREATED` event, starter characters, relations, and foreshadows.
4. Unknown seed returns `404 SEED_NOT_FOUND`.
5. Seed endpoints require auth.

### Frontend TDD

- Add API helper tests to `frontend/src/api/client.test.ts`.
- Add `SeedLibraryPanel.test.tsx` for card rendering, apply/direct-create buttons, loading/error/empty states.
- Update `WorldCreationForm.test.tsx` to verify applying a seed fills the form and direct seed creation calls the right callback.
- Update `WorldPage.test.tsx` to mock seed list/direct creation and verify the no-world creation screen loads seeds.

## Acceptance criteria

- New authenticated seed catalog endpoints exist.
- Users can browse official seeds on the creation screen.
- Users can apply a seed to the editable form.
- Users can directly create a world from a seed.
- Created seed worlds use the existing formal world creation pipeline and produce normal `WORLD_CREATED` history.
- Backend targeted tests, frontend targeted tests, and frontend build pass.

## Risks and mitigations

- **Route conflict with `/{world_id}`.** Register `/seeds` and `/from-seed/{seed_key}` before dynamic world-id routes.
- **Seed payload drift from backend validation.** Validate payloads with `WorldCreateRequest.model_validate()` in service and cover via tests.
- **UI overload on creation screen.** Keep seed cards concise and collapsible in spirit: a compact card grid above the existing form, not a full wizard rewrite.
- **Duplicate frontend/backend seed definitions.** Backend is source of truth; frontend loads seed summaries through API and only uses returned detail payload when applying a seed.

## Self-review

- No placeholders remain.
- Scope is a small static official seed library, not a marketplace.
- It directly supports the product vision’s high-tension world embryos and cold-start paths.
- It preserves the canon invariant by delegating all writes to the existing world creation path.
