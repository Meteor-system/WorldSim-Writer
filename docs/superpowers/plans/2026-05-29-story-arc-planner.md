# Story Arc Planner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a persisted Story Arc Planner that generates a 10-chapter arc from world canon, characters, and foreshadows, displays it on the world overview page, and prefills the Studio goal for the next approved-chapter slot.

**Architecture:** Store the latest arc as JSONB on `World.story_arc`, expose it through world overview, and add a world-scoped `POST /worlds/{world_id}/story-arc` endpoint. Keep Story Arc Planner prompt/service code in `app.world.story_arc`, parse the LLM response as a strict top-level JSON array, and keep formal world-state changes limited to existing chapter approval paths.

**Tech Stack:** FastAPI, SQLAlchemy 2, Alembic, Pydantic v2, pytest, React, TypeScript, Vite.

---

## File structure

- Create `backend/app/world/story_arc.py` — Story Arc Planner prompt builder, service function, model-client setup, and model error mapping.
- Create `backend/tests/test_story_arc.py` — backend parser, prompt, API, overwrite, error, and approved-count tests.
- Create `backend/alembic/versions/0006_add_world_story_arc.py` — adds `worlds.story_arc` JSONB column.
- Modify `backend/app/llm/schemas.py` — add `StoryArcChapter`, `parse_story_arc()`, and validation helper.
- Modify `backend/app/llm/client.py` — add `MOCK_STORY_ARC`, allow top-level JSON array calls, and add `generate_story_arc()`.
- Modify `backend/app/world/models.py` — add `story_arc` mapped JSONB column.
- Modify `backend/app/world/schemas.py` — add `StoryArcResponse`; add `story_arc` and `approved_chapter_count` to overview response.
- Modify `backend/app/world/service.py` — add `count_approved_chapters()` and include arc/count in `get_world_overview()`.
- Modify `backend/app/world/router.py` — add `POST /worlds/{world_id}/story-arc`.
- Modify `frontend/src/api/types.ts` — add story arc types and extend `WorldOverview`.
- Modify `frontend/src/api/client.ts` — add `generateStoryArc()`.
- Modify `frontend/src/world/WorldPage.tsx` — add generation button, loading state, error handling, and arc card list.
- Modify `frontend/src/studio/StudioPage.tsx` — prefill chapter goal from next story arc chapter.

---

### Task 1: Add backend Story Arc parser and validation

**Files:**
- Modify: `backend/app/llm/schemas.py`
- Create: `backend/tests/test_story_arc.py`

- [ ] **Step 1: Write failing parser tests**

Append these tests to new file `backend/tests/test_story_arc.py`:

```python
import json

import pytest

from app.llm.schemas import StoryArcChapter, parse_story_arc


def valid_story_arc_payload(title_suffix: str = '') -> list[dict]:
    return [
        {
            'chapter_number': index,
            'title': f'第{index}章 暗潮{title_suffix}',
            'summary': f'第{index}章推进灵脉危机，并让林砚面对新的选择。',
            'core_conflict': '林砚必须在自保与揭露城主府秘密之间做选择。',
            'pov_suggestion': '林砚',
            'foreshadow_hints': ['裂纹玉佩'],
        }
        for index in range(1, 11)
    ]


def test_parse_story_arc_accepts_strict_ten_chapter_array():
    parsed = parse_story_arc(json.dumps(valid_story_arc_payload()))

    assert len(parsed) == 10
    assert parsed[0].chapter_number == 1
    assert parsed[-1].chapter_number == 10
    assert parsed[0].foreshadow_hints == ['裂纹玉佩']


@pytest.mark.parametrize(
    'payload',
    [
        {'story_arc': valid_story_arc_payload()},
        valid_story_arc_payload()[:9],
        valid_story_arc_payload() + [valid_story_arc_payload()[0] | {'chapter_number': 11}],
        [valid_story_arc_payload()[0] | {'chapter_number': 2}] + valid_story_arc_payload()[1:],
        [valid_story_arc_payload()[0] | {'title': '   '}] + valid_story_arc_payload()[1:],
    ],
)
def test_parse_story_arc_rejects_invalid_shape(payload):
    with pytest.raises(ValueError, match='MODEL_RESPONSE_INVALID'):
        parse_story_arc(json.dumps(payload))
```

- [ ] **Step 2: Run parser tests to verify they fail**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_story_arc.py::test_parse_story_arc_accepts_strict_ten_chapter_array tests/test_story_arc.py::test_parse_story_arc_rejects_invalid_shape -v'
```

Expected: FAIL because `StoryArcChapter` and `parse_story_arc` do not exist yet.

- [ ] **Step 3: Implement parser and strict validation**

Modify `backend/app/llm/schemas.py`:

```python
import json
from typing import Any

from pydantic import BaseModel, Field, TypeAdapter, ValidationError, field_validator
```

Add this code after `ChapterOutline`:

```python
class StoryArcChapter(BaseModel):
    chapter_number: int = Field(ge=1, le=10)
    title: str
    summary: str
    core_conflict: str
    pov_suggestion: str
    foreshadow_hints: list[str] = Field(default_factory=list)

    @field_validator('title', 'summary', 'core_conflict', 'pov_suggestion')
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError('must not be blank')
        return stripped

    @field_validator('foreshadow_hints')
    @classmethod
    def validate_foreshadow_hints(cls, value: list[str]) -> list[str]:
        hints = [hint.strip() for hint in value if hint.strip()]
        if len(hints) != len(value):
            raise ValueError('foreshadow hints must not be blank')
        return hints
```

Add this helper and parser after `parse_chapter_outline()`:

```python
def _validate_story_arc(chapters: list[StoryArcChapter]) -> list[StoryArcChapter]:
    if len(chapters) != 10:
        raise ValueError('MODEL_RESPONSE_INVALID')
    if [chapter.chapter_number for chapter in chapters] != list(range(1, 11)):
        raise ValueError('MODEL_RESPONSE_INVALID')
    return chapters


def parse_story_arc(raw_text: str) -> list[StoryArcChapter]:
    try:
        payload = _load_json(raw_text)
        if not isinstance(payload, list):
            raise ValueError('MODEL_RESPONSE_INVALID')
        chapters = TypeAdapter(list[StoryArcChapter]).validate_python(payload)
        return _validate_story_arc(chapters)
    except (ValidationError, ValueError) as exc:
        raise ValueError('MODEL_RESPONSE_INVALID') from exc
```

- [ ] **Step 4: Run parser tests to verify they pass**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_story_arc.py::test_parse_story_arc_accepts_strict_ten_chapter_array tests/test_story_arc.py::test_parse_story_arc_rejects_invalid_shape -v'
```

Expected: PASS.

- [ ] **Step 5: Commit parser changes if commits are authorized**

Run only if the user has explicitly authorized commits for this session:

```bash
git add backend/app/llm/schemas.py backend/tests/test_story_arc.py
git commit -m "feat: validate story arc model output"
```

---

### Task 2: Add Story Arc LLM client support and mock response

**Files:**
- Modify: `backend/app/llm/client.py`
- Modify: `backend/tests/test_story_arc.py`

- [ ] **Step 1: Write failing LLM client tests**

Append to `backend/tests/test_story_arc.py`:

```python
from app.llm.client import LLMClient


def test_llm_client_mock_generates_ten_chapter_story_arc():
    chapters = LLMClient(mock=True).generate_story_arc([])

    assert len(chapters) == 10
    assert chapters[0].chapter_number == 1
    assert chapters[-1].chapter_number == 10
    assert chapters[0].summary


def test_story_arc_client_call_does_not_force_json_object_response(monkeypatch):
    captured_payloads = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                'choices': [
                    {'message': {'content': json.dumps(valid_story_arc_payload())}}
                ]
            }

    def fake_post(*args, **kwargs):
        captured_payloads.append(kwargs['json'])
        return FakeResponse()

    monkeypatch.setattr('app.llm.client.httpx.post', fake_post)

    chapters = LLMClient(mock=False).generate_story_arc([{'role': 'user', 'content': '返回数组'}])

    assert len(chapters) == 10
    assert 'response_format' not in captured_payloads[0]
```

- [ ] **Step 2: Run LLM client tests to verify they fail**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_story_arc.py::test_llm_client_mock_generates_ten_chapter_story_arc tests/test_story_arc.py::test_story_arc_client_call_does_not_force_json_object_response -v'
```

Expected: FAIL because `generate_story_arc()` is not implemented.

- [ ] **Step 3: Implement mock and array-safe client call**

Modify imports in `backend/app/llm/client.py`:

```python
from app.llm.schemas import (
    ChapterGeneration,
    ChapterOutline,
    CritiqueReport,
    StoryArcChapter,
    parse_chapter_generation,
    parse_chapter_outline,
    parse_critique_report,
    parse_story_arc,
)
```

Add after `MOCK_CRITIQUE`:

```python
MOCK_STORY_ARC = [
    {
        "chapter_number": 1,
        "title": "裂纹玉佩的召唤",
        "summary": "林砚发现裂纹玉佩开始指向青岚城深处。城主府的异常灵力让他意识到灵脉危机并非自然衰退。",
        "core_conflict": "林砚必须决定是否冒险调查城主府。",
        "pov_suggestion": "林砚",
        "foreshadow_hints": ["裂纹玉佩"],
    },
    {
        "chapter_number": 2,
        "title": "密道外的拦截",
        "summary": "沈微霜在城主府外阻止林砚靠近密道。两人的对峙暴露她知道灵脉衰退的隐情。",
        "core_conflict": "林砚必须判断沈微霜是敌是友。",
        "pov_suggestion": "林砚",
        "foreshadow_hints": ["城主府密道"],
    },
    {
        "chapter_number": 3,
        "title": "忘归书阁",
        "summary": "雨夜中，林砚进入只在灵力紊乱时出现的忘归书阁。古书预言青岚灵脉将在三日后断绝。",
        "core_conflict": "林砚必须接受预言并寻找可信盟友。",
        "pov_suggestion": "林砚",
        "foreshadow_hints": ["预言古书"],
    },
    {
        "chapter_number": 4,
        "title": "师门旧债",
        "summary": "林砚发现师门旧案与城主府封印有关。继续追查可能让他背负叛徒后人的污名。",
        "core_conflict": "林砚必须在个人名誉与真相之间取舍。",
        "pov_suggestion": "林砚",
        "foreshadow_hints": ["师门旧案"],
    },
    {
        "chapter_number": 5,
        "title": "灵井回声",
        "summary": "地下灵井传来第二个人的脚步声，证明有人正在提前抽离灵脉。沈微霜被迫透露她一直在监视灵井。",
        "core_conflict": "林砚与沈微霜必须短暂合作却无法互相信任。",
        "pov_suggestion": "沈微霜",
        "foreshadow_hints": ["灵井异响"],
    },
    {
        "chapter_number": 6,
        "title": "城主的空座",
        "summary": "城主公开露面时表现得像被某种契约操控。林砚意识到真正的对手可能藏在城主身后。",
        "core_conflict": "林砚必须揭穿操控者而不惊动城主府守卫。",
        "pov_suggestion": "林砚",
        "foreshadow_hints": ["城主府叛乱传闻"],
    },
    {
        "chapter_number": 7,
        "title": "玉佩中的名字",
        "summary": "裂纹玉佩映出一个被抹去的名字，指向林砚家族与灵脉契约的源头。线索同时引来城主府追兵。",
        "core_conflict": "林砚必须保护线索并面对自己的血脉身份。",
        "pov_suggestion": "林砚",
        "foreshadow_hints": ["裂纹玉佩", "血脉契约"],
    },
    {
        "chapter_number": 8,
        "title": "三日之限",
        "summary": "预言中的最后一日到来，青岚城开始出现灵力枯竭。林砚必须选择先救城民还是先阻止幕后仪式。",
        "core_conflict": "救人会错过仪式，阻止仪式会牺牲眼前城民。",
        "pov_suggestion": "林砚",
        "foreshadow_hints": ["三日倒计时"],
    },
    {
        "chapter_number": 9,
        "title": "地下封印",
        "summary": "林砚与沈微霜进入地下封印核心，发现灵脉断绝是旧契约反噬。两人必须共同承担解除封印的代价。",
        "core_conflict": "解除封印需要牺牲一段关键记忆。",
        "pov_suggestion": "沈微霜",
        "foreshadow_hints": ["地下封印", "血脉契约"],
    },
    {
        "chapter_number": 10,
        "title": "青岚新脉",
        "summary": "林砚用玉佩重写契约，保住青岚城但改变了自己与灵脉的关系。旧伏笔得到回收，新危机在灵脉深处苏醒。",
        "core_conflict": "胜利的代价让林砚成为新契约的承载者。",
        "pov_suggestion": "林砚",
        "foreshadow_hints": ["裂纹玉佩", "青岚灵脉"],
    },
]
```

Replace `_post_json()` with this version:

```python
    def _post_json(self, messages: list[dict[str, str]], temperature: float = 0.7, json_object: bool = True) -> str:
        base_url = str(self.settings.llm_base_url).rstrip('/')
        request_payload = {
            'model': self.settings.llm_model,
            'messages': messages,
            'temperature': temperature,
        }
        if json_object:
            request_payload['response_format'] = {'type': 'json_object'}
        try:
            response = httpx.post(
                f'{base_url}/chat/completions',
                headers={'Authorization': f'Bearer {self.settings.llm_api_key}'},
                json=request_payload,
                timeout=self.settings.llm_timeout_seconds,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise TimeoutError('MODEL_TIMEOUT') from exc
        except httpx.HTTPError as exc:
            raise RuntimeError('MODEL_REQUEST_FAILED') from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise ValueError('MODEL_RESPONSE_INVALID') from exc
        if not isinstance(payload, dict):
            raise ValueError('MODEL_RESPONSE_INVALID')
        choices = payload.get('choices', [])
        if not choices or not isinstance(choices[0], dict):
            raise ValueError('MODEL_RESPONSE_INVALID')
        content = choices[0].get('message', {}).get('content')
        if not isinstance(content, str):
            raise ValueError('MODEL_RESPONSE_INVALID')
        return content
```

Add this method before `generate_outline()`:

```python
    def generate_story_arc(self, messages: list[dict[str, str]]) -> list[StoryArcChapter]:
        if self.mock:
            return parse_story_arc(json.dumps(MOCK_STORY_ARC, ensure_ascii=False))
        return parse_story_arc(self._post_json(messages, temperature=0.4, json_object=False))
```

Also add `import json` at the top of `backend/app/llm/client.py`.

- [ ] **Step 4: Run LLM client tests to verify they pass**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_story_arc.py::test_llm_client_mock_generates_ten_chapter_story_arc tests/test_story_arc.py::test_story_arc_client_call_does_not_force_json_object_response -v'
```

Expected: PASS.

- [ ] **Step 5: Run existing narrative tests for client compatibility**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_approval.py::test_create_draft_with_fake_llm -v'
```

Expected: PASS.

- [ ] **Step 6: Commit LLM client changes if commits are authorized**

Run only if the user has explicitly authorized commits for this session:

```bash
git add backend/app/llm/client.py backend/tests/test_story_arc.py
git commit -m "feat: add story arc llm client"
```

---

### Task 3: Persist story arcs and expose overview metadata

**Files:**
- Create: `backend/alembic/versions/0006_add_world_story_arc.py`
- Modify: `backend/app/world/models.py`
- Modify: `backend/app/world/schemas.py`
- Modify: `backend/app/world/service.py`
- Modify: `backend/tests/test_story_arc.py`

- [ ] **Step 1: Write failing overview persistence/count tests**

Append to `backend/tests/test_story_arc.py`:

```python
from app.narrative.models import Chapter
from app.world.models import World


def register_and_create_world(client):
    token = client.post('/auth/register', json={'email': 'arc-writer@example.com', 'password': 'strongpass123'}).json()['access_token']
    world = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {token}'}).json()
    return token, world['id']


def test_world_overview_includes_story_arc_and_approved_chapter_count(client, db_session):
    token, world_id = register_and_create_world(client)
    world = db_session.get(World, world_id)
    world.story_arc = [chapter.model_dump() for chapter in parse_story_arc(json.dumps(valid_story_arc_payload()))]
    db_session.add_all(
        [
            Chapter(world_id=world_id, title='批准章', status='approved', draft_version=1, base_world_version=1),
            Chapter(world_id=world_id, title='草稿章', status='drafting', draft_version=1, base_world_version=1),
            Chapter(world_id=world_id, title='驳回章', status='rejected', draft_version=1, base_world_version=1),
        ]
    )
    db_session.commit()

    response = client.get(f'/worlds/{world_id}/overview', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    payload = response.json()
    assert payload['story_arc'][0]['chapter_number'] == 1
    assert payload['approved_chapter_count'] == 1
```

- [ ] **Step 2: Run overview test to verify it fails**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_story_arc.py::test_world_overview_includes_story_arc_and_approved_chapter_count -v'
```

Expected: FAIL because `World.story_arc` and overview fields do not exist.

- [ ] **Step 3: Add database migration**

Create `backend/alembic/versions/0006_add_world_story_arc.py`:

```python
"""add world story arc

Revision ID: 0006_add_world_story_arc
Revises: 0005_add_foreshadow_events
Create Date: 2026-05-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0006_add_world_story_arc'
down_revision: str | None = '0005_add_foreshadow_events'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'worlds',
        sa.Column(
            'story_arc',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column('worlds', 'story_arc')
```

- [ ] **Step 4: Add model field**

Modify `backend/app/world/models.py` by adding this mapped column after `current_foreshadows`:

```python
    story_arc: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
```

- [ ] **Step 5: Add response schema fields**

Modify imports in `backend/app/world/schemas.py`:

```python
from app.llm.schemas import StoryArcChapter
```

Add to `WorldOverviewResponse`:

```python
    story_arc: list[StoryArcChapter]
    approved_chapter_count: int
```

- [ ] **Step 6: Add approved chapter counting and overview fields**

Modify imports in `backend/app/world/service.py`:

```python
from app.narrative.models import Chapter
```

Add after `require_owned_world()`:

```python
def count_approved_chapters(db: Session, world_id: int) -> int:
    return db.scalar(
        select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id).where(Chapter.status == 'approved')
    ) or 0
```

Add these keys to the `get_world_overview()` return dict:

```python
        'story_arc': world.story_arc,
        'approved_chapter_count': count_approved_chapters(db, world.id),
```

- [ ] **Step 7: Run overview test to verify it passes**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_story_arc.py::test_world_overview_includes_story_arc_and_approved_chapter_count -v'
```

Expected: PASS.

- [ ] **Step 8: Commit persistence changes if commits are authorized**

Run only if the user has explicitly authorized commits for this session:

```bash
git add backend/alembic/versions/0006_add_world_story_arc.py backend/app/world/models.py backend/app/world/schemas.py backend/app/world/service.py backend/tests/test_story_arc.py
git commit -m "feat: persist world story arcs"
```

---

### Task 4: Add Story Arc Planner service and API endpoint

**Files:**
- Create: `backend/app/world/story_arc.py`
- Modify: `backend/app/world/router.py`
- Modify: `backend/app/world/schemas.py`
- Modify: `backend/tests/test_story_arc.py`

- [ ] **Step 1: Write failing service/API tests**

Append to `backend/tests/test_story_arc.py`:

```python
from app.world import story_arc as story_arc_service


class FakeStoryArcLLMClient:
    def __init__(self, title_suffix: str = ''):
        self.title_suffix = title_suffix
        self.messages = []

    def generate_story_arc(self, messages):
        self.messages = messages
        return parse_story_arc(json.dumps(valid_story_arc_payload(self.title_suffix)))


class FailingStoryArcLLMClient:
    def generate_story_arc(self, messages):
        raise RuntimeError('MODEL_REQUEST_FAILED')


class InvalidStoryArcLLMClient:
    def generate_story_arc(self, messages):
        raise ValueError('MODEL_RESPONSE_INVALID')


def test_build_story_arc_messages_include_world_context(client, db_session):
    token, world_id = register_and_create_world(client)
    world = db_session.get(World, world_id)
    characters = list(world.characters)
    foreshadows = list(world.foreshadows)

    messages = story_arc_service.build_story_arc_messages(world, characters, foreshadows, approved_chapter_count=0)
    combined = '\n'.join(message['content'] for message in messages)

    assert '严格 JSON 数组' in combined
    assert '正好 10 章' in combined
    assert world.truth_canon in combined
    assert characters[0].name in combined
    assert foreshadows[0].title in combined


def test_generate_story_arc_api_persists_and_returns_ten_chapters(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(story_arc_service, 'LLMClient', lambda: FakeStoryArcLLMClient())

    response = client.post(f'/worlds/{world_id}/story-arc', headers={'Authorization': f'Bearer {token}'})
    overview = client.get(f'/worlds/{world_id}/overview', headers={'Authorization': f'Bearer {token}'}).json()

    assert response.status_code == 200
    assert response.json()['world_id'] == world_id
    assert len(response.json()['story_arc']) == 10
    assert overview['story_arc'] == response.json()['story_arc']


def test_generate_story_arc_overwrites_existing_arc(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(story_arc_service, 'LLMClient', lambda: FakeStoryArcLLMClient('旧'))
    first = client.post(f'/worlds/{world_id}/story-arc', headers={'Authorization': f'Bearer {token}'}).json()

    monkeypatch.setattr(story_arc_service, 'LLMClient', lambda: FakeStoryArcLLMClient('新'))
    second = client.post(f'/worlds/{world_id}/story-arc', headers={'Authorization': f'Bearer {token}'}).json()

    assert first['story_arc'][0]['title'].endswith('旧')
    assert second['story_arc'][0]['title'].endswith('新')
    assert len(second['story_arc']) == 10


def test_generate_story_arc_maps_model_request_failure(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(story_arc_service, 'LLMClient', lambda: FailingStoryArcLLMClient())

    response = client.post(f'/worlds/{world_id}/story-arc', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 502
    assert response.json()['detail'] == 'MODEL_REQUEST_FAILED'


def test_generate_story_arc_maps_invalid_model_response(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(story_arc_service, 'LLMClient', lambda: InvalidStoryArcLLMClient())

    response = client.post(f'/worlds/{world_id}/story-arc', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 502
    assert response.json()['detail'] == 'MODEL_RESPONSE_INVALID'
```

- [ ] **Step 2: Run API tests to verify they fail**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_story_arc.py::test_build_story_arc_messages_include_world_context tests/test_story_arc.py::test_generate_story_arc_api_persists_and_returns_ten_chapters tests/test_story_arc.py::test_generate_story_arc_overwrites_existing_arc tests/test_story_arc.py::test_generate_story_arc_maps_model_request_failure tests/test_story_arc.py::test_generate_story_arc_maps_invalid_model_response -v'
```

Expected: FAIL because `app.world.story_arc` and route do not exist.

- [ ] **Step 3: Add response schema**

Add to `backend/app/world/schemas.py`:

```python
class StoryArcResponse(BaseModel):
    world_id: int
    story_arc: list[StoryArcChapter]
```

- [ ] **Step 4: Implement Story Arc Planner service**

Create `backend/app/world/story_arc.py`:

```python
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.character.models import Character
from app.core.config import get_settings
from app.foreshadow.models import Foreshadow
from app.llm.client import LLMClient
from app.llm.schemas import StoryArcChapter
from app.world.models import World
from app.world.service import count_approved_chapters, require_owned_world


def _model_client(llm_client: LLMClient | None = None) -> LLMClient:
    settings = get_settings()
    client = llm_client or LLMClient()
    if hasattr(client, 'mock'):
        client.mock = settings.llm_mock
    return client


def _map_model_error(exc: Exception) -> HTTPException:
    if isinstance(exc, TimeoutError):
        return HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail='MODEL_TIMEOUT')
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='MODEL_RESPONSE_INVALID')
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='MODEL_REQUEST_FAILED')


def _load_story_arc_context(db: Session, world: World) -> tuple[list[Character], list[Foreshadow]]:
    characters = list(db.scalars(select(Character).where(Character.world_id == world.id).order_by(Character.id)))
    foreshadows = list(
        db.scalars(select(Foreshadow).where(Foreshadow.world_id == world.id).order_by(Foreshadow.urgency_level.desc(), Foreshadow.id))
    )
    return characters, foreshadows


def build_story_arc_messages(
    world: World,
    characters: list[Character],
    foreshadows: list[Foreshadow],
    approved_chapter_count: int,
) -> list[dict[str, str]]:
    character_lines = '\n'.join(
        f'- {character.id}: {character.name}, role={character.role_type}, status={character.status}, goals={character.current_goals}, profile={character.public_profile}'
        for character in characters
    )
    foreshadow_lines = '\n'.join(
        f'- {foreshadow.id}: {foreshadow.title}, type={foreshadow.foreshadow_type}, status={foreshadow.status}, urgency={foreshadow.urgency_level}, window={foreshadow.expected_resolution_window}, description={foreshadow.description}'
        for foreshadow in foreshadows
    )
    return [
        {
            'role': 'system',
            'content': (
                '你是 WorldSim-Writer 的 Story Arc Planner。必须只返回严格 JSON 数组，不要返回对象包装、Markdown、解释或代码块。'
                '数组必须正好 10 章，每章对象只能包含字段：'
                'chapter_number, title, summary, core_conflict, pov_suggestion, foreshadow_hints。'
                'chapter_number 必须从 1 到 10 顺序排列。summary 必须是 1-2 句。'
                'foreshadow_hints 必须使用输入伏笔的 title 或 type 作为 tag，可以为空数组。'
            ),
        },
        {
            'role': 'user',
            'content': (
                f'世界标题：{world.title}\n'
                f'类型模板：{world.genre_template}\n'
                f'语气配置：{world.tone_profile}\n'
                f'世界设定：{world.truth_canon}\n'
                f'世界版本：{world.world_version}\n'
                f'已批准章节数：{approved_chapter_count}\n'
                f'角色：\n{character_lines or "无"}\n'
                f'伏笔：\n{foreshadow_lines or "无"}\n'
                '请规划前 10 章故事弧线，保持冲突递进、角色目标变化和伏笔推进节奏。'
            ),
        },
    ]


def generate_story_arc(db: Session, user: User, world_id: int, llm_client: LLMClient | None = None) -> dict:
    world = require_owned_world(db, user, world_id)
    characters, foreshadows = _load_story_arc_context(db, world)
    approved_count = count_approved_chapters(db, world.id)
    client = _model_client(llm_client)
    try:
        chapters = client.generate_story_arc(build_story_arc_messages(world, characters, foreshadows, approved_count))
    except (TimeoutError, ValueError, RuntimeError) as exc:
        raise _map_model_error(exc) from exc

    world.story_arc = [chapter.model_dump() if isinstance(chapter, StoryArcChapter) else chapter for chapter in chapters]
    db.commit()
    db.refresh(world)
    return {'world_id': world.id, 'story_arc': world.story_arc}
```

- [ ] **Step 5: Add route**

Modify `backend/app/world/router.py` imports:

```python
from app.world.schemas import StoryArcResponse, WorldCreateRequest, WorldOverviewResponse, WorldResponse
from app.world.story_arc import generate_story_arc
```

Add after the overview route:

```python
@router.post('/{world_id}/story-arc', response_model=StoryArcResponse)
def story_arc(
    world_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> StoryArcResponse:
    return StoryArcResponse.model_validate(generate_story_arc(db, current_user, world_id))
```

- [ ] **Step 6: Run API tests to verify they pass**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_story_arc.py -v'
```

Expected: PASS.

- [ ] **Step 7: Commit service/API changes if commits are authorized**

Run only if the user has explicitly authorized commits for this session:

```bash
git add backend/app/world/story_arc.py backend/app/world/router.py backend/app/world/schemas.py backend/tests/test_story_arc.py
git commit -m "feat: add story arc planner endpoint"
```

---

### Task 5: Add frontend API types and client

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/api/client.ts`

- [ ] **Step 1: Add frontend story arc types**

Modify `frontend/src/api/types.ts` after `EventLog`:

```ts
export type StoryArcChapter = {
  chapter_number: number;
  title: string;
  summary: string;
  core_conflict: string;
  pov_suggestion: string;
  foreshadow_hints: string[];
};

export type StoryArcResponse = {
  world_id: number;
  story_arc: StoryArcChapter[];
};
```

Add these fields to `WorldOverview`:

```ts
  story_arc: StoryArcChapter[];
  approved_chapter_count: number;
```

- [ ] **Step 2: Add API client helper**

Modify the type import block in `frontend/src/api/client.ts` to include `StoryArcResponse`.

Add after `getWorldEvents()`:

```ts
export function generateStoryArc(worldId: number) {
  return apiRequest<StoryArcResponse>(`/worlds/${worldId}/story-arc`, {
    method: 'POST',
    body: '{}',
  });
}
```

- [ ] **Step 3: Run TypeScript build to verify current frontend compiles**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: PASS. If it fails because later UI steps are not present yet, complete Task 6 and rerun the same command.

- [ ] **Step 4: Commit frontend API changes if commits are authorized**

Run only if the user has explicitly authorized commits for this session:

```bash
git add frontend/src/api/types.ts frontend/src/api/client.ts
git commit -m "feat: add story arc frontend client"
```

---

### Task 6: Display story arcs on WorldPage

**Files:**
- Modify: `frontend/src/world/WorldPage.tsx`

- [ ] **Step 1: Import client and type support**

Change the imports at the top of `frontend/src/world/WorldPage.tsx`:

```ts
import { apiRequest, createWorld, generateStoryArc } from '../api/client';
import type { StoryArcChapter, WorldCreateRequest, WorldOverview } from '../api/types';
```

- [ ] **Step 2: Add local generation state**

Add after the existing `error` state:

```ts
  const [arcLoading, setArcLoading] = useState(false);
```

- [ ] **Step 3: Add generation handler**

Add after `submitWorld()`:

```ts
  async function runStoryArcPlanner() {
    if (!world) return;
    setArcLoading(true);
    setError('');
    try {
      const response = await generateStoryArc(world.id);
      setWorld({ ...world, story_arc: response.story_arc });
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成故事大纲失败');
    } finally {
      setArcLoading(false);
    }
  }
```

- [ ] **Step 4: Add small render helper for arc cards**

Add above `export function WorldPage`:

```tsx
function StoryArcCard({ chapter }: { chapter: StoryArcChapter }) {
  return (
    <article className="rounded-2xl border border-amber-900/15 bg-white/35 p-4">
      <p className="chapter-kicker">第 {chapter.chapter_number} 章</p>
      <h3 className="mt-2 text-xl font-black text-[#34210f]">{chapter.title}</h3>
      <p className="manuscript mt-3">{chapter.summary}</p>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <div className="rounded-2xl bg-amber-50/60 p-3">
          <p className="text-sm font-bold text-[#5e3b1c]">核心冲突</p>
          <p className="manuscript mt-1">{chapter.core_conflict}</p>
        </div>
        <div className="rounded-2xl bg-amber-50/60 p-3">
          <p className="text-sm font-bold text-[#5e3b1c]">POV 建议</p>
          <p className="manuscript mt-1">{chapter.pov_suggestion}</p>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {chapter.foreshadow_hints.length === 0 && <span className="ink-muted text-sm">无指定伏笔</span>}
        {chapter.foreshadow_hints.map((hint) => (
          <span key={hint} className="rounded-full border border-amber-900/15 bg-amber-100/70 px-3 py-1 text-xs font-bold text-[#5e3b1c]">
            {hint}
          </span>
        ))}
      </div>
    </article>
  );
}
```

- [ ] **Step 5: Add buttons and story arc section to overview tab**

Replace the existing single Studio button:

```tsx
              <button className="primary-button mt-8" onClick={() => onEnterStudio(world)}>
                进入创作台
              </button>
```

with:

```tsx
              <div className="mt-8 flex flex-wrap gap-3">
                <button className="primary-button" onClick={() => onEnterStudio(world)}>
                  进入创作台
                </button>
                <button className="secondary-button" disabled={arcLoading} onClick={runStoryArcPlanner}>
                  {arcLoading ? '规划中...' : world.story_arc.length ? '重新生成故事大纲' : '生成故事大纲'}
                </button>
              </div>
```

Add this section after the closing `</div>` for the two-column overview grid and before `{tab === 'characters' ...}`:

```tsx
              <section className="book-card p-5 md:col-span-2">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="chapter-kicker">Story Arc Planner</p>
                    <h2 className="mt-2 text-2xl font-black text-[#34210f]">前 10 章故事弧线</h2>
                  </div>
                  <p className="ink-muted text-sm">下一章目标会按已批准章节数自动带入创作台。</p>
                </div>
                {world.story_arc.length === 0 ? (
                  <p className="manuscript mt-4">还没有故事弧线。生成后会自动为创作台填入下一章目标。</p>
                ) : (
                  <div className="mt-5 grid gap-4">
                    {world.story_arc.map((chapter) => (
                      <StoryArcCard key={chapter.chapter_number} chapter={chapter} />
                    ))}
                  </div>
                )}
              </section>
```

Keep this section inside the `tab === 'overview'` branch. If the inserted section is outside the grid, wrap the overview branch in a parent fragment so the arc section still appears only on the overview tab.

- [ ] **Step 6: Run frontend build**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: PASS.

- [ ] **Step 7: Commit WorldPage UI changes if commits are authorized**

Run only if the user has explicitly authorized commits for this session:

```bash
git add frontend/src/world/WorldPage.tsx frontend/src/api/types.ts frontend/src/api/client.ts
git commit -m "feat: display story arc planner"
```

---

### Task 7: Prefill Studio chapter goal from story arc

**Files:**
- Modify: `frontend/src/studio/StudioPage.tsx`

- [ ] **Step 1: Add prefill effect**

Add after the existing initial focus effect in `frontend/src/studio/StudioPage.tsx`:

```tsx
  useEffect(() => {
    if (chapter || goal.trim().length > 0) return;
    const nextChapterNumber = world.approved_chapter_count + 1;
    const nextArcChapter = world.story_arc.find((item) => item.chapter_number === nextChapterNumber);
    if (nextArcChapter) setGoal(nextArcChapter.summary);
  }, [chapter, goal, world.approved_chapter_count, world.story_arc]);
```

- [ ] **Step 2: Add sidebar hint for current arc target**

Add inside the `当前上下文` book-card after the POV line:

```tsx
            <p className="mt-2 ink-muted">故事大纲进度：下一章第 {world.approved_chapter_count + 1} 章</p>
```

- [ ] **Step 3: Run frontend build**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: PASS.

- [ ] **Step 4: Commit Studio prefill changes if commits are authorized**

Run only if the user has explicitly authorized commits for this session:

```bash
git add frontend/src/studio/StudioPage.tsx
git commit -m "feat: prefill studio goal from story arc"
```

---

### Task 8: Run full backend and frontend verification

**Files:**
- No planned source edits.

- [ ] **Step 1: Run backend tests**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest -v'
```

Expected: PASS for the full backend suite.

- [ ] **Step 2: Run frontend build**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: PASS.

- [ ] **Step 3: Manual smoke path**

Start backend and frontend if manual verification is requested:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && uvicorn app.main:app --reload'
```

```bash
cd /opt/WorldSim-Writer/frontend && npm run dev
```

In the browser:

1. Register or log in.
2. Create the built-in sample world.
3. Click `生成故事大纲`.
4. Confirm 10 arc cards appear.
5. Click `重新生成故事大纲` and confirm the cards refresh.
6. Enter Studio and confirm `章节目标` is filled with chapter 1 summary.
7. Create chapter, run Outliner, run Writer, approve the draft.
8. Return to WorldPage, enter Studio again, and confirm `章节目标` is filled with chapter 2 summary.

- [ ] **Step 4: Final git status review**

Run:

```bash
git status --short
```

Expected: only Story Arc Planner files and the already-existing unrelated user changes are listed. Do not revert unrelated user changes.

---

## Self-review checklist

- Spec coverage: Tasks cover persistence, API, strict JSON array parsing, mock mode, overview cards, Studio prefill, approved chapter counting, overwrite behavior, and verification.
- Placeholder scan: This plan contains concrete paths, commands, expected outcomes, and code snippets for each code change.
- Type consistency: Backend uses `StoryArcChapter`, `StoryArcResponse`, `story_arc`, and `approved_chapter_count`; frontend uses the same JSON property names.
- Scope check: The plan does not add story arc history, editing, formal events, or planning beyond 10 chapters.
