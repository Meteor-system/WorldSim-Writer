# MVP11 Continuity / Consistency Review 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This repository run is constrained by the user to inline execution only: NO dynamic workflows, no subagents, skip code-review subagent, use inline self-review.

**Goal:** Add deterministic approval consistency checks for the selected approval change set so blocking world-state risks prevent approval, warnings remain approvable, and approval history records the actual consistency summary.

**Architecture:** Add shared backend helpers in `app.narrative.service` to build the selected approval change set and evaluate it. Reuse those helpers from approval preview, a new selected consistency endpoint, and the final approval mutation. Extend the React Studio approval preview to show consistency state, recalculate it when checkbox selections change, and disable approval only for blocking states.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy, pytest, React, TypeScript, Vitest, Testing Library, Vite.

---

## File map

- Modify `backend/app/narrative/schemas.py`
  - Add response schemas for consistency warnings, summary, and selected consistency response.
- Modify `backend/app/narrative/router.py`
  - Add `POST /chapters/{chapter_id}/approval-consistency` endpoint.
- Modify `backend/app/narrative/service.py`
  - Add shared selected change-set builder.
  - Add deterministic consistency evaluator.
  - Include consistency output in approval preview.
  - Block approval on selected blocking consistency warnings.
  - Record consistency output in `chapter_approved` EventLog payload.
- Modify `backend/tests/test_narrative_approval.py`
  - Add RED tests for preview consistency, selected consistency recalculation, blocking approval guard, warning-only approval, and EventLog consistency summary.
- Modify `frontend/src/api/types.ts`
  - Add consistency types and extend approval preview response.
- Modify `frontend/src/api/client.ts`
  - Add `checkApprovalConsistency()` helper.
- Modify `frontend/src/api/client.test.ts`
  - Extend existing narrative helper endpoint test to include approval consistency helper.
- Modify `frontend/src/studio/StudioPage.tsx`
  - Import new helper/types.
  - Track current consistency summary/warnings.
  - Recalculate after checkbox toggles.
  - Render warning list and blocking state.
  - Disable approve button when consistency status is `blocked`.
- Modify `frontend/src/studio/StudioPage.test.tsx`
  - Add RED tests for warning rendering, blocking disable, warning-only approval, and selection-triggered recalculation.
- Create/update docs already written:
  - `docs/superpowers/specs/2026-05-31-mvp11-consistency-review-design.md`
  - `docs/superpowers/plans/2026-05-31-mvp11-consistency-review.md`

---

## Task 1: Backend RED tests for consistency behavior

**Files:**
- Modify: `backend/tests/test_narrative_approval.py`

- [ ] **Step 1: Add test LLM fixtures for rollback and warning-only scenarios**

Add classes near `MultiChangeLLMClient`:

```python
class RollbackForeshadowLLMClient:
    def generate_chapter(self, messages):
        return ChapterGeneration(
            title='第二章 玉佩回潮',
            draft_content='裂纹玉佩已经被解释清楚，却又在雨夜重新发出旧光。',
            context_summary='已解决伏笔被重新推进。',
            review_hints=['确认伏笔是否允许倒退'],
            proposed_character_changes=[],
            proposed_foreshadow_changes=[
                ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='尝试重新推进已解决伏笔'),
            ],
        )


class CharacterJumpLLMClient:
    def generate_chapter(self, messages):
        return ChapterGeneration(
            title='第二章 急转',
            draft_content='林砚放弃旧案，转而追查城主府密信。',
            context_summary='角色目标发生明显切换。',
            review_hints=['确认角色目标跳变是否有铺垫'],
            proposed_character_changes=[
                ProposedCharacterChange(character_id=1, status='转向追查密信', current_goals=['追查城主府密信']),
            ],
            proposed_foreshadow_changes=[],
        )
```

- [ ] **Step 2: Add helper to force foreshadow status**

Add near existing helpers:

```python
def set_foreshadow_status(db_session, foreshadow_id: int, status: str) -> None:
    from app.foreshadow.models import Foreshadow

    foreshadow = db_session.get(Foreshadow, foreshadow_id)
    assert foreshadow is not None
    foreshadow.status = status
    db_session.commit()
```

- [ ] **Step 3: Add preview consistency RED test**

Add test:

```python
def test_approval_preview_includes_consistency_summary_and_warnings(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    set_foreshadow_status(db_session, 1, 'resolved')
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: RollbackForeshadowLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '重新推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    response = client.get(f"/chapters/{draft['chapter_id']}/approval-preview", headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    body = response.json()
    assert body['consistency_summary']['status'] == 'blocked'
    assert body['consistency_summary']['blocking_count'] == 1
    assert body['consistency_warnings'][0]['severity'] == 'blocking'
    assert body['consistency_warnings'][0]['category'] == 'foreshadow_transition'
    assert body['consistency_warnings'][0]['object_type'] == 'foreshadow'
    assert body['consistency_warnings'][0]['object_id'] == 1
    assert body['consistency_warnings'][0]['change_index'] == 0
```

- [ ] **Step 4: Add selected consistency RED test**

Add test:

```python
def test_approval_consistency_recalculates_for_selected_change_set(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    set_foreshadow_status(db_session, 1, 'resolved')
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: RollbackForeshadowLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '重新推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    response = client.post(
        f"/chapters/{draft['chapter_id']}/approval-consistency",
        json={
            'draft_version': draft['draft_version'],
            'selected_character_change_indexes': [],
            'selected_foreshadow_change_indexes': [],
        },
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    body = response.json()
    assert body['selected_change_indexes'] == {'characters': [], 'foreshadows': []}
    assert body['consistency_summary']['status'] == 'clear'
    assert body['consistency_warnings'] == []
```

- [ ] **Step 5: Add blocking approval RED test**

Add test:

```python
def test_approve_chapter_blocks_selected_consistency_violations(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    set_foreshadow_status(db_session, 1, 'resolved')
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: RollbackForeshadowLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '重新推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    response = client.post(
        f"/chapters/{draft['chapter_id']}/approve",
        json={'draft_version': draft['draft_version'], 'selected_foreshadow_change_indexes': [0]},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 409
    detail = response.json()['detail']
    assert detail['code'] == 'CONSISTENCY_BLOCKED'
    assert detail['summary']['blocking_count'] == 1
    assert detail['warnings'][0]['category'] == 'foreshadow_transition'
```

- [ ] **Step 6: Add warning-only approval and EventLog RED test**

Add test:

```python
def test_approve_chapter_allows_warning_only_consistency_and_records_summary(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: CharacterJumpLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '切换角色目标'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    response = client.post(
        f"/chapters/{draft['chapter_id']}/approve",
        json={'draft_version': draft['draft_version'], 'selected_character_change_indexes': [0]},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    approved = chapter_approved_event(db_session, world_id)
    assert approved.payload['consistency_summary']['status'] == 'needs_review'
    assert approved.payload['consistency_summary']['warning_count'] == 1
    assert approved.payload['consistency_warnings'][0]['severity'] == 'warning'
    assert approved.payload['consistency_warnings'][0]['category'] == 'character_jump'
```

- [ ] **Step 7: Run backend RED tests**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_approval.py -v
```

Expected: new tests fail because `consistency_summary` / `approval-consistency` / `CONSISTENCY_BLOCKED` are not implemented yet.

---

## Task 2: Backend GREEN implementation

**Files:**
- Modify: `backend/app/narrative/schemas.py`
- Modify: `backend/app/narrative/router.py`
- Modify: `backend/app/narrative/service.py`
- Test: `backend/tests/test_narrative_approval.py`

- [ ] **Step 1: Add response schemas**

In `backend/app/narrative/schemas.py`, after `ApproveRequest`, add:

```python
class ConsistencyWarning(BaseModel):
    severity: Literal['info', 'warning', 'blocking']
    category: str
    message: str
    object_type: Literal['character', 'foreshadow', 'chapter']
    object_id: int | None = None
    change_index: int | None = None
    details: dict = Field(default_factory=dict)


class ConsistencySummary(BaseModel):
    status: Literal['clear', 'needs_review', 'blocked']
    total: int
    info_count: int
    warning_count: int
    blocking_count: int


class ApprovalConsistencyResponse(BaseModel):
    chapter_id: int
    draft_version: int
    selected_change_indexes: dict
    consistency_summary: ConsistencySummary
    consistency_warnings: list[ConsistencyWarning]
```

- [ ] **Step 2: Add router endpoint**

In `backend/app/narrative/router.py`, import `ApprovalConsistencyResponse` and `get_approval_consistency`, then add after `approval_preview`:

```python
@router.post('/chapters/{chapter_id}/approval-consistency', response_model=ApprovalConsistencyResponse)
def approval_consistency(
    chapter_id: int,
    payload: ApproveRequest | None = None,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> ApprovalConsistencyResponse:
    return ApprovalConsistencyResponse.model_validate(get_approval_consistency(db, current_user, chapter_id, payload))
```

- [ ] **Step 3: Add consistency helper functions in service**

In `backend/app/narrative/service.py`, near `_selected_changes`, add helpers:

```python
FORESHADOW_STATUS_ORDER = {'planted': 0, 'advanced': 1, 'resolved': 2, 'expired': 3}


def _consistency_warning(severity: str, category: str, message: str, object_type: str, object_id=None, change_index=None, details=None) -> dict:
    return {
        'severity': severity,
        'category': category,
        'message': message,
        'object_type': object_type,
        'object_id': object_id,
        'change_index': change_index,
        'details': details or {},
    }


def _consistency_summary(warnings: list[dict]) -> dict:
    info_count = sum(1 for warning in warnings if warning['severity'] == 'info')
    warning_count = sum(1 for warning in warnings if warning['severity'] == 'warning')
    blocking_count = sum(1 for warning in warnings if warning['severity'] == 'blocking')
    if blocking_count:
        summary_status = 'blocked'
    elif warning_count:
        summary_status = 'needs_review'
    else:
        summary_status = 'clear'
    return {
        'status': summary_status,
        'total': len(warnings),
        'info_count': info_count,
        'warning_count': warning_count,
        'blocking_count': blocking_count,
    }


def _goals_overlap(before_goals, after_goals) -> bool:
    return bool(set(before_goals or []) & set(after_goals or []))


def _evaluate_approval_consistency(character_changes: list[tuple], foreshadow_changes: list[tuple]) -> dict:
    warnings = []
    for index, character, _change, before, after in character_changes:
        before_status = before.get('status')
        after_status = after.get('status')
        before_goals = before.get('current_goals') or []
        after_goals = after.get('current_goals') or []
        changed_status = before_status != after_status
        changed_goals = before_goals != after_goals
        if not changed_status and not changed_goals:
            warnings.append(_consistency_warning(
                'info',
                'world_projection',
                f'角色「{character.name}」的拟提交变化不会改变当前投影。',
                'character',
                character.id,
                index,
                {'before': before, 'after': after},
            ))
        elif changed_status and changed_goals and before_goals and after_goals and not _goals_overlap(before_goals, after_goals):
            warnings.append(_consistency_warning(
                'warning',
                'character_jump',
                f'角色「{character.name}」的状态与目标同时大幅变化，请确认正文已有足够铺垫。',
                'character',
                character.id,
                index,
                {'before_status': before_status, 'after_status': after_status, 'before_goals': before_goals, 'after_goals': after_goals},
            ))
        elif before_goals and changed_goals and not after_goals:
            warnings.append(_consistency_warning(
                'warning',
                'character_goal_shift',
                f'角色「{character.name}」的当前目标将被清空，请确认这符合角色弧线。',
                'character',
                character.id,
                index,
                {'before_goals': before_goals, 'after_goals': after_goals},
            ))

    for index, foreshadow, _change, before, after in foreshadow_changes:
        before_status = before.get('status')
        after_status = after.get('status')
        before_rank = FORESHADOW_STATUS_ORDER.get(before_status)
        after_rank = FORESHADOW_STATUS_ORDER.get(after_status)
        if before_rank is None or after_rank is None:
            warnings.append(_consistency_warning(
                'blocking',
                'foreshadow_transition',
                f'伏笔「{foreshadow.title}」包含未知状态转换，不能批准。',
                'foreshadow',
                foreshadow.id,
                index,
                {'before_status': before_status, 'after_status': after_status},
            ))
        elif after_rank < before_rank:
            warnings.append(_consistency_warning(
                'blocking',
                'foreshadow_transition',
                f'伏笔「{foreshadow.title}」不能从 {before_status} 回退到 {after_status}。',
                'foreshadow',
                foreshadow.id,
                index,
                {'before_status': before_status, 'after_status': after_status},
            ))
        elif after_rank == before_rank:
            warnings.append(_consistency_warning(
                'info',
                'foreshadow_transition',
                f'伏笔「{foreshadow.title}」状态保持为 {after_status}。',
                'foreshadow',
                foreshadow.id,
                index,
                {'before_status': before_status, 'after_status': after_status},
            ))
    return {'summary': _consistency_summary(warnings), 'warnings': warnings}
```

- [ ] **Step 4: Extract selected change-set builder**

Add helper after evaluator:

```python
def _approval_change_set(db: Session, world: World, draft: ChapterDraft, selection=None) -> dict:
    proposed_character_changes = list((draft.proposed_changes or {}).get('characters', []))
    proposed_foreshadow_changes = list((draft.proposed_changes or {}).get('foreshadows', []))
    selected_character_indexes = _change_index_set(
        selection.selected_character_change_indexes if selection is not None else None,
        len(proposed_character_changes),
    )
    selected_foreshadow_indexes = _change_index_set(
        selection.selected_foreshadow_change_indexes if selection is not None else None,
        len(proposed_foreshadow_changes),
    )

    character_changes = []
    for index, change in _selected_changes(proposed_character_changes, selected_character_indexes):
        character = db.get(Character, change.get('character_id'))
        if character is None or character.world_id != world.id:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='MODEL_RESPONSE_INVALID')
        before = character_projection(character)
        after = before | {key: change[key] for key in ('status', 'current_goals') if key in change}
        character_changes.append((index, character, change, before, after))

    foreshadow_changes = []
    for index, change in _selected_changes(proposed_foreshadow_changes, selected_foreshadow_indexes):
        foreshadow = db.get(Foreshadow, change.get('foreshadow_id'))
        if foreshadow is None or foreshadow.world_id != world.id or 'status' not in change:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='MODEL_RESPONSE_INVALID')
        before = foreshadow_projection(foreshadow)
        after = before | {'status': change['status']}
        if change.get('description_note'):
            after['description'] = f"{foreshadow.description}\n审核备注：{change['description_note']}"
        foreshadow_changes.append((index, foreshadow, change, before, after))

    return {
        'selected_change_indexes': {
            'characters': [index for index, _character, _change, _before, _after in character_changes],
            'foreshadows': [index for index, _foreshadow, _change, _before, _after in foreshadow_changes],
        },
        'character_changes': character_changes,
        'foreshadow_changes': foreshadow_changes,
    }
```

- [ ] **Step 5: Update approval preview**

Change `get_approval_preview()` to build all preview rows as today, then compute:

```python
change_set = _approval_change_set(db, world, draft)
consistency = _evaluate_approval_consistency(change_set['character_changes'], change_set['foreshadow_changes'])
```

Return fields:

```python
'consistency_summary': consistency['summary'],
'consistency_warnings': consistency['warnings'],
```

Keep existing `warnings: ['WORLD_VERSION_MISMATCH'] if version_conflict else []` unchanged.

- [ ] **Step 6: Add selected consistency service function**

Add:

```python
def get_approval_consistency(db: Session, user: User, chapter_id: int, selection=None) -> dict:
    chapter = _require_owned_chapter(db, user, chapter_id)
    draft = _latest_draft(db, chapter)
    if draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    if selection is not None and selection.draft_version is not None and selection.draft_version != draft.draft_version:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='DRAFT_VERSION_MISMATCH')
    world = db.get(World, chapter.world_id)
    assert world is not None
    change_set = _approval_change_set(db, world, draft, selection)
    consistency = _evaluate_approval_consistency(change_set['character_changes'], change_set['foreshadow_changes'])
    return {
        'chapter_id': chapter.id,
        'draft_version': draft.draft_version,
        'selected_change_indexes': change_set['selected_change_indexes'],
        'consistency_summary': consistency['summary'],
        'consistency_warnings': consistency['warnings'],
    }
```

- [ ] **Step 7: Update approve flow**

Inside `approve_chapter()`, replace duplicated selected-change construction with:

```python
change_set = _approval_change_set(db, world, draft, selection)
character_changes = change_set['character_changes']
foreshadow_changes = change_set['foreshadow_changes']
consistency = _evaluate_approval_consistency(character_changes, foreshadow_changes)
if consistency['summary']['blocking_count'] > 0:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            'code': 'CONSISTENCY_BLOCKED',
            'summary': consistency['summary'],
            'warnings': consistency['warnings'],
        },
    )
```

Then add to `chapter_approved` payload:

```python
'consistency_summary': consistency['summary'],
'consistency_warnings': consistency['warnings'],
```

- [ ] **Step 8: Run backend GREEN tests**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_approval.py -v
```

Expected: all tests in `test_narrative_approval.py` pass.

---

## Task 3: Frontend RED tests

**Files:**
- Modify: `frontend/src/studio/StudioPage.test.tsx`
- Modify: `frontend/src/api/client.test.ts`

- [ ] **Step 1: Extend Studio mock imports**

In `frontend/src/studio/StudioPage.test.tsx`, import `checkApprovalConsistency` from `../api/client`.

- [ ] **Step 2: Add mock helper and default consistency data**

Update the mocked `getApprovalPreview` response to include:

```ts
consistency_summary: { status: 'needs_review', total: 1, info_count: 0, warning_count: 1, blocking_count: 0 },
consistency_warnings: [
  { severity: 'warning', category: 'character_jump', message: '角色「林砚」的状态与目标同时大幅变化，请确认正文已有足够铺垫。', object_type: 'character', object_id: 1, change_index: 0, details: {} },
],
```

Add mocked helper:

```ts
checkApprovalConsistency: vi.fn(async () => ({
  chapter_id: 11,
  draft_version: 1,
  selected_change_indexes: { characters: [0], foreshadows: [0] },
  consistency_summary: { status: 'needs_review', total: 1, info_count: 0, warning_count: 1, blocking_count: 0 },
  consistency_warnings: [
    { severity: 'warning', category: 'character_jump', message: '角色「林砚」的状态与目标同时大幅变化，请确认正文已有足够铺垫。', object_type: 'character', object_id: 1, change_index: 0, details: {} },
  ],
})),
```

Clear it in `afterEach()`.

- [ ] **Step 3: Add Studio warning render RED test**

Add:

```tsx
it('renders approval consistency warnings from the preview', async () => {
  const user = userEvent.setup();
  render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

  await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
  await user.click(screen.getByRole('button', { name: '创建章节' }));
  await user.click(await screen.findByRole('button', { name: '生成大纲' }));
  await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));

  expect(await screen.findByText('一致性检查')).toBeInTheDocument();
  expect(screen.getByText('存在需复核项')).toBeInTheDocument();
  expect(screen.getByText('角色「林砚」的状态与目标同时大幅变化，请确认正文已有足够铺垫。')).toBeInTheDocument();
});
```

- [ ] **Step 4: Add blocking disables approve RED test**

Add:

```tsx
it('disables approval when selected consistency is blocked', async () => {
  const user = userEvent.setup();
  vi.mocked(checkApprovalConsistency).mockResolvedValueOnce({
    chapter_id: 11,
    draft_version: 1,
    selected_change_indexes: { characters: [0], foreshadows: [] },
    consistency_summary: { status: 'blocked', total: 1, info_count: 0, warning_count: 0, blocking_count: 1 },
    consistency_warnings: [
      { severity: 'blocking', category: 'foreshadow_transition', message: '伏笔「裂纹玉佩」不能从 resolved 回退到 advanced。', object_type: 'foreshadow', object_id: 1, change_index: 0, details: {} },
    ],
  });
  render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

  await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
  await user.click(screen.getByRole('button', { name: '创建章节' }));
  await user.click(await screen.findByRole('button', { name: '生成大纲' }));
  await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));
  await user.click(await screen.findByRole('checkbox', { name: /伏笔：裂纹玉佩/ }));

  expect(await screen.findByText('存在阻塞项')).toBeInTheDocument();
  expect(screen.getByText('伏笔「裂纹玉佩」不能从 resolved 回退到 advanced。')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '通过并更新世界' })).toBeDisabled();
});
```

- [ ] **Step 5: Add selected consistency payload RED test**

Add assertion to selection test or new test:

```tsx
expect(checkApprovalConsistency).toHaveBeenCalledWith(11, {
  draft_version: 1,
  selected_character_change_indexes: [0],
  selected_foreshadow_change_indexes: [],
});
```

- [ ] **Step 6: Update API helper RED test**

In `frontend/src/api/client.test.ts`, import `checkApprovalConsistency`. Extend the existing test `calls draft stash, paragraph revision, full revision, exact version, diff, and approval preview endpoints` to include one more mocked response and call:

```ts
await checkApprovalConsistency(11, { draft_version: 1, selected_character_change_indexes: [0], selected_foreshadow_change_indexes: [] });
```

Assert:

```ts
expect(fetchMock).toHaveBeenNthCalledWith(
  7,
  'http://localhost:8000/chapters/11/approval-consistency',
  expect.objectContaining({
    method: 'POST',
    body: JSON.stringify({ draft_version: 1, selected_character_change_indexes: [0], selected_foreshadow_change_indexes: [] }),
  }),
);
```

- [ ] **Step 7: Run frontend RED tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx src/api/client.test.ts
```

Expected: new tests fail because frontend consistency types/helper/UI are not implemented yet.

---

## Task 4: Frontend GREEN implementation

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/studio/StudioPage.tsx`
- Test: `frontend/src/studio/StudioPage.test.tsx`
- Test: `frontend/src/api/client.test.ts`

- [ ] **Step 1: Add frontend types**

In `frontend/src/api/types.ts`, after `ApproveRequest`, add:

```ts
export type ConsistencySeverity = 'info' | 'warning' | 'blocking';
export type ConsistencyStatus = 'clear' | 'needs_review' | 'blocked';

export type ConsistencyWarning = {
  severity: ConsistencySeverity;
  category: string;
  message: string;
  object_type: 'character' | 'foreshadow' | 'chapter';
  object_id: number | null;
  change_index: number | null;
  details: Record<string, unknown>;
};

export type ConsistencySummary = {
  status: ConsistencyStatus;
  total: number;
  info_count: number;
  warning_count: number;
  blocking_count: number;
};

export type ApprovalConsistencyResponse = {
  chapter_id: number;
  draft_version: number;
  selected_change_indexes: { characters: number[]; foreshadows: number[] };
  consistency_summary: ConsistencySummary;
  consistency_warnings: ConsistencyWarning[];
};
```

Extend `ApprovalPreviewResponse` with:

```ts
consistency_summary: ConsistencySummary;
consistency_warnings: ConsistencyWarning[];
```

- [ ] **Step 2: Add API client helper**

In `frontend/src/api/client.ts`, import `ApprovalConsistencyResponse`, then add after `getApprovalPreview`:

```ts
export function checkApprovalConsistency(chapterId: number, data: ApproveRequest = {}) {
  return apiRequest<ApprovalConsistencyResponse>(`/chapters/${chapterId}/approval-consistency`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
```

- [ ] **Step 3: Update Studio imports and state**

In `frontend/src/studio/StudioPage.tsx`, import `checkApprovalConsistency`. Extend type import with `ConsistencySummary` and `ConsistencyWarning`.

Add state:

```tsx
const [consistencySummary, setConsistencySummary] = useState<ConsistencySummary | null>(null);
const [consistencyWarnings, setConsistencyWarnings] = useState<ConsistencyWarning[]>([]);
```

- [ ] **Step 4: Add consistency helper functions**

Add near selection helpers:

```tsx
function clearApprovalConsistency() {
  setConsistencySummary(null);
  setConsistencyWarnings([]);
}

function setPreviewConsistency(preview: ApprovalPreviewResponse) {
  setConsistencySummary(preview.consistency_summary);
  setConsistencyWarnings(preview.consistency_warnings);
}

function consistencyLabel(summary: ConsistencySummary): string {
  if (summary.status === 'blocked') return '存在阻塞项';
  if (summary.status === 'needs_review') return '存在需复核项';
  return '一致性检查通过';
}

async function refreshApprovalConsistency(characterIndexes: number[], foreshadowIndexes: number[]) {
  if (!draft) return;
  const result = await checkApprovalConsistency(draft.chapter_id, {
    draft_version: resolveDraftVersion(draft),
    selected_character_change_indexes: characterIndexes,
    selected_foreshadow_change_indexes: foreshadowIndexes,
  });
  setConsistencySummary(result.consistency_summary);
  setConsistencyWarnings(result.consistency_warnings);
}
```

- [ ] **Step 5: Update preview load and clear flows**

After `setApprovalPreview(preview)` in `refreshReviewStudioPanels()`, call:

```tsx
setPreviewConsistency(preview);
```

Where approval preview is cleared, call `clearApprovalConsistency()` alongside `clearApprovalSelection()`.

- [ ] **Step 6: Add selection toggle wrappers**

Add:

```tsx
async function toggleCharacterSelection(changeIndex: number) {
  const nextCharacterIndexes = toggleIndex(selectedCharacterChangeIndexes, changeIndex);
  setSelectedCharacterChangeIndexes(nextCharacterIndexes);
  try {
    await refreshApprovalConsistency(nextCharacterIndexes, selectedForeshadowChangeIndexes);
  } catch (err) {
    setError(err instanceof Error ? err.message : '刷新一致性检查失败');
  }
}

async function toggleForeshadowSelection(changeIndex: number) {
  const nextForeshadowIndexes = toggleIndex(selectedForeshadowChangeIndexes, changeIndex);
  setSelectedForeshadowChangeIndexes(nextForeshadowIndexes);
  try {
    await refreshApprovalConsistency(selectedCharacterChangeIndexes, nextForeshadowIndexes);
  } catch (err) {
    setError(err instanceof Error ? err.message : '刷新一致性检查失败');
  }
}
```

Replace checkbox `onChange` handlers with:

```tsx
onChange={() => void toggleCharacterSelection(changeIndex)}
```

and:

```tsx
onChange={() => void toggleForeshadowSelection(changeIndex)}
```

- [ ] **Step 7: Render consistency panel**

Inside the approval preview card after selected count, add:

```tsx
{consistencySummary && (
  <div className="space-y-2 rounded-xl bg-white/45 p-3">
    <h4 className="font-black text-[#3b2511]">一致性检查</h4>
    <p className="manuscript text-sm">{consistencyLabel(consistencySummary)} · blocking {consistencySummary.blocking_count} / warning {consistencySummary.warning_count} / info {consistencySummary.info_count}</p>
    {consistencyWarnings.map((warning, index) => (
      <p key={`${warning.severity}-${warning.category}-${warning.object_id}-${warning.change_index}-${index}`} className={warning.severity === 'blocking' ? 'paper-error' : warning.severity === 'warning' ? 'rounded bg-amber-100 px-3 py-2 text-sm text-amber-900' : 'manuscript text-sm'}>
        {warning.message}
      </p>
    ))}
  </div>
)}
```

- [ ] **Step 8: Disable approval on blocking consistency**

Add derived value:

```tsx
const approvalBlockedByConsistency = consistencySummary?.status === 'blocked';
```

Change approve button disabled expression:

```tsx
disabled={working || !isViewingLatestDraft() || approvalBlockedByConsistency}
```

Add text near approval controls or preview card:

```tsx
{approvalBlockedByConsistency && <p className="paper-error">存在阻塞项，请取消相关变化或重新修订草稿。</p>}
```

- [ ] **Step 9: Run frontend GREEN tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx src/api/client.test.ts
```

Expected: targeted frontend tests pass.

---

## Task 5: Full targeted verification and inline self-review

**Files:**
- Review changed files inline through `git diff`.
- No code-review subagent.

- [ ] **Step 1: Run backend targeted tests**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_approval.py tests/test_narrative_draft_versioning.py tests/test_story_bible_management.py -v
```

Expected: all targeted backend tests pass.

- [ ] **Step 2: Run frontend targeted tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx src/api/client.test.ts
```

Expected: all targeted frontend tests pass.

- [ ] **Step 3: Run frontend build**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: TypeScript and Vite build succeed.

- [ ] **Step 4: Inline self-review**

Review `git diff` and verify:

- Preview, selected consistency endpoint, and approve use shared evaluator.
- Blocking warnings are enforced on backend, not only frontend.
- EventLog records consistency summary/warnings for the actual selected set.
- Existing MVP10 selection semantics remain intact.
- No Workflow tool or subagents were used.
- No push was performed.

---

## Task 6: Commit, merge to main, no push

**Files:**
- All MVP11 changed files.

- [ ] **Step 1: Check branch and status**

Run:

```bash
cd /opt/WorldSim-Writer && git status --short --branch
```

Expected: on `feat/mvp11-consistency-review`, with MVP11 changes staged or unstaged.

- [ ] **Step 2: Commit MVP11**

Run:

```bash
cd /opt/WorldSim-Writer && git add docs/superpowers/specs/2026-05-31-mvp11-consistency-review-design.md docs/superpowers/plans/2026-05-31-mvp11-consistency-review.md backend/app/narrative/schemas.py backend/app/narrative/router.py backend/app/narrative/service.py backend/tests/test_narrative_approval.py frontend/src/api/types.ts frontend/src/api/client.ts frontend/src/api/client.test.ts frontend/src/studio/StudioPage.tsx frontend/src/studio/StudioPage.test.tsx && git commit -m "feat: add approval consistency review" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

Expected: commit succeeds on `feat/mvp11-consistency-review`.

- [ ] **Step 3: Merge back to main**

Run:

```bash
cd /opt/WorldSim-Writer && git switch main && git merge feat/mvp11-consistency-review
```

Expected: fast-forward or clean merge succeeds.

- [ ] **Step 4: Post-merge verification**

Run the same targeted backend tests, frontend targeted tests, and frontend build after merge:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_approval.py tests/test_narrative_draft_versioning.py tests/test_story_bible_management.py -v
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx src/api/client.test.ts
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: all pass.

- [ ] **Step 5: Final status**

Run:

```bash
cd /opt/WorldSim-Writer && git status --short --branch
```

Expected: clean `main`, ahead of `origin/main` by 7 commits, no push performed.

---

## Plan self-review

- Spec coverage: preview warnings, selected recalculation, blocking approval guard, warning-only approval, EventLog consistency audit, MVP10 compatibility, and targeted verification are each mapped to a task.
- Placeholder scan: no `TBD`, `TODO`, or vague implementation-only steps remain; code snippets and exact commands are included.
- Type consistency: backend `consistency_summary` / `consistency_warnings` names match frontend types and planned response payloads; `ApproveRequest` is reused for approve and consistency endpoint.
- Scope check: the work is a single approval-flow slice and does not include auto-repair, complex rules engine, multi-user policy, or LLM-driven approval.
