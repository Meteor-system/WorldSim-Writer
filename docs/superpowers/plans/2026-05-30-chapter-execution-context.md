# Chapter Execution Context 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze a structured chapter execution context from the Narrative Control Center into chapter/draft records and use it in outline/write prompts while preserving approval-only formal world-state mutation.

**Architecture:** Frontend builds a `ChapterExecutionContext` from `NextChapterPrepResponse` and carries it through `StudioLaunchContext` from `WorldPage` to `App` to `StudioPage`. Backend stores the normalized context on `Chapter.execution_context`, copies it to `ChapterDraft.execution_context`, and passes compact summaries into outline/write prompts. Review/history UI displays frozen context snapshots as read-only evidence.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy, Alembic, pytest, React, TypeScript, Vite, Vitest, Testing Library.

---

## File Structure

### Backend

- Create: `backend/alembic/versions/0011_add_chapter_execution_context.py`
  - Adds JSONB `execution_context` columns to `chapters` and `chapter_drafts`.
- Create: `backend/tests/test_chapter_execution_context.py`
  - Covers schema, persistence, prompt use, direct draft compatibility, history exposure, and invariants.
- Modify: `backend/app/narrative/models.py`
  - Adds `execution_context` mapped JSONB columns.
- Modify: `backend/app/narrative/schemas.py`
  - Adds execution context Pydantic schemas and exposes context in request/response models.
- Modify: `backend/app/narrative/router.py`
  - Passes optional context from request payloads into service functions.
- Modify: `backend/app/narrative/service.py`
  - Normalizes/manual-builds context, saves it, copies it across draft versions, formats prompt context, and exposes it in payloads.
- Modify: `backend/app/narrative_control_center/service.py`
  - Adds `execution_context` to chapter history detail response construction.
- Modify: `backend/app/narrative_control_center/schemas.py`
  - Adds `execution_context` to `ApprovedChapterHistoryDetailResponse`.

### Frontend

- Create: `frontend/src/world/chapterExecutionContext.ts`
  - Converts `NextChapterPrepResponse` to `ChapterExecutionContext`, creates manual contexts, and applies edited goals.
- Create: `frontend/src/world/chapterExecutionContext.test.ts`
  - Unit tests for the helper.
- Modify: `frontend/src/api/types.ts`
  - Adds `ChapterExecutionContext`, `StudioLaunchContext`, and context fields on chapter/draft/history response types.
- Modify: `frontend/src/api/client.ts`
  - Extends `createChapter()` payload with optional `execution_context`; leaves `writeChapter()` unchanged.
- Modify: `frontend/src/world/NextChapterPrepPanel.tsx`
  - Emits full context instead of only a goal string.
- Modify: `frontend/src/world/NextChapterPrepPanel.test.tsx`
  - Verifies callbacks receive context.
- Modify: `frontend/src/world/WorldPage.tsx`
  - Stores selected `ChapterExecutionContext` and passes `StudioLaunchContext`.
- Modify: `frontend/src/world/WorldPage.test.tsx`
  - Verifies regular and direct Studio handoff include full context.
- Modify: `frontend/src/App.tsx`
  - Stores and clears `StudioLaunchContext`.
- Modify: `frontend/src/studio/StudioPage.tsx`
  - Accepts `launchContext`, displays context summary, submits normalized context, and renders frozen draft context.
- Modify: `frontend/src/studio/StudioPage.test.tsx`
  - Verifies editable goal, context summary, create payload, and draft snapshot display.
- Modify: `frontend/src/world/ChapterHistoryPanel.tsx`
  - Displays execution context snapshot in approved chapter detail.
- Modify: `frontend/src/world/ChapterHistoryPanel.test.tsx`
  - Verifies history detail context rendering.

---

## Task 1: Backend schema, model, and migration

**Files:**
- Create: `backend/alembic/versions/0011_add_chapter_execution_context.py`
- Create: `backend/tests/test_chapter_execution_context.py`
- Modify: `backend/app/narrative/models.py`
- Modify: `backend/app/narrative/schemas.py`

- [ ] **Step 1: Write failing schema/model tests**

Add to `backend/tests/test_chapter_execution_context.py`:

```python
from sqlalchemy import inspect

from app.narrative.models import Chapter, ChapterDraft
from app.narrative.schemas import CreateChapterRequest, DraftRequest


def sample_execution_context(goal='林砚带着湿信赴城主府外墙，并设置一次试探。'):
    return {
        'source': 'next_chapter_prep',
        'source_world_version': 2,
        'next_chapter_number': 2,
        'goal': goal,
        'recommended_pov': {'character_id': 1, 'name': '林砚'},
        'source_signals': ['character_arc_progression_hint'],
        'priority_characters': [
            {
                'character_id': 1,
                'name': '林砚',
                'role_type': 'protagonist',
                'status': '开始调查密信',
                'reason': '上一章提示。',
            }
        ],
        'priority_foreshadows': [
            {
                'foreshadow_id': 1,
                'title': '裂纹玉佩',
                'status': 'advanced',
                'urgency_level': 4,
                'reason': '该伏笔需要推进。',
            }
        ],
        'progression_hints': [
            {
                'hint_type': 'character',
                'priority': 'high',
                'title': '试探沈微霜是否可信',
                'rationale': '上一章已经建立湿信线索。',
                'suggested_next_beat': goal,
                'related_character_ids': [1],
                'related_foreshadow_ids': [1],
                'can_seed_next_chapter_goal': True,
            }
        ],
        'continuity_warnings': [
            {
                'severity': 'medium',
                'category': 'character_arc',
                'message': '下一章需要补足试探过程。',
                'related_character_ids': [1],
                'related_foreshadow_ids': [],
            }
        ],
        'recent_events': [
            {
                'id': 4,
                'event_type': 'chapter_approved',
                'world_version_before': 1,
                'world_version_after': 2,
                'created_at': '2026-05-30T00:00:00Z',
            }
        ],
    }


def test_execution_context_columns_exist(db_session):
    inspector = inspect(db_session.get_bind())
    chapter_columns = {column['name'] for column in inspector.get_columns('chapters')}
    draft_columns = {column['name'] for column in inspector.get_columns('chapter_drafts')}

    assert 'execution_context' in chapter_columns
    assert 'execution_context' in draft_columns
    assert hasattr(Chapter, 'execution_context')
    assert hasattr(ChapterDraft, 'execution_context')


def test_create_and_draft_requests_accept_execution_context():
    context = sample_execution_context()

    create_payload = CreateChapterRequest(chapter_goal=context['goal'], execution_context=context)
    draft_payload = DraftRequest(chapter_goal=context['goal'], execution_context=context)

    assert create_payload.execution_context is not None
    assert create_payload.execution_context.recommended_pov.name == '林砚'
    assert draft_payload.execution_context is not None
    assert draft_payload.execution_context.priority_foreshadows[0].title == '裂纹玉佩'
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && pytest tests/test_chapter_execution_context.py::test_execution_context_columns_exist tests/test_chapter_execution_context.py::test_create_and_draft_requests_accept_execution_context -v
```

Expected: FAIL because `Chapter.execution_context`, `ChapterDraft.execution_context`, and request schema fields do not exist.

- [ ] **Step 3: Add model columns**

Modify `backend/app/narrative/models.py`:

Add this line inside `Chapter`, immediately after `character_arc_report`:

```python
execution_context: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
```

Add this line inside `ChapterDraft`, immediately after `parent_draft_version`:

```python
execution_context: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
```

- [ ] **Step 4: Add Pydantic schemas**

Modify `backend/app/narrative/schemas.py`:

```python
class ExecutionContextPov(BaseModel):
    character_id: int | None = None
    name: str | None = None


class ExecutionContextPriorityCharacter(BaseModel):
    character_id: int
    name: str
    role_type: str
    status: str
    reason: str


class ExecutionContextPriorityForeshadow(BaseModel):
    foreshadow_id: int
    title: str
    status: str
    urgency_level: int
    reason: str


class ExecutionContextProgressionHint(BaseModel):
    hint_type: str
    priority: str
    title: str
    rationale: str
    suggested_next_beat: str
    related_character_ids: list[int] = Field(default_factory=list)
    related_foreshadow_ids: list[int] = Field(default_factory=list)
    can_seed_next_chapter_goal: bool = False


class ExecutionContextContinuityWarning(BaseModel):
    severity: str
    category: str
    message: str
    related_character_ids: list[int] = Field(default_factory=list)
    related_foreshadow_ids: list[int] = Field(default_factory=list)


class ExecutionContextRecentEvent(BaseModel):
    id: int
    event_type: str
    world_version_before: int
    world_version_after: int
    created_at: str


class ChapterExecutionContext(BaseModel):
    source: Literal['next_chapter_prep', 'manual'] = 'manual'
    source_world_version: int
    next_chapter_number: int | None = None
    goal: str = Field(min_length=3)
    recommended_pov: ExecutionContextPov = Field(default_factory=ExecutionContextPov)
    source_signals: list[str] = Field(default_factory=list)
    priority_characters: list[ExecutionContextPriorityCharacter] = Field(default_factory=list)
    priority_foreshadows: list[ExecutionContextPriorityForeshadow] = Field(default_factory=list)
    progression_hints: list[ExecutionContextProgressionHint] = Field(default_factory=list)
    continuity_warnings: list[ExecutionContextContinuityWarning] = Field(default_factory=list)
    recent_events: list[ExecutionContextRecentEvent] = Field(default_factory=list)
```

Update requests:

```python
class DraftRequest(BaseModel):
    chapter_goal: str = Field(min_length=3)
    execution_context: ChapterExecutionContext | None = None


class CreateChapterRequest(BaseModel):
    chapter_goal: str = Field(min_length=3)
    title: str | None = None
    execution_context: ChapterExecutionContext | None = None
```

Add response fields:

Add this field to `DraftResponse`, immediately after `critique_report`:

```python
execution_context: dict | None = None
```

Add this field to `ChapterPipelineResponse`, immediately after `critique_report`:

```python
execution_context: dict | None = None
```

Add this field to `ChapterResponse`, immediately after `critique_report`:

```python
execution_context: dict | None = None
```

- [ ] **Step 5: Add Alembic migration**

Create `backend/alembic/versions/0011_add_chapter_execution_context.py`:

```python
"""add chapter execution context

Revision ID: 0011_add_chapter_execution_context
Revises: 0010_add_world_snapshots
Create Date: 2026-05-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0011_add_chapter_execution_context'
down_revision: str | None = '0010_add_world_snapshots'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'chapters',
        sa.Column(
            'execution_context',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        'chapter_drafts',
        sa.Column(
            'execution_context',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.alter_column('chapters', 'execution_context', server_default=None)
    op.alter_column('chapter_drafts', 'execution_context', server_default=None)


def downgrade() -> None:
    op.drop_column('chapter_drafts', 'execution_context')
    op.drop_column('chapters', 'execution_context')
```

- [ ] **Step 6: Run tests to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/backend && pytest tests/test_chapter_execution_context.py::test_execution_context_columns_exist tests/test_chapter_execution_context.py::test_create_and_draft_requests_accept_execution_context -v
```

Expected: PASS.

---

## Task 2: Backend persistence, prompt use, and invariants

**Files:**
- Modify: `backend/tests/test_chapter_execution_context.py`
- Modify: `backend/app/narrative/router.py`
- Modify: `backend/app/narrative/service.py`

- [ ] **Step 1: Add failing backend service tests**

Append to `backend/tests/test_chapter_execution_context.py`:

```python
from sqlalchemy import func, select

from app.event.models import EventLog
from app.llm.schemas import ChapterGeneration, ProposedCharacterChange, ProposedForeshadowChange
from app.narrative import service as narrative_service
from app.narrative.models import Chapter, ChapterDraft
from app.world.models import World


class CapturingLLMClient:
    def __init__(self):
        self.messages = []

    def generate_chapter(self, messages):
        self.messages.append(messages)
        return ChapterGeneration(
            title='第二章 城主府外墙',
            draft_content='林砚抵达城主府外墙，借湿信试探沈微霜。',
            context_summary='本章执行城主府外墙试探。',
            review_hints=['确认沈微霜动机是否可信'],
            proposed_character_changes=[ProposedCharacterChange(character_id=1, current_goals=['试探沈微霜'])],
            proposed_foreshadow_changes=[
                ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='湿信线索继续推进')
            ],
        )


def register_and_create_world(client, email='execution-context@example.com'):
    token = client.post('/auth/register', json={'email': email, 'password': 'strongpass123'}).json()['access_token']
    world = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {token}'}).json()
    return token, world['id']


def test_create_chapter_freezes_execution_context_without_mutating_world(client, db_session):
    token, world_id = register_and_create_world(client)
    context = sample_execution_context()
    before_events = db_session.scalar(select(func.count()).select_from(EventLog))

    response = client.post(
        f'/worlds/{world_id}/chapters',
        json={'chapter_goal': context['goal'], 'title': '第二章 城主府外墙', 'execution_context': context},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['execution_context']['source'] == 'next_chapter_prep'
    assert payload['execution_context']['recommended_pov']['name'] == '林砚'
    db_session.expire_all()
    chapter = db_session.get(Chapter, payload['id'])
    world = db_session.get(World, world_id)
    assert chapter.execution_context['goal'] == context['goal']
    assert world.world_version == 1
    assert db_session.scalar(select(func.count()).select_from(EventLog)) == before_events


def test_create_chapter_without_context_creates_manual_context(client, db_session):
    token, world_id = register_and_create_world(client, 'manual-execution-context@example.com')

    response = client.post(
        f'/worlds/{world_id}/chapters',
        json={'chapter_goal': '手动推进湿信线索', 'title': '手动推进湿信线索'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['execution_context']['source'] == 'manual'
    assert payload['execution_context']['goal'] == '手动推进湿信线索'
    assert payload['execution_context']['source_signals'] == ['manual']
    assert payload['execution_context']['source_world_version'] == 1


def test_outline_and_writer_prompts_use_frozen_execution_context(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'prompt-context@example.com')
    context = sample_execution_context()
    chapter_response = client.post(
        f'/worlds/{world_id}/chapters',
        json={'chapter_goal': context['goal'], 'title': '第二章 城主府外墙', 'execution_context': context},
        headers={'Authorization': f'Bearer {token}'},
    )
    chapter_id = chapter_response.json()['id']
    world = db_session.get(World, world_id)
    chapter = db_session.get(Chapter, chapter_id)
    characters, foreshadows = narrative_service._load_world_context(db_session, world)

    outline_messages = narrative_service.build_outline_messages(
        world,
        characters,
        foreshadows,
        chapter.chapter_goal,
        execution_context=chapter.execution_context,
    )
    writer_messages = narrative_service.build_generation_messages(
        world,
        characters,
        foreshadows,
        chapter.chapter_goal,
        execution_context=chapter.execution_context,
    )

    outline_text = outline_messages[-1]['content']
    writer_text = writer_messages[-1]['content']
    assert '本章执行上下文' in outline_text
    assert '推荐 POV：林砚' in outline_text
    assert '试探沈微霜是否可信' in outline_text
    assert '本章执行上下文' in writer_text
    assert '优先满足执行上下文' in writer_text
    assert '裂纹玉佩' in writer_text


def test_write_chapter_copies_chapter_execution_context_to_draft(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'write-context@example.com')
    context = sample_execution_context()
    chapter = client.post(
        f'/worlds/{world_id}/chapters',
        json={'chapter_goal': context['goal'], 'title': '第二章 城主府外墙', 'execution_context': context},
        headers={'Authorization': f'Bearer {token}'},
    ).json()
    llm = CapturingLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)

    response = client.post(
        f"/chapters/{chapter['id']}/write",
        json={'outline_beats': []},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['execution_context']['recommended_pov']['name'] == '林砚'
    draft = db_session.scalar(select(ChapterDraft).where(ChapterDraft.chapter_id == chapter['id']))
    assert draft.execution_context['goal'] == context['goal']


def test_direct_draft_endpoint_accepts_execution_context(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'direct-context@example.com')
    context = sample_execution_context()
    llm = CapturingLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)

    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': context['goal'], 'execution_context': context},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['execution_context']['source'] == 'next_chapter_prep'
    chapter = db_session.get(Chapter, payload['chapter_id'])
    draft = db_session.get(ChapterDraft, payload['draft_id'])
    assert chapter.execution_context['goal'] == context['goal']
    assert draft.execution_context['priority_characters'][0]['name'] == '林砚'
    assert '本章执行上下文' in llm.messages[0][-1]['content']
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && pytest tests/test_chapter_execution_context.py -v
```

Expected: FAIL because routes do not pass context, service does not persist/use/copy context, and payloads do not expose it.

- [ ] **Step 3: Update router to pass context**

Modify `backend/app/narrative/router.py`:

Update the existing route bodies to pass `payload.execution_context`:

```python
return ChapterPipelineResponse.model_validate(
    create_chapter_session(db, current_user, world_id, payload.chapter_goal, payload.title, payload.execution_context)
)
```

```python
return DraftResponse.model_validate(
    create_chapter_draft(db, current_user, world_id, payload.chapter_goal, payload.execution_context)
)
```

- [ ] **Step 4: Add context helpers and prompt formatter**

Modify `backend/app/narrative/service.py`:

```python
def _approved_chapter_count(db: Session, world_id: int) -> int:
    return db.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id).where(Chapter.status == 'approved')) or 0


def build_manual_execution_context(db: Session, world: World, chapter_goal: str) -> dict:
    return {
        'source': 'manual',
        'source_world_version': world.world_version,
        'next_chapter_number': _approved_chapter_count(db, world.id) + 1,
        'goal': chapter_goal,
        'recommended_pov': {'character_id': None, 'name': None},
        'source_signals': ['manual'],
        'priority_characters': [],
        'priority_foreshadows': [],
        'progression_hints': [],
        'continuity_warnings': [],
        'recent_events': [],
    }


def normalize_execution_context(db: Session, world: World, chapter_goal: str, execution_context) -> dict:
    if execution_context is None:
        context = build_manual_execution_context(db, world, chapter_goal)
    elif hasattr(execution_context, 'model_dump'):
        context = execution_context.model_dump(mode='json')
    else:
        context = dict(execution_context)
    context['goal'] = chapter_goal
    return context


def format_execution_context_for_prompt(execution_context: dict | None) -> str:
    if not execution_context:
        return '本章执行上下文：无\n'
    pov = execution_context.get('recommended_pov') or {}
    lines = [
        '本章执行上下文：',
        f"- 来源：{execution_context.get('source', 'manual')}",
        f"- 源世界版本：{execution_context.get('source_world_version', '未知')}",
        f"- 推荐 POV：{pov.get('name') or '暂无'}",
    ]
    characters = execution_context.get('priority_characters') or []
    if characters:
        lines.append('- 优先角色：' + '；'.join(f"{c.get('name')}（理由：{c.get('reason')}）" for c in characters))
    foreshadows = execution_context.get('priority_foreshadows') or []
    if foreshadows:
        lines.append('- 优先伏笔：' + '；'.join(f"{f.get('title')}（urgency {f.get('urgency_level')}，理由：{f.get('reason')}）" for f in foreshadows))
    hints = execution_context.get('progression_hints') or []
    if hints:
        lines.append('- 推进提示：' + '；'.join(f"{h.get('title')} → {h.get('suggested_next_beat')}" for h in hints))
    warnings = execution_context.get('continuity_warnings') or []
    if warnings:
        lines.append('- 连续性提醒：' + '；'.join(str(w.get('message')) for w in warnings))
    recent_events = execution_context.get('recent_events') or []
    if recent_events:
        lines.append('- 近期事件：' + '；'.join(f"{e.get('event_type')} 世界 {e.get('world_version_before')}→{e.get('world_version_after')}" for e in recent_events))
    return '\n'.join(lines) + '\n'
```

Also add `func` to the SQLAlchemy imports:

```python
from sqlalchemy import func, select
```

- [ ] **Step 5: Update service signatures and payloads**

Modify `create_chapter_session()`:

```python
def create_chapter_session(db: Session, user: User, world_id: int, chapter_goal: str, title: str | None = None, execution_context=None) -> Chapter:
    world = require_owned_world(db, user, world_id)
    context = normalize_execution_context(db, world, chapter_goal, execution_context)
    chapter = Chapter(
        world_id=world.id,
        title=title or chapter_goal[:80],
        status='drafting',
        draft_version=0,
        approved_version=None,
        base_world_version=world.world_version,
        approved_content=None,
        chapter_goal=chapter_goal,
        outline_beats=[],
        outline_context={},
        critique_report={},
        execution_context=context,
    )
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return chapter
```

Modify direct draft creation to normalize context, save it on chapter and draft, and pass it to `build_generation_messages()`. In `create_chapter_draft()`, add `execution_context=None` to the function signature, compute context after loading the world, add `execution_context=context` to the `Chapter(...)` constructor, pass `execution_context=context` to the `build_generation_messages` call, and add `execution_context=context` to the `ChapterDraft(...)` constructor:

```python
context = normalize_execution_context(db, world, chapter_goal, execution_context)
```

```python
execution_context=context,
```

```python
messages = build_generation_messages(
    world,
    characters,
    foreshadows,
    chapter_goal,
    execution_context=context,
)
```

Modify `_draft_payload()`:

```python
'execution_context': draft.execution_context or chapter.execution_context,
```

- [ ] **Step 6: Update prompt builders**

Modify `build_outline_messages()` by adding the new parameter after `chapter_context`:

```python
execution_context: dict | None = None,
```

Add this line to the user prompt content immediately after the `用户额外上下文` line:

```python
f'{format_execution_context_for_prompt(execution_context)}'
```

Modify `build_generation_messages()` by adding the new parameter after `outline_context`:

```python
execution_context: dict | None = None,
```

Add this line to the user prompt content before `outline_lines`:

```python
f'{format_execution_context_for_prompt(execution_context)}'
```

Change final instruction:

```python
'请基于本章目标、执行上下文与 Outliner 节拍生成章节正文。优先满足执行上下文中的 POV、优先角色、优先伏笔、推进提示和连续性提醒。返回 JSON。'
```

- [ ] **Step 7: Copy context into pipeline drafts and draft revisions**

In `write_chapter_from_outline()`, set new `ChapterDraft` field:

```python
execution_context=chapter.execution_context,
```

In `_create_draft_version()`, set:

```python
execution_context=previous_draft.execution_context,
```

In `generate_chapter_outline()`, call:

```python
messages = build_outline_messages(world, characters, foreshadows, chapter.chapter_goal or '', chapter_context, chapter.execution_context)
```

- [ ] **Step 8: Run backend context tests to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/backend && pytest tests/test_chapter_execution_context.py -v
```

Expected: PASS.

---

## Task 3: Backend history detail context exposure

**Files:**
- Modify: `backend/tests/test_chapter_execution_context.py`
- Modify: `backend/app/narrative_control_center/service.py`
- Modify: `backend/app/narrative_control_center/schemas.py`

- [ ] **Step 1: Add failing history detail test**

Append to `backend/tests/test_chapter_execution_context.py`:

```python
def test_chapter_history_detail_exposes_execution_context(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'history-context@example.com')
    context = sample_execution_context()
    llm = CapturingLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': context['goal'], 'execution_context': context},
        headers={'Authorization': f'Bearer {token}'},
    ).json()
    approve = client.post(f"/chapters/{draft['chapter_id']}/approve", headers={'Authorization': f'Bearer {token}'})
    assert approve.status_code == 200

    response = client.get(f"/chapters/{draft['chapter_id']}/history", headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    payload = response.json()
    assert payload['execution_context']['source'] == 'next_chapter_prep'
    assert payload['execution_context']['goal'] == context['goal']
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && pytest tests/test_chapter_execution_context.py::test_chapter_history_detail_exposes_execution_context -v
```

Expected: FAIL because history detail response does not include `execution_context`.

- [ ] **Step 3: Update history detail response builder and schema**

Modify `backend/app/narrative_control_center/schemas.py`:

```python
class ApprovedChapterHistoryDetailResponse(BaseModel):
    id: int
    world_id: int
    title: str
    status: str
    approved_version: int
    base_world_version: int
    approved_content: str
    world_version_before: int
    world_version_after: int
    events: list[ChapterHistoryEvent]
    character_changes: list[ChapterHistoryChange]
    foreshadow_changes: list[ChapterHistoryChange]
    critic_summary: str | None = None
    character_arc_summary: str | None = None
    execution_context: dict | None = None
```

Modify the detail payload returned by `backend/app/narrative_control_center/service.py` for `/chapters/{chapter_id}/history`:

```python
'execution_context': latest_draft.execution_context if latest_draft and latest_draft.execution_context else chapter.execution_context,
```

- [ ] **Step 4: Run history detail test to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/backend && pytest tests/test_chapter_execution_context.py::test_chapter_history_detail_exposes_execution_context -v
```

Expected: PASS.

---

## Task 4: Frontend types, helper, and API client

**Files:**
- Create: `frontend/src/world/chapterExecutionContext.ts`
- Create: `frontend/src/world/chapterExecutionContext.test.ts`
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/api/client.ts`

- [ ] **Step 1: Add failing helper tests**

Create `frontend/src/world/chapterExecutionContext.test.ts`:

```ts
import { describe, expect, it } from 'vitest';
import type { NextChapterPrepResponse, WorldOverview } from '../api/types';
import { buildExecutionContextFromPrep, buildManualExecutionContext, withEditedGoal } from './chapterExecutionContext';

const prep: NextChapterPrepResponse = {
  world_id: 7,
  world_version: 2,
  next_chapter_number: 2,
  suggested_goal: '林砚带着湿信赴城主府外墙，并设置一次试探。',
  recommended_pov_character_id: 1,
  recommended_pov_character_name: '林砚',
  source_signals: ['character_arc_progression_hint'],
  priority_characters: [
    { character_id: 1, name: '林砚', role_type: 'protagonist', status: '开始调查密信', reason: '上一章提示。' },
  ],
  priority_foreshadows: [
    { foreshadow_id: 1, title: '裂纹玉佩', status: 'advanced', urgency_level: 4, reason: '该伏笔需要推进。' },
  ],
  progression_hints: [
    {
      hint_type: 'character',
      priority: 'high',
      title: '试探沈微霜是否可信',
      rationale: '上一章已经建立湿信线索。',
      suggested_next_beat: '林砚带着湿信赴城主府外墙，并设置一次试探。',
      related_character_ids: [1],
      related_foreshadow_ids: [1],
      can_seed_next_chapter_goal: true,
    },
  ],
  continuity_warnings: [
    { severity: 'medium', category: 'character_arc', message: '下一章需要补足试探过程。', related_character_ids: [1], related_foreshadow_ids: [] },
  ],
  recent_events: [
    { id: 4, event_type: 'chapter_approved', world_version_before: 1, world_version_after: 2, payload: {}, created_at: '2026-05-30T00:00:00Z' },
  ],
};

const world = {
  id: 7,
  world_version: 3,
  approved_chapter_count: 2,
} as WorldOverview;

describe('chapterExecutionContext', () => {
  it('builds structured context from next chapter prep', () => {
    const context = buildExecutionContextFromPrep(prep);

    expect(context.source).toBe('next_chapter_prep');
    expect(context.source_world_version).toBe(2);
    expect(context.next_chapter_number).toBe(2);
    expect(context.goal).toBe(prep.suggested_goal);
    expect(context.recommended_pov.name).toBe('林砚');
    expect(context.priority_characters[0].reason).toBe('上一章提示。');
    expect(context.priority_foreshadows[0].title).toBe('裂纹玉佩');
    expect(context.progression_hints[0].title).toBe('试探沈微霜是否可信');
    expect(context.continuity_warnings[0].message).toBe('下一章需要补足试探过程。');
    expect(context.recent_events[0].event_type).toBe('chapter_approved');
  });

  it('builds manual context from world and goal', () => {
    const context = buildManualExecutionContext(world, '用户手动目标');

    expect(context.source).toBe('manual');
    expect(context.source_world_version).toBe(3);
    expect(context.next_chapter_number).toBe(3);
    expect(context.goal).toBe('用户手动目标');
    expect(context.source_signals).toEqual(['manual']);
    expect(context.priority_characters).toEqual([]);
  });

  it('applies edited goal to provided or manual context', () => {
    const context = buildExecutionContextFromPrep(prep);

    expect(withEditedGoal(context, world, '用户修改后的目标').goal).toBe('用户修改后的目标');
    expect(withEditedGoal(undefined, world, '无 NCC 的目标').source).toBe('manual');
  });
});
```

- [ ] **Step 2: Run helper test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/chapterExecutionContext.test.ts
```

Expected: FAIL because `chapterExecutionContext.ts` and types do not exist.

- [ ] **Step 3: Add frontend types**

Modify `frontend/src/api/types.ts` before `ChapterPipelineResponse`:

```ts
export type ChapterExecutionContext = {
  source: 'next_chapter_prep' | 'manual';
  source_world_version: number;
  next_chapter_number: number | null;
  goal: string;
  recommended_pov: { character_id: number | null; name: string | null };
  source_signals: string[];
  priority_characters: NextChapterPrepCharacter[];
  priority_foreshadows: NextChapterPrepForeshadow[];
  progression_hints: ChapterProgressionHint[];
  continuity_warnings: NextChapterPrepWarning[];
  recent_events: Array<Omit<NextChapterPrepEvent, 'payload'>>;
};

export type StudioLaunchContext = {
  initialChapterGoal?: string;
  executionContext?: ChapterExecutionContext;
};
```

Add `execution_context` fields:

Add this field to `ChapterPipelineResponse`, immediately after `critique_report`:

```ts
execution_context: ChapterExecutionContext | null;
```

Add this field to `ChapterHistoryDetailResponse`, immediately after `character_arc_summary`:

```ts
execution_context: ChapterExecutionContext | null;
```

Add this field to `DraftResponse`, immediately after `critique_report`:

```ts
execution_context?: ChapterExecutionContext | null;
```

- [ ] **Step 4: Create helper**

Create `frontend/src/world/chapterExecutionContext.ts`:

```ts
import type { ChapterExecutionContext, NextChapterPrepResponse, WorldOverview } from '../api/types';

export function buildExecutionContextFromPrep(prep: NextChapterPrepResponse): ChapterExecutionContext {
  return {
    source: 'next_chapter_prep',
    source_world_version: prep.world_version,
    next_chapter_number: prep.next_chapter_number,
    goal: prep.suggested_goal,
    recommended_pov: {
      character_id: prep.recommended_pov_character_id,
      name: prep.recommended_pov_character_name,
    },
    source_signals: prep.source_signals,
    priority_characters: prep.priority_characters,
    priority_foreshadows: prep.priority_foreshadows,
    progression_hints: prep.progression_hints,
    continuity_warnings: prep.continuity_warnings,
    recent_events: prep.recent_events.map(({ id, event_type, world_version_before, world_version_after, created_at }) => ({
      id,
      event_type,
      world_version_before,
      world_version_after,
      created_at,
    })),
  };
}

export function buildManualExecutionContext(world: WorldOverview, goal: string): ChapterExecutionContext {
  return {
    source: 'manual',
    source_world_version: world.world_version,
    next_chapter_number: world.approved_chapter_count + 1,
    goal,
    recommended_pov: { character_id: null, name: null },
    source_signals: ['manual'],
    priority_characters: [],
    priority_foreshadows: [],
    progression_hints: [],
    continuity_warnings: [],
    recent_events: [],
  };
}

export function withEditedGoal(
  context: ChapterExecutionContext | undefined,
  world: WorldOverview,
  goal: string,
): ChapterExecutionContext {
  if (context) return { ...context, goal };
  return buildManualExecutionContext(world, goal);
}
```

- [ ] **Step 5: Update API client**

Modify `frontend/src/api/client.ts` imports to include `ChapterExecutionContext` and update:

```ts
export function createChapter(worldId: number, data: { chapter_goal: string; title?: string; execution_context?: ChapterExecutionContext }) {
  return apiRequest<ChapterPipelineResponse>(`/worlds/${worldId}/chapters`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
```

Do not change `writeChapter()`.

- [ ] **Step 6: Run helper test to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/chapterExecutionContext.test.ts
```

Expected: PASS.

---

## Task 5: Frontend NCC handoff with full context

**Files:**
- Modify: `frontend/src/world/NextChapterPrepPanel.tsx`
- Modify: `frontend/src/world/NextChapterPrepPanel.test.tsx`
- Modify: `frontend/src/world/WorldPage.tsx`
- Modify: `frontend/src/world/WorldPage.test.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Update tests to expect full context callbacks**

Modify `frontend/src/world/NextChapterPrepPanel.test.tsx`:

```ts
const onUseContext = vi.fn();
const onEnterStudioWithContext = vi.fn();

render(<NextChapterPrepPanel prep={prep} onUseContext={onUseContext} onEnterStudioWithContext={onEnterStudioWithContext} />);

expect(screen.getByText('下一章准备台')).toBeInTheDocument();
await user.click(screen.getByRole('button', { name: '用作下一章目标' }));
expect(onUseContext).toHaveBeenCalledWith(expect.objectContaining({
  source: 'next_chapter_prep',
  goal: '林砚带着湿信赴城主府外墙，并设置一次试探。',
  recommended_pov: { character_id: 1, name: '林砚' },
}));

await user.click(screen.getByRole('button', { name: '进入创作台并使用此目标' }));
expect(onEnterStudioWithContext).toHaveBeenCalledWith(expect.objectContaining({
  source: 'next_chapter_prep',
  goal: '林砚带着湿信赴城主府外墙，并设置一次试探。',
}));
```

Modify `frontend/src/world/WorldPage.test.tsx` expectations:

```ts
expect(onEnterStudio).toHaveBeenCalledWith(world, {
  initialChapterGoal: '林砚带着湿信赴城主府外墙，并设置一次试探。',
  executionContext: expect.objectContaining({
    source: 'next_chapter_prep',
    recommended_pov: { character_id: 1, name: '林砚' },
  }),
});
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/NextChapterPrepPanel.test.tsx src/world/WorldPage.test.tsx
```

Expected: FAIL because components still use goal string callbacks.

- [ ] **Step 3: Update NextChapterPrepPanel**

Modify `frontend/src/world/NextChapterPrepPanel.tsx`:

```tsx
import type { ChapterExecutionContext, NextChapterPrepResponse } from '../api/types';
import { buildExecutionContextFromPrep } from './chapterExecutionContext';

type Props = {
  prep: NextChapterPrepResponse | null;
  loading?: boolean;
  error?: string;
  onUseContext?: (context: ChapterExecutionContext) => void;
  onEnterStudioWithContext?: (context: ChapterExecutionContext) => void;
};
```

Inside non-null render:

```tsx
const context = buildExecutionContextFromPrep(prep);
```

Buttons:

```tsx
{onUseContext && (
  <button className="secondary-button" onClick={() => onUseContext(context)}>
    用作下一章目标
  </button>
)}
{onEnterStudioWithContext && (
  <button className="primary-button" onClick={() => onEnterStudioWithContext(context)}>
    进入创作台并使用此目标
  </button>
)}
```

- [ ] **Step 4: Update WorldPage**

Modify imports:

```tsx
import type { ChapterExecutionContext, ChapterHistoryResponse, NextChapterPrepResponse, StoryArcChapter, StudioLaunchContext, WorldCreateRequest, WorldOverview } from '../api/types';
```

Update props:

```tsx
type Props = { onEnterStudio: (world: WorldOverview, context?: StudioLaunchContext) => void; autoFocusTitle?: boolean };
```

Replace state:

```tsx
const [selectedExecutionContext, setSelectedExecutionContext] = useState<ChapterExecutionContext | null>(null);
```

Update regular Studio button:

```tsx
<button className="primary-button" onClick={() => onEnterStudio(world, {
  initialChapterGoal: selectedExecutionContext?.goal,
  executionContext: selectedExecutionContext ?? undefined,
})}>
  进入创作台
</button>
```

Update selected message:

```tsx
{selectedExecutionContext && <p className="mt-3 rounded-2xl bg-amber-100/70 p-3 text-sm font-bold text-[#5e3b1c]">已设为下一章目标：{selectedExecutionContext.goal}</p>}
```

Update `NextChapterPrepPanel` props:

```tsx
<NextChapterPrepPanel
  prep={nextPrep}
  loading={nextPrepLoading}
  error={nextPrepError}
  onUseContext={setSelectedExecutionContext}
  onEnterStudioWithContext={(context) => onEnterStudio(world, {
    initialChapterGoal: context.goal,
    executionContext: context,
  })}
/>
```

- [ ] **Step 5: Update App**

Modify imports:

```tsx
import type { StudioLaunchContext, WorldOverview } from './api/types';
```

Replace state:

```tsx
const [studioLaunchContext, setStudioLaunchContext] = useState<StudioLaunchContext>({});
```

Update `enterStudio`:

```tsx
function enterStudio(world: WorldOverview, context: StudioLaunchContext = {}) {
  setStudioWorld(world);
  setStudioLaunchContext(context);
}
```

Pass to Studio:

```tsx
<StudioPage
  world={studioWorld}
  launchContext={studioLaunchContext}
  onBack={() => {
    setStudioWorld(null);
    setStudioLaunchContext({});
  }}
  onApproved={(world) => {
    setApprovedWorld(world);
    setStudioWorld(null);
    setStudioLaunchContext({});
  }}
/>
```

- [ ] **Step 6: Run tests to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/NextChapterPrepPanel.test.tsx src/world/WorldPage.test.tsx
```

Expected: PASS.

---

## Task 6: Studio context summary, create payload, and draft snapshot display

**Files:**
- Modify: `frontend/src/studio/StudioPage.tsx`
- Modify: `frontend/src/studio/StudioPage.test.tsx`

- [ ] **Step 1: Add failing Studio tests**

Modify `frontend/src/studio/StudioPage.test.tsx` imports:

```ts
import { createChapter, generateCharacterArcReport, writeChapter } from '../api/client';
import type { ChapterExecutionContext, DraftResponse, WorldOverview } from '../api/types';
```

Add test context:

```ts
const executionContext: ChapterExecutionContext = {
  source: 'next_chapter_prep',
  source_world_version: 2,
  next_chapter_number: 2,
  goal: '林砚带着湿信赴城主府外墙，并设置一次试探。',
  recommended_pov: { character_id: 1, name: '林砚' },
  source_signals: ['character_arc_progression_hint'],
  priority_characters: [{ character_id: 1, name: '林砚', role_type: 'protagonist', status: '开始调查密信', reason: '上一章提示。' }],
  priority_foreshadows: [{ foreshadow_id: 1, title: '裂纹玉佩', status: 'advanced', urgency_level: 4, reason: '该伏笔需要推进。' }],
  progression_hints: [{ hint_type: 'character', priority: 'high', title: '试探沈微霜是否可信', rationale: '上一章已经建立湿信线索。', suggested_next_beat: '林砚带着湿信赴城主府外墙，并设置一次试探。', related_character_ids: [1], related_foreshadow_ids: [1], can_seed_next_chapter_goal: true }],
  continuity_warnings: [{ severity: 'medium', category: 'character_arc', message: '下一章需要补足试探过程。', related_character_ids: [1], related_foreshadow_ids: [] }],
  recent_events: [{ id: 4, event_type: 'chapter_approved', world_version_before: 1, world_version_after: 2, created_at: '2026-05-30T00:00:00Z' }],
};
```

Update mocked `createChapter` result to include:

```ts
execution_context: executionContext,
```

Update `draftResponse` to include:

```ts
execution_context: executionContext,
```

Add tests:

```tsx
it('shows launch execution context summary and submits edited context when creating chapter', async () => {
  const user = userEvent.setup();
  render(<StudioPage world={world} launchContext={{ initialChapterGoal: executionContext.goal, executionContext }} onBack={vi.fn()} onApproved={vi.fn()} />);

  expect(screen.getByText('本章执行上下文')).toBeInTheDocument();
  expect(screen.getByText('来源：下一章准备台')).toBeInTheDocument();
  expect(screen.getByText('推荐 POV：林砚')).toBeInTheDocument();
  expect(screen.getByText('优先角色：林砚')).toBeInTheDocument();
  expect(screen.getByText('优先伏笔：裂纹玉佩')).toBeInTheDocument();

  const goal = screen.getByLabelText('章节目标');
  await user.clear(goal);
  await user.type(goal, '用户编辑后的执行目标');
  await user.click(screen.getByRole('button', { name: '创建章节' }));

  expect(createChapter).toHaveBeenCalledWith(7, expect.objectContaining({
    chapter_goal: '用户编辑后的执行目标',
    execution_context: expect.objectContaining({
      source: 'next_chapter_prep',
      goal: '用户编辑后的执行目标',
      recommended_pov: { character_id: 1, name: '林砚' },
    }),
  }));
  expect(await screen.findByText('已冻结执行上下文：next_chapter_prep · v2')).toBeInTheDocument();
});

it('creates manual context when Studio opens without NCC execution context', async () => {
  const user = userEvent.setup();
  render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

  expect(screen.getByText('本章暂无 NCC 执行上下文。创建章节时会根据当前目标生成手动上下文快照。')).toBeInTheDocument();
  await user.type(screen.getByLabelText('章节目标'), '手动输入章节目标');
  await user.click(screen.getByRole('button', { name: '创建章节' }));

  expect(createChapter).toHaveBeenCalledWith(7, expect.objectContaining({
    execution_context: expect.objectContaining({
      source: 'manual',
      goal: '手动输入章节目标',
      source_signals: ['manual'],
    }),
  }));
});

it('shows frozen execution context snapshot after drafting', async () => {
  const user = userEvent.setup();
  render(<StudioPage world={world} launchContext={{ initialChapterGoal: executionContext.goal, executionContext }} onBack={vi.fn()} onApproved={vi.fn()} />);

  await user.click(screen.getByRole('button', { name: '创建章节' }));
  await user.click(await screen.findByRole('button', { name: '生成大纲' }));
  await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));

  expect(await screen.findByText('执行上下文快照')).toBeInTheDocument();
  expect(screen.getByText('目标：林砚带着湿信赴城主府外墙，并设置一次试探。')).toBeInTheDocument();
  expect(screen.getByText('连续性提醒：下一章需要补足试探过程。')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run Studio tests to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx
```

Expected: FAIL because `StudioPage` still accepts `initialChapterGoal`, does not display context summary, and does not submit context.

- [ ] **Step 3: Update StudioPage props and create payload**

Modify imports:

```tsx
import type { ApprovalPreviewResponse, BeatCard, ChapterExecutionContext, ChapterPipelineResponse, CharacterArcReportResponse, CriticReportResponse, DraftDiffResponse, DraftResponse, StudioLaunchContext, WorldOverview } from '../api/types';
import { withEditedGoal } from '../world/chapterExecutionContext';
```

Update props:

```tsx
type Props = { world: WorldOverview; launchContext?: StudioLaunchContext; onBack: () => void; onApproved: (world: WorldOverview) => void };
```

Update component signature/state:

```tsx
export function StudioPage({ world, launchContext, onBack, onApproved }: Props) {
  const [goal, setGoal] = useState(launchContext?.initialChapterGoal ?? '');
  const [executionContext] = useState(launchContext?.executionContext);
```

Update story arc fallback guard:

```tsx
if (launchContext?.initialChapterGoal || chapter || goal.trim().length > 0) return;
```

Update create call:

```tsx
const frozenContext = withEditedGoal(executionContext, world, goal);
const created = await createChapterRequest(world.id, {
  chapter_goal: goal,
  title: goal.slice(0, 40),
  execution_context: frozenContext,
});
```

- [ ] **Step 4: Add context summary renderer**

In `StudioPage.tsx`, add helper components above `StudioPage`:

```tsx
function sourceLabel(source: ChapterExecutionContext['source']): string {
  return source === 'next_chapter_prep' ? '下一章准备台' : '手动';
}

function names(values: Array<{ name?: string; title?: string }>): string {
  return values.map((value) => value.name ?? value.title).filter(Boolean).join('、') || '无';
}

function ExecutionContextSummary({ context, frozen }: { context?: ChapterExecutionContext | null; frozen?: boolean }) {
  if (!context) {
    return (
      <div className="book-card p-5">
        <h2 className="font-black text-[#3b2511]">本章执行上下文</h2>
        <p className="mt-3 ink-muted">本章暂无 NCC 执行上下文。创建章节时会根据当前目标生成手动上下文快照。</p>
      </div>
    );
  }
  return (
    <div className="book-card p-5">
      <h2 className="font-black text-[#3b2511]">本章执行上下文</h2>
      {frozen && <p className="mt-2 text-sm font-bold text-[#5e3b1c]">已冻结执行上下文：{context.source} · v{context.source_world_version}</p>}
      <p className="mt-3 ink-muted">来源：{sourceLabel(context.source)}</p>
      <p className="mt-2 ink-muted">源世界版本：v{context.source_world_version}</p>
      <p className="mt-2 ink-muted">建议章节：第 {context.next_chapter_number ?? '?'} 章</p>
      <p className="mt-2 ink-muted">推荐 POV：{context.recommended_pov.name ?? '暂无'}</p>
      <p className="mt-2 ink-muted">优先角色：{names(context.priority_characters)}</p>
      <p className="mt-2 ink-muted">优先伏笔：{names(context.priority_foreshadows)}</p>
      <p className="mt-2 ink-muted">推进提示：{context.progression_hints.length} 条</p>
      <p className="mt-2 ink-muted">连续性提醒：{context.continuity_warnings.length} 条</p>
    </div>
  );
}

function ExecutionContextSnapshot({ context }: { context?: ChapterExecutionContext | null }) {
  if (!context) return null;
  return (
    <section className="space-y-3 rounded-2xl bg-white/35 p-4">
      <h3 className="font-black text-[#3b2511]">执行上下文快照</h3>
      <p className="manuscript text-sm">来源：{sourceLabel(context.source)} · v{context.source_world_version}</p>
      <p className="manuscript text-sm">目标：{context.goal}</p>
      <p className="manuscript text-sm">推荐 POV：{context.recommended_pov.name ?? '暂无'}</p>
      <p className="manuscript text-sm">优先角色：{names(context.priority_characters)}</p>
      <p className="manuscript text-sm">优先伏笔：{names(context.priority_foreshadows)}</p>
      {context.progression_hints.map((hint) => (
        <p key={hint.title} className="manuscript text-sm">推进提示：{hint.title}</p>
      ))}
      {context.continuity_warnings.map((warning, index) => (
        <p key={`${warning.category}-${index}`} className="manuscript text-sm">连续性提醒：{warning.message}</p>
      ))}
    </section>
  );
}
```

Render in sidebar after current context card:

```tsx
<ExecutionContextSummary context={chapter?.execution_context ?? executionContext} frozen={Boolean(chapter?.execution_context)} />
```

Render in draft article near context summary:

```tsx
<ExecutionContextSnapshot context={draft.execution_context ?? chapter?.execution_context} />
```

- [ ] **Step 5: Run Studio tests to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx
```

Expected: PASS.

---

## Task 7: Chapter history frontend context display

**Files:**
- Modify: `frontend/src/world/ChapterHistoryPanel.tsx`
- Modify: `frontend/src/world/ChapterHistoryPanel.test.tsx`

- [ ] **Step 1: Add failing history panel test**

Modify `frontend/src/world/ChapterHistoryPanel.test.tsx` `detail` object to include:

```ts
execution_context: {
  source: 'next_chapter_prep',
  source_world_version: 2,
  next_chapter_number: 2,
  goal: '林砚带着湿信赴城主府外墙，并设置一次试探。',
  recommended_pov: { character_id: 1, name: '林砚' },
  source_signals: ['character_arc_progression_hint'],
  priority_characters: [{ character_id: 1, name: '林砚', role_type: 'protagonist', status: '开始调查密信', reason: '上一章提示。' }],
  priority_foreshadows: [{ foreshadow_id: 1, title: '裂纹玉佩', status: 'advanced', urgency_level: 4, reason: '该伏笔需要推进。' }],
  progression_hints: [],
  continuity_warnings: [{ severity: 'medium', category: 'character_arc', message: '下一章需要补足试探过程。', related_character_ids: [1], related_foreshadow_ids: [] }],
  recent_events: [],
},
```

Add assertions after detail loads:

```ts
expect(screen.getByText('执行上下文快照')).toBeInTheDocument();
expect(screen.getByText('目标：林砚带着湿信赴城主府外墙，并设置一次试探。')).toBeInTheDocument();
expect(screen.getByText('推荐 POV：林砚')).toBeInTheDocument();
expect(screen.getByText('优先伏笔：裂纹玉佩')).toBeInTheDocument();
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/ChapterHistoryPanel.test.tsx
```

Expected: FAIL because the panel does not display execution context.

- [ ] **Step 3: Render history context snapshot**

Modify `frontend/src/world/ChapterHistoryPanel.tsx`:

```tsx
function contextNames(values: Array<{ name?: string; title?: string }>): string {
  return values.map((value) => value.name ?? value.title).filter(Boolean).join('、') || '无';
}
```

Inside `selectedDetail` rendering after approved content:

```tsx
{selectedDetail.execution_context && (
  <div className="rounded-2xl bg-white/35 p-4">
    <h4 className="font-black text-[#3b2511]">执行上下文快照</h4>
    <p className="manuscript mt-2 text-sm">目标：{selectedDetail.execution_context.goal}</p>
    <p className="manuscript mt-1 text-sm">推荐 POV：{selectedDetail.execution_context.recommended_pov.name ?? '暂无'}</p>
    <p className="manuscript mt-1 text-sm">优先角色：{contextNames(selectedDetail.execution_context.priority_characters)}</p>
    <p className="manuscript mt-1 text-sm">优先伏笔：{contextNames(selectedDetail.execution_context.priority_foreshadows)}</p>
  </div>
)}
```

- [ ] **Step 4: Run test to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/ChapterHistoryPanel.test.tsx
```

Expected: PASS.

---

## Task 8: Regression and final integration

**Files:**
- No planned code changes unless tests expose integration errors.

- [ ] **Step 1: Run targeted backend tests**

Run:

```bash
cd /opt/WorldSim-Writer/backend && pytest tests/test_chapter_execution_context.py -v
cd /opt/WorldSim-Writer/backend && pytest tests/test_narrative_approval.py -v
cd /opt/WorldSim-Writer/backend && pytest tests/test_narrative_control_center.py::test_next_chapter_prep_does_not_mutate_world_version_or_write_events -v
```

Expected: all targeted backend tests PASS.

- [ ] **Step 2: Run full backend tests**

Run:

```bash
cd /opt/WorldSim-Writer/backend && pytest -v
```

Expected: full backend suite PASS.

- [ ] **Step 3: Run targeted frontend tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/chapterExecutionContext.test.ts src/world/NextChapterPrepPanel.test.tsx src/world/WorldPage.test.tsx src/studio/StudioPage.test.tsx src/world/ChapterHistoryPanel.test.tsx
```

Expected: all targeted frontend tests PASS.

- [ ] **Step 4: Run full frontend tests and build**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: frontend test suite and build PASS.

- [ ] **Step 5: Inspect git diff**

Run:

```bash
git status --short
git diff --stat
```

Expected: only MVP #4 implementation files are changed.

- [ ] **Step 6: Commit implementation**

Run:

```bash
git add backend/app/narrative/models.py backend/app/narrative/schemas.py backend/app/narrative/router.py backend/app/narrative/service.py backend/alembic/versions/0011_add_chapter_execution_context.py backend/tests/test_chapter_execution_context.py frontend/src/api/types.ts frontend/src/api/client.ts frontend/src/world/chapterExecutionContext.ts frontend/src/world/chapterExecutionContext.test.ts frontend/src/world/NextChapterPrepPanel.tsx frontend/src/world/NextChapterPrepPanel.test.tsx frontend/src/world/WorldPage.tsx frontend/src/world/WorldPage.test.tsx frontend/src/App.tsx frontend/src/studio/StudioPage.tsx frontend/src/studio/StudioPage.test.tsx frontend/src/world/ChapterHistoryPanel.tsx frontend/src/world/ChapterHistoryPanel.test.tsx
git commit -m "feat: add chapter execution context" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

Expected: commit succeeds on `feat/mvp-4-chapter-execution-context`.

- [ ] **Step 7: Merge to main after verification**

Run:

```bash
git switch main
git merge --no-ff feat/mvp-4-chapter-execution-context -m "Merge branch 'feat/mvp-4-chapter-execution-context'"
```

Expected: merge succeeds with no conflicts.

---

## Plan Self-Review

- Spec coverage: covered schema, persistence, frontend handoff, Studio display, create payload, backend prompt use, draft/history exposure, direct draft compatibility, and approval/read-only invariants.
- Placeholder scan: no `TBD`, `TODO`, `fill in`, or open-ended implementation instructions are intentionally present.
- Type consistency: `ChapterExecutionContext`, `StudioLaunchContext`, `execution_context`, `onUseContext`, and `onEnterStudioWithContext` are used consistently across backend and frontend tasks.
