# MVP14 Custom World / Genre Template Creation 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans inline for this repository because the user explicitly forbids subagents and dynamic workflows. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete custom world creation so users can create an original world from the UI, preserve one-click sample creation, and initialize auditable canon state.

**Architecture:** Harden the existing `POST /worlds` endpoint and `WorldCreationForm` rather than adding parallel APIs. Add backend creation governance (`WORLD_CREATED` event), stricter starter asset validation, a frontend `createSampleWorld()` helper, and creation-form tests for custom and sample paths.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, React, TypeScript, Vite, Vitest, Testing Library.

---

## File map

- Modify `backend/app/world/schemas.py`
  - Add relation intensity bounds (`1..5`).
  - Keep existing starter payload shape.
- Modify `backend/app/world/service.py`
  - Add relation self-reference validation.
  - Add pre-commit `WORLD_CREATED` EventLog for all world creation, including sample worlds.
- Modify `backend/tests/test_world_template.py`
  - Add RED tests for `WORLD_CREATED`, event listing, export timeline compatibility, relation self-reference, invalid intensity/status/urgency, and custom-world draft smoke.
  - Update existing overview expectations to account for `WORLD_CREATED` recent event.
- Modify `frontend/src/api/client.ts`
  - Add `createSampleWorld()` helper for `POST /worlds/from-template`.
- Modify `frontend/src/api/client.test.ts`
  - Add API helper coverage for custom and sample world creation.
- Modify `frontend/src/world/WorldCreationForm.tsx`
  - Add `onCreateSample` prop and one-click sample button.
- Create `frontend/src/world/WorldCreationForm.test.tsx`
  - Test custom payload submission and sample shortcut.
- Modify `frontend/src/world/WorldPage.tsx`
  - Wire sample shortcut to `createSampleWorld()`, then load overview.
- Modify `frontend/src/world/WorldPage.test.tsx`
  - Mock `createWorld` and `createSampleWorld`; test custom creation error display and sample shortcut success.

## Task 1: Backend creation governance and validation

**Files:**
- Modify: `backend/tests/test_world_template.py`
- Modify: `backend/app/world/schemas.py`
- Modify: `backend/app/world/service.py`

- [ ] **Step 1: Write failing tests**

Add tests to `backend/tests/test_world_template.py`:

```python
def test_create_custom_world_records_world_created_event_and_export_timeline(client):
    token = register(client, 'world-created@example.com')

    create_response = client.post('/worlds', headers=auth(token), json=custom_world_payload())

    assert create_response.status_code == 200
    world_id = create_response.json()['id']
    overview = client.get(f'/worlds/{world_id}/overview', headers=auth(token)).json()
    assert overview['recent_events'][0]['event_type'] == 'WORLD_CREATED'
    assert overview['recent_events'][0]['source_type'] == 'world_creation'
    assert overview['recent_events'][0]['world_version_before'] == 0
    assert overview['recent_events'][0]['world_version_after'] == 1
    assert overview['recent_events'][0]['payload']['starter_counts'] == {
        'characters': 2,
        'relations': 1,
        'foreshadows': 1,
    }

    events = client.get(f'/worlds/{world_id}/events', headers=auth(token)).json()
    assert events['total'] == 1
    assert events['items'][0]['event_type'] == 'WORLD_CREATED'

    export = client.post(f'/worlds/{world_id}/export/markdown', headers=auth(token)).json()
    timeline = next(file for file in export['files'] if file['path'] == 'Timeline.md')['content']
    assert 'WORLD_CREATED' in timeline
    assert '0 → 1' in timeline
```

Add validation tests:

```python
def test_create_custom_world_rejects_relation_self_reference(client):
    token = register(client, 'world-self-relation@example.com')
    payload = custom_world_payload()
    payload['starter_assets']['relations'][0]['target_index'] = 0

    response = client.post('/worlds', headers=auth(token), json=payload)

    assert response.status_code == 422
    assert response.json()['detail'] == 'INVALID_RELATION_SELF_REFERENCE'
    assert client.get('/worlds', headers=auth(token)).json() == []


def test_create_custom_world_rejects_invalid_relation_intensity(client):
    token = register(client, 'world-relation-intensity@example.com')
    payload = custom_world_payload()
    payload['starter_assets']['relations'][0]['intensity'] = 9

    response = client.post('/worlds', headers=auth(token), json=payload)

    assert response.status_code == 422
    assert client.get('/worlds', headers=auth(token)).json() == []


def test_create_custom_world_rejects_invalid_foreshadow_status(client):
    token = register(client, 'world-foreshadow-status@example.com')
    payload = custom_world_payload()
    payload['starter_assets']['foreshadows'][0]['status'] = 'partially_resolved'

    response = client.post('/worlds', headers=auth(token), json=payload)

    assert response.status_code == 400
    assert response.json()['detail'] == 'INVALID_STATUS'
    assert client.get('/worlds', headers=auth(token)).json() == []
```

Update existing expectations where overview had no events:

```python
assert [event['event_type'] for event in overview['recent_events']] == ['WORLD_CREATED']
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_world_template.py::test_create_custom_world_records_world_created_event_and_export_timeline tests/test_world_template.py::test_create_custom_world_rejects_relation_self_reference tests/test_world_template.py::test_create_custom_world_rejects_invalid_relation_intensity tests/test_world_template.py::test_create_custom_world_rejects_invalid_foreshadow_status -v
```

Expected: FAIL because `WORLD_CREATED` is missing, relation self-reference is accepted, and relation intensity is not bounded.

- [ ] **Step 3: Implement backend validation and event**

In `backend/app/world/schemas.py`, change:

```python
intensity: int = 1
```

to:

```python
intensity: int = Field(default=1, ge=1, le=5)
```

In `backend/app/world/service.py`:

- import `uuid4`;
- in `_validate_starter_asset_indexes()`, reject self-reference with `INVALID_RELATION_SELF_REFERENCE`;
- after `refresh_world_projection(db, world)` and before `db.commit()`, add a `WORLD_CREATED` EventLog.

Use payload:

```python
{
    'world_id': world.id,
    'title': world.title,
    'genre_template': world.genre_template,
    'starter_counts': {
        'characters': len(characters),
        'relations': len(data.starter_assets.relations),
        'foreshadows': len(foreshadows),
    },
}
```

- [ ] **Step 4: Run backend tests to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_world_template.py tests/test_snapshot_export.py -v
```

Expected: PASS.

## Task 2: Backend custom world generation compatibility

**Files:**
- Modify: `backend/tests/test_world_template.py`

- [ ] **Step 1: Write failing compatibility test if needed**

Add a fake LLM smoke test to `backend/tests/test_world_template.py`:

```python
from app.llm.schemas import ChapterGeneration
from app.narrative import service as narrative_service


class CustomWorldLLMClient:
    def generate_chapter(self, messages):
        return ChapterGeneration(
            title='第一章 灯塔低鸣',
            draft_content='许砚听见跃迁灯塔深处传来低鸣。',
            context_summary='许砚开始追查灯塔异常。',
            review_hints=['确认灯塔异常是否推进黑匣子脉冲伏笔。'],
            proposed_character_changes=[],
            proposed_foreshadow_changes=[],
        )


def test_custom_world_can_create_reviewing_draft(client, monkeypatch):
    token = register(client, 'world-draft@example.com')
    world = client.post('/worlds', headers=auth(token), json=custom_world_payload()).json()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: CustomWorldLLMClient())

    response = client.post(
        f"/worlds/{world['id']}/chapters/draft",
        headers=auth(token),
        json={'chapter_goal': '让许砚第一次听见灯塔低鸣'},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'reviewing'
    assert payload['title'] == '第一章 灯塔低鸣'
    assert payload['source_world_version'] == 1
```

- [ ] **Step 2: Run test**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_world_template.py::test_custom_world_can_create_reviewing_draft -v
```

Expected: PASS if existing generation compatibility already works. If it fails, fix only the missing compatibility issue.

## Task 3: Frontend sample shortcut and creation tests

**Files:**
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/api/client.test.ts`
- Modify: `frontend/src/world/WorldCreationForm.tsx`
- Create: `frontend/src/world/WorldCreationForm.test.tsx`
- Modify: `frontend/src/world/WorldPage.tsx`
- Modify: `frontend/src/world/WorldPage.test.tsx`

- [ ] **Step 1: Write frontend API RED test**

In `frontend/src/api/client.test.ts`, import `createWorld` and `createSampleWorld`, then add a test asserting:

```ts
await createWorld(payload);
await createSampleWorld();
expect(fetchMock).toHaveBeenNthCalledWith(1, 'http://localhost:8000/worlds', expect.objectContaining({ method: 'POST' }));
expect(fetchMock).toHaveBeenNthCalledWith(2, 'http://localhost:8000/worlds/from-template', expect.objectContaining({ method: 'POST', body: '{}' }));
```

Expected RED: `createSampleWorld` is not exported.

- [ ] **Step 2: Implement API helper**

In `frontend/src/api/client.ts`, add:

```ts
export function createSampleWorld() {
  return apiRequest<{ id: number }>('/worlds/from-template', {
    method: 'POST',
    body: '{}',
  });
}
```

- [ ] **Step 3: Write `WorldCreationForm` RED tests**

Create `frontend/src/world/WorldCreationForm.test.tsx` with tests that:

- render the form;
- edit world title to `自定义群星边境`;
- click `添加关系` and `添加伏笔`;
- submit and assert `onCreate` received starter characters/relations/foreshadows;
- click `创建内置示例世界` and assert `onCreateSample` was called.

Expected RED: `onCreateSample` prop/button does not exist.

- [ ] **Step 4: Implement form sample shortcut**

In `WorldCreationForm.tsx`:

- update props to include `onCreateSample: () => Promise<void>`;
- add a secondary button labelled `创建内置示例世界`;
- ensure it uses `type="button"` and calls `onCreateSample`.

- [ ] **Step 5: Wire WorldPage**

In `WorldPage.tsx`:

- import `createSampleWorld`;
- add `submitSampleWorld()`;
- pass `onCreateSample={submitSampleWorld}` to `WorldCreationForm`.

- [ ] **Step 6: Update WorldPage tests**

In `WorldPage.test.tsx`:

- mock `createWorld` and `createSampleWorld`;
- add a test where `/worlds` returns `[]`, user clicks `创建内置示例世界`, and World overview loads;
- add a test where custom creation rejects with `INVALID_CHARACTER_INDEX` and error is shown.

- [ ] **Step 7: Run frontend tests to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts src/world/WorldCreationForm.test.tsx src/world/WorldPage.test.tsx
```

Expected: PASS.

## Task 4: Full targeted verification, commit, and merge

**Files:** all files modified above plus docs.

- [ ] **Step 1: Create feature branch before implementation if not already on it**

Run:

```bash
git switch -c feat/mvp14-custom-world-creation
```

Expected: branch created from current `main` with uncommitted spec/plan changes carried over.

- [ ] **Step 2: Run backend targeted tests**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_world_template.py tests/test_narrative_pipeline.py tests/test_narrative_approval.py tests/test_foreshadow_crud.py tests/test_snapshot_export.py -v
```

Expected: PASS.

- [ ] **Step 3: Run frontend targeted tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts src/world/WorldCreationForm.test.tsx src/world/WorldPage.test.tsx src/world/WorldArchivePanel.test.tsx src/components/ForeshadowManager.test.tsx
```

Expected: PASS.

- [ ] **Step 4: Run frontend build**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: PASS.

- [ ] **Step 5: Inline self-review**

Check:

- no Workflow/subagent/code-review subagent used;
- sample world shortcut still works;
- custom world creation initializes formal projection and `WORLD_CREATED` event;
- invalid references are rejected before a world is listed;
- studio draft creation works from custom world;
- foreshadow ledger/export compatibility remains covered.

- [ ] **Step 6: Commit**

Run:

```bash
git add docs/superpowers/specs/2026-05-31-mvp14-custom-world-creation-design.md docs/superpowers/plans/2026-05-31-mvp14-custom-world-creation.md backend/app/world/schemas.py backend/app/world/service.py backend/tests/test_world_template.py frontend/src/api/client.ts frontend/src/api/client.test.ts frontend/src/world/WorldCreationForm.tsx frontend/src/world/WorldCreationForm.test.tsx frontend/src/world/WorldPage.tsx frontend/src/world/WorldPage.test.tsx
git commit -m "feat: complete custom world creation" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 7: Merge back to main without pushing**

Run:

```bash
git switch main
git merge feat/mvp14-custom-world-creation
```

- [ ] **Step 8: Post-merge verification**

Run the same backend targeted tests, frontend targeted tests, and frontend build again on `main`.

Expected: all pass.

- [ ] **Step 9: Final status**

Run:

```bash
git status --short --branch
```

Expected: `main...origin/main [领先 10]` and clean worktree. Do not push.

## Plan self-review

- Spec coverage: custom creation, sample shortcut, validation, `WORLD_CREATED`, compatibility, tests, commit/merge/no-push are covered.
- Placeholder scan: no TBD/TODO placeholders are present.
- Type consistency: frontend helper names use `createWorld` and `createSampleWorld`; backend event uses `WORLD_CREATED` consistently.
- Scope: single hardening/completion pass around existing world creation API and creation form; no decomposition needed.
