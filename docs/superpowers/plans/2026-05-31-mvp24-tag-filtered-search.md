# MVP24 Tag-filtered Global Search 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use sequential inline execution because this repository request explicitly forbids subagents and dynamic workflows. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users filter Global Search results by the tags created in MVP23.

**Architecture:** Extend the existing world search service and route with an optional `tags` query parameter, using existing `tags` / `object_tags` persistence to narrow results and attach matched tag metadata. Extend the frontend search API helper and `WorldSearchPanel` with optional tag loading and tag chips. This is read-only metadata filtering and does not change canon state.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, React, TypeScript, Vite, Vitest, Testing Library.

---

## File map

- Modify `backend/app/world/router.py` — accept `tags` query parameter and pass it to service.
- Modify `backend/app/world/service.py` — resolve tag filters and filter/annotate search results.
- Modify `backend/tests/test_world_search.py` — backend RED/GREEN tests for tag-filtered search.
- Modify `frontend/src/api/client.ts` — add optional `tags` search param.
- Modify `frontend/src/api/client.test.ts` — helper test for tags query string.
- Modify `frontend/src/world/WorldSearchPanel.tsx` — optional tag loading/toggling and result tag chips.
- Modify `frontend/src/world/WorldSearchPanel.test.tsx` — panel RED/GREEN tests for tag filters.
- Modify `frontend/src/world/WorldPage.tsx` — pass `listWorldTags` to `WorldSearchPanel`.
- Modify `frontend/src/world/WorldPage.test.tsx` — verify Global Search tag loading through page integration.

---

### Task 1: Backend RED tests

- [ ] Extend `backend/tests/test_world_search.py` with tag-filter behavior.
- [ ] Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_world_search.py -q
```

Expected: fail because `/worlds/{world_id}/search` does not accept or apply `tags` yet.

---

### Task 2: Backend GREEN implementation

- [ ] Import `Tag` and `ObjectTag` in `backend/app/world/service.py`.
- [ ] Add tag parsing and assignment-loading helpers.
- [ ] Update `search_world()` signature to accept `tags`.
- [ ] Filter each candidate result by `(object_type, object_id)` when tag filters are active.
- [ ] Attach matched tag metadata to `result['metadata']['tags']`.
- [ ] Update `backend/app/world/router.py` to pass `tags`.
- [ ] Rerun backend search tests until green.

---

### Task 3: Frontend API RED/GREEN

- [ ] Extend `frontend/src/api/client.test.ts` to expect a `tags` query parameter from `searchWorld()`.
- [ ] Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts
```

Expected: fail because `searchWorld()` ignores `tags`.

- [ ] Update `frontend/src/api/client.ts` search params type and query serialization.
- [ ] Rerun API tests until green.

---

### Task 4: WorldSearchPanel RED/GREEN

- [ ] Extend `frontend/src/world/WorldSearchPanel.test.tsx` to pass `onListTags`, wait for tag buttons, toggle one, and assert `onSearch` receives `tags`.
- [ ] Add a result fixture with `metadata.tags` and assert tag chips render.
- [ ] Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldSearchPanel.test.tsx
```

Expected: fail because `WorldSearchPanel` does not load tags or submit tag filters.

- [ ] Update `WorldSearchPanel.tsx` minimally.
- [ ] Rerun panel tests until green.

---

### Task 5: WorldPage integration RED/GREEN

- [ ] Update `frontend/src/world/WorldPage.test.tsx` expectations so Global Search tag loading calls `listWorldTags(7)` through `WorldSearchPanel`.
- [ ] Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: fail until `WorldPage.tsx` passes `listWorldTags` to `WorldSearchPanel`.

- [ ] Update `WorldPage.tsx`.
- [ ] Rerun WorldPage tests until green.

---

### Task 6: Final verification, commit, merge

- [ ] Run backend targeted tests:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_world_search.py tests/test_tags.py tests/test_world_seed_library.py tests/test_world_template.py tests/test_world_pulse.py tests/test_open_threads.py tests/test_arc_plan.py -q
```

- [ ] Run frontend targeted tests and build:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts src/world/WorldSearchPanel.test.tsx src/world/WorldTagsPanel.test.tsx src/world/WorldPage.test.tsx && npm run build
```

- [ ] Commit spec/plan and implementation on `feat/mvp24-tag-filtered-search` with the required co-author trailer.
- [ ] Fast-forward merge to `main`.
- [ ] Run the same backend/frontend verification on `main`.
- [ ] Do not push.

---

## Self-review

- No placeholders remain.
- TDD RED/GREEN gates are explicit.
- Scope is limited to read-only tag-filtered search.
- The plan respects inline execution, no dynamic workflows, no subagents, skip review, commit/merge main, and no push.
