# Archived Story Arc Write Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline execution only for this session. Do not use dynamic workflows, subagents, or code-review subagent. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reject story arc regeneration for archived worlds while keeping archived story arc reads available.

**Architecture:** Reuse existing world update governance by changing `generate_story_arc()` to load the world via `require_owned_world_for_update()` instead of read-only `require_owned_world()`. Add one focused regression test proving archived regeneration is blocked before it overwrites persisted arc data.

**Tech Stack:** FastAPI, SQLAlchemy, pytest, Vite/React verification.

---

## File Structure

- Modify: `backend/tests/test_story_arc.py`
  - Add one TDD regression for archived story arc regeneration.
- Modify: `backend/app/world/story_arc.py`
  - Import `require_owned_world_for_update`.
  - Use it in `generate_story_arc()` only.

---

### Task 1: Add archived story arc regression

**Files:**
- Modify: `backend/tests/test_story_arc.py`

- [ ] **Step 1: Write the failing test**

Add this test after `test_generate_story_arc_overwrites_existing_arc`:

```python
def test_archived_world_rejects_story_arc_regeneration_without_overwriting_existing_arc(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(story_arc_service, 'LLMClient', lambda: FakeStoryArcLLMClient('旧'))
    first = client.post(f'/worlds/{world_id}/story-arc', headers={'Authorization': f'Bearer {token}'})
    assert first.status_code == 200
    original_arc = first.json()['story_arc']

    archive_response = client.patch(f'/worlds/{world_id}/status', headers={'Authorization': f'Bearer {token}'}, json={'status': 'archived'})
    assert archive_response.status_code == 200

    monkeypatch.setattr(story_arc_service, 'LLMClient', lambda: FakeStoryArcLLMClient('新'))
    response = client.post(f'/worlds/{world_id}/story-arc', headers={'Authorization': f'Bearer {token}'})
    overview = client.get(f'/worlds/{world_id}/overview', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 409
    assert response.json()['detail'] == 'WORLD_ARCHIVED'
    assert overview.status_code == 200
    assert overview.json()['story_arc'] == original_arc

    db_session.expire_all()
    world = db_session.get(World, world_id)
    assert world.story_arc == original_arc
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_story_arc.py::test_archived_world_rejects_story_arc_regeneration_without_overwriting_existing_arc -q
```

Expected: FAIL because archived story arc regeneration currently returns `200` and overwrites `world.story_arc`.

---

### Task 2: Implement minimal story arc update guard

**Files:**
- Modify: `backend/app/world/story_arc.py`

- [ ] **Step 1: Import update guard**

Change imports from:

```python
from app.world.service import count_approved_chapters, require_owned_world
```

to:

```python
from app.world.governance import require_owned_world_for_update
from app.world.service import count_approved_chapters, require_owned_world
```

- [ ] **Step 2: Guard persistent story arc generation**

Change `generate_story_arc()` from:

```python
def generate_story_arc(db: Session, user: User, world_id: int, llm_client: LLMClient | None = None) -> dict:
    world = require_owned_world(db, user, world_id)
```

to:

```python
def generate_story_arc(db: Session, user: User, world_id: int, llm_client: LLMClient | None = None) -> dict:
    world = require_owned_world_for_update(db, user, world_id)
```

Do not change `suggest_chapter_goal()`.

- [ ] **Step 3: Run focused test**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_story_arc.py::test_archived_world_rejects_story_arc_regeneration_without_overwriting_existing_arc -q
```

Expected: PASS.

---

### Task 3: Verify and commit

- [ ] **Step 1: Run story arc backend suite**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_story_arc.py -q
```

Expected: all story arc tests pass.

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

- [ ] **Step 4: Check untracked files and diff hygiene**

```bash
cd /opt/WorldSim-Writer && git status --short && git diff --check
```

Expected: no whitespace errors. Preserve unrelated untracked files, especially `backend/worldsim-dev.db`.

- [ ] **Step 5: Stage relevant files only and commit**

```bash
cd /opt/WorldSim-Writer && git add backend/app/world/story_arc.py backend/tests/test_story_arc.py docs/superpowers/specs/2026-06-01-archived-story-arc-write-guard-design.md docs/superpowers/plans/2026-06-01-archived-story-arc-write-guard.md && git commit -m "fix: reject archived story arc writes"
```

Expected: commit created. Do not push. Do not merge.
