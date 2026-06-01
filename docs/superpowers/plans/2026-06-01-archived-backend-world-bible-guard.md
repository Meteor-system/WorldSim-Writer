# Archived Backend World Bible Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This run explicitly forbids subagents and dynamic workflows, so execute inline with strict TDD.

**Goal:** Reject World Bible API write operations while a world is archived.

**Architecture:** Backend-only governance guard in `require_owned_world_for_update()`, plus targeted regression tests for character, relation, and foreshadow write endpoints.

**Tech Stack:** FastAPI, SQLAlchemy, pytest.

---

## File Structure

- Modify: `backend/tests/test_character_crud.py`
  - Add archived-world write guard regression test for character endpoints.
- Modify: `backend/tests/test_relation_crud.py`
  - Add archived-world write guard regression test for relation endpoints.
- Modify: `backend/tests/test_foreshadow_crud.py`
  - Add archived-world write guard regression test for foreshadow endpoints.
- Modify: `backend/app/world/governance.py`
  - Add the archived-world update guard.
- Create: `docs/superpowers/specs/2026-06-01-archived-backend-world-bible-guard-design.md`
  - Design spec for this MVP.
- Create: `docs/superpowers/plans/2026-06-01-archived-backend-world-bible-guard.md`
  - This implementation plan.

---

### Task 1: Add RED tests

**Files:**
- Modify: `backend/tests/test_character_crud.py`
- Modify: `backend/tests/test_relation_crud.py`
- Modify: `backend/tests/test_foreshadow_crud.py`

- [ ] **Step 1: Add character archived-write guard test**

Add to `backend/tests/test_character_crud.py`:

```python
def test_archived_world_rejects_character_writes_but_allows_reads(client):
    token = register(client)
    world_id = create_world(client, token)
    existing = client.get(f'/worlds/{world_id}/characters', headers=auth(token)).json()[0]

    archive_response = client.patch(f'/worlds/{world_id}/status', headers=auth(token), json={'status': 'archived'})
    assert archive_response.status_code == 200

    create_response = client.post(
        f'/worlds/{world_id}/characters',
        headers=auth(token),
        json={'name': '归档后角色', 'role_type': 'supporting'},
    )
    update_response = client.put(
        f"/characters/{existing['id']}",
        headers=auth(token),
        json={'name': '不应修改'},
    )
    delete_response = client.delete(f"/characters/{existing['id']}", headers=auth(token))

    assert create_response.status_code == 409
    assert create_response.json()['detail'] == 'WORLD_ARCHIVED'
    assert update_response.status_code == 409
    assert update_response.json()['detail'] == 'WORLD_ARCHIVED'
    assert delete_response.status_code == 409
    assert delete_response.json()['detail'] == 'WORLD_ARCHIVED'

    list_response = client.get(f'/worlds/{world_id}/characters', headers=auth(token))
    get_response = client.get(f"/characters/{existing['id']}", headers=auth(token))
    assert list_response.status_code == 200
    assert get_response.status_code == 200
```

- [ ] **Step 2: Add relation archived-write guard test**

Add to `backend/tests/test_relation_crud.py`:

```python
def test_archived_world_rejects_relation_writes_but_allows_reads(client, db_session):
    token = register(client)
    world_id = create_world(client, token)
    source_id, target_id = character_ids(client, token, world_id)[:2]
    existing_id = db_session.scalar(select(CharacterRelation.id).where(CharacterRelation.world_id == world_id))

    archive_response = client.patch(f'/worlds/{world_id}/status', headers=auth(token), json={'status': 'archived'})
    assert archive_response.status_code == 200

    create_response = client.post(
        f'/worlds/{world_id}/relations',
        headers=auth(token),
        json={'source_character_id': source_id, 'target_character_id': target_id, 'relation_type': 'archived_link'},
    )
    update_response = client.put(
        f'/relations/{existing_id}',
        headers=auth(token),
        json={'relation_type': '不应修改'},
    )
    delete_response = client.delete(f'/relations/{existing_id}', headers=auth(token))

    assert create_response.status_code == 409
    assert create_response.json()['detail'] == 'WORLD_ARCHIVED'
    assert update_response.status_code == 409
    assert update_response.json()['detail'] == 'WORLD_ARCHIVED'
    assert delete_response.status_code == 409
    assert delete_response.json()['detail'] == 'WORLD_ARCHIVED'

    list_response = client.get(f'/worlds/{world_id}/relations', headers=auth(token))
    get_response = client.get(f'/relations/{existing_id}', headers=auth(token))
    assert list_response.status_code == 200
    assert get_response.status_code == 200
```

- [ ] **Step 3: Add foreshadow archived-write guard test**

Add to `backend/tests/test_foreshadow_crud.py`:

```python
def test_archived_world_rejects_foreshadow_writes_but_allows_reads(client):
    token = register(client)
    world_id = create_world(client, token)
    existing = create_foreshadow(client, token, world_id)

    archive_response = client.patch(f'/worlds/{world_id}/status', headers=auth(token), json={'status': 'archived'})
    assert archive_response.status_code == 200

    create_response = client.post(
        f'/worlds/{world_id}/foreshadows',
        headers=auth(token),
        json={'title': '归档后伏笔', 'description': '不应创建。', 'foreshadow_type': 'plot'},
    )
    update_response = client.put(
        f"/foreshadows/{existing['id']}",
        headers=auth(token),
        json={'status': 'advanced'},
    )
    delete_response = client.delete(f"/foreshadows/{existing['id']}", headers=auth(token))

    assert create_response.status_code == 409
    assert create_response.json()['detail'] == 'WORLD_ARCHIVED'
    assert update_response.status_code == 409
    assert update_response.json()['detail'] == 'WORLD_ARCHIVED'
    assert delete_response.status_code == 409
    assert delete_response.json()['detail'] == 'WORLD_ARCHIVED'

    list_response = client.get(f'/worlds/{world_id}/foreshadows', headers=auth(token))
    get_response = client.get(f"/foreshadows/{existing['id']}", headers=auth(token))
    assert list_response.status_code == 200
    assert get_response.status_code == 200
```

- [ ] **Step 4: Run targeted tests and verify RED**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 conda run -n worldsim pytest tests/test_character_crud.py tests/test_relation_crud.py tests/test_foreshadow_crud.py -q
```

Expected: the three new tests fail because writes currently succeed on archived worlds.

---

### Task 2: Implement minimal GREEN

**Files:**
- Modify: `backend/app/world/governance.py`

- [ ] **Step 1: Add archived guard to `require_owned_world_for_update()`**

Change:

```python
def require_owned_world_for_update(db: Session, user: User, world_id: int) -> World:
    world = db.scalar(select(World).where(World.id == world_id).with_for_update())
    if world is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    if world.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='FORBIDDEN')
    return world
```

To:

```python
def require_owned_world_for_update(db: Session, user: User, world_id: int) -> World:
    world = db.scalar(select(World).where(World.id == world_id).with_for_update())
    if world is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    if world.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='FORBIDDEN')
    if world.status == 'archived':
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='WORLD_ARCHIVED')
    return world
```

- [ ] **Step 2: Run targeted tests and verify GREEN**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 conda run -n worldsim pytest tests/test_character_crud.py tests/test_relation_crud.py tests/test_foreshadow_crud.py -q
```

Expected: targeted backend tests pass.

---

### Task 3: Verification and commit

**Files:**
- Verify changed docs, tests, and implementation.

- [ ] **Step 1: Run frontend build**

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: build succeeds; frontend not changed in this slice, but user requested build verification.

- [ ] **Step 2: Run relevant frontend targeted tests**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: existing archive UI tests remain green.

- [ ] **Step 3: Run diff check and status review**

```bash
cd /opt/WorldSim-Writer && git diff --check && git status --short && git diff --stat
```

Expected: no whitespace errors; do not stage `backend/worldsim-dev.db` or unrelated `.hermes/plans/*`.

- [ ] **Step 4: Commit relevant files only**

```bash
cd /opt/WorldSim-Writer && git add docs/superpowers/specs/2026-06-01-archived-backend-world-bible-guard-design.md docs/superpowers/plans/2026-06-01-archived-backend-world-bible-guard.md backend/tests/test_character_crud.py backend/tests/test_relation_crud.py backend/tests/test_foreshadow_crud.py backend/app/world/governance.py && git commit -m "fix: reject archived world bible writes"
```

Expected: commit succeeds. Do not push and do not merge.
