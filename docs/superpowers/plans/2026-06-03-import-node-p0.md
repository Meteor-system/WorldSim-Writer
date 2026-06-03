# Import Node P0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This session must execute inline because the user explicitly prohibited subagents.

**Goal:** Build the P0 import/material ingestion node that previews single-file or pasted story material, classifies candidate assets, detects basic conflicts, and confirms candidate assets without mutating formal canon.

**Architecture:** Add a focused `import_node` backend domain with models, schemas, service, router, and migration. Add a frontend `WorldImportPanel` connected through typed API client functions and mounted in the world workspace. Keep preview side-effect-free; confirmation writes only import batches, candidate assets, and an audit `EventLog` at the current world version.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic, pytest, React, TypeScript, Vitest, React Testing Library.

---

## File Structure

- Create `backend/app/import_node/__init__.py`: package marker.
- Create `backend/app/import_node/models.py`: `ImportBatch` and `ImportCandidateAsset` tables.
- Create `backend/app/import_node/schemas.py`: request and response schemas for preview, confirm, and list.
- Create `backend/app/import_node/service.py`: deterministic cleaning, classification, conflict detection, confirmation write, list batches.
- Create `backend/app/import_node/router.py`: `/worlds/{world_id}/imports/*` endpoints.
- Modify `backend/app/core/database.py`: import import-node models.
- Modify `backend/app/api/router.py`: include import-node router.
- Create `backend/alembic/versions/0013_add_import_node.py`: persistent import batch/candidate tables.
- Create `backend/tests/test_import_node.py`: backend TDD tests.
- Modify `frontend/src/api/types.ts`: import-node request/response types.
- Modify `frontend/src/api/client.ts`: `previewWorldImport`, `confirmWorldImport`, `listWorldImports`.
- Create `frontend/src/world/WorldImportPanel.tsx`: import UI.
- Create `frontend/src/world/WorldImportPanel.test.tsx`: frontend TDD tests.
- Modify `frontend/src/world/WorldPage.tsx`: mount panel in tools/workspace area.
- Modify `WorldSim-Writer.md`: keep existing 2.7.2 docs change in this branch.

---

## Task 1: Backend RED tests

**Files:**
- Create: `backend/tests/test_import_node.py`

- [ ] **Step 1: Write failing backend tests**

Create tests that assert:

```python
from sqlalchemy import select

from app.event.models import EventLog
from app.import_node.models import ImportBatch, ImportCandidateAsset
from app.world.models import World


def auth_headers(token: str) -> dict[str, str]:
    return {'Authorization': f'Bearer {token}'}


def register(client, email: str) -> str:
    return client.post('/auth/register', json={'email': email, 'password': 'strongpass123'}).json()['access_token']


def create_sample_world(client, token: str) -> dict:
    response = client.post('/worlds/from-template', headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def test_import_preview_classifies_material_and_reports_conflicts(client):
    token = register(client, 'import-preview@example.com')
    world = create_sample_world(client, token)

    response = client.post(
        f"/worlds/{world['id']}/imports/preview",
        headers=auth_headers(token),
        json={
            'source_type': 'markdown',
            'source_title': '旧设定.md',
            'content': '# 设定\n规则：黑水城所有密探必须隐藏真实姓名。\n\n角色：林夜：黑水城剑修，追查湿信。\n\n灵感：雨巷里有人递来一封湿透的信。',
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['asset_counts']['canon'] >= 1
    assert payload['asset_counts']['character'] >= 1
    assert payload['asset_counts']['inspiration'] >= 1
    assert {asset['asset_pool'] for asset in payload['assets']} == {'canon', 'character', 'inspiration'}
    assert any(conflict['category'] in {'canon_overlap', 'character_duplicate'} for conflict in payload['conflicts'])


def test_import_confirm_writes_candidates_and_audit_without_mutating_canon_or_world_version(client, db_session):
    token = register(client, 'import-confirm@example.com')
    world_payload = create_sample_world(client, token)
    original_world = db_session.get(World, world_payload['id'])
    original_canon = original_world.truth_canon
    original_version = original_world.world_version

    preview = client.post(
        f"/worlds/{world_payload['id']}/imports/preview",
        headers=auth_headers(token),
        json={
            'source_type': 'txt',
            'source_title': '灵感.txt',
            'content': '设定：黑水城城墙下埋着旧王朝的骨印。\n角色：沈微霜：密探，擅长伪装。\n灵感：雨夜审讯从一盏坏灯开始。',
        },
    ).json()

    response = client.post(
        f"/worlds/{world_payload['id']}/imports/confirm",
        headers=auth_headers(token),
        json={
            'source_type': 'txt',
            'source_title': '灵感.txt',
            'content': '设定：黑水城城墙下埋着旧王朝的骨印。\n角色：沈微霜：密探，擅长伪装。\n灵感：雨夜审讯从一盏坏灯开始。',
            'assets': preview['assets'],
            'conflicts': preview['conflicts'],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['batch']['status'] == 'confirmed'
    assert payload['batch']['asset_counts']['canon'] >= 1
    assert len(payload['assets']) == len(preview['assets'])

    db_session.expire_all()
    world = db_session.get(World, world_payload['id'])
    assert world.truth_canon == original_canon
    assert world.world_version == original_version

    batch = db_session.get(ImportBatch, payload['batch']['id'])
    assert batch is not None
    candidates = list(db_session.scalars(select(ImportCandidateAsset).where(ImportCandidateAsset.batch_id == batch.id)))
    assert len(candidates) == len(preview['assets'])
    assert all(candidate.status == 'candidate' for candidate in candidates)

    event = db_session.scalar(select(EventLog).where(EventLog.world_id == world.id).where(EventLog.event_type == 'material_import_confirmed'))
    assert event is not None
    assert event.source_type == 'import_node'
    assert event.world_version_before == original_version
    assert event.world_version_after == original_version


def test_import_list_returns_recent_batches_with_candidates(client):
    token = register(client, 'import-list@example.com')
    world = create_sample_world(client, token)
    preview = client.post(
        f"/worlds/{world['id']}/imports/preview",
        headers=auth_headers(token),
        json={'source_type': 'pasted_text', 'source_title': '片段', 'content': '灵感：城门口出现第二个月亮。'},
    ).json()
    client.post(
        f"/worlds/{world['id']}/imports/confirm",
        headers=auth_headers(token),
        json={'source_type': 'pasted_text', 'source_title': '片段', 'content': '灵感：城门口出现第二个月亮。', 'assets': preview['assets'], 'conflicts': preview['conflicts']},
    )

    response = client.get(f"/worlds/{world['id']}/imports", headers=auth_headers(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['world_id'] == world['id']
    assert payload['batches'][0]['source_title'] == '片段'
    assert payload['batches'][0]['assets'][0]['asset_pool'] == 'inspiration'


def test_non_owner_cannot_preview_or_confirm_import(client):
    owner_token = register(client, 'import-owner@example.com')
    other_token = register(client, 'import-other@example.com')
    world = create_sample_world(client, owner_token)

    preview = client.post(
        f"/worlds/{world['id']}/imports/preview",
        headers=auth_headers(other_token),
        json={'source_type': 'txt', 'source_title': 'x.txt', 'content': '灵感：越权导入。'},
    )
    confirm = client.post(
        f"/worlds/{world['id']}/imports/confirm",
        headers=auth_headers(other_token),
        json={'source_type': 'txt', 'source_title': 'x.txt', 'content': '灵感：越权导入。', 'assets': [], 'conflicts': []},
    )

    assert preview.status_code == 403
    assert confirm.status_code == 403
```

- [ ] **Step 2: Run backend RED tests**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_import_node.py -v'
```

Expected: fail because `app.import_node` and routes do not exist.

---

## Task 2: Backend GREEN implementation

**Files:**
- Create: `backend/app/import_node/__init__.py`
- Create: `backend/app/import_node/models.py`
- Create: `backend/app/import_node/schemas.py`
- Create: `backend/app/import_node/service.py`
- Create: `backend/app/import_node/router.py`
- Modify: `backend/app/core/database.py`
- Modify: `backend/app/api/router.py`
- Create: `backend/alembic/versions/0013_add_import_node.py`

- [ ] **Step 1: Implement import-node models**

Create `ImportBatch` and `ImportCandidateAsset` with JSONB fields and relationships.

- [ ] **Step 2: Implement schemas**

Add source-type validation for `pasted_text`, `markdown`, `txt`, asset-pool validation for `inspiration`, `character`, `canon`, and response models.

- [ ] **Step 3: Implement service**

Add:

- `preview_import(db, user, world_id, request)`
- `confirm_import(db, user, world_id, request)`
- `list_import_batches(db, user, world_id)`

Keep preview side-effect-free. Confirmation writes batch, candidates, and audit event only.

- [ ] **Step 4: Implement router and register it**

Add endpoints:

- `POST /worlds/{world_id}/imports/preview`
- `POST /worlds/{world_id}/imports/confirm`
- `GET /worlds/{world_id}/imports`

- [ ] **Step 5: Add Alembic migration**

Create tables matching the models with foreign keys to `worlds` and import batches.

- [ ] **Step 6: Run backend GREEN tests**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_import_node.py -v'
```

Expected: all tests in `test_import_node.py` pass.

---

## Task 3: Frontend RED tests

**Files:**
- Create: `frontend/src/world/WorldImportPanel.test.tsx`

- [ ] **Step 1: Write failing frontend tests**

Test that the panel:

- renders Chinese canon safety copy
- previews grouped assets and conflicts
- confirms assets and shows audit batch result

- [ ] **Step 2: Run frontend RED tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx
```

Expected: fail because component/API functions do not exist.

---

## Task 4: Frontend GREEN implementation

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/api/client.ts`
- Create: `frontend/src/world/WorldImportPanel.tsx`
- Modify: `frontend/src/world/WorldPage.tsx`

- [ ] **Step 1: Add API types and client functions**

Add types for import preview, confirm, batch list, conflicts, candidate assets. Add `previewWorldImport`, `confirmWorldImport`, and `listWorldImports`.

- [ ] **Step 2: Implement `WorldImportPanel`**

Provide Chinese UI copy and forms. Render preview groups and warnings. Confirm all preview assets in P0.

- [ ] **Step 3: Mount in `WorldPage.tsx`**

Place near existing tools panels without making it the primary chapter operation.

- [ ] **Step 4: Run frontend GREEN tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx
```

Expected: pass.

---

## Task 5: Verification, self-review, and commit

**Files:**
- All changed docs/backend/frontend files.

- [ ] **Step 1: Run key backend tests**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_import_node.py tests/test_world_routes.py tests/test_world_search.py -v'
```

- [ ] **Step 2: Run frontend tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test
```

- [ ] **Step 3: Run frontend build**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

- [ ] **Step 4: Run diff check**

Run:

```bash
git -C /opt/WorldSim-Writer diff --check
```

- [ ] **Step 5: Inline self-review**

Check:

- Preview endpoint has no database writes.
- Confirm endpoint does not mutate `truth_canon` or `world_version`.
- Candidate assets have source batch and `candidate` status.
- Audit event records same world version before/after.
- UI copy says imported materials enter candidate pools first.
- No dynamic workflows or subagents were used.

- [ ] **Step 6: Commit**

Run:

```bash
git -C /opt/WorldSim-Writer status --short --branch
git -C /opt/WorldSim-Writer add WorldSim-Writer.md docs/superpowers/specs/2026-06-03-import-node-p0-design.md docs/superpowers/plans/2026-06-03-import-node-p0.md backend frontend
git -C /opt/WorldSim-Writer commit -m "feat: add import node material ingestion" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
git -C /opt/WorldSim-Writer status --short --branch
```

Expected: commit created on `feat/import-node-p0`, no push, no merge.
