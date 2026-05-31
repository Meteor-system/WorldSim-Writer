# MVP22 Sandbox Seed Library 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use sequential inline execution because this repository request explicitly forbids subagents and dynamic workflows. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a static official Sandbox Seed Library so users can browse high-tension world embryos, apply one to the editable world creation form, or directly create a compatible world from a seed.

**Architecture:** Add a backend static seed catalog and authenticated read/create endpoints under `/worlds`, delegating seed creation to the existing `create_world_from_template()` pipeline. Add typed frontend API helpers, a `SeedLibraryPanel`, and creation-screen integration. No migrations, LLM calls, marketplace features, or new canon-write semantics are introduced.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, React, TypeScript, Vite, Vitest, Testing Library.

---

## File map

- Create `backend/app/world/seed_library.py` — static official seed definitions and lookup helpers.
- Modify `backend/app/world/schemas.py` — seed summary/detail/list response models.
- Modify `backend/app/world/service.py` — list/detail/create seed service functions.
- Modify `backend/app/world/router.py` — add seed catalog and seed creation routes before dynamic `/{world_id}` routes.
- Create `backend/tests/test_world_seed_library.py` — backend RED/GREEN seed endpoint tests.
- Modify `frontend/src/api/types.ts` — seed response types.
- Modify `frontend/src/api/client.ts` — seed API helpers.
- Modify `frontend/src/api/client.test.ts` — API helper RED/GREEN tests.
- Create `frontend/src/world/SeedLibraryPanel.tsx` — seed cards UI.
- Create `frontend/src/world/SeedLibraryPanel.test.tsx` — panel RED/GREEN tests.
- Modify `frontend/src/world/WorldCreationForm.tsx` — render seed library and apply/direct-create callbacks.
- Modify `frontend/src/world/WorldCreationForm.test.tsx` — form integration tests.
- Modify `frontend/src/world/WorldPage.tsx` — load seed summaries and handle direct seed creation.
- Modify `frontend/src/world/WorldPage.test.tsx` — no-world seed loading/direct-create integration tests.

---

### Task 1: Backend RED tests

- [ ] Create `backend/tests/test_world_seed_library.py` covering seed list, detail, create, unknown seed, and auth requirements.
- [ ] Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_world_seed_library.py -q
```

Expected: fail with missing `/worlds/seeds` or missing implementation.

---

### Task 2: Backend GREEN implementation

- [ ] Create `backend/app/world/seed_library.py` with at least five high-tension seed payloads.
- [ ] Add seed response schemas to `backend/app/world/schemas.py`.
- [ ] Add `list_world_seeds()`, `get_world_seed()`, and `create_world_from_seed()` to `backend/app/world/service.py`.
- [ ] Add `/worlds/seeds`, `/worlds/seeds/{seed_key}`, and `/worlds/from-seed/{seed_key}` routes before dynamic routes.
- [ ] Run backend seed tests until green.

---

### Task 3: Frontend API RED/GREEN

- [ ] Add failing helper tests for `listWorldSeeds()`, `getWorldSeed()`, and `createWorldFromSeed()` in `frontend/src/api/client.test.ts`.
- [ ] Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts
```

Expected: fail because helpers/types are missing.

- [ ] Add seed types and helpers.
- [ ] Rerun API tests until green.

---

### Task 4: SeedLibraryPanel RED/GREEN

- [ ] Create failing `frontend/src/world/SeedLibraryPanel.test.tsx` for seed card rendering, apply, create, loading, error, and empty states.
- [ ] Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/SeedLibraryPanel.test.tsx
```

Expected: fail because panel does not exist.

- [ ] Create `SeedLibraryPanel.tsx` and rerun until green.

---

### Task 5: WorldCreationForm RED/GREEN

- [ ] Update `WorldCreationForm.test.tsx` to verify seed cards can apply a seed payload to the form and direct seed creation calls the supplied callback.
- [ ] Run form tests and observe RED.
- [ ] Update `WorldCreationForm.tsx` props/state wiring and rerun until green.

---

### Task 6: WorldPage integration RED/GREEN

- [ ] Update `WorldPage.test.tsx` to mock seed API helpers, verify seed list loads on no-world screen, and verify direct seed creation loads overview.
- [ ] Run WorldPage tests and observe RED.
- [ ] Update `WorldPage.tsx` imports/state/load/direct-create wiring and rerun until green.

---

### Task 7: Final verification, commit, merge

- [ ] Run backend targeted tests:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_world_seed_library.py tests/test_world_template.py tests/test_world_pulse.py tests/test_open_threads.py tests/test_arc_plan.py -q
```

- [ ] Run frontend targeted tests and build:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts src/world/SeedLibraryPanel.test.tsx src/world/WorldCreationForm.test.tsx src/world/WorldPage.test.tsx && npm run build
```

- [ ] Commit implementation and plan on `feat/mvp22-seed-library`.
- [ ] Fast-forward merge to `main`.
- [ ] Run the same backend/frontend verification on `main`.
- [ ] Do not push.

---

## Self-review

- No placeholders remain.
- TDD RED/GREEN gates are explicit.
- The plan respects inline execution, no dynamic workflows, no subagents, skip review, commit/merge main, and no push.
