# MVP23 Tags / Collections 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use sequential inline execution because this repository request explicitly forbids subagents and dynamic workflows. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add owner-scoped tags so users can organize characters, foreshadows, approved chapters, and events without changing canon state.

**Architecture:** Add a new backend `app.tags` domain with `tags` and `object_tags` tables, owner-scoped services, and routes under `/worlds/{world_id}/tags`. Add typed frontend helpers, a `WorldTagsPanel`, and mount it in the Narrative Control Center. Tags are metadata only: no `world_version` increments and no EventLog entries.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic, pytest, React, TypeScript, Vite, Vitest, Testing Library.

---

## File map

- Create `backend/app/tags/__init__.py` — tags domain package marker.
- Create `backend/app/tags/models.py` — `Tag` and `ObjectTag` SQLAlchemy models.
- Create `backend/app/tags/schemas.py` — request/response schemas.
- Create `backend/app/tags/service.py` — owner-scoped tag CRUD, assignment validation, detail summaries.
- Create `backend/app/tags/router.py` — tag API routes.
- Modify `backend/app/core/database.py` — import tag models for test metadata registration.
- Modify `backend/app/api/router.py` — include tag router.
- Create `backend/alembic/versions/0012_add_tags.py` — persistent tag tables.
- Create `backend/tests/test_tags.py` — backend RED/GREEN tests.
- Modify `frontend/src/api/types.ts` — tag response/request types.
- Modify `frontend/src/api/client.ts` — tag API helpers.
- Modify `frontend/src/api/client.test.ts` — helper tests.
- Create `frontend/src/world/WorldTagsPanel.tsx` — tag board UI.
- Create `frontend/src/world/WorldTagsPanel.test.tsx` — panel tests.
- Modify `frontend/src/world/WorldPage.tsx` — import helpers/panel and mount it.
- Modify `frontend/src/world/WorldPage.test.tsx` — mock tag helpers and assert panel render.

---

### Task 1: Backend RED tests

- [ ] Create `backend/tests/test_tags.py` with tests for tag create/list, duplicate handling, assignment/detail counts, idempotent assignment, unsupported object type, deletion, auth, and no `world_version` increment.
- [ ] Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_tags.py -q
```

Expected: fail because tag endpoints do not exist.

---

### Task 2: Backend GREEN implementation

- [ ] Add `Tag` and `ObjectTag` models.
- [ ] Add Pydantic schemas.
- [ ] Add service functions for create/list/detail/delete/assign/unassign.
- [ ] Add routes and include them in the API router.
- [ ] Add Alembic migration `0012_add_tags.py`.
- [ ] Import tag models in `import_models()`.
- [ ] Rerun `tests/test_tags.py` until green.

---

### Task 3: Frontend API RED/GREEN

- [ ] Add failing API helper tests in `frontend/src/api/client.test.ts` for list/create/detail/assign/unassign/delete tag endpoints.
- [ ] Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts
```

Expected: fail because tag helpers are missing.

- [ ] Add tag types and helpers.
- [ ] Rerun API tests until green.

---

### Task 4: WorldTagsPanel RED/GREEN

- [ ] Create failing `frontend/src/world/WorldTagsPanel.test.tsx` covering list rendering, create tag, select detail, assign object, unassign object, delete tag, error state, and empty state.
- [ ] Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx
```

Expected: fail because `WorldTagsPanel` does not exist.

- [ ] Create `WorldTagsPanel.tsx` and rerun until green.

---

### Task 5: WorldPage integration RED/GREEN

- [ ] Update `WorldPage.test.tsx` to mock tag helpers and assert `Tags / Collections` renders in Narrative Control Center.
- [ ] Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: fail because panel is not mounted.

- [ ] Update `WorldPage.tsx` imports and mount `WorldTagsPanel` after `WorldSearchPanel`.
- [ ] Rerun WorldPage tests until green.

---

### Task 6: Final verification, commit, merge

- [ ] Run backend targeted tests:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_tags.py tests/test_world_seed_library.py tests/test_world_template.py tests/test_world_pulse.py tests/test_open_threads.py tests/test_arc_plan.py -q
```

- [ ] Run frontend targeted tests and build:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts src/world/WorldTagsPanel.test.tsx src/world/WorldPage.test.tsx && npm run build
```

- [ ] Commit implementation and plan on `feat/mvp23-tags-collections` with the required co-author trailer.
- [ ] Fast-forward merge to `main`.
- [ ] Run the same backend/frontend verification on `main`.
- [ ] Do not push.

---

## Self-review

- No placeholders remain.
- TDD RED/GREEN gates are explicit.
- The plan preserves the core canon invariant: tags are metadata only.
- The plan respects inline execution, no dynamic workflows, no subagents, skip review, commit/merge main, and no push.
