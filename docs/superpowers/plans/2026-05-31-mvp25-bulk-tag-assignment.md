# MVP25 Bulk Tag Assignment 0.5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use sequential inline execution because this repository request explicitly forbids subagents and dynamic workflows. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users paste multiple object IDs and assign one tag to those objects in a single metadata-only operation.

**Architecture:** Extend the existing `app.tags` domain with a bulk assignment schema, service function, and route. Add a frontend API helper and optional bulk input in `WorldTagsPanel`, then wire it through `WorldPage`. No schema migration is needed.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, React, TypeScript, Vite, Vitest, Testing Library.

---

## File map

- Modify `backend/app/tags/schemas.py` — add bulk request/response schemas.
- Modify `backend/app/tags/service.py` — add atomic bulk assignment service.
- Modify `backend/app/tags/router.py` — add `POST /worlds/{world_id}/tags/{tag_id}/objects/bulk`.
- Modify `backend/tests/test_tags.py` — backend RED/GREEN tests.
- Modify `frontend/src/api/types.ts` — add bulk assignment response type.
- Modify `frontend/src/api/client.ts` — add `bulkAssignWorldTag` helper.
- Modify `frontend/src/api/client.test.ts` — helper test.
- Modify `frontend/src/world/WorldTagsPanel.tsx` — optional bulk ID input and summary message.
- Modify `frontend/src/world/WorldTagsPanel.test.tsx` — panel tests.
- Modify `frontend/src/world/WorldPage.tsx` — pass bulk helper into panel.
- Modify `frontend/src/world/WorldPage.test.tsx` — mock bulk helper.

---

### Task 1: Backend RED tests

- [ ] Extend `backend/tests/test_tags.py` with bulk assignment tests.
- [ ] Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_tags.py -q
```

Expected: fail because the bulk route does not exist.

---

### Task 2: Backend GREEN implementation

- [ ] Add `ObjectTagBulkAssignRequest` and `ObjectTagBulkAssignResponse` schemas.
- [ ] Add `bulk_assign_tag()` service.
- [ ] Add bulk route in `backend/app/tags/router.py`.
- [ ] Rerun `tests/test_tags.py` until green.

---

### Task 3: Frontend API RED/GREEN

- [ ] Extend `frontend/src/api/client.test.ts` for the bulk helper endpoint.
- [ ] Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts
```

Expected: fail because `bulkAssignWorldTag` is missing.

- [ ] Add response type and API helper.
- [ ] Rerun API tests until green.

---

### Task 4: WorldTagsPanel RED/GREEN

- [ ] Extend `frontend/src/world/WorldTagsPanel.test.tsx` for valid bulk ID parsing and invalid list rejection.
- [ ] Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx
```

Expected: fail because bulk UI does not exist.

- [ ] Update `WorldTagsPanel.tsx` minimally.
- [ ] Rerun panel tests until green.

---

### Task 5: WorldPage integration RED/GREEN

- [ ] Update `WorldPage.test.tsx` mocks for `bulkAssignWorldTag`.
- [ ] Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: fail until `WorldPage.tsx` imports and passes the helper.

- [ ] Update `WorldPage.tsx`.
- [ ] Rerun WorldPage tests until green.

---

### Task 6: Final verification, commit, merge

- [ ] Run backend targeted tests:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_tags.py tests/test_world_search.py tests/test_world_seed_library.py tests/test_world_template.py tests/test_world_pulse.py tests/test_open_threads.py tests/test_arc_plan.py -q
```

- [ ] Run frontend targeted tests and build:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts src/world/WorldTagsPanel.test.tsx src/world/WorldSearchPanel.test.tsx src/world/WorldPage.test.tsx && npm run build
```

- [ ] Commit spec/plan and implementation on `feat/mvp25-bulk-tag-assignment` with the required co-author trailer.
- [ ] Fast-forward merge to `main`.
- [ ] Run the same backend/frontend verification on `main`.
- [ ] Do not push.

---

## Self-review

- No placeholders remain.
- TDD RED/GREEN gates are explicit.
- Scope is limited to metadata-only bulk tag assignment.
- The plan respects inline execution, no dynamic workflows, no subagents, skip review, commit/merge main, and no push.
