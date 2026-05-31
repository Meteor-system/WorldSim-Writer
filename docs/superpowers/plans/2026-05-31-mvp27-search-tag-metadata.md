# MVP27 Search Tag Metadata 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use sequential inline execution because this repository request explicitly forbids subagents and dynamic workflows. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show existing object tags on normal Global Search results, not only on tag-filtered searches.

**Architecture:** Extend backend search enrichment in `app.world.service` by loading world-scoped object tag metadata and attaching it to result metadata after normal search matching and optional tag filtering. Reuse existing frontend tag-chip rendering in `WorldSearchPanel`; no production frontend UI change is expected.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, React, TypeScript, Vite, Vitest.

---

## File map

- Create: `docs/superpowers/specs/2026-05-31-mvp27-search-tag-metadata-design.md` — design spec.
- Create: `docs/superpowers/plans/2026-05-31-mvp27-search-tag-metadata.md` — implementation plan.
- Modify: `backend/tests/test_world_search.py` — backend RED/GREEN coverage for unfiltered tag metadata.
- Modify: `backend/app/world/service.py` — search metadata enrichment helper and result append update.
- Optional verify only: `frontend/src/world/WorldSearchPanel.test.tsx` — existing chip rendering coverage.

---

### Task 1: Backend RED tests

- [ ] Add `test_world_search_adds_tag_metadata_without_tag_filter` to `backend/tests/test_world_search.py`:

```python
def test_world_search_adds_tag_metadata_without_tag_filter(client, monkeypatch):
    token = register(client, 'search-tag-metadata@example.com')
    world, _ = create_searchable_world(client, token, monkeypatch)
    overview = client.get(f"/worlds/{world['id']}/overview", headers=auth(token)).json()
    tag = create_tag(client, token, world['id'], '灯塔线')
    assign_tag(client, token, world['id'], tag['id'], 'foreshadow', overview['foreshadows'][0]['id'])

    response = client.get(f"/worlds/{world['id']}/search?q=黑匣子", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    foreshadow_result = next(result for result in payload['results'] if result['object_type'] == 'foreshadow')
    assert foreshadow_result['metadata']['tags'] == [
        {'id': tag['id'], 'name': '灯塔线', 'slug': '灯塔线', 'color': 'amber'}
    ]
```

- [ ] Add a second test if needed to prove a tag in another world does not appear in the owner world’s unfiltered search results.
- [ ] Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_world_search.py -q
```

Expected: fail because unfiltered search currently omits `metadata.tags`.

---

### Task 2: Backend GREEN implementation

- [ ] Add helper in `backend/app/world/service.py`:

```python
def _load_object_tag_metadata(db: Session, world_id: int) -> dict[tuple[str, int], list[dict]]:
    assignments = list(db.scalars(select(ObjectTag).where(ObjectTag.world_id == world_id).order_by(ObjectTag.id)))
    if not assignments:
        return {}
    tag_ids = {assignment.tag_id for assignment in assignments}
    tags = list(db.scalars(select(Tag).where(Tag.world_id == world_id).where(Tag.id.in_(tag_ids)).order_by(Tag.id)))
    tag_by_id = {tag.id: tag for tag in tags}
    metadata_by_object: dict[tuple[str, int], list[dict]] = {}
    for assignment in assignments:
        tag = tag_by_id.get(assignment.tag_id)
        if tag is None:
            continue
        key = (assignment.object_type, assignment.object_id)
        metadata_by_object.setdefault(key, []).append(_tag_metadata(tag))
    return metadata_by_object
```

- [ ] Update `_append_search_result()` to accept `metadata_by_object` and attach `metadata.tags` for matching objects.
- [ ] Update all `_append_search_result()` call sites in `search_world()`.
- [ ] Rerun:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_world_search.py -q
```

Expected: PASS.

---

### Task 3: Frontend and targeted verification

- [ ] Run existing frontend search panel tests:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldSearchPanel.test.tsx
```

- [ ] Run frontend build:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

- [ ] Run backend targeted regression tests for tags/search:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_world_search.py tests/test_tags.py -q
```

Expected: all commands pass.

---

### Task 4: Commit and merge

- [ ] Confirm branch is `feat/mvp27-search-tag-metadata`.
- [ ] Confirm changed files are limited to MVP27 docs, backend search tests, and backend search service.
- [ ] Commit with Conventional Commit message:

```bash
git add docs/superpowers/specs/2026-05-31-mvp27-search-tag-metadata-design.md docs/superpowers/plans/2026-05-31-mvp27-search-tag-metadata.md backend/tests/test_world_search.py backend/app/world/service.py
git commit -m "feat: show tags on world search results"
```

Commit body must include:

```text
Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```

- [ ] Fast-forward merge feature branch into `main` after verification.
- [ ] Do not push.
- [ ] Report branch, commit hash, verification results, merge status, and no push.

---

## Self-review

- No placeholders remain.
- Backend production code is only touched after a failing backend test.
- Frontend production code is not changed because existing result-chip UI already handles `metadata.tags`.
- The plan preserves inline execution, no dynamic workflows, no subagents, skip code-review subagent, commit feature branch, merge main after verification, and no push.
