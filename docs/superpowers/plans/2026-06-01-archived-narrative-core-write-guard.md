# Archived Narrative Core Write Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This run explicitly forbids subagents and dynamic workflows, so execute inline with strict TDD.

**Goal:** Reject core narrative write operations while a world is archived.

**Architecture:** Add a small service-level archived-world guard in `app.narrative.service` and call it from core narrative write paths. Keep read-only approval inspection endpoints available.

**Tech Stack:** FastAPI, SQLAlchemy, pytest.

---

## File Structure

- Modify: `backend/tests/test_narrative_approval.py`
  - Add one regression test for archived-world core narrative write rejection.
- Modify: `backend/app/narrative/service.py`
  - Add `_ensure_world_is_active()` helper.
  - Guard `create_chapter_session()`, `create_chapter_draft()`, `reject_chapter()`, and `approve_chapter()`.
- Create: `docs/superpowers/specs/2026-06-01-archived-narrative-core-write-guard-design.md`
  - Design spec for this MVP.
- Create: `docs/superpowers/plans/2026-06-01-archived-narrative-core-write-guard.md`
  - This implementation plan.

---

### Task 1: Add RED regression test

**Files:**
- Modify: `backend/tests/test_narrative_approval.py`

- [ ] **Step 1: Add archived narrative write guard test**

Add this test near the existing draft/approval tests:

```python
def test_archived_world_rejects_core_narrative_writes_but_allows_review_reads(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    archive_response = client.patch(f'/worlds/{world_id}/status', headers={'Authorization': f'Bearer {token}'}, json={'status': 'archived'})
    assert archive_response.status_code == 200

    session_response = client.post(
        f'/worlds/{world_id}/chapters',
        json={'chapter_goal': '归档后开章'},
        headers={'Authorization': f'Bearer {token}'},
    )
    draft_response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '归档后草稿'},
        headers={'Authorization': f'Bearer {token}'},
    )
    approve_response = client.post(f"/chapters/{draft['chapter_id']}/approve", headers={'Authorization': f'Bearer {token}'})
    reject_response = client.post(
        f"/chapters/{draft['chapter_id']}/reject",
        json={'feedback': '归档后不应驳回'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert session_response.status_code == 409
    assert session_response.json()['detail'] == 'WORLD_ARCHIVED'
    assert draft_response.status_code == 409
    assert draft_response.json()['detail'] == 'WORLD_ARCHIVED'
    assert approve_response.status_code == 409
    assert approve_response.json()['detail'] == 'WORLD_ARCHIVED'
    assert reject_response.status_code == 409
    assert reject_response.json()['detail'] == 'WORLD_ARCHIVED'

    preview_response = client.get(f"/chapters/{draft['chapter_id']}/approval-preview", headers={'Authorization': f'Bearer {token}'})
    readiness_response = client.get(f"/chapters/{draft['chapter_id']}/approval-readiness", headers={'Authorization': f'Bearer {token}'})
    assert preview_response.status_code == 200
    assert readiness_response.status_code == 200

    db_session.expire_all()
    world = db_session.get(World, world_id)
    chapter = db_session.get(Chapter, draft['chapter_id'])
    assert world.world_version == 1
    assert chapter.status == 'reviewing'
```

- [ ] **Step 2: Run targeted RED test**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_narrative_approval.py::test_archived_world_rejects_core_narrative_writes_but_allows_review_reads -q
```

Expected: fail because archived narrative writes currently succeed.

---

### Task 2: Implement minimal GREEN

**Files:**
- Modify: `backend/app/narrative/service.py`

- [ ] **Step 1: Add helper**

Add near `_require_owned_chapter()`:

```python
def _ensure_world_is_active(world: World) -> None:
    if world.status == 'archived':
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='WORLD_ARCHIVED')
```

- [ ] **Step 2: Guard world-scoped narrative creation**

Call `_ensure_world_is_active(world)` in `create_chapter_session()` and `create_chapter_draft()` after `require_owned_world()`.

- [ ] **Step 3: Guard reject**

In `reject_chapter()`, load the chapter's world after `_require_owned_chapter()` and call `_ensure_world_is_active(world)` before changing chapter/draft state.

- [ ] **Step 4: Guard approve**

In `approve_chapter()`, call `_ensure_world_is_active(world)` after the locked world ownership check and before loading/applying the draft.

- [ ] **Step 5: Run targeted GREEN test**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_narrative_approval.py::test_archived_world_rejects_core_narrative_writes_but_allows_review_reads -q
```

Expected: pass.

---

### Task 3: Verification and commit

**Files:**
- Verify changed docs, tests, and implementation.

- [ ] **Step 1: Run relevant backend narrative tests**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_narrative_approval.py tests/test_narrative_pipeline.py -q
```

Expected: pass.

- [ ] **Step 2: Run frontend build**

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 3: Run relevant frontend archive regression tests**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: pass.

- [ ] **Step 4: Run diff check and status review**

```bash
cd /opt/WorldSim-Writer && git diff --check && git status --short && git diff --stat
```

Expected: no whitespace errors; do not stage unrelated `.hermes/plans/*` or `backend/worldsim-dev.db`.

- [ ] **Step 5: Commit relevant files only**

```bash
cd /opt/WorldSim-Writer && git add docs/superpowers/specs/2026-06-01-archived-narrative-core-write-guard-design.md docs/superpowers/plans/2026-06-01-archived-narrative-core-write-guard.md backend/tests/test_narrative_approval.py backend/app/narrative/service.py && git commit -m "fix: reject archived narrative writes"
```

Expected: commit succeeds. Do not push and do not merge.
