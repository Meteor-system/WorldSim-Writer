# Archived Tags Write Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline execution only for this session. Do not use dynamic workflows, subagents, or code-review subagent. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject tag catalog and tag-assignment writes for archived worlds while keeping tag reads available.

**Architecture:** Add a service-level archive guard in `app.tags.service` and call it from mutating tag functions immediately after ownership lookup. Read functions keep using `require_owned_world()` without the update guard.

**Tech Stack:** FastAPI, SQLAlchemy, pytest, Vite/React verification.

---

## File Structure

- Modify: `backend/tests/test_tags.py`
  - Add one TDD regression covering archived tag catalog writes, assignment writes, and read-only tag inspection.
- Modify: `backend/app/tags/service.py`
  - Add `_ensure_world_is_active()` helper.
  - Call it from `create_tag`, `update_tag`, `merge_tag`, `delete_tag`, `assign_tag`, `bulk_assign_tag`, and `unassign_tag`.

---

### Task 1: Add archived tag write regression

**Files:**
- Modify: `backend/tests/test_tags.py`

- [ ] **Step 1: Write the failing test**

Add this test before `test_tag_endpoints_require_login`:

```python
def test_archived_world_rejects_tag_writes_but_allows_reads(client):
    token = register(client, 'tags-archived@example.com')
    world = create_world(client, token)
    overview = client.get(f"/worlds/{world['id']}/overview", headers=auth(token)).json()
    character_id = overview['characters'][0]['id']
    first = client.post(f"/worlds/{world['id']}/tags", headers=auth(token), json={'name': '主线'}).json()
    second = client.post(f"/worlds/{world['id']}/tags", headers=auth(token), json={'name': '支线'}).json()
    assign_before_archive = client.post(
        f"/worlds/{world['id']}/tags/{first['id']}/objects",
        headers=auth(token),
        json={'object_type': 'character', 'object_id': character_id},
    )
    assert assign_before_archive.status_code == 200

    archive_response = client.patch(f"/worlds/{world['id']}/status", headers=auth(token), json={'status': 'archived'})
    assert archive_response.status_code == 200

    create_response = client.post(f"/worlds/{world['id']}/tags", headers=auth(token), json={'name': '归档后新标签'})
    update_response = client.patch(
        f"/worlds/{world['id']}/tags/{first['id']}",
        headers=auth(token),
        json={'name': '归档后改名'},
    )
    merge_response = client.post(
        f"/worlds/{world['id']}/tags/{first['id']}/merge",
        headers=auth(token),
        json={'target_tag_id': second['id']},
    )
    assign_response = client.post(
        f"/worlds/{world['id']}/tags/{second['id']}/objects",
        headers=auth(token),
        json={'object_type': 'character', 'object_id': character_id},
    )
    bulk_assign_response = client.post(
        f"/worlds/{world['id']}/tags/{second['id']}/objects/bulk",
        headers=auth(token),
        json={'object_type': 'character', 'object_ids': [character_id]},
    )
    unassign_response = client.delete(
        f"/worlds/{world['id']}/tags/{first['id']}/objects/character/{character_id}",
        headers=auth(token),
    )
    delete_response = client.delete(f"/worlds/{world['id']}/tags/{first['id']}", headers=auth(token))

    for response in (
        create_response,
        update_response,
        merge_response,
        assign_response,
        bulk_assign_response,
        unassign_response,
        delete_response,
    ):
        assert response.status_code == 409
        assert response.json()['detail'] == 'WORLD_ARCHIVED'

    list_response = client.get(f"/worlds/{world['id']}/tags", headers=auth(token))
    detail_response = client.get(f"/worlds/{world['id']}/tags/{first['id']}", headers=auth(token))

    assert list_response.status_code == 200
    assert detail_response.status_code == 200
    tags = list_response.json()['tags']
    assert [tag['name'] for tag in tags] == ['主线', '支线']
    assert detail_response.json()['tag']['assignment_count'] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_tags.py::test_archived_world_rejects_tag_writes_but_allows_reads -q
```

Expected: FAIL because at least one archived tag write returns success instead of `409 WORLD_ARCHIVED`.

---

### Task 2: Implement minimal tag archive guard

**Files:**
- Modify: `backend/app/tags/service.py`

- [ ] **Step 1: Add helper near `_require_tag`**

```python
def _ensure_world_is_active(world) -> None:
    if world.status == 'archived':
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='WORLD_ARCHIVED')
```

- [ ] **Step 2: Guard every mutating tag service**

Call `_ensure_world_is_active(world)` immediately after each `world = require_owned_world(...)` line in:

- `create_tag`
- `update_tag`
- `merge_tag`
- `delete_tag`
- `assign_tag`
- `bulk_assign_tag`
- `unassign_tag`

Do not call it from `list_tags()` or `get_tag_detail()`.

- [ ] **Step 3: Run focused test**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_tags.py::test_archived_world_rejects_tag_writes_but_allows_reads -q
```

Expected: PASS.

---

### Task 3: Verify and commit

- [ ] **Step 1: Run tag suite**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_tags.py -q
```

Expected: all tag tests pass.

- [ ] **Step 2: Run frontend build**

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 3: Run WorldPage targeted tests**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: tests pass.

- [ ] **Step 4: Check diff hygiene**

```bash
cd /opt/WorldSim-Writer && git diff --check
```

Expected: no output.

- [ ] **Step 5: Commit relevant files only**

```bash
cd /opt/WorldSim-Writer && git add backend/app/tags/service.py backend/tests/test_tags.py docs/superpowers/specs/2026-06-01-archived-tags-write-guard-design.md docs/superpowers/plans/2026-06-01-archived-tags-write-guard.md && git commit -m "fix: reject archived tag writes"
```

Expected: commit created. Do not push. Do not merge. Preserve unrelated untracked files.
