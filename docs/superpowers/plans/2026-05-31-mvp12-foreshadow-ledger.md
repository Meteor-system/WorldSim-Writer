# MVP12 Foreshadow Ledger 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans inline for this repository because the user explicitly forbids subagents and dynamic workflows. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a managed Foreshadow Ledger with lifecycle grouping, urgency/stale pressure, related character context, timeline continuity, and Next Chapter Prep prioritization.

**Architecture:** Add a shared backend Foreshadow Ledger evaluator in `app.foreshadow.service`, expose it via a typed read-only endpoint, and update Next Chapter Prep to reuse the same pressure ranking. Update the React foreshadow manager to consume the ledger response while preserving existing CRUD and approval behavior.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, React, TypeScript, Vite, Vitest, Testing Library.

---

## File Map

- Modify `backend/app/foreshadow/schemas.py`: add ledger response models.
- Modify `backend/app/foreshadow/service.py`: add ledger evaluator helpers and endpoint service function.
- Modify `backend/app/foreshadow/router.py`: add `GET /worlds/{world_id}/foreshadows/ledger`.
- Modify `backend/app/narrative_control_center/service.py`: reuse ledger pressure entries in Next Chapter Prep priority foreshadows and fallback suggested goal.
- Modify `backend/tests/test_foreshadow_crud.py`: backend RED/GREEN tests for ledger endpoint and timeline continuity.
- Modify `backend/tests/test_narrative_control_center.py`: backend RED/GREEN tests for high-pressure foreshadow prioritization.
- Modify `frontend/src/api/types.ts`: add ledger types.
- Modify `frontend/src/api/client.ts`: add `getForeshadowLedger` helper.
- Modify `frontend/src/api/client.test.ts`: frontend API helper RED/GREEN test.
- Modify `frontend/src/components/ForeshadowManager.tsx`: consume ledger endpoint and render ledger pressure.
- Modify `frontend/src/components/ForeshadowManager.test.tsx`: component RED/GREEN tests.
- Modify `frontend/src/world/NextChapterPrepPanel.test.tsx`: verify high-pressure reason display.

---

## Task 1: Backend ledger endpoint RED tests

**Files:**
- Modify: `backend/tests/test_foreshadow_crud.py`

- [ ] **Step 1: Add failing ledger tests**

Append tests that call `GET /worlds/{world_id}/foreshadows/ledger` and assert:

```python
def test_foreshadow_ledger_groups_pressure_related_characters_and_events(client, db_session):
    token = register(client)
    world_id = create_world(client, token)
    character_id = first_character_id(client, token, world_id)
    source_id = create_approved_chapter(db_session, world_id, '源章节')
    urgent = client.post(
        f'/worlds/{world_id}/foreshadows',
        headers=auth(token),
        json={
            'source_chapter_id': source_id,
            'title': '裂纹玉佩',
            'description': '玉佩出现裂纹。',
            'foreshadow_type': 'plot',
            'status': 'planted',
            'urgency_level': 5,
            'related_character_ids': [character_id],
            'expected_resolution_window': '第2-4章',
        },
    ).json()
    assert client.put(f"/foreshadows/{urgent['id']}", headers=auth(token), json={'status': 'advanced'}).status_code == 200
    resolved = create_foreshadow(client, token, world_id, title='旧盟约', status='planted')
    assert client.put(f"/foreshadows/{resolved['id']}", headers=auth(token), json={'status': 'advanced'}).status_code == 200
    assert client.put(f"/foreshadows/{resolved['id']}", headers=auth(token), json={'status': 'resolved'}).status_code == 200

    response = client.get(f'/worlds/{world_id}/foreshadows/ledger', headers=auth(token))

    assert response.status_code == 200
    body = response.json()
    assert body['world_id'] == world_id
    assert body['summary']['total'] >= 2
    assert body['summary']['advanced_count'] >= 1
    assert body['summary']['resolved_count'] >= 1
    advanced_entry = next(item for item in body['groups']['advanced'] if item['foreshadow']['id'] == urgent['id'])
    assert advanced_entry['status_group'] == 'advanced'
    assert advanced_entry['is_open'] is True
    assert advanced_entry['is_high_urgency'] is True
    assert advanced_entry['pressure_level'] == 'high'
    assert '高紧迫度：5' in advanced_entry['pressure_reasons']
    assert advanced_entry['related_characters'][0]['id'] == character_id
    assert advanced_entry['related_characters'][0]['name']
    assert advanced_entry['recent_events'][-1]['event_type'] == 'advanced'
    assert body['high_pressure'][0]['foreshadow']['id'] == urgent['id']
```

Add a read-only test:

```python
def test_foreshadow_ledger_marks_stale_overdue_and_does_not_mutate_world(client, db_session):
    token = register(client)
    world_id = create_world(client, token)
    source_id = create_approved_chapter(db_session, world_id, '源章节')
    stale = create_foreshadow(client, token, world_id, title='井中红光', source_chapter_id=source_id)
    for index in range(6):
        create_approved_chapter(db_session, world_id, f'后续 {index}')
    world_before = world_state(db_session, world_id)
    version_before = world_before.world_version
    event_count_before = len(world_events(db_session, world_id))

    response = client.get(f'/worlds/{world_id}/foreshadows/ledger', headers=auth(token))

    assert response.status_code == 200
    body = response.json()
    entry = next(item for item in body['groups']['planted'] if item['foreshadow']['id'] == stale['id'])
    assert entry['is_stale'] is True
    assert entry['is_overdue'] is True
    assert entry['chapters_since_planted'] == 6
    assert entry['pressure_level'] == 'critical'
    assert '已埋设 6 章未推进' in entry['pressure_reasons']
    assert body['summary']['stale_count'] >= 1
    assert body['summary']['overdue_count'] >= 1
    db_session.expire_all()
    assert world_state(db_session, world_id).world_version == version_before
    assert len(world_events(db_session, world_id)) == event_count_before
```

- [ ] **Step 2: Run backend RED tests**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_foreshadow_crud.py -v
```

Expected: FAIL because `/worlds/{world_id}/foreshadows/ledger` does not exist and ledger fields are missing.

---

## Task 2: Backend ledger implementation GREEN

**Files:**
- Modify: `backend/app/foreshadow/schemas.py`
- Modify: `backend/app/foreshadow/service.py`
- Modify: `backend/app/foreshadow/router.py`

- [ ] **Step 1: Add schemas**

Add Pydantic models in `backend/app/foreshadow/schemas.py`:

```python
class RelatedCharacterBrief(BaseModel):
    id: int
    name: str
    role_type: str


class ForeshadowLedgerSummary(BaseModel):
    total: int
    open_count: int
    planted_count: int
    advanced_count: int
    resolved_count: int
    expired_count: int
    high_urgency_count: int
    stale_count: int
    overdue_count: int


class ForeshadowLedgerEntry(BaseModel):
    foreshadow: ForeshadowResponse
    status_group: Literal['planted', 'advanced', 'resolved', 'expired']
    is_open: bool
    is_high_urgency: bool
    is_stale: bool
    is_overdue: bool
    chapters_since_planted: int
    pressure_level: Literal['medium', 'high', 'critical', 'resolved', 'expired']
    pressure_reasons: list[str]
    related_characters: list[RelatedCharacterBrief]
    recent_events: list[ForeshadowEventResponse]


class ForeshadowLedgerResponse(BaseModel):
    world_id: int
    world_version: int
    summary: ForeshadowLedgerSummary
    groups: dict[Literal['planted', 'advanced', 'resolved', 'expired'], list[ForeshadowLedgerEntry]]
    high_pressure: list[ForeshadowLedgerEntry]
```

- [ ] **Step 2: Add service evaluator**

Implement in `backend/app/foreshadow/service.py`:

```python
LEDGER_GROUPS = ('planted', 'advanced', 'resolved', 'expired')


def _approved_chapters_after_source(db: Session, world_id: int, source_chapter_id: int | None) -> int:
    if source_chapter_id is None:
        return 0
    return db.scalar(
        select(func.count())
        .select_from(Chapter)
        .where(Chapter.world_id == world_id)
        .where(Chapter.status == 'approved')
        .where(Chapter.id > source_chapter_id)
    ) or 0


def _recent_foreshadow_events(db: Session, foreshadow_id: int, limit: int = 3) -> list[dict]:
    rows = db.execute(
        select(ForeshadowEvent, Chapter.title)
        .outerjoin(Chapter, ForeshadowEvent.chapter_id == Chapter.id)
        .where(ForeshadowEvent.foreshadow_id == foreshadow_id)
        .order_by(ForeshadowEvent.created_at.desc(), ForeshadowEvent.id.desc())
        .limit(limit)
    ).all()
    return [
        {
            'event_type': event.event_type,
            'chapter_id': event.chapter_id,
            'chapter_title': chapter_title,
            'note': event.note,
            'created_at': event.created_at,
        }
        for event, chapter_title in reversed(rows)
    ]


def _pressure_for_foreshadow(db: Session, foreshadow: Foreshadow) -> tuple[bool, bool, bool, int, str, list[str]]:
    is_open = foreshadow.status in {'planted', 'advanced'}
    is_high_urgency = is_open and foreshadow.urgency_level >= 4
    chapters_since = _approved_chapters_after_source(db, foreshadow.world_id, foreshadow.source_chapter_id)
    is_stale = foreshadow.status == 'planted' and foreshadow.source_chapter_id is not None and chapters_since >= 3
    is_overdue = is_stale and chapters_since >= 6
    reasons: list[str] = []
    if is_high_urgency:
        reasons.append(f'高紧迫度：{foreshadow.urgency_level}')
    if is_stale:
        reasons.append(f'已埋设 {chapters_since} 章未推进')
    if is_overdue:
        reasons.append('超过建议回收窗口，请优先推进或收束')
    if foreshadow.expected_resolution_window:
        reasons.append(f'预期收束窗口：{foreshadow.expected_resolution_window}')
    if foreshadow.status == 'resolved':
        pressure_level = 'resolved'
    elif foreshadow.status == 'expired':
        pressure_level = 'expired'
    elif is_overdue:
        pressure_level = 'critical'
    elif is_stale or is_high_urgency:
        pressure_level = 'high'
    else:
        pressure_level = 'medium'
    return is_open, is_high_urgency, is_stale, is_overdue, chapters_since, pressure_level, reasons
```

Add entry and response builders that load characters once, compute groups, summary, and `high_pressure` sorted by critical/high, urgency, stale age, and id.

- [ ] **Step 3: Add router endpoint**

Import `ForeshadowLedgerResponse` and `get_foreshadow_ledger`, then add:

```python
@router.get('/worlds/{world_id}/foreshadows/ledger', response_model=ForeshadowLedgerResponse)
def ledger(...):
    return ForeshadowLedgerResponse.model_validate(get_foreshadow_ledger(db, current_user, world_id))
```

- [ ] **Step 4: Run backend GREEN tests**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_foreshadow_crud.py -v
```

Expected: PASS.

---

## Task 3: Next Chapter Prep ledger pressure RED/GREEN

**Files:**
- Modify: `backend/tests/test_narrative_control_center.py`
- Modify: `backend/app/narrative_control_center/service.py`

- [ ] **Step 1: Add failing prep test**

Add a test that creates a stale planted foreshadow and verifies it is prioritized with a stale/overdue reason:

```python
def test_next_chapter_prep_prioritizes_stale_ledger_foreshadows(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    approve_chapter(client, token, world_id, monkeypatch)
    world = db_session.get(World, world_id)
    world.story_arc = []
    db_session.commit()
    from app.foreshadow.models import Foreshadow
    stale = db_session.get(Foreshadow, 1)
    stale.status = 'planted'
    stale.urgency_level = 5
    stale.source_chapter_id = create_approved_chapter(db_session, world_id, '伏笔源章节')
    db_session.commit()
    for index in range(6):
        create_approved_chapter(db_session, world_id, f'后续章节 {index}')

    response = client.get(f'/worlds/{world_id}/next-chapter-prep', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    payload = response.json()
    assert payload['priority_foreshadows'][0]['foreshadow_id'] == stale.id
    assert payload['priority_foreshadows'][0]['urgency_level'] == 5
    assert '已埋设 6 章未推进' in payload['priority_foreshadows'][0]['reason']
    assert payload['suggested_goal'].startswith('推进伏笔《')
    assert 'urgent_foreshadow' in payload['source_signals']
```

- [ ] **Step 2: Run RED test**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_control_center.py::test_next_chapter_prep_prioritizes_stale_ledger_foreshadows -v
```

Expected: FAIL because Next Chapter Prep does not use ledger pressure reasons.

- [ ] **Step 3: Implement prep reuse**

In `app.narrative_control_center.service`, import a ledger helper from `app.foreshadow.service` and use ledger entries for priority foreshadows. Keep existing progression hint precedence and response shape.

- [ ] **Step 4: Run GREEN test**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_control_center.py::test_next_chapter_prep_prioritizes_stale_ledger_foreshadows -v
```

Expected: PASS.

---

## Task 4: Frontend API and component RED tests

**Files:**
- Modify: `frontend/src/api/client.test.ts`
- Modify: `frontend/src/components/ForeshadowManager.test.tsx`
- Modify: `frontend/src/world/NextChapterPrepPanel.test.tsx`

- [ ] **Step 1: Add failing API helper test**

Update the import to include `getForeshadowLedger`; add it to the existing API helper test or a new foreshadow helper test. Assert it calls:

```text
http://localhost:8000/worlds/7/foreshadows/ledger
```

- [ ] **Step 2: Add failing ForeshadowManager ledger tests**

Mock `getForeshadowLedger` and assert the manager renders:

- `Foreshadow Ledger`
- `总数：4`
- `高压力：2`
- high-pressure callout text,
- related character name,
- recent event note.

Also update create/update/delete assertions so reload expects `getForeshadowLedger` to be called again.

- [ ] **Step 3: Add NextChapterPrepPanel reason assertion**

Add a priority foreshadow reason like `高紧迫度：5；已埋设 6 章未推进` and assert it renders.

- [ ] **Step 4: Run frontend RED tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts src/components/ForeshadowManager.test.tsx src/world/NextChapterPrepPanel.test.tsx
```

Expected: FAIL because `getForeshadowLedger` and ledger rendering are missing.

---

## Task 5: Frontend implementation GREEN

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/components/ForeshadowManager.tsx`

- [ ] **Step 1: Add types and API helper**

Add ledger types and `getForeshadowLedger(worldId)`.

- [ ] **Step 2: Update ForeshadowManager data loading**

Replace the dual `getForeshadows/getStaleForeshadows` ledger load with `getForeshadowLedger`. Derive `foreshadows`, `staleForeshadows`, visible entries, and card rendering from ledger entries. Keep old CRUD calls unchanged.

- [ ] **Step 3: Render ledger pressure fields**

Display high-pressure counts, pressure reasons, related character names, expected resolution windows, and recent lifecycle event notes.

- [ ] **Step 4: Run frontend GREEN tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts src/components/ForeshadowManager.test.tsx src/world/NextChapterPrepPanel.test.tsx
```

Expected: PASS.

---

## Task 6: Full targeted verification, inline self-review, commit, merge

**Files:**
- All modified files.

- [ ] **Step 1: Run backend targeted tests**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_foreshadow_crud.py tests/test_narrative_control_center.py tests/test_narrative_approval.py -v
```

Expected: PASS.

- [ ] **Step 2: Run frontend targeted tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts src/components/ForeshadowManager.test.tsx src/world/NextChapterPrepPanel.test.tsx src/world/WorldPage.test.tsx
```

Expected: PASS.

- [ ] **Step 3: Run frontend build**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: PASS.

- [ ] **Step 4: Inline self-review**

Check:

- no dynamic workflows,
- no subagents,
- no code-review subagent,
- ledger endpoint is read-only,
- approval selection/consistency behavior untouched,
- next-chapter prep response shape remains compatible,
- frontend build and targeted tests pass.

- [ ] **Step 5: Commit on feature branch**

Run:

```bash
git status --short
git diff --check
git add docs/superpowers/specs/2026-05-31-mvp12-foreshadow-ledger-design.md docs/superpowers/plans/2026-05-31-mvp12-foreshadow-ledger.md backend/app/foreshadow/schemas.py backend/app/foreshadow/service.py backend/app/foreshadow/router.py backend/app/narrative_control_center/service.py backend/tests/test_foreshadow_crud.py backend/tests/test_narrative_control_center.py frontend/src/api/types.ts frontend/src/api/client.ts frontend/src/api/client.test.ts frontend/src/components/ForeshadowManager.tsx frontend/src/components/ForeshadowManager.test.tsx frontend/src/world/NextChapterPrepPanel.test.tsx
git commit -m "feat: add foreshadow ledger pressure view"
```

Commit body must end with:

```text
Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```

- [ ] **Step 6: Merge to main without pushing**

Run:

```bash
git switch main
git merge feat/mvp12-foreshadow-ledger
```

- [ ] **Step 7: Post-merge verification**

Repeat backend targeted tests, frontend targeted tests, and frontend build on `main`. Report exact results and confirm no push was performed.

## Plan self-review

- Spec coverage: lifecycle grouping, urgency/stale pressure, next-chapter prep prioritization, timeline continuity, compatibility, and verification are all covered.
- Placeholder scan: no TBD/TODO placeholders remain.
- Type consistency: ledger type names are consistent across backend and frontend.
- Scope control: no database migrations, timeline editor, graph UI, AI mutation strategy, or export changes are included.
