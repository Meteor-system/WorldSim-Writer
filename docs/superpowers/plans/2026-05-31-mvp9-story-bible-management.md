# MVP #9 Story Bible Management 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This project explicitly forbids dynamic workflows and subagents; skip code-review subagents and use inline self-review.

**Goal:** Constrain and harden Story Bible Management so WorldPage lets users update existing characters and create/update relations as formal world-state edits with versioning, event logs, projection refresh, and draft non-mutation guarantees.

**Architecture:** Reuse existing backend character/relation services and `commit_manual_world_change()` governance. Narrow the frontend MVP9 UI by hiding character create/delete and relation delete controls, and add focused tests for governance, ownership, cross-world validation, draft non-mutation, and approval version mismatch.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, React, TypeScript, Vite, Vitest, Testing Library.

---

## File Structure

- Create: `backend/tests/test_story_bible_management.py`
  - Backend integration tests for character update, relation create/update, ownership, cross-world validation, draft non-mutation, and approval readiness/preview mismatch.
- Modify: `frontend/src/components/CharacterManager.tsx`
  - Remove MVP9 UI access to character create/delete and scope edit payload to status/current_goals/edit_reason.
- Modify: `frontend/src/components/CharacterManager.test.tsx`
  - Update tests to assert update-only character UI and save/error/loading behavior.
- Modify: `frontend/src/components/RelationManager.tsx`
  - Remove MVP9 UI access to relation delete while preserving create/update.
- Modify: `frontend/src/components/RelationManager.test.tsx`
  - Update tests to assert create/update-only relation UI and save/error/loading behavior.
- Modify: `frontend/src/world/WorldPage.test.tsx`
  - Update tab assertions so MVP9 no longer expects `+ 新增角色`.
- Modify if tests expose missing contract only: `backend/app/character/service.py`, `backend/app/character/relation_service.py`, `backend/app/world/governance.py`
  - Keep changes minimal; existing implementation should mostly satisfy backend requirements.

---

## Task 1: Create feature branch

**Files:** none

- [ ] **Step 1: Create branch from current main**

Run:

```bash
git checkout -b feat/mvp9-story-bible-management
```

Expected: branch switches to `feat/mvp9-story-bible-management`.

---

## Task 2: Backend Story Bible governance tests

**Files:**
- Create: `backend/tests/test_story_bible_management.py`

- [ ] **Step 1: Write failing backend tests**

Create `backend/tests/test_story_bible_management.py` with these tests:

```python
from sqlalchemy import select

from app.character.models import Character, CharacterRelation
from app.event.models import EventLog
from app.llm.schemas import ChapterGeneration, ProposedCharacterChange, ProposedForeshadowChange
from app.narrative import service as narrative_service
from app.narrative.models import Chapter, ChapterDraft
from app.world.models import World


class StoryBibleDraftLLMClient:
    def generate_chapter(self, messages):
        return ChapterGeneration(
            title='第一章 雨巷密谈',
            draft_content='第一段：林砚停在雨巷口。\n\n第二段：沈微霜递来一封湿透的信。',
            context_summary='林砚与沈微霜交换线索。',
            review_hints=['确认第二段信息揭示是否过快'],
            proposed_character_changes=[
                ProposedCharacterChange(character_id=1, status='开始调查密信', current_goals=['追查湿信来源'])
            ],
            proposed_foreshadow_changes=[
                ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='湿信推进玉佩线索')
            ],
        )


def register_user(client, email='story-bible@example.com'):
    return client.post('/auth/register', json={'email': email, 'password': 'strongpass123'}).json()['access_token']


def auth(token):
    return {'Authorization': f'Bearer {token}'}


def create_world(client, token):
    return client.post('/worlds/from-template', headers=auth(token)).json()


def first_character(db_session, world_id):
    return db_session.scalar(select(Character).where(Character.world_id == world_id).order_by(Character.id))


def second_character(db_session, world_id):
    return list(db_session.scalars(select(Character).where(Character.world_id == world_id).order_by(Character.id)))[1]


def first_relation(db_session, world_id):
    return db_session.scalar(select(CharacterRelation).where(CharacterRelation.world_id == world_id).order_by(CharacterRelation.id))


def manual_events(db_session, world_id):
    return list(
        db_session.scalars(
            select(EventLog)
            .where(EventLog.world_id == world_id)
            .where(EventLog.source_type == 'manual_edit')
            .order_by(EventLog.id)
        )
    )


def create_reviewing_draft(client, token, world_id, monkeypatch):
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: StoryBibleDraftLLMClient())
    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进雨巷密谈'},
        headers=auth(token),
    )
    assert response.status_code == 200
    return response.json()


def test_update_character_increments_world_version_refreshes_projection_and_writes_events(client, db_session):
    token = register_user(client)
    world_payload = create_world(client, token)
    world_id = world_payload['id']
    character = first_character(db_session, world_id)

    response = client.put(
        f'/characters/{character.id}',
        json={
            'status': '谨慎调查密信',
            'current_goals': ['验证沈微霜是否可信', '追查湿信来源'],
            'edit_reason': '同步 Story Bible 设定',
        },
        headers=auth(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == '谨慎调查密信'
    assert payload['current_goals'] == ['验证沈微霜是否可信', '追查湿信来源']

    db_session.expire_all()
    world = db_session.get(World, world_id)
    updated = db_session.get(Character, character.id)
    events = manual_events(db_session, world_id)

    assert world.world_version == 2
    assert updated.status == '谨慎调查密信'
    assert updated.current_goals == ['验证沈微霜是否可信', '追查湿信来源']
    projected = next(item for item in world.current_characters if item['id'] == character.id)
    assert projected['status'] == '谨慎调查密信'
    assert projected['current_goals'] == ['验证沈微霜是否可信', '追查湿信来源']
    assert [event.event_type for event in events] == ['character_change', 'world_version_increment']
    assert events[0].payload['action'] == 'updated'
    assert events[0].payload['edit_reason'] == '同步 Story Bible 设定'
    assert events[0].world_version_before == 1
    assert events[0].world_version_after == 2


def test_non_owner_cannot_update_character(client, db_session):
    owner_token = register_user(client, 'owner-story-bible@example.com')
    other_token = register_user(client, 'intruder-story-bible@example.com')
    world_payload = create_world(client, owner_token)
    character = first_character(db_session, world_payload['id'])

    response = client.put(
        f'/characters/{character.id}',
        json={'status': '非法修改'},
        headers=auth(other_token),
    )

    assert response.status_code == 403
    assert response.json()['detail'] == 'FORBIDDEN'


def test_missing_character_update_returns_not_found(client):
    token = register_user(client)

    response = client.put('/characters/999999', json={'status': '不存在'}, headers=auth(token))

    assert response.status_code == 404
    assert response.json()['detail'] == 'NOT_FOUND'


def test_create_relation_increments_world_version_refreshes_projection_and_writes_events(client, db_session):
    token = register_user(client)
    world_payload = create_world(client, token)
    world_id = world_payload['id']
    source = first_character(db_session, world_id)
    target = second_character(db_session, world_id)

    response = client.post(
        f'/worlds/{world_id}/relations',
        json={
            'source_character_id': source.id,
            'target_character_id': target.id,
            'relation_type': 'cautious_alliance',
            'intensity': 3,
            'visibility': 'private',
            'edit_reason': '补充试探关系',
        },
        headers=auth(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['relation_type'] == 'cautious_alliance'
    assert payload['intensity'] == 3
    assert payload['visibility'] == 'private'

    db_session.expire_all()
    world = db_session.get(World, world_id)
    events = manual_events(db_session, world_id)

    assert world.world_version == 2
    assert any(item['id'] == payload['id'] and item['relation_type'] == 'cautious_alliance' for item in world.current_relations)
    assert [event.event_type for event in events] == ['relation_change', 'world_version_increment']
    assert events[0].payload['action'] == 'created'
    assert events[0].payload['edit_reason'] == '补充试探关系'


def test_update_relation_increments_world_version_and_refreshes_projection(client, db_session):
    token = register_user(client)
    world_payload = create_world(client, token)
    world_id = world_payload['id']
    relation = first_relation(db_session, world_id)

    response = client.put(
        f'/relations/{relation.id}',
        json={'relation_type': 'trusted_ally', 'intensity': 4, 'visibility': 'public', 'edit_reason': '关系升温'},
        headers=auth(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['relation_type'] == 'trusted_ally'
    assert payload['intensity'] == 4

    db_session.expire_all()
    world = db_session.get(World, world_id)
    updated = db_session.get(CharacterRelation, relation.id)
    events = manual_events(db_session, world_id)

    assert world.world_version == 2
    assert updated.relation_type == 'trusted_ally'
    projected = next(item for item in world.current_relations if item['id'] == relation.id)
    assert projected['relation_type'] == 'trusted_ally'
    assert projected['intensity'] == 4
    assert [event.event_type for event in events] == ['relation_change', 'world_version_increment']
    assert events[0].payload['action'] == 'updated'


def test_relation_create_and_update_reject_invalid_or_cross_world_characters(client, db_session):
    token = register_user(client)
    first_world = create_world(client, token)
    second_world = create_world(client, token)
    source = first_character(db_session, first_world['id'])
    target = second_character(db_session, first_world['id'])
    cross_world_character = first_character(db_session, second_world['id'])
    relation = first_relation(db_session, first_world['id'])

    self_response = client.post(
        f"/worlds/{first_world['id']}/relations",
        json={'source_character_id': source.id, 'target_character_id': source.id, 'relation_type': 'mirror'},
        headers=auth(token),
    )
    cross_create = client.post(
        f"/worlds/{first_world['id']}/relations",
        json={'source_character_id': source.id, 'target_character_id': cross_world_character.id, 'relation_type': 'impossible'},
        headers=auth(token),
    )
    cross_update = client.put(
        f'/relations/{relation.id}',
        json={'source_character_id': source.id, 'target_character_id': cross_world_character.id},
        headers=auth(token),
    )

    assert self_response.status_code == 400
    assert self_response.json()['detail'] == 'INVALID_SELF_RELATION'
    assert cross_create.status_code == 404
    assert cross_create.json()['detail'] == 'RELATED_CHARACTER_NOT_FOUND'
    assert cross_update.status_code == 404
    assert cross_update.json()['detail'] == 'RELATED_CHARACTER_NOT_FOUND'


def test_story_bible_edit_does_not_mutate_reviewing_draft_and_readiness_reports_version_mismatch(client, db_session, monkeypatch):
    token = register_user(client)
    world_payload = create_world(client, token)
    world_id = world_payload['id']
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)
    character = first_character(db_session, world_id)

    response = client.put(
        f'/characters/{character.id}',
        json={'status': '手动更新后的正式状态', 'current_goals': ['正式目标']},
        headers=auth(token),
    )
    assert response.status_code == 200

    db_session.expire_all()
    world = db_session.get(World, world_id)
    chapter = db_session.get(Chapter, draft['chapter_id'])
    stored_draft = db_session.scalar(select(ChapterDraft).where(ChapterDraft.id == draft['draft_id']))

    assert world.world_version == 2
    assert chapter.status == 'reviewing'
    assert chapter.draft_version == draft['draft_version']
    assert stored_draft.content == draft['content']
    assert stored_draft.source_world_version == 1

    readiness = client.get(f"/chapters/{draft['chapter_id']}/approval-readiness", headers=auth(token))
    preview = client.get(f"/chapters/{draft['chapter_id']}/approval-preview", headers=auth(token))

    assert readiness.status_code == 200
    readiness_payload = readiness.json()
    assert readiness_payload['world_version']['source_world_version'] == 1
    assert readiness_payload['world_version']['current_world_version'] == 2
    assert readiness_payload['world_version']['matches'] is False
    assert readiness_payload['status'] == 'blocked'

    assert preview.status_code == 200
    preview_payload = preview.json()
    assert preview_payload['source_world_version'] == 1
    assert preview_payload['current_world_version'] == 2
    assert preview_payload['version_conflict'] is True
```

- [ ] **Step 2: Run backend tests to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_story_bible_management.py -v
```

Expected: at least one failure if current implementation does not fully satisfy MVP9 acceptance. If every test already passes, document that MVP9 backend behavior already existed and continue to frontend RED tests.

- [ ] **Step 3: Implement minimal backend fixes if RED exposed a gap**

If tests fail because existing code does not satisfy the specified contract, make only the needed minimal changes in:

- `backend/app/character/service.py`
- `backend/app/character/relation_service.py`
- `backend/app/world/governance.py`

Expected implementation constraints:

```python
# Character update must continue to call commit_manual_world_change(... object_type='character', action='updated')
# Relation create must continue to call commit_manual_world_change(... object_type='relation', action='created')
# Relation update must continue to call commit_manual_world_change(... object_type='relation', action='updated')
# Cross-world relation characters must raise HTTPException(status_code=404, detail='RELATED_CHARACTER_NOT_FOUND')
# Self-relations must raise HTTPException(status_code=400, detail='INVALID_SELF_RELATION')
```

- [ ] **Step 4: Run backend tests to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_story_bible_management.py -v
```

Expected: all tests in `test_story_bible_management.py` pass.

---

## Task 3: CharacterManager update-only UI

**Files:**
- Modify: `frontend/src/components/CharacterManager.test.tsx`
- Modify: `frontend/src/components/CharacterManager.tsx`

- [ ] **Step 1: Write failing frontend tests for update-only character UI**

Update `frontend/src/components/CharacterManager.test.tsx` so it imports only `getCharacters` and `updateCharacter` from `../api/client`, and includes these tests:

```tsx
import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { getCharacters, updateCharacter } from '../api/client';
import type { Character } from '../api/types';
import { CharacterManager } from './CharacterManager';

vi.mock('../api/client', () => ({
  getCharacters: vi.fn(),
  updateCharacter: vi.fn(),
}));

const characters: Character[] = [
  {
    id: 1,
    name: '林砚',
    role_type: 'protagonist',
    status: 'active',
    public_profile: {},
    hidden_traits: {},
    destiny_flag: '灵脉异动见证者',
    current_goals: ['调查灵脉衰退'],
  },
];

beforeEach(() => {
  vi.mocked(updateCharacter).mockReset().mockResolvedValue({
    ...characters[0],
    status: 'inactive',
    current_goals: ['验证沈微霜是否可信', '追查湿信来源'],
  });
  vi.mocked(getCharacters).mockReset().mockResolvedValue(characters);
});

afterEach(() => cleanup());

describe('CharacterManager', () => {
  it('renders existing characters with world version governance warning', async () => {
    render(<CharacterManager worldId={7} />);

    expect(await screen.findByText('林砚')).toBeInTheDocument();
    expect(screen.getByText('这些编辑会正式写入世界状态，并使 world_version 增长。')).toBeInTheDocument();
    expect(screen.getByText('目标：')).toBeInTheDocument();
    expect(screen.getByText('调查灵脉衰退')).toBeInTheDocument();
  });

  it('hides character create and delete controls for MVP9 scope', async () => {
    render(<CharacterManager worldId={7} />);

    expect(await screen.findByText('林砚')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '+ 新增角色' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '删除' })).not.toBeInTheDocument();
  });

  it('edits only character status and current goals then refreshes the world overview', async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn();
    render(<CharacterManager worldId={7} onChanged={onChanged} />);

    await screen.findByText('林砚');
    await user.click(screen.getByRole('button', { name: '编辑' }));
    expect(screen.getByText('林砚 · protagonist')).toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText('状态'), 'inactive');
    const goals = screen.getByLabelText('当前目标');
    await user.clear(goals);
    await user.type(goals, '验证沈微霜是否可信、追查湿信来源');
    await user.type(screen.getByLabelText('修改原因（可选）'), '同步章节结果');
    await user.click(screen.getByRole('button', { name: '保存' }));

    await waitFor(() => expect(updateCharacter).toHaveBeenCalledWith(1, {
      status: 'inactive',
      current_goals: ['验证沈微霜是否可信', '追查湿信来源'],
      edit_reason: '同步章节结果',
    }));
    expect(onChanged).toHaveBeenCalledTimes(1);
  });

  it('shows saving state while updating a character', async () => {
    const user = userEvent.setup();
    let resolveUpdate: (value: Character) => void = () => undefined;
    vi.mocked(updateCharacter).mockReturnValueOnce(new Promise((resolve) => { resolveUpdate = resolve; }));
    render(<CharacterManager worldId={7} />);

    await screen.findByText('林砚');
    await user.click(screen.getByRole('button', { name: '编辑' }));
    await user.click(screen.getByRole('button', { name: '保存' }));

    expect(screen.getByRole('button', { name: '保存中…' })).toBeDisabled();
    resolveUpdate(characters[0]);
  });

  it('shows save errors without closing the edit form', async () => {
    const user = userEvent.setup();
    vi.mocked(updateCharacter).mockRejectedValueOnce(new Error('保存角色失败'));
    render(<CharacterManager worldId={7} />);

    await screen.findByText('林砚');
    await user.click(screen.getByRole('button', { name: '编辑' }));
    await user.click(screen.getByRole('button', { name: '保存' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('保存角色失败');
    expect(screen.getByText('林砚 · protagonist')).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run CharacterManager tests to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/components/CharacterManager.test.tsx
```

Expected: tests fail because `+ 新增角色` and delete controls still exist and the edit form still sends broader payload fields.

- [ ] **Step 3: Implement CharacterManager update-only UI**

Modify `frontend/src/components/CharacterManager.tsx`:

- Remove imports for `createCharacter` and `deleteCharacter`.
- Keep only `getCharacters` and `updateCharacter`.
- Remove create/delete state and handlers.
- Keep `editingId` and form state for update only.
- Change form payload helper to return `CharacterUpdate` with only `status`, `current_goals`, and optional `edit_reason`.
- Render read-only character identity in the modal.
- Hide `+ 新增角色` and all delete controls.

Key implementation shape:

```tsx
function formToUpdatePayload(f: FormData): CharacterUpdate {
  return {
    status: f.status,
    current_goals: f.current_goals
      .split(/[、,，]/)
      .map((s) => s.trim())
      .filter(Boolean),
    edit_reason: f.edit_reason.trim() || undefined,
  };
}
```

The submit handler should call:

```tsx
await updateCharacter(editingId, formToUpdatePayload(form));
```

- [ ] **Step 4: Run CharacterManager tests to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/components/CharacterManager.test.tsx
```

Expected: all CharacterManager tests pass.

---

## Task 4: RelationManager create/update-only UI

**Files:**
- Modify: `frontend/src/components/RelationManager.test.tsx`
- Modify: `frontend/src/components/RelationManager.tsx`

- [ ] **Step 1: Write failing frontend tests for relation delete hiding and states**

Update `frontend/src/components/RelationManager.test.tsx` so delete imports/mocks are removed and tests include:

```tsx
import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { createRelation, getRelations, updateRelation } from '../api/client';
import type { Character, CharacterRelation } from '../api/types';
import { RelationManager } from './RelationManager';

vi.mock('../api/client', () => ({
  getRelations: vi.fn(),
  createRelation: vi.fn(),
  updateRelation: vi.fn(),
}));

const characters: Character[] = [
  { id: 1, name: '林砚', role_type: 'protagonist', status: 'active', public_profile: {}, hidden_traits: {}, destiny_flag: null, current_goals: [] },
  { id: 2, name: '沈微霜', role_type: 'ally', status: 'active', public_profile: {}, hidden_traits: {}, destiny_flag: null, current_goals: [] },
];

const relations: CharacterRelation[] = [
  { id: 1, source_character_id: 1, target_character_id: 2, relation_type: 'uneasy_alliance', intensity: 2, visibility: 'public' },
];

beforeEach(() => {
  vi.mocked(getRelations).mockReset().mockResolvedValue(relations);
  vi.mocked(createRelation).mockReset().mockResolvedValue(relations[0]);
  vi.mocked(updateRelation).mockReset().mockResolvedValue(relations[0]);
});

afterEach(() => cleanup());

describe('RelationManager', () => {
  it('renders relationship cards with character names and world version governance warning', async () => {
    render(<RelationManager worldId={7} characters={characters} />);

    expect(await screen.findByText('林砚 → 沈微霜')).toBeInTheDocument();
    expect(screen.getByText('这些编辑会正式写入世界状态，并使 world_version 增长。')).toBeInTheDocument();
    expect(screen.getByText('关系：uneasy_alliance')).toBeInTheDocument();
    expect(screen.getByText('强度：2')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '+ 新增关系' })).toBeInTheDocument();
  });

  it('hides relation delete controls for MVP9 scope', async () => {
    render(<RelationManager worldId={7} characters={characters} />);

    expect(await screen.findByText('林砚 → 沈微霜')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '删除' })).not.toBeInTheDocument();
  });

  it('creates a relation and refreshes the world overview', async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn();
    render(<RelationManager worldId={7} characters={characters} onChanged={onChanged} />);

    await screen.findByText('林砚 → 沈微霜');
    await user.click(screen.getByRole('button', { name: '+ 新增关系' }));
    await user.type(screen.getByLabelText('关系类型 *'), 'mentor');
    await user.type(screen.getByLabelText('备注 / 修改原因（可选）'), '补充师承关系');
    await user.click(screen.getByRole('button', { name: '保存' }));

    await waitFor(() => expect(createRelation).toHaveBeenCalledWith(7, {
      source_character_id: 1,
      target_character_id: 2,
      relation_type: 'mentor',
      intensity: 1,
      visibility: 'public',
      edit_reason: '补充师承关系',
    }));
    expect(onChanged).toHaveBeenCalledTimes(1);
  });

  it('edits a relation and refreshes the world overview', async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn();
    render(<RelationManager worldId={7} characters={characters} onChanged={onChanged} />);

    await screen.findByText('林砚 → 沈微霜');
    await user.click(screen.getByRole('button', { name: '编辑' }));
    const relationType = screen.getByLabelText('关系类型 *');
    await user.clear(relationType);
    await user.type(relationType, 'trusted_ally');
    await user.type(screen.getByLabelText('备注 / 修改原因（可选）'), '关系升温');
    await user.click(screen.getByRole('button', { name: '保存' }));

    await waitFor(() => expect(updateRelation).toHaveBeenCalledWith(1, {
      source_character_id: 1,
      target_character_id: 2,
      relation_type: 'trusted_ally',
      intensity: 2,
      visibility: 'public',
      edit_reason: '关系升温',
    }));
    expect(onChanged).toHaveBeenCalledTimes(1);
  });

  it('shows saving state while saving a relation', async () => {
    const user = userEvent.setup();
    let resolveCreate: (value: CharacterRelation) => void = () => undefined;
    vi.mocked(createRelation).mockReturnValueOnce(new Promise((resolve) => { resolveCreate = resolve; }));
    render(<RelationManager worldId={7} characters={characters} />);

    await screen.findByText('林砚 → 沈微霜');
    await user.click(screen.getByRole('button', { name: '+ 新增关系' }));
    await user.type(screen.getByLabelText('关系类型 *'), 'mentor');
    await user.click(screen.getByRole('button', { name: '保存' }));

    expect(screen.getByRole('button', { name: '保存中…' })).toBeDisabled();
    resolveCreate(relations[0]);
  });

  it('shows save errors without closing the form', async () => {
    const user = userEvent.setup();
    vi.mocked(updateRelation).mockRejectedValueOnce(new Error('保存关系失败'));
    render(<RelationManager worldId={7} characters={characters} />);

    await screen.findByText('林砚 → 沈微霜');
    await user.click(screen.getByRole('button', { name: '编辑' }));
    await user.click(screen.getByRole('button', { name: '保存' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('保存关系失败');
    expect(screen.getByText('编辑关系')).toBeInTheDocument();
  });

  it('prevents saving a relation with the same source and target character', async () => {
    const user = userEvent.setup();
    render(<RelationManager worldId={7} characters={characters} />);

    await screen.findByText('林砚 → 沈微霜');
    await user.click(screen.getByRole('button', { name: '+ 新增关系' }));
    await user.selectOptions(screen.getByLabelText('目标角色'), '1');

    expect(screen.getByText('起点角色和目标角色不能相同。')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '保存' })).toBeDisabled();
  });
});
```

- [ ] **Step 2: Run RelationManager tests to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/components/RelationManager.test.tsx
```

Expected: tests fail because delete controls still exist.

- [ ] **Step 3: Implement RelationManager create/update-only UI**

Modify `frontend/src/components/RelationManager.tsx`:

- Remove import for `deleteRelation`.
- Remove `confirmDelete`, `deleteReason`, and `handleDelete`.
- Remove delete button and confirmation UI from each relation card.
- Keep create/update form and saving/error behavior unchanged.

- [ ] **Step 4: Run RelationManager tests to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/components/RelationManager.test.tsx
```

Expected: all RelationManager tests pass.

---

## Task 5: WorldPage and API client acceptance tests

**Files:**
- Modify: `frontend/src/world/WorldPage.test.tsx`
- Modify if needed: `frontend/src/api/client.test.ts`

- [ ] **Step 1: Update WorldPage test expectations for MVP9 scope**

In `frontend/src/world/WorldPage.test.tsx`, update the `renders World Bible Editor manager tabs with governance warning` test so it no longer expects `+ 新增角色`. The character tab assertion should be:

```tsx
await user.click(screen.getByRole('button', { name: '角色管理' }));
expect(screen.getAllByText('角色管理').length).toBeGreaterThanOrEqual(2);
expect(getCharacters).toHaveBeenCalledWith(7);
expect(screen.getByText('这些编辑会正式写入世界状态，并使 world_version 增长。')).toBeInTheDocument();
expect(screen.queryByRole('button', { name: '+ 新增角色' })).not.toBeInTheDocument();
```

Keep the relation tab expectation for `+ 新增关系`.

- [ ] **Step 2: Run WorldPage test to verify GREEN with updated components**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: WorldPage tests pass.

- [ ] **Step 3: Run API client targeted tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts
```

Expected: API client tests pass. If they fail because old character/relation helper expectations changed, update only expectations that conflict with MVP9 UI scope; do not remove backend helper coverage unless it is directly incompatible.

---

## Task 6: Inline self-review and full targeted verification

**Files:**
- Review modified files only.

- [ ] **Step 1: Inline self-review**

Review the diff manually and verify:

- No dynamic workflows were used.
- No subagents were used.
- No code-review subagent was used.
- Character create/delete UI is hidden.
- Relation delete UI is hidden.
- Character update payload is scoped to `status`, `current_goals`, and `edit_reason`.
- Relation create/update behavior remains intact.
- Backend tests assert world-version governance and draft non-mutation.
- No automatic draft repair or approval behavior was added.

- [ ] **Step 2: Run backend targeted tests**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_story_bible_management.py tests/test_narrative_draft_versioning.py tests/test_narrative_approval.py -v
```

Expected: all tests pass.

- [ ] **Step 3: Run frontend targeted tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/components/CharacterManager.test.tsx src/components/RelationManager.test.tsx src/world/WorldPage.test.tsx src/api/client.test.ts
```

Expected: all targeted frontend tests pass.

- [ ] **Step 4: Run frontend build**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: TypeScript and Vite build succeed.

---

## Task 7: Commit and merge without pushing

**Files:** all modified MVP9 files.

- [ ] **Step 1: Check status**

Run:

```bash
git status --short
```

Expected: modified/created files are only MVP9 spec, plan, tests, and implementation files.

- [ ] **Step 2: Commit on feature branch**

Run:

```bash
git add docs/superpowers/specs/2026-05-31-mvp9-story-bible-management-design.md docs/superpowers/plans/2026-05-31-mvp9-story-bible-management.md backend/tests/test_story_bible_management.py frontend/src/components/CharacterManager.tsx frontend/src/components/CharacterManager.test.tsx frontend/src/components/RelationManager.tsx frontend/src/components/RelationManager.test.tsx frontend/src/world/WorldPage.test.tsx frontend/src/api/client.test.ts
git commit -m "feat: add story bible management" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

Expected: commit succeeds.

- [ ] **Step 3: Merge back to main**

Run:

```bash
git checkout main
git merge feat/mvp9-story-bible-management
```

Expected: merge succeeds. Do not push.

- [ ] **Step 4: Post-merge verification**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_story_bible_management.py tests/test_narrative_draft_versioning.py tests/test_narrative_approval.py -v
cd /opt/WorldSim-Writer/frontend && npm run test -- src/components/CharacterManager.test.tsx src/components/RelationManager.test.tsx src/world/WorldPage.test.tsx src/api/client.test.ts && npm run build
```

Expected: backend tests pass, frontend tests pass, frontend build succeeds.

- [ ] **Step 5: Final status**

Run:

```bash
git status --short --branch
```

Expected: on `main`, clean working tree, ahead of origin by local commits, no push performed.

---

## Plan self-review

- Spec coverage: character update, relation create/update, world-version governance, event logs, ownership, cross-world rejection, draft non-mutation, approval mismatch, frontend save/error/loading states, and non-goals are all covered by tasks.
- Placeholder scan: no TBD/TODO/fill-in-later placeholders remain.
- Type consistency: frontend payload names match `CharacterUpdate`, `CharacterRelationCreate`, and `CharacterRelationUpdate`; backend endpoint paths match existing routers.
- Scope consistency: plan hides create/delete from MVP9 UI without deleting legacy backend endpoints.
