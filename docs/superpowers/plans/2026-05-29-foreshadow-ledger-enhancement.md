# Foreshadow Ledger Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Do not use subagents for this project because the user explicitly disallowed them.

**Goal:** Build a foreshadow lifecycle ledger with validated status transitions, timeline/stale APIs, chapter-approval event recording, and a frontend kanban/timeline/stale-alert UI.

**Architecture:** Foreshadow lifecycle rules live in `backend/app/foreshadow/service.py` and are reused by both manual CRUD updates and narrative approval. `ForeshadowEvent` stores the ledger timeline. The frontend keeps `ForeshadowManager` as the primary UI container and adds native HTML5 drag/drop plus a small timeline subcomponent without new dependencies.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, pytest/TestClient, React, TypeScript, Vite, Tailwind utility classes.

---

## File Structure

- Modify `backend/app/foreshadow/models.py`: add `ForeshadowEvent` ORM model and relationships.
- Modify `backend/app/foreshadow/schemas.py`: add status literals, timeline/stale response schemas, include `source_chapter_id` in response for stale/card context.
- Modify `backend/app/foreshadow/service.py`: add lifecycle constants/helpers, timeline query, status filtering, stale detection.
- Modify `backend/app/foreshadow/router.py`: add `status` query parameter, timeline endpoint, stale endpoint.
- Modify `backend/app/narrative/service.py`: call foreshadow lifecycle helper during approval.
- Create `backend/alembic/versions/0005_add_foreshadow_events.py`: create `foreshadow_events` table and indexes.
- Modify `backend/tests/test_foreshadow_crud.py`: add lifecycle, timeline, filtering, stale, and transition event tests.
- Modify `backend/tests/test_narrative_approval.py`: add approval-path foreshadow event test if current fixtures make it cleaner than CRUD tests.
- Modify `frontend/src/api/types.ts`: add `ForeshadowStatus`, `ForeshadowEvent`, `StaleForeshadow`.
- Modify `frontend/src/api/client.ts`: add status filter, timeline API, stale API.
- Modify `frontend/src/components/ForeshadowManager.tsx`: add expired status, view toggle, kanban, drag/drop, stale banner, expandable timeline.

---

### Task 1: Backend model and migration

**Files:**
- Modify: `backend/app/foreshadow/models.py`
- Create: `backend/alembic/versions/0005_add_foreshadow_events.py`
- Test indirectly: `backend/tests/conftest.py` creates all metadata in SQLite

- [ ] **Step 1: Add failing model expectation test to existing CRUD test file**

Add this test near the top of `backend/tests/test_foreshadow_crud.py` after helpers:

```python
def test_foreshadow_event_model_is_registered(db_session):
    from app.foreshadow.models import ForeshadowEvent

    table_names = set(db_session.bind.dialect.get_table_names(db_session.bind.connect()))
    assert 'foreshadow_events' in table_names
    assert ForeshadowEvent.__tablename__ == 'foreshadow_events'
```

- [ ] **Step 2: Run test and verify it fails**

Run:

```bash
cd /opt/WorldSim-Writer/backend && python -m pytest tests/test_foreshadow_crud.py::test_foreshadow_event_model_is_registered -v
```

Expected: FAIL because `ForeshadowEvent` is not defined or the table is missing.

- [ ] **Step 3: Implement ORM model**

Update `backend/app/foreshadow/models.py` imports:

```python
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
```

Add TYPE_CHECKING imports:

```python
if TYPE_CHECKING:
    from app.narrative.models import Chapter
    from app.world.models import World
```

Add relationship to `Foreshadow`:

```python
    events: Mapped[list['ForeshadowEvent']] = relationship(
        'ForeshadowEvent', back_populates='foreshadow', cascade='all, delete-orphan'
    )
```

Add class:

```python
class ForeshadowEvent(Base):
    __tablename__ = 'foreshadow_events'

    id: Mapped[int] = mapped_column(primary_key=True)
    foreshadow_id: Mapped[int] = mapped_column(ForeignKey('foreshadows.id', ondelete='CASCADE'), nullable=False, index=True)
    chapter_id: Mapped[int | None] = mapped_column(ForeignKey('chapters.id', ondelete='SET NULL'), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    foreshadow: Mapped['Foreshadow'] = relationship('Foreshadow', back_populates='events')
    chapter: Mapped['Chapter | None'] = relationship('Chapter')
```

- [ ] **Step 4: Create migration**

Create `backend/alembic/versions/0005_add_foreshadow_events.py`:

```python
"""add foreshadow events

Revision ID: 0005_add_foreshadow_events
Revises: 0004_add_state_consistency_foundation
Create Date: 2026-05-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0005_add_foreshadow_events'
down_revision: str | None = '0004_add_state_consistency_foundation'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'foreshadow_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('foreshadow_id', sa.Integer(), nullable=False),
        sa.Column('chapter_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(length=40), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['foreshadow_id'], ['foreshadows.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_foreshadow_events_chapter_id'), 'foreshadow_events', ['chapter_id'], unique=False)
    op.create_index(op.f('ix_foreshadow_events_foreshadow_id'), 'foreshadow_events', ['foreshadow_id'], unique=False)
    op.create_index('ix_foreshadow_events_foreshadow_created', 'foreshadow_events', ['foreshadow_id', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_foreshadow_events_foreshadow_created', table_name='foreshadow_events')
    op.drop_index(op.f('ix_foreshadow_events_foreshadow_id'), table_name='foreshadow_events')
    op.drop_index(op.f('ix_foreshadow_events_chapter_id'), table_name='foreshadow_events')
    op.drop_table('foreshadow_events')
```

- [ ] **Step 5: Run model test**

Run:

```bash
cd /opt/WorldSim-Writer/backend && python -m pytest tests/test_foreshadow_crud.py::test_foreshadow_event_model_is_registered -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/foreshadow/models.py backend/alembic/versions/0005_add_foreshadow_events.py backend/tests/test_foreshadow_crud.py
git commit -m "feat: add foreshadow event model"
```

---

### Task 2: Lifecycle schemas and service helpers

**Files:**
- Modify: `backend/app/foreshadow/schemas.py`
- Modify: `backend/app/foreshadow/service.py`
- Test: `backend/tests/test_foreshadow_crud.py`

- [ ] **Step 1: Write failing lifecycle tests**

Add these tests to `backend/tests/test_foreshadow_crud.py`:

```python
def create_foreshadow(client, token, world_id, title='铜铃异响', status='planted', source_chapter_id=None):
    payload = {
        'title': title,
        'description': '夜半铜铃无人自鸣。',
        'foreshadow_type': 'plot',
        'status': status,
    }
    if source_chapter_id is not None:
        payload['source_chapter_id'] = source_chapter_id
    response = client.post(f'/worlds/{world_id}/foreshadows', headers=auth(token), json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_foreshadow_status_transitions(client):
    token = register(client)
    world_id = create_world(client, token)
    foreshadow = create_foreshadow(client, token, world_id)

    advanced = client.put(f"/foreshadows/{foreshadow['id']}", headers=auth(token), json={'status': 'advanced'})
    assert advanced.status_code == 200
    assert advanced.json()['status'] == 'advanced'

    backwards = client.put(f"/foreshadows/{foreshadow['id']}", headers=auth(token), json={'status': 'planted'})
    assert backwards.status_code == 400
    assert backwards.json()['detail'] == 'INVALID_STATUS_TRANSITION'

    resolved = client.put(f"/foreshadows/{foreshadow['id']}", headers=auth(token), json={'status': 'resolved'})
    assert resolved.status_code == 200
    assert resolved.json()['status'] == 'resolved'

    terminal = client.put(f"/foreshadows/{foreshadow['id']}", headers=auth(token), json={'status': 'expired'})
    assert terminal.status_code == 400
    assert terminal.json()['detail'] == 'INVALID_STATUS_TRANSITION'

    expiring = create_foreshadow(client, token, world_id, title='井中红光')
    expired = client.put(f"/foreshadows/{expiring['id']}", headers=auth(token), json={'status': 'expired'})
    assert expired.status_code == 200
    assert expired.json()['status'] == 'expired'


def test_foreshadow_rejects_invalid_status(client):
    token = register(client)
    world_id = create_world(client, token)

    create_response = client.post(
        f'/worlds/{world_id}/foreshadows',
        headers=auth(token),
        json={'title': '铜铃异响', 'description': '夜半铜铃无人自鸣。', 'foreshadow_type': 'plot', 'status': 'bad'},
    )
    assert create_response.status_code == 400
    assert create_response.json()['detail'] == 'INVALID_STATUS'

    foreshadow = create_foreshadow(client, token, world_id)
    update_response = client.put(f"/foreshadows/{foreshadow['id']}", headers=auth(token), json={'status': 'bad'})
    assert update_response.status_code == 400
    assert update_response.json()['detail'] == 'INVALID_STATUS'
```

- [ ] **Step 2: Run tests and verify failure**

```bash
cd /opt/WorldSim-Writer/backend && python -m pytest tests/test_foreshadow_crud.py::test_foreshadow_status_transitions tests/test_foreshadow_crud.py::test_foreshadow_rejects_invalid_status -v
```

Expected: FAIL because invalid statuses and transitions are not enforced yet.

- [ ] **Step 3: Add schema types**

Update `backend/app/foreshadow/schemas.py`:

```python
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ForeshadowStatus = Literal['planted', 'advanced', 'resolved', 'expired']
```

Change status fields:

```python
status: ForeshadowStatus | None = None
```

for create/update and:

```python
status: ForeshadowStatus
```

for response. Also add `source_chapter_id` to `ForeshadowResponse`:

```python
source_chapter_id: int | None
```

- [ ] **Step 4: Add lifecycle helpers**

In `backend/app/foreshadow/service.py`, import `ForeshadowEvent`:

```python
from app.foreshadow.models import Foreshadow, ForeshadowEvent
```

Add constants and helpers after imports:

```python
FORESHADOW_STATUSES = {'planted', 'advanced', 'resolved', 'expired'}
VALID_STATUS_TRANSITIONS = {
    'planted': {'advanced', 'expired'},
    'advanced': {'resolved', 'expired'},
    'resolved': set(),
    'expired': set(),
}


def validate_foreshadow_status(status_value: str) -> None:
    if status_value not in FORESHADOW_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='INVALID_STATUS')


def validate_foreshadow_transition(current_status: str, next_status: str) -> None:
    validate_foreshadow_status(next_status)
    if current_status == next_status:
        return
    if next_status not in VALID_STATUS_TRANSITIONS.get(current_status, set()):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='INVALID_STATUS_TRANSITION')


def add_foreshadow_event(
    db: Session,
    foreshadow: Foreshadow,
    event_type: str,
    chapter_id: int | None = None,
    note: str | None = None,
) -> ForeshadowEvent:
    validate_foreshadow_status(event_type)
    event = ForeshadowEvent(
        foreshadow_id=foreshadow.id,
        chapter_id=chapter_id,
        event_type=event_type,
        note=note,
    )
    db.add(event)
    return event


def apply_foreshadow_status_transition(
    db: Session,
    foreshadow: Foreshadow,
    next_status: str,
    chapter_id: int | None = None,
    note: str | None = None,
) -> bool:
    validate_foreshadow_transition(foreshadow.status, next_status)
    if foreshadow.status == next_status:
        return False
    foreshadow.status = next_status
    add_foreshadow_event(db, foreshadow, next_status, chapter_id=chapter_id, note=note)
    return True
```

- [ ] **Step 5: Use helpers in create/update**

In `create_foreshadow`, compute and validate status before constructing model:

```python
foreshadow_status = data.status if data.status is not None else 'planted'
validate_foreshadow_status(foreshadow_status)
```

Use `status=foreshadow_status`, then after `db.add(foreshadow)` call `db.flush()` before event creation:

```python
db.add(foreshadow)
db.flush()
add_foreshadow_event(db, foreshadow, foreshadow.status, chapter_id=foreshadow.source_chapter_id)
db.commit()
```

In `update_foreshadow`, pop status before generic setattr:

```python
next_status = update_data.pop('status', None)
...
for field, value in update_data.items():
    setattr(foreshadow, field, value)
if next_status is not None:
    apply_foreshadow_status_transition(db, foreshadow, next_status)
db.commit()
```

- [ ] **Step 6: Run lifecycle tests**

```bash
cd /opt/WorldSim-Writer/backend && python -m pytest tests/test_foreshadow_crud.py::test_foreshadow_status_transitions tests/test_foreshadow_crud.py::test_foreshadow_rejects_invalid_status -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/foreshadow/schemas.py backend/app/foreshadow/service.py backend/tests/test_foreshadow_crud.py
git commit -m "feat: validate foreshadow lifecycle transitions"
```

---

### Task 3: Timeline API and transition event tests

**Files:**
- Modify: `backend/app/foreshadow/schemas.py`
- Modify: `backend/app/foreshadow/service.py`
- Modify: `backend/app/foreshadow/router.py`
- Test: `backend/tests/test_foreshadow_crud.py`

- [ ] **Step 1: Write failing timeline tests**

Add tests:

```python
def test_foreshadow_timeline(client):
    token = register(client)
    world_id = create_world(client, token)
    foreshadow = create_foreshadow(client, token, world_id)

    update = client.put(f"/foreshadows/{foreshadow['id']}", headers=auth(token), json={'status': 'advanced'})
    assert update.status_code == 200

    timeline = client.get(f"/foreshadows/{foreshadow['id']}/timeline", headers=auth(token))
    assert timeline.status_code == 200
    events = timeline.json()
    assert [event['event_type'] for event in events] == ['planted', 'advanced']
    assert events[0]['chapter_id'] is None
    assert events[0]['chapter_title'] is None
    assert events[0]['note'] is None
    assert events[0]['created_at']


def test_foreshadow_event_created_on_transition(client):
    token = register(client)
    world_id = create_world(client, token)
    foreshadow = create_foreshadow(client, token, world_id)

    before = client.get(f"/foreshadows/{foreshadow['id']}/timeline", headers=auth(token))
    assert before.status_code == 200
    assert len(before.json()) == 1

    response = client.put(f"/foreshadows/{foreshadow['id']}", headers=auth(token), json={'status': 'advanced'})
    assert response.status_code == 200

    after = client.get(f"/foreshadows/{foreshadow['id']}/timeline", headers=auth(token))
    assert after.status_code == 200
    assert len(after.json()) == 2
    assert after.json()[-1]['event_type'] == 'advanced'
```

- [ ] **Step 2: Run tests and verify failure**

```bash
cd /opt/WorldSim-Writer/backend && python -m pytest tests/test_foreshadow_crud.py::test_foreshadow_timeline tests/test_foreshadow_crud.py::test_foreshadow_event_created_on_transition -v
```

Expected: FAIL because route/schema/service do not exist.

- [ ] **Step 3: Add timeline schema**

In `backend/app/foreshadow/schemas.py` add:

```python
class ForeshadowEventResponse(BaseModel):
    event_type: ForeshadowStatus
    chapter_id: int | None
    chapter_title: str | None
    note: str | None
    created_at: datetime
```

- [ ] **Step 4: Add service function**

In `backend/app/foreshadow/service.py` add:

```python
def get_foreshadow_timeline(db: Session, user: User, foreshadow_id: int) -> list[dict]:
    foreshadow = _require_owned_foreshadow(db, user, foreshadow_id)
    rows = db.execute(
        select(ForeshadowEvent, Chapter.title)
        .outerjoin(Chapter, ForeshadowEvent.chapter_id == Chapter.id)
        .where(ForeshadowEvent.foreshadow_id == foreshadow.id)
        .order_by(ForeshadowEvent.created_at, ForeshadowEvent.id)
    ).all()
    return [
        {
            'event_type': event.event_type,
            'chapter_id': event.chapter_id,
            'chapter_title': chapter_title,
            'note': event.note,
            'created_at': event.created_at,
        }
        for event, chapter_title in rows
    ]
```

- [ ] **Step 5: Add router endpoint**

Update imports in `backend/app/foreshadow/router.py` to include `ForeshadowEventResponse` and `get_foreshadow_timeline`.

Add route before `@router.get('/foreshadows/{foreshadow_id}')`:

```python
@router.get('/foreshadows/{foreshadow_id}/timeline', response_model=list[ForeshadowEventResponse])
def timeline(
    foreshadow_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> list[ForeshadowEventResponse]:
    return [
        ForeshadowEventResponse.model_validate(item)
        for item in get_foreshadow_timeline(db, current_user, foreshadow_id)
    ]
```

- [ ] **Step 6: Run timeline tests**

```bash
cd /opt/WorldSim-Writer/backend && python -m pytest tests/test_foreshadow_crud.py::test_foreshadow_timeline tests/test_foreshadow_crud.py::test_foreshadow_event_created_on_transition -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/foreshadow/schemas.py backend/app/foreshadow/service.py backend/app/foreshadow/router.py backend/tests/test_foreshadow_crud.py
git commit -m "feat: add foreshadow timeline API"
```

---

### Task 4: Filtering and stale detection APIs

**Files:**
- Modify: `backend/app/foreshadow/schemas.py`
- Modify: `backend/app/foreshadow/service.py`
- Modify: `backend/app/foreshadow/router.py`
- Test: `backend/tests/test_foreshadow_crud.py`

- [ ] **Step 1: Write failing API tests**

Add:

```python
def create_approved_chapter(db_session, world_id, title):
    from app.narrative.models import Chapter

    chapter = Chapter(
        world_id=world_id,
        title=title,
        status='approved',
        draft_version=1,
        approved_version=1,
        base_world_version=1,
        approved_content='正文',
    )
    db_session.add(chapter)
    db_session.commit()
    db_session.refresh(chapter)
    return chapter.id


def test_foreshadow_filter_by_status(client):
    token = register(client)
    world_id = create_world(client, token)
    planted = create_foreshadow(client, token, world_id, title='A')
    advanced = create_foreshadow(client, token, world_id, title='B')
    expired = create_foreshadow(client, token, world_id, title='C')
    assert client.put(f"/foreshadows/{advanced['id']}", headers=auth(token), json={'status': 'advanced'}).status_code == 200
    assert client.put(f"/foreshadows/{expired['id']}", headers=auth(token), json={'status': 'expired'}).status_code == 200

    only_planted = client.get(f'/worlds/{world_id}/foreshadows?status=planted', headers=auth(token))
    assert only_planted.status_code == 200
    assert [item['id'] for item in only_planted.json()] == [planted['id']]

    multi = client.get(f'/worlds/{world_id}/foreshadows?status=planted,advanced', headers=auth(token))
    assert multi.status_code == 200
    assert {item['id'] for item in multi.json()} == {planted['id'], advanced['id']}

    invalid = client.get(f'/worlds/{world_id}/foreshadows?status=bad', headers=auth(token))
    assert invalid.status_code == 400
    assert invalid.json()['detail'] == 'INVALID_STATUS'


def test_foreshadow_stale_detection(client, db_session):
    token = register(client)
    world_id = create_world(client, token)
    source_id = create_approved_chapter(db_session, world_id, '源章节')
    foreshadow = create_foreshadow(client, token, world_id, title='旧伏笔', source_chapter_id=source_id)

    for idx in range(3):
        create_approved_chapter(db_session, world_id, f'后续 {idx}')

    warning = client.get(f'/worlds/{world_id}/foreshadows/stale', headers=auth(token))
    assert warning.status_code == 200
    assert warning.json() == [
        {
            'foreshadow': warning.json()[0]['foreshadow'],
            'chapters_since_planted': 3,
            'alert_level': 'warning',
        }
    ]
    assert warning.json()[0]['foreshadow']['id'] == foreshadow['id']

    for idx in range(3, 6):
        create_approved_chapter(db_session, world_id, f'后续 {idx}')

    critical = client.get(f'/worlds/{world_id}/foreshadows/stale', headers=auth(token))
    assert critical.status_code == 200
    assert critical.json()[0]['chapters_since_planted'] == 6
    assert critical.json()[0]['alert_level'] == 'critical'
```

- [ ] **Step 2: Run tests and verify failure**

```bash
cd /opt/WorldSim-Writer/backend && python -m pytest tests/test_foreshadow_crud.py::test_foreshadow_filter_by_status tests/test_foreshadow_crud.py::test_foreshadow_stale_detection -v
```

Expected: FAIL because filter/stale APIs do not exist.

- [ ] **Step 3: Add stale schema**

In `backend/app/foreshadow/schemas.py` add:

```python
class StaleForeshadowResponse(BaseModel):
    foreshadow: ForeshadowResponse
    chapters_since_planted: int
    alert_level: Literal['warning', 'critical']
```

- [ ] **Step 4: Update service functions**

Change `get_foreshadows` signature:

```python
def get_foreshadows(db: Session, user: User, world_id: int, statuses: list[str] | None = None) -> list[Foreshadow]:
    require_owned_world(db, user, world_id)
    if statuses:
        for status_value in statuses:
            validate_foreshadow_status(status_value)
    query = select(Foreshadow).where(Foreshadow.world_id == world_id)
    if statuses:
        query = query.where(Foreshadow.status.in_(statuses))
    return list(db.scalars(query.order_by(Foreshadow.id)))
```

Add stale detection:

```python
def get_stale_foreshadows(db: Session, user: User, world_id: int) -> list[dict]:
    world = require_owned_world(db, user, world_id)
    planted = list(
        db.scalars(
            select(Foreshadow)
            .where(Foreshadow.world_id == world.id)
            .where(Foreshadow.status == 'planted')
            .where(Foreshadow.source_chapter_id.is_not(None))
            .order_by(Foreshadow.id)
        )
    )
    stale = []
    for foreshadow in planted:
        assert foreshadow.source_chapter_id is not None
        count = db.scalar(
            select(func.count())
            .select_from(Chapter)
            .where(Chapter.world_id == world.id)
            .where(Chapter.status == 'approved')
            .where(Chapter.id > foreshadow.source_chapter_id)
        ) or 0
        if count >= 3:
            stale.append(
                {
                    'foreshadow': foreshadow,
                    'chapters_since_planted': count,
                    'alert_level': 'critical' if count >= 6 else 'warning',
                }
            )
    return stale
```

Also import `func` from SQLAlchemy.

- [ ] **Step 5: Update router**

In `backend/app/foreshadow/router.py`, import `Query`, `StaleForeshadowResponse`, and `get_stale_foreshadows`.

Update list route:

```python
@router.get('/worlds/{world_id}/foreshadows', response_model=list[ForeshadowResponse])
def list_foreshadows(
    world_id: int,
    status_filter: str | None = Query(default=None, alias='status'),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> list[ForeshadowResponse]:
    statuses = [item.strip() for item in status_filter.split(',') if item.strip()] if status_filter else None
    return [
        ForeshadowResponse.model_validate(f)
        for f in get_foreshadows(db, current_user, world_id, statuses)
    ]
```

Add stale route before `/{foreshadow_id}` routes:

```python
@router.get('/worlds/{world_id}/foreshadows/stale', response_model=list[StaleForeshadowResponse])
def stale(
    world_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> list[StaleForeshadowResponse]:
    return [
        StaleForeshadowResponse.model_validate(item)
        for item in get_stale_foreshadows(db, current_user, world_id)
    ]
```

- [ ] **Step 6: Run tests**

```bash
cd /opt/WorldSim-Writer/backend && python -m pytest tests/test_foreshadow_crud.py::test_foreshadow_filter_by_status tests/test_foreshadow_crud.py::test_foreshadow_stale_detection -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/foreshadow/schemas.py backend/app/foreshadow/service.py backend/app/foreshadow/router.py backend/tests/test_foreshadow_crud.py
git commit -m "feat: add foreshadow filters and stale detection"
```

---

### Task 5: Chapter approval lifecycle events

**Files:**
- Modify: `backend/app/narrative/service.py`
- Test: `backend/tests/test_narrative_approval.py`

- [ ] **Step 1: Inspect existing narrative approval tests**

Read `backend/tests/test_narrative_approval.py` and reuse existing helpers for creating approved drafts. Do not rewrite unrelated tests.

- [ ] **Step 2: Add failing approval event assertion**

Add a test shaped like this, adapting helper names to the existing file:

```python
def test_approve_chapter_creates_foreshadow_lifecycle_event(client, db_session):
    token = register(client)
    world_id = create_world(client, token)
    foreshadow = create_foreshadow(client, token, world_id)
    chapter_id = create_reviewing_chapter_with_draft(
        db_session,
        world_id,
        proposed_changes={
            'characters': [],
            'foreshadows': [
                {'foreshadow_id': foreshadow['id'], 'status': 'advanced', 'description_note': '本章听见铜铃。'}
            ],
        },
    )

    response = client.post(f'/chapters/{chapter_id}/approve', headers=auth(token))
    assert response.status_code == 200

    timeline = client.get(f"/foreshadows/{foreshadow['id']}/timeline", headers=auth(token))
    assert timeline.status_code == 200
    event = timeline.json()[-1]
    assert event['event_type'] == 'advanced'
    assert event['chapter_id'] == chapter_id
    assert event['chapter_title']
    assert event['note'] == '本章听见铜铃。'
```

If the existing narrative test file has different helper names, define local helpers copied from `test_foreshadow_crud.py` plus direct `Chapter`/`ChapterDraft` construction.

- [ ] **Step 3: Run approval test and verify failure**

```bash
cd /opt/WorldSim-Writer/backend && python -m pytest tests/test_narrative_approval.py::test_approve_chapter_creates_foreshadow_lifecycle_event -v
```

Expected: FAIL because approval does not create `ForeshadowEvent` yet.

- [ ] **Step 4: Update narrative service imports**

In `backend/app/narrative/service.py`, change foreshadow imports:

```python
from app.foreshadow.models import Foreshadow
from app.foreshadow.service import apply_foreshadow_status_transition
```

- [ ] **Step 5: Use lifecycle helper in approval**

In the loop that applies foreshadow changes, replace direct status assignment:

```python
for foreshadow, change, _before, _after in foreshadow_changes:
    apply_foreshadow_status_transition(
        db,
        foreshadow,
        change['status'],
        chapter_id=chapter.id,
        note=change.get('description_note'),
    )
    if change.get('description_note'):
        foreshadow.description = f"{foreshadow.description}\n审核备注：{change['description_note']}"
```

Keep the existing `before`/`after` event-log payload behavior.

- [ ] **Step 6: Run approval test**

```bash
cd /opt/WorldSim-Writer/backend && python -m pytest tests/test_narrative_approval.py::test_approve_chapter_creates_foreshadow_lifecycle_event -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/app/narrative/service.py backend/tests/test_narrative_approval.py
git commit -m "feat: record foreshadow events on approval"
```

---

### Task 6: Frontend API types and client

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/api/client.ts`

- [ ] **Step 1: Update TypeScript types**

In `frontend/src/api/types.ts`, add before `Foreshadow`:

```ts
export type ForeshadowStatus = 'planted' | 'advanced' | 'resolved' | 'expired';
```

Change status fields:

```ts
status: ForeshadowStatus;
```

and optional create/update statuses:

```ts
status?: ForeshadowStatus;
```

Add `source_chapter_id` to `Foreshadow`:

```ts
source_chapter_id: number | null;
```

Add:

```ts
export type ForeshadowEvent = {
  event_type: ForeshadowStatus;
  chapter_id: number | null;
  chapter_title: string | null;
  note: string | null;
  created_at: string;
};

export type StaleForeshadow = {
  foreshadow: Foreshadow;
  chapters_since_planted: number;
  alert_level: 'warning' | 'critical';
};
```

- [ ] **Step 2: Update client imports**

In `frontend/src/api/client.ts`, import `ForeshadowEvent`, `ForeshadowStatus`, and `StaleForeshadow`.

- [ ] **Step 3: Update foreshadow API functions**

Replace `getForeshadows` with:

```ts
export function getForeshadows(worldId: number, params: { status?: ForeshadowStatus[] } = {}) {
  const search = new URLSearchParams();
  if (params.status?.length) search.set('status', params.status.join(','));
  const query = search.toString();
  return apiRequest<Foreshadow[]>(`/worlds/${worldId}/foreshadows${query ? `?${query}` : ''}`);
}
```

Add:

```ts
export function getForeshadowTimeline(foreshadowId: number) {
  return apiRequest<ForeshadowEvent[]>(`/foreshadows/${foreshadowId}/timeline`);
}

export function getStaleForeshadows(worldId: number) {
  return apiRequest<StaleForeshadow[]>(`/worlds/${worldId}/foreshadows/stale`);
}
```

- [ ] **Step 4: Run frontend build and observe current UI errors**

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: It may fail until `ForeshadowManager` uses the narrower status type correctly. Fix in Task 7.

- [ ] **Step 5: Commit if build still passes, otherwise defer commit to Task 7**

If build passes:

```bash
git add frontend/src/api/types.ts frontend/src/api/client.ts
git commit -m "feat: add foreshadow ledger client types"
```

If build fails due to `ForeshadowManager`, do not commit yet; continue to Task 7 and commit frontend changes together.

---

### Task 7: Frontend ForeshadowManager kanban, timeline, stale alert

**Files:**
- Modify: `frontend/src/components/ForeshadowManager.tsx`
- May also commit: `frontend/src/api/types.ts`, `frontend/src/api/client.ts` if not committed in Task 6

- [ ] **Step 1: Update imports and constants**

Import new client functions and types:

```ts
import {
  createForeshadow,
  deleteForeshadow,
  getForeshadowTimeline,
  getForeshadows,
  getStaleForeshadows,
  updateForeshadow,
} from '../api/client';
import type {
  Character,
  Foreshadow,
  ForeshadowCreate,
  ForeshadowEvent,
  ForeshadowStatus,
  ForeshadowUpdate,
  StaleForeshadow,
} from '../api/types';
```

Change statuses:

```ts
const STATUS_OPTIONS = ['planted', 'advanced', 'resolved', 'expired'] as const satisfies readonly ForeshadowStatus[];
```

Add `expired` label and color:

```ts
expired: '已过期'
expired: 'bg-red-100 text-red-800 border-red-700/20'
```

Change `FormData.status` to `ForeshadowStatus`.

- [ ] **Step 2: Add UI state**

Inside component state:

```ts
const [viewMode, setViewMode] = useState<'list' | 'kanban'>('list');
const [staleForeshadows, setStaleForeshadows] = useState<StaleForeshadow[]>([]);
const [expandedId, setExpandedId] = useState<number | null>(null);
const [draggingId, setDraggingId] = useState<number | null>(null);
```

Update `load` to fetch both:

```ts
const [foreshadowItems, staleItems] = await Promise.all([
  getForeshadows(worldId),
  getStaleForeshadows(worldId),
]);
setForeshadows(foreshadowItems);
setStaleForeshadows(staleItems);
```

- [ ] **Step 3: Replace unsafe cycleStatus**

Use legal next status only:

```ts
function nextForwardStatus(statusValue: ForeshadowStatus): ForeshadowStatus | null {
  if (statusValue === 'planted') return 'advanced';
  if (statusValue === 'advanced') return 'resolved';
  return null;
}

async function advanceStatus(f: Foreshadow) {
  const next = nextForwardStatus(f.status);
  if (!next) return;
  try {
    await updateForeshadow(f.id, { status: next });
    await load();
    await onChanged?.();
  } catch (err) {
    setError(err instanceof Error ? err.message : '更新伏笔状态失败');
  }
}
```

- [ ] **Step 4: Add drag/drop handler**

```ts
async function dropOnStatus(statusValue: ForeshadowStatus) {
  if (draggingId === null) return;
  const source = foreshadows.find((item) => item.id === draggingId);
  setDraggingId(null);
  if (!source || source.status === statusValue) return;
  try {
    await updateForeshadow(source.id, { status: statusValue });
    await load();
    await onChanged?.();
  } catch (err) {
    setError(err instanceof Error ? err.message : '更新伏笔状态失败');
  }
}
```

- [ ] **Step 5: Add stale banner and view toggle**

Render above errors:

```tsx
{staleForeshadows.length > 0 && (
  <button
    type="button"
    className="mt-4 w-full rounded-2xl border border-amber-700/30 bg-amber-100 px-4 py-3 text-left text-sm font-semibold text-amber-900 shadow-sm"
    onClick={() => setViewMode('kanban')}
  >
    ⚠️ 有 {staleForeshadows.length} 条伏笔已超过{' '}
    {Math.min(...staleForeshadows.map((item) => item.chapters_since_planted))} 章未推进，建议尽快处理
  </button>
)}
```

Add toggle buttons next to create button:

```tsx
<div className="flex gap-2">
  <button className={viewMode === 'list' ? 'primary-button' : 'secondary-button'} onClick={() => setViewMode('list')}>列表视图</button>
  <button className={viewMode === 'kanban' ? 'primary-button' : 'secondary-button'} onClick={() => setViewMode('kanban')}>看板视图</button>
  <button className="primary-button" onClick={openCreate}>+ 新增伏笔</button>
</div>
```

- [ ] **Step 6: Extract card renderer**

Create a local `renderForeshadowCard(f: Foreshadow)` function that contains the existing article markup, adds `draggable`, `onDragStart`, and an expand button:

```tsx
<article
  key={f.id}
  draggable
  onDragStart={() => setDraggingId(f.id)}
  onDragEnd={() => setDraggingId(null)}
  className="book-card p-5 flex flex-col gap-3"
>
```

Replace status button with:

```tsx
<button
  className={`shrink-0 rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors ${STATUS_COLORS[f.status]}`}
  onClick={() => void advanceStatus(f)}
  disabled={nextForwardStatus(f.status) === null}
  title={nextForwardStatus(f.status) ? '推进到下一状态' : '终态不可继续推进'}
>
  {STATUS_LABELS[f.status]}
</button>
```

Add details toggle before actions:

```tsx
<button className="ghost-button text-sm self-start" onClick={() => setExpandedId(expandedId === f.id ? null : f.id)}>
  {expandedId === f.id ? '收起时间线' : '展开时间线'}
</button>
{expandedId === f.id && <ForeshadowTimeline foreshadowId={f.id} />}
```

- [ ] **Step 7: Add kanban render branch**

Where the list grid renders, branch:

```tsx
{viewMode === 'list' ? (
  <div className="mt-6 grid gap-4 md:grid-cols-2">
    {foreshadows.map((f) => renderForeshadowCard(f))}
  </div>
) : (
  <div className="mt-6 grid gap-4 lg:grid-cols-4">
    {STATUS_OPTIONS.map((statusValue) => {
      const items = foreshadows.filter((item) => item.status === statusValue);
      return (
        <section
          key={statusValue}
          className="min-h-[220px] rounded-3xl border border-amber-900/15 bg-amber-50/40 p-3"
          onDragOver={(event) => event.preventDefault()}
          onDrop={() => void dropOnStatus(statusValue)}
        >
          <div className="mb-3 flex items-center justify-between">
            <h3 className="font-black text-[#3b2511]">{STATUS_LABELS[statusValue]}</h3>
            <span className="rounded-full bg-white/70 px-2 py-0.5 text-xs font-bold ink-muted">{items.length}</span>
          </div>
          <div className="space-y-3">
            {items.map((f) => renderForeshadowCard(f))}
          </div>
        </section>
      );
    })}
  </div>
)}
```

- [ ] **Step 8: Add timeline component**

At bottom of `ForeshadowManager.tsx` add:

```tsx
function ForeshadowTimeline({ foreshadowId }: { foreshadowId: number }) {
  const [events, setEvents] = useState<ForeshadowEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    async function loadTimeline() {
      setLoading(true);
      setError('');
      try {
        const items = await getForeshadowTimeline(foreshadowId);
        if (!cancelled) setEvents(items);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : '加载时间线失败');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void loadTimeline();
    return () => {
      cancelled = true;
    };
  }, [foreshadowId]);

  if (loading) return <p className="text-xs ink-muted">正在加载时间线…</p>;
  if (error) return <p className="paper-error text-xs" role="alert">{error}</p>;
  if (events.length === 0) return <p className="text-xs ink-muted">暂无生命周期事件。</p>;

  return (
    <ol className="space-y-2 border-l border-amber-900/20 pl-3">
      {events.map((event, index) => (
        <li key={`${event.event_type}-${event.created_at}-${index}`} className="text-xs ink-muted">
          <span className="font-bold text-[#4a321e]">{STATUS_LABELS[event.event_type]}</span>
          <span> · {new Date(event.created_at).toLocaleString()}</span>
          {event.chapter_title && <span> · 章节：{event.chapter_title}</span>}
          {event.note && <p className="mt-1 manuscript text-xs">{event.note}</p>}
        </li>
      ))}
    </ol>
  );
}
```

- [ ] **Step 9: Run frontend build**

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: PASS.

- [ ] **Step 10: Commit frontend UI**

```bash
git add frontend/src/api/types.ts frontend/src/api/client.ts frontend/src/components/ForeshadowManager.tsx
git commit -m "feat: add foreshadow kanban ledger UI"
```

---

### Task 8: Full verification, review, and final commit if needed

**Files:**
- Any modified files not committed by earlier tasks

- [ ] **Step 1: Run full backend tests**

```bash
cd /opt/WorldSim-Writer/backend && python -m pytest tests/ -x -v
```

Expected: all tests pass.

- [ ] **Step 2: Run frontend build**

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: TypeScript and Vite build pass.

- [ ] **Step 3: Review diff**

```bash
git status --short
git diff --stat HEAD
```

Expected: no uncommitted implementation files. If verification fixes were needed, commit them with:

```bash
git add <changed-files>
git commit -m "fix: stabilize foreshadow ledger verification"
```

- [ ] **Step 4: Final status**

```bash
git log --oneline -5
git status --short
```

Expected: recent commits include design and implementation commits; only pre-existing unrelated untracked files may remain.
