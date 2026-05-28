# Character and Foreshadow CRUD Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden Character and Foreshadow CRUD with strict validation, owner-safe references, readable frontend errors, backend tests, and verified builds.

**Architecture:** Keep the existing FastAPI domain-folder pattern and React tab components. Add schema-level validation at request boundaries, service-level ownership/reference validation before persistence, and minimal frontend fixes for no-content responses, stale world overview data, and foreshadow related-character selection.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic v2, pytest/TestClient, Vite, React, TypeScript.

---

## File structure

- Modify `backend/app/character/schemas.py`: add Pydantic validation for non-blank character strings.
- Modify `backend/app/character/service.py`: keep world ownership checks and preserve default handling while applying validated schema data.
- Modify `backend/app/foreshadow/schemas.py`: add Pydantic validation for non-blank strings and urgency range.
- Modify `backend/app/foreshadow/service.py`: add same-world validation for `related_character_ids` and `source_chapter_id` on create/update.
- Create `backend/tests/test_character_crud.py`: owner/auth and CRUD coverage for characters.
- Create `backend/tests/test_foreshadow_crud.py`: owner/auth, CRUD, and strict reference validation coverage for foreshadows.
- Modify `frontend/src/api/client.ts`: parse API errors into readable messages and return `undefined` for `204` responses.
- Modify `frontend/src/components/CharacterManager.tsx`: call parent refresh after mutations and trim submitted values.
- Modify `frontend/src/components/ForeshadowManager.tsx`: call parent refresh after mutations, replace free-text related-character IDs with selectable checkboxes, and surface quick-toggle errors.
- Modify `frontend/src/world/WorldPage.tsx`: pass a refresh callback and up-to-date characters to managers.

---

### Task 1: Add failing Character CRUD backend tests

**Files:**
- Create: `backend/tests/test_character_crud.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_character_crud.py` with:

```python
def register(client, email='writer@example.com'):
    response = client.post('/auth/register', json={'email': email, 'password': 'strongpass123'})
    return response.json()['access_token']


def create_world(client, token):
    response = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {token}'})
    return response.json()['id']


def auth(token):
    return {'Authorization': f'Bearer {token}'}


def test_character_crud_lifecycle(client):
    token = register(client)
    world_id = create_world(client, token)

    create_response = client.post(
        f'/worlds/{world_id}/characters',
        headers=auth(token),
        json={
            'name': '林七',
            'role_type': 'supporting',
            'status': 'active',
            'destiny_flag': '守门人',
            'current_goals': ['保护青岚城'],
        },
    )

    assert create_response.status_code == 200
    created = create_response.json()
    assert created['name'] == '林七'
    assert created['role_type'] == 'supporting'
    assert created['public_profile'] == {}
    assert created['hidden_traits'] == {}
    assert created['current_goals'] == ['保护青岚城']

    list_response = client.get(f'/worlds/{world_id}/characters', headers=auth(token))
    assert list_response.status_code == 200
    assert created['id'] in [item['id'] for item in list_response.json()]

    get_response = client.get(f"/characters/{created['id']}", headers=auth(token))
    assert get_response.status_code == 200
    assert get_response.json()['id'] == created['id']

    update_response = client.put(
        f"/characters/{created['id']}",
        headers=auth(token),
        json={'name': '林七改', 'current_goals': ['追查旧案']},
    )
    assert update_response.status_code == 200
    assert update_response.json()['name'] == '林七改'
    assert update_response.json()['current_goals'] == ['追查旧案']

    delete_response = client.delete(f"/characters/{created['id']}", headers=auth(token))
    assert delete_response.status_code == 204
    assert delete_response.content == b''

    missing_response = client.get(f"/characters/{created['id']}", headers=auth(token))
    assert missing_response.status_code == 404
    assert missing_response.json()['detail'] == 'NOT_FOUND'


def test_character_endpoints_require_login(client):
    response = client.get('/worlds/1/characters')

    assert response.status_code == 401
    assert response.json()['detail'] == 'UNAUTHORIZED'


def test_character_access_is_limited_to_owner(client):
    owner_token = register(client, 'owner@example.com')
    other_token = register(client, 'other@example.com')
    world_id = create_world(client, owner_token)
    create_response = client.post(
        f'/worlds/{world_id}/characters',
        headers=auth(owner_token),
        json={'name': '林七', 'role_type': 'supporting'},
    )
    character_id = create_response.json()['id']

    list_response = client.get(f'/worlds/{world_id}/characters', headers=auth(other_token))
    get_response = client.get(f'/characters/{character_id}', headers=auth(other_token))
    update_response = client.put(
        f'/characters/{character_id}',
        headers=auth(other_token),
        json={'name': '越权'},
    )
    delete_response = client.delete(f'/characters/{character_id}', headers=auth(other_token))

    assert list_response.status_code == 403
    assert list_response.json()['detail'] == 'FORBIDDEN'
    assert get_response.status_code == 403
    assert get_response.json()['detail'] == 'FORBIDDEN'
    assert update_response.status_code == 403
    assert update_response.json()['detail'] == 'FORBIDDEN'
    assert delete_response.status_code == 403
    assert delete_response.json()['detail'] == 'FORBIDDEN'


def test_character_create_rejects_blank_required_fields(client):
    token = register(client)
    world_id = create_world(client, token)

    response = client.post(
        f'/worlds/{world_id}/characters',
        headers=auth(token),
        json={'name': '   ', 'role_type': '   '},
    )

    assert response.status_code == 422
```

- [ ] **Step 2: Run character CRUD tests to verify failure**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_character_crud.py -v'
```

Expected: failure on blank-field validation if current schema accepts whitespace.

---

### Task 2: Implement Character schema validation

**Files:**
- Modify: `backend/app/character/schemas.py`
- Test: `backend/tests/test_character_crud.py`

- [ ] **Step 1: Update schemas**

Replace `backend/app/character/schemas.py` with:

```python
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _strip_required(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError('must not be blank')
    return stripped


class CharacterCreate(BaseModel):
    name: str
    role_type: str
    status: str | None = None
    public_profile: dict[str, Any] | None = None
    hidden_traits: dict[str, Any] | None = None
    destiny_flag: str | None = None
    current_goals: list[str] | None = None

    @field_validator('name', 'role_type')
    @classmethod
    def validate_required_strings(cls, value: str) -> str:
        return _strip_required(value)


class CharacterUpdate(BaseModel):
    name: str | None = None
    role_type: str | None = None
    status: str | None = None
    public_profile: dict[str, Any] | None = None
    hidden_traits: dict[str, Any] | None = None
    destiny_flag: str | None = None
    current_goals: list[str] | None = None

    @field_validator('name', 'role_type')
    @classmethod
    def validate_optional_required_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _strip_required(value)


class CharacterResponse(BaseModel):
    id: int
    name: str
    role_type: str
    status: str
    public_profile: dict[str, Any]
    hidden_traits: dict[str, Any]
    destiny_flag: str | None
    current_goals: list[str]

    model_config = ConfigDict(from_attributes=True)


class CharacterRelationResponse(BaseModel):
    id: int
    source_character_id: int
    target_character_id: int
    relation_type: str
    intensity: int
    visibility: str

    model_config = ConfigDict(from_attributes=True)
```

- [ ] **Step 2: Run character CRUD tests to verify pass**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_character_crud.py -v'
```

Expected: all tests in `test_character_crud.py` pass.

---

### Task 3: Add failing Foreshadow CRUD and reference validation tests

**Files:**
- Create: `backend/tests/test_foreshadow_crud.py`
- Uses models from: `backend/app/narrative/models.py`

- [ ] **Step 1: Write failing foreshadow tests**

Create `backend/tests/test_foreshadow_crud.py` with:

```python
def register(client, email='writer@example.com'):
    response = client.post('/auth/register', json={'email': email, 'password': 'strongpass123'})
    return response.json()['access_token']


def create_world(client, token):
    response = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {token}'})
    return response.json()['id']


def auth(token):
    return {'Authorization': f'Bearer {token}'}


def first_character_id(client, token, world_id):
    response = client.get(f'/worlds/{world_id}/characters', headers=auth(token))
    return response.json()[0]['id']


def create_chapter(db_session, world_id):
    from app.narrative.models import Chapter

    chapter = Chapter(
        world_id=world_id,
        title='测试章节',
        status='reviewing',
        draft_version=1,
        base_world_version=1,
    )
    db_session.add(chapter)
    db_session.commit()
    db_session.refresh(chapter)
    return chapter.id


def test_foreshadow_crud_lifecycle(client, db_session):
    token = register(client)
    world_id = create_world(client, token)
    character_id = first_character_id(client, token, world_id)
    chapter_id = create_chapter(db_session, world_id)

    create_response = client.post(
        f'/worlds/{world_id}/foreshadows',
        headers=auth(token),
        json={
            'source_chapter_id': chapter_id,
            'title': '铜铃异响',
            'description': '夜半铜铃无人自鸣。',
            'foreshadow_type': 'plot',
            'status': 'planted',
            'urgency_level': 4,
            'related_character_ids': [character_id],
            'expected_resolution_window': '第三幕',
        },
    )

    assert create_response.status_code == 200
    created = create_response.json()
    assert created['title'] == '铜铃异响'
    assert created['urgency_level'] == 4
    assert created['related_character_ids'] == [character_id]

    list_response = client.get(f'/worlds/{world_id}/foreshadows', headers=auth(token))
    assert list_response.status_code == 200
    assert created['id'] in [item['id'] for item in list_response.json()]

    get_response = client.get(f"/foreshadows/{created['id']}", headers=auth(token))
    assert get_response.status_code == 200
    assert get_response.json()['id'] == created['id']

    update_response = client.put(
        f"/foreshadows/{created['id']}",
        headers=auth(token),
        json={'status': 'advanced', 'urgency_level': 5, 'related_character_ids': []},
    )
    assert update_response.status_code == 200
    assert update_response.json()['status'] == 'advanced'
    assert update_response.json()['urgency_level'] == 5
    assert update_response.json()['related_character_ids'] == []

    delete_response = client.delete(f"/foreshadows/{created['id']}", headers=auth(token))
    assert delete_response.status_code == 204
    assert delete_response.content == b''

    missing_response = client.get(f"/foreshadows/{created['id']}", headers=auth(token))
    assert missing_response.status_code == 404
    assert missing_response.json()['detail'] == 'NOT_FOUND'


def test_foreshadow_endpoints_require_login(client):
    response = client.get('/worlds/1/foreshadows')

    assert response.status_code == 401
    assert response.json()['detail'] == 'UNAUTHORIZED'


def test_foreshadow_access_is_limited_to_owner(client):
    owner_token = register(client, 'owner@example.com')
    other_token = register(client, 'other@example.com')
    world_id = create_world(client, owner_token)
    create_response = client.post(
        f'/worlds/{world_id}/foreshadows',
        headers=auth(owner_token),
        json={
            'title': '铜铃异响',
            'description': '夜半铜铃无人自鸣。',
            'foreshadow_type': 'plot',
        },
    )
    foreshadow_id = create_response.json()['id']

    list_response = client.get(f'/worlds/{world_id}/foreshadows', headers=auth(other_token))
    get_response = client.get(f'/foreshadows/{foreshadow_id}', headers=auth(other_token))
    update_response = client.put(
        f'/foreshadows/{foreshadow_id}',
        headers=auth(other_token),
        json={'status': 'resolved'},
    )
    delete_response = client.delete(f'/foreshadows/{foreshadow_id}', headers=auth(other_token))

    assert list_response.status_code == 403
    assert list_response.json()['detail'] == 'FORBIDDEN'
    assert get_response.status_code == 403
    assert get_response.json()['detail'] == 'FORBIDDEN'
    assert update_response.status_code == 403
    assert update_response.json()['detail'] == 'FORBIDDEN'
    assert delete_response.status_code == 403
    assert delete_response.json()['detail'] == 'FORBIDDEN'


def test_foreshadow_rejects_blank_required_fields_and_bad_urgency(client):
    token = register(client)
    world_id = create_world(client, token)

    blank_response = client.post(
        f'/worlds/{world_id}/foreshadows',
        headers=auth(token),
        json={'title': ' ', 'description': ' ', 'foreshadow_type': ' '},
    )
    low_urgency_response = client.post(
        f'/worlds/{world_id}/foreshadows',
        headers=auth(token),
        json={
            'title': '铜铃异响',
            'description': '夜半铜铃无人自鸣。',
            'foreshadow_type': 'plot',
            'urgency_level': 0,
        },
    )
    high_urgency_response = client.post(
        f'/worlds/{world_id}/foreshadows',
        headers=auth(token),
        json={
            'title': '铜铃异响',
            'description': '夜半铜铃无人自鸣。',
            'foreshadow_type': 'plot',
            'urgency_level': 6,
        },
    )

    assert blank_response.status_code == 422
    assert low_urgency_response.status_code == 422
    assert high_urgency_response.status_code == 422


def test_foreshadow_rejects_unknown_related_character(client):
    token = register(client)
    world_id = create_world(client, token)

    response = client.post(
        f'/worlds/{world_id}/foreshadows',
        headers=auth(token),
        json={
            'title': '铜铃异响',
            'description': '夜半铜铃无人自鸣。',
            'foreshadow_type': 'plot',
            'related_character_ids': [99999],
        },
    )

    assert response.status_code == 404
    assert response.json()['detail'] == 'RELATED_CHARACTER_NOT_FOUND'


def test_foreshadow_rejects_foreign_related_character(client):
    owner_token = register(client, 'owner@example.com')
    other_token = register(client, 'other@example.com')
    owner_world_id = create_world(client, owner_token)
    other_world_id = create_world(client, other_token)
    foreign_character_id = first_character_id(client, other_token, other_world_id)

    response = client.post(
        f'/worlds/{owner_world_id}/foreshadows',
        headers=auth(owner_token),
        json={
            'title': '铜铃异响',
            'description': '夜半铜铃无人自鸣。',
            'foreshadow_type': 'plot',
            'related_character_ids': [foreign_character_id],
        },
    )

    assert response.status_code == 404
    assert response.json()['detail'] == 'RELATED_CHARACTER_NOT_FOUND'


def test_foreshadow_rejects_unknown_source_chapter(client):
    token = register(client)
    world_id = create_world(client, token)

    response = client.post(
        f'/worlds/{world_id}/foreshadows',
        headers=auth(token),
        json={
            'source_chapter_id': 99999,
            'title': '铜铃异响',
            'description': '夜半铜铃无人自鸣。',
            'foreshadow_type': 'plot',
        },
    )

    assert response.status_code == 404
    assert response.json()['detail'] == 'SOURCE_CHAPTER_NOT_FOUND'


def test_foreshadow_rejects_foreign_source_chapter(client, db_session):
    owner_token = register(client, 'owner@example.com')
    other_token = register(client, 'other@example.com')
    owner_world_id = create_world(client, owner_token)
    other_world_id = create_world(client, other_token)
    foreign_chapter_id = create_chapter(db_session, other_world_id)

    response = client.post(
        f'/worlds/{owner_world_id}/foreshadows',
        headers=auth(owner_token),
        json={
            'source_chapter_id': foreign_chapter_id,
            'title': '铜铃异响',
            'description': '夜半铜铃无人自鸣。',
            'foreshadow_type': 'plot',
        },
    )

    assert response.status_code == 404
    assert response.json()['detail'] == 'SOURCE_CHAPTER_NOT_FOUND'
```

- [ ] **Step 2: Run foreshadow tests to verify failure**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_foreshadow_crud.py -v'
```

Expected: failures for urgency validation and/or strict reference validation before implementation.

---

### Task 4: Implement Foreshadow schema and service validation

**Files:**
- Modify: `backend/app/foreshadow/schemas.py`
- Modify: `backend/app/foreshadow/service.py`
- Test: `backend/tests/test_foreshadow_crud.py`

- [ ] **Step 1: Update foreshadow schemas**

Replace `backend/app/foreshadow/schemas.py` with:

```python
from pydantic import BaseModel, ConfigDict, Field, field_validator


def _strip_required(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError('must not be blank')
    return stripped


class ForeshadowCreate(BaseModel):
    source_chapter_id: int | None = None
    title: str
    description: str
    foreshadow_type: str
    status: str | None = None
    urgency_level: int | None = Field(default=None, ge=1, le=5)
    related_character_ids: list[int] | None = None
    expected_resolution_window: str | None = None

    @field_validator('title', 'description', 'foreshadow_type')
    @classmethod
    def validate_required_strings(cls, value: str) -> str:
        return _strip_required(value)


class ForeshadowUpdate(BaseModel):
    source_chapter_id: int | None = None
    title: str | None = None
    description: str | None = None
    foreshadow_type: str | None = None
    status: str | None = None
    urgency_level: int | None = Field(default=None, ge=1, le=5)
    related_character_ids: list[int] | None = None
    expected_resolution_window: str | None = None

    @field_validator('title', 'description', 'foreshadow_type')
    @classmethod
    def validate_optional_required_strings(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _strip_required(value)


class ForeshadowResponse(BaseModel):
    id: int
    title: str
    description: str
    foreshadow_type: str
    status: str
    urgency_level: int
    related_character_ids: list[int]
    expected_resolution_window: str | None

    model_config = ConfigDict(from_attributes=True)
```

- [ ] **Step 2: Update foreshadow service**

Replace `backend/app/foreshadow/service.py` with:

```python
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.character.models import Character
from app.foreshadow.models import Foreshadow
from app.foreshadow.schemas import ForeshadowCreate, ForeshadowUpdate
from app.narrative.models import Chapter
from app.world.service import require_owned_world


def _validate_source_chapter(db: Session, world_id: int, source_chapter_id: int | None) -> None:
    if source_chapter_id is None:
        return
    chapter = db.get(Chapter, source_chapter_id)
    if chapter is None or chapter.world_id != world_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='SOURCE_CHAPTER_NOT_FOUND')


def _validate_related_characters(db: Session, world_id: int, related_character_ids: list[int] | None) -> list[int]:
    if related_character_ids is None:
        return []
    if not related_character_ids:
        return []
    character_ids = set(related_character_ids)
    found_ids = set(
        db.scalars(
            select(Character.id).where(
                Character.world_id == world_id,
                Character.id.in_(character_ids),
            )
        )
    )
    if found_ids != character_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='RELATED_CHARACTER_NOT_FOUND')
    return related_character_ids


def create_foreshadow(db: Session, user: User, world_id: int, data: ForeshadowCreate) -> Foreshadow:
    require_owned_world(db, user, world_id)
    _validate_source_chapter(db, world_id, data.source_chapter_id)
    related_character_ids = _validate_related_characters(db, world_id, data.related_character_ids)
    foreshadow = Foreshadow(
        world_id=world_id,
        source_chapter_id=data.source_chapter_id,
        title=data.title,
        description=data.description,
        foreshadow_type=data.foreshadow_type,
        status=data.status if data.status is not None else 'planted',
        urgency_level=data.urgency_level if data.urgency_level is not None else 1,
        related_character_ids=related_character_ids,
        expected_resolution_window=data.expected_resolution_window,
    )
    db.add(foreshadow)
    db.commit()
    db.refresh(foreshadow)
    return foreshadow


def get_foreshadows(db: Session, user: User, world_id: int) -> list[Foreshadow]:
    require_owned_world(db, user, world_id)
    return list(
        db.scalars(
            select(Foreshadow).where(Foreshadow.world_id == world_id).order_by(Foreshadow.id)
        )
    )


def _require_owned_foreshadow(db: Session, user: User, foreshadow_id: int) -> Foreshadow:
    foreshadow = db.get(Foreshadow, foreshadow_id)
    if foreshadow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    if foreshadow.world.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='FORBIDDEN')
    return foreshadow


def get_foreshadow(db: Session, user: User, foreshadow_id: int) -> Foreshadow:
    return _require_owned_foreshadow(db, user, foreshadow_id)


def update_foreshadow(db: Session, user: User, foreshadow_id: int, data: ForeshadowUpdate) -> Foreshadow:
    foreshadow = _require_owned_foreshadow(db, user, foreshadow_id)
    update_data = data.model_dump(exclude_unset=True)
    if 'source_chapter_id' in update_data:
        _validate_source_chapter(db, foreshadow.world_id, update_data['source_chapter_id'])
    if 'related_character_ids' in update_data:
        update_data['related_character_ids'] = _validate_related_characters(
            db,
            foreshadow.world_id,
            update_data['related_character_ids'],
        )
    for field, value in update_data.items():
        setattr(foreshadow, field, value)
    db.commit()
    db.refresh(foreshadow)
    return foreshadow


def delete_foreshadow(db: Session, user: User, foreshadow_id: int) -> None:
    foreshadow = _require_owned_foreshadow(db, user, foreshadow_id)
    db.delete(foreshadow)
    db.commit()
```

- [ ] **Step 3: Run foreshadow tests to verify pass**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_foreshadow_crud.py -v'
```

Expected: all tests in `test_foreshadow_crud.py` pass.

---

### Task 5: Fix frontend API client and manager refresh contracts

**Files:**
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/components/CharacterManager.tsx`
- Modify: `frontend/src/components/ForeshadowManager.tsx`
- Modify: `frontend/src/world/WorldPage.tsx`

- [ ] **Step 1: Update API client error/no-content handling**

In `frontend/src/api/client.ts`, replace `apiRequest` with:

```ts
function formatApiError(body: string): string {
  if (!body) return '请求失败';
  try {
    const parsed = JSON.parse(body) as { detail?: unknown };
    if (typeof parsed.detail === 'string') return parsed.detail;
    if (Array.isArray(parsed.detail)) {
      return parsed.detail
        .map((item) => {
          if (typeof item === 'object' && item && 'msg' in item) {
            return String((item as { msg: unknown }).msg);
          }
          return String(item);
        })
        .join('；');
    }
  } catch {
    return body;
  }
  return body;
}

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('worldsim_token');
  const headers = new Headers(options.headers);
  headers.set('Content-Type', 'application/json');
  if (token) headers.set('Authorization', `Bearer ${token}`);
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!response.ok) throw new Error(formatApiError(await response.text()));
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
```

Keep the existing imports and API wrapper functions.

- [ ] **Step 2: Add refresh callback to CharacterManager**

Change props and mutation success handling in `frontend/src/components/CharacterManager.tsx`:

```ts
type Props = { worldId: number; onChanged?: () => Promise<void> | void };
```

```ts
export function CharacterManager({ worldId, onChanged }: Props) {
```

After each successful create/update/delete and `await load();`, call:

```ts
await onChanged?.();
```

- [ ] **Step 3: Add refresh callback, selectable characters, and surfaced toggle errors to ForeshadowManager**

Change props in `frontend/src/components/ForeshadowManager.tsx`:

```ts
type Props = { worldId: number; characters: Character[]; onChanged?: () => Promise<void> | void };
```

Change `FormData.related_character_ids` to `number[]`:

```ts
type FormData = {
  title: string;
  description: string;
  foreshadow_type: string;
  status: string;
  urgency_level: number;
  related_character_ids: number[];
  expected_resolution_window: string;
};
```

Use an empty array in `EMPTY_FORM`, copy arrays in `formFromForeshadow`, and return `related_character_ids: f.related_character_ids` in `formToPayload`.

Add this helper inside the component:

```ts
function toggleRelatedCharacter(characterId: number) {
  setForm((current) => ({
    ...current,
    related_character_ids: current.related_character_ids.includes(characterId)
      ? current.related_character_ids.filter((id) => id !== characterId)
      : [...current.related_character_ids, characterId],
  }));
}
```

Replace the related-character ID text input with checkbox options:

```tsx
<div className="block">
  <span className="text-sm font-semibold text-[#4a321e]">关联角色</span>
  {characters.length === 0 ? (
    <p className="mt-1 text-sm ink-muted">暂无可关联角色。</p>
  ) : (
    <div className="mt-2 space-y-2 rounded-2xl border border-amber-900/15 bg-amber-50/40 p-3">
      {characters.map((character) => (
        <label key={character.id} className="flex items-center gap-2 text-sm text-[#4a321e]">
          <input
            type="checkbox"
            checked={form.related_character_ids.includes(character.id)}
            onChange={() => toggleRelatedCharacter(character.id)}
          />
          {character.name}
        </label>
      ))}
    </div>
  )}
</div>
```

After each successful create/update/delete and `await load();`, call:

```ts
await onChanged?.();
```

Replace the silent catch in `cycleStatus` with:

```ts
    } catch (err) {
      setError(err instanceof Error ? err.message : '更新伏笔状态失败');
    }
```

- [ ] **Step 4: Pass refresh callback from WorldPage**

In `frontend/src/world/WorldPage.tsx`, pass `loadWorld` into managers:

```tsx
{tab === 'characters' && <CharacterManager worldId={world.id} onChanged={loadWorld} />}

{tab === 'foreshadows' && (
  <ForeshadowManager worldId={world.id} characters={world.characters} onChanged={loadWorld} />
)}
```

- [ ] **Step 5: Run frontend build**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: build passes.

---

### Task 6: Run full backend verification

**Files:**
- No code changes expected.

- [ ] **Step 1: Run full pytest suite**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest -v'
```

Expected: all backend tests pass.

- [ ] **Step 2: Run frontend build again after any fixes**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: build passes.

---

### Task 7: Review and commit implementation

**Files:**
- Include only relevant CRUD hardening files from this plan.

- [ ] **Step 1: Request code review**

Run a code review using the repository's available review tooling before claiming completion. Address high-confidence correctness findings only.

- [ ] **Step 2: Inspect final diff**

Run:

```bash
git diff -- backend/app/character/schemas.py backend/app/character/service.py backend/app/foreshadow/schemas.py backend/app/foreshadow/service.py backend/tests/test_character_crud.py backend/tests/test_foreshadow_crud.py frontend/src/api/client.ts frontend/src/components/CharacterManager.tsx frontend/src/components/ForeshadowManager.tsx frontend/src/world/WorldPage.tsx
```

Expected: diff contains only the intended CRUD hardening changes.

- [ ] **Step 3: Commit relevant implementation files**

Run:

```bash
git add backend/app/character/schemas.py backend/app/character/service.py backend/app/foreshadow/schemas.py backend/app/foreshadow/service.py backend/tests/test_character_crud.py backend/tests/test_foreshadow_crud.py frontend/src/api/client.ts frontend/src/components/CharacterManager.tsx frontend/src/components/ForeshadowManager.tsx frontend/src/world/WorldPage.tsx docs/superpowers/plans/2026-05-29-character-foreshadow-crud.md
git commit -m "$(cat <<'EOF'
Harden character and foreshadow CRUD

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

Expected: commit succeeds without bypassing hooks.

---

## Self-review

- Spec coverage: backend ownership/reference validation is covered in Tasks 1-4; frontend no-content errors, readable errors, selectable related characters, status toggle errors, and stale overview refresh are covered in Task 5; backend pytest and frontend build verification are covered in Task 6; review and commit are covered in Task 7.
- Placeholder scan: no TBD/TODO/fill-in placeholders remain.
- Type consistency: schema field names match existing backend/frontend types: `name`, `role_type`, `status`, `current_goals`, `source_chapter_id`, `title`, `description`, `foreshadow_type`, `urgency_level`, `related_character_ids`, and `expected_resolution_window`.
