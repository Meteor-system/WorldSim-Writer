# MVP #10 Approval Change Set Review 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add draft-version-scoped approval change-set selection so writers can approve a chapter while committing only selected proposed character and foreshadow changes.

**Architecture:** Extend the existing narrative approval flow rather than adding a new subsystem. The backend adds an optional approve request schema, selection validation helpers, additive preview indexes, and subset application/logging in `approve_chapter()`. The frontend makes the existing approval preview panel selectable and sends selected indexes through a typed `approveChapter()` helper.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy, pytest, React, TypeScript, Vite, Vitest, Testing Library.

---

## File map

- Modify `backend/app/narrative/schemas.py`: add `ApproveRequest`.
- Modify `backend/app/narrative/router.py`: accept optional approve payload and pass it to the service.
- Modify `backend/app/narrative/service.py`: add preview indexes, validate selected indexes, apply/log selected subset only.
- Modify `backend/tests/test_narrative_approval.py`: add RED/GREEN tests for preview indexes, selected subset approval, empty selection, invalid indexes, stale draft version, and existing no-selection behavior.
- Modify `frontend/src/api/types.ts`: add `ApproveRequest` and preview change index fields.
- Modify `frontend/src/api/client.ts`: add `approveChapter()` helper.
- Modify `frontend/src/studio/StudioPage.tsx`: add checkbox state, initialize from preview, submit selected indexes.
- Modify `frontend/src/studio/StudioPage.test.tsx`: add RED/GREEN tests for selectable approval preview and payload submission.

## Constraints

- NO dynamic workflows.
- No subagents.
- Skip code-review subagent; use inline self-review.
- TDD required: add failing tests before production changes.
- Do not push.
- Finish by committing on `feat/mvp10-approval-change-set-review`, merging to `main`, and leaving local `main` ahead of `origin/main`.

---

### Task 1: Create feature branch

**Files:** none

- [ ] **Step 1: Check current branch and worktree**

Run:

```bash
git status --short --branch
```

Expected: on `main`, ahead of `origin/main`, with only MVP10 spec/plan docs uncommitted.

- [ ] **Step 2: Create implementation branch**

Run:

```bash
git switch -c feat/mvp10-approval-change-set-review
```

Expected: branch changes to `feat/mvp10-approval-change-set-review`; uncommitted spec/plan docs remain present.

---

### Task 2: Backend RED tests for approval selection

**Files:**
- Modify: `backend/tests/test_narrative_approval.py`

- [ ] **Step 1: Add test helpers**

Add imports and helpers near the top of `backend/tests/test_narrative_approval.py`:

```python
from sqlalchemy import select

from app.event.models import EventLog
from app.foreshadow.models import Foreshadow
from app.llm.schemas import ChapterGeneration, ProposedCharacterChange, ProposedForeshadowChange
from app.narrative import service as narrative_service
from app.narrative.models import Chapter, ChapterDraft
from app.world.models import World
```

If an import already exists, do not duplicate it. Add this fake client below `FakeLLMClient`:

```python
class MultiChangeLLMClient:
    def generate_chapter(self, messages):
        return ChapterGeneration(
            title='第一章 雨巷密谈',
            draft_content='林砚停在雨巷口，沈微霜递来一封湿透的信。',
            context_summary='林砚与沈微霜交换线索。',
            review_hints=['确认角色状态与伏笔推进是否都应提交'],
            proposed_character_changes=[
                ProposedCharacterChange(character_id=1, status='开始调查密信', current_goals=['追查湿信来源']),
                ProposedCharacterChange(character_id=2, status='隐瞒湿信来历', current_goals=['观察林砚反应']),
            ],
            proposed_foreshadow_changes=[
                ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='湿信推进玉佩线索'),
            ],
        )
```

Add helper functions:

```python
def event_logs(db_session, world_id):
    return list(
        db_session.scalars(
            select(EventLog)
            .where(EventLog.world_id == world_id)
            .order_by(EventLog.id)
        )
    )


def chapter_approved_event(db_session, world_id):
    return next(event for event in event_logs(db_session, world_id) if event.event_type == 'chapter_approved')
```

- [ ] **Step 2: Add preview index test**

Add:

```python
def test_approval_preview_exposes_change_indexes_and_default_selection(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    response = client.get(f"/chapters/{draft['chapter_id']}/approval-preview", headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    body = response.json()
    assert body['character_changes'][0]['change_index'] == 0
    assert body['character_changes'][0]['selected_by_default'] is True
    assert body['foreshadow_changes'][0]['change_index'] == 0
    assert body['foreshadow_changes'][0]['selected_by_default'] is True
```

- [ ] **Step 3: Add selected subset approval test**

Add:

```python
def test_approve_chapter_applies_only_selected_character_and_foreshadow_changes(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: MultiChangeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进雨巷密谈'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    response = client.post(
        f"/chapters/{draft['chapter_id']}/approve",
        json={
            'draft_version': draft['draft_version'],
            'selected_character_change_indexes': [1],
            'selected_foreshadow_change_indexes': [0],
        },
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    overview = client.get(f'/worlds/{world_id}/overview', headers={'Authorization': f'Bearer {token}'}).json()
    assert overview['world_version'] == 2
    characters_by_id = {character['id']: character for character in overview['characters']}
    foreshadows_by_id = {foreshadow['id']: foreshadow for foreshadow in overview['foreshadows']}
    assert characters_by_id[1]['status'] == 'active'
    assert characters_by_id[2]['status'] == '隐瞒湿信来历'
    assert foreshadows_by_id[1]['status'] == 'advanced'

    events = event_logs(db_session, world_id)
    assert [event.event_type for event in events].count('character_change') == 1
    assert [event.event_type for event in events].count('foreshadow_change') == 1
    approved = chapter_approved_event(db_session, world_id)
    assert approved.payload['applied_change_indexes'] == {'characters': [1], 'foreshadows': [0]}
    assert approved.payload['applied_changes']['characters'] == [draft['proposed_changes']['characters'][1]]
    assert approved.payload['applied_changes']['foreshadows'] == [draft['proposed_changes']['foreshadows'][0]]
    assert 'proposed_changes' not in approved.payload
```

- [ ] **Step 4: Add empty selection test**

Add:

```python
def test_approve_chapter_allows_empty_selection_without_object_changes(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    response = client.post(
        f"/chapters/{draft['chapter_id']}/approve",
        json={
            'draft_version': draft['draft_version'],
            'selected_character_change_indexes': [],
            'selected_foreshadow_change_indexes': [],
        },
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    overview = client.get(f'/worlds/{world_id}/overview', headers={'Authorization': f'Bearer {token}'}).json()
    assert overview['world_version'] == 2
    assert overview['characters'][0]['current_goals'] == []
    assert overview['foreshadows'][0]['status'] == 'planted'
    events = event_logs(db_session, world_id)
    assert 'character_change' not in [event.event_type for event in events]
    assert 'foreshadow_change' not in [event.event_type for event in events]
    approved = chapter_approved_event(db_session, world_id)
    assert approved.payload['applied_changes'] == {'characters': [], 'foreshadows': []}
```

- [ ] **Step 5: Add validation tests**

Add:

```python
def test_approve_chapter_rejects_invalid_change_selection(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    response = client.post(
        f"/chapters/{draft['chapter_id']}/approve",
        json={'draft_version': draft['draft_version'], 'selected_character_change_indexes': [0, 0]},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 400
    assert response.json()['detail'] == 'INVALID_CHANGE_SELECTION'


def test_approve_chapter_rejects_stale_draft_version_selection(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    response = client.post(
        f"/chapters/{draft['chapter_id']}/approve",
        json={'draft_version': draft['draft_version'] + 1, 'selected_character_change_indexes': [0]},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 409
    assert response.json()['detail'] == 'DRAFT_VERSION_MISMATCH'
```

- [ ] **Step 6: Run backend RED tests**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_approval.py -v'
```

Expected: new tests fail because preview lacks indexes, approve request schema is missing, and approve applies all changes.

---

### Task 3: Backend GREEN implementation

**Files:**
- Modify: `backend/app/narrative/schemas.py`
- Modify: `backend/app/narrative/router.py`
- Modify: `backend/app/narrative/service.py`

- [ ] **Step 1: Add approve schema**

In `backend/app/narrative/schemas.py`, add after `DraftResponse`:

```python
class ApproveRequest(BaseModel):
    draft_version: int | None = None
    selected_character_change_indexes: list[int] | None = None
    selected_foreshadow_change_indexes: list[int] | None = None
```

- [ ] **Step 2: Route approve payload into service**

In `backend/app/narrative/router.py`, import `ApproveRequest` and change approve endpoint to:

```python
@router.post('/chapters/{chapter_id}/approve', response_model=ChapterResponse)
def approve(
    chapter_id: int,
    payload: ApproveRequest | None = None,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> ChapterResponse:
    return ChapterResponse.model_validate(approve_chapter(db, current_user, chapter_id, payload))
```

- [ ] **Step 3: Add selection helpers**

In `backend/app/narrative/service.py`, above `get_approval_preview()`, add helpers:

```python
def _change_index_set(selection: list[int] | None, total: int) -> set[int]:
    if selection is None:
        return set(range(total))
    if len(selection) != len(set(selection)) or any(index < 0 or index >= total for index in selection):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='INVALID_CHANGE_SELECTION')
    return set(selection)


def _selected_changes(changes: list[dict], indexes: set[int]) -> list[tuple[int, dict]]:
    return [(index, change) for index, change in enumerate(changes) if index in indexes]
```

- [ ] **Step 4: Add preview indexes**

Change `get_approval_preview()` loops to use `enumerate(...)` and include:

```python
'change_index': index,
'selected_by_default': True,
```

in both character and foreshadow preview objects.

- [ ] **Step 5: Apply selected subset in approve_chapter**

Change signature to:

```python
def approve_chapter(db: Session, user: User, chapter_id: int, selection=None) -> Chapter:
```

Inside the function after loading `draft` and before `WORLD_VERSION_MISMATCH`, add:

```python
if selection is not None and selection.draft_version is not None and selection.draft_version != draft.draft_version:
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='DRAFT_VERSION_MISMATCH')
```

After world-version check, compute:

```python
proposed_character_changes = list(draft.proposed_changes.get('characters', []))
proposed_foreshadow_changes = list(draft.proposed_changes.get('foreshadows', []))
selected_character_indexes = _change_index_set(
    selection.selected_character_change_indexes if selection is not None else None,
    len(proposed_character_changes),
)
selected_foreshadow_indexes = _change_index_set(
    selection.selected_foreshadow_change_indexes if selection is not None else None,
    len(proposed_foreshadow_changes),
)
applied_character_changes = _selected_changes(proposed_character_changes, selected_character_indexes)
applied_foreshadow_changes = _selected_changes(proposed_foreshadow_changes, selected_foreshadow_indexes)
```

Then build `character_changes` and `foreshadow_changes` from `applied_*` tuples, preserving each index in the tuple:

```python
character_changes.append((index, character, change, before, after))
foreshadow_changes.append((index, foreshadow, change, before, after))
```

Update downstream loops to unpack the index.

Change `chapter_approved` payload to:

```python
payload={
    'commit_group_id': commit_group_id,
    'chapter_id': chapter.id,
    'chapter_title': chapter.title,
    'approved_version': draft.draft_version,
    'applied_changes': {
        'characters': [change for _index, _character, change, _before, _after in character_changes],
        'foreshadows': [change for _index, _foreshadow, change, _before, _after in foreshadow_changes],
    },
    'applied_change_indexes': {
        'characters': [index for index, _character, _change, _before, _after in character_changes],
        'foreshadows': [index for index, _foreshadow, _change, _before, _after in foreshadow_changes],
    },
}
```

- [ ] **Step 6: Run backend GREEN tests**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_approval.py -v'
```

Expected: all tests in `test_narrative_approval.py` pass.

---

### Task 4: Frontend RED tests for selectable approval preview

**Files:**
- Modify: `frontend/src/studio/StudioPage.test.tsx`

- [ ] **Step 1: Import approveChapter in test**

Change the test import to include `approveChapter`:

```ts
import { approveChapter, createChapter, generateCharacterArcReport, getApprovalReadiness, getDraftVersion, reviseDraft, writeChapter } from '../api/client';
```

Add `approveChapter: vi.fn(async () => ({ status: 'approved' }))` to the `vi.mock('../api/client', ...)` object.

- [ ] **Step 2: Add default checkbox test**

Add:

```tsx
it('renders approval preview changes as selected checkboxes by default', async () => {
  const user = userEvent.setup();
  render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

  await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
  await user.click(screen.getByRole('button', { name: '创建章节' }));
  await user.click(await screen.findByRole('button', { name: '生成大纲' }));
  await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));

  expect(await screen.findByRole('checkbox', { name: /角色：林砚/ })).toBeChecked();
  expect(screen.getByRole('checkbox', { name: /伏笔：裂纹玉佩/ })).toBeChecked();
  expect(screen.getByText('已选择 2 / 2 条拟提交变化')).toBeInTheDocument();
});
```

- [ ] **Step 3: Add approve payload test**

Add:

```tsx
it('submits only selected approval change indexes with the current draft version', async () => {
  const user = userEvent.setup();
  const onApproved = vi.fn();
  render(<StudioPage world={world} onBack={vi.fn()} onApproved={onApproved} />);

  await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
  await user.click(screen.getByRole('button', { name: '创建章节' }));
  await user.click(await screen.findByRole('button', { name: '生成大纲' }));
  await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));
  await user.click(await screen.findByRole('checkbox', { name: /伏笔：裂纹玉佩/ }));
  await user.click(screen.getByRole('button', { name: '通过并更新世界' }));

  expect(approveChapter).toHaveBeenCalledWith(11, {
    draft_version: 1,
    selected_character_change_indexes: [0],
    selected_foreshadow_change_indexes: [],
  });
});
```

- [ ] **Step 4: Run frontend RED test**

Run:

```bash
npm run test -- src/studio/StudioPage.test.tsx
```

Expected: new tests fail because checkboxes and `approveChapter()` do not exist yet.

---

### Task 5: Frontend GREEN implementation

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/studio/StudioPage.tsx`

- [ ] **Step 1: Update API types**

In `frontend/src/api/types.ts`, change `ApprovalPreviewChange` and add `ApproveRequest`:

```ts
export type ApprovalPreviewChange = {
  change_index: number;
  selected_by_default: boolean;
  before: Record<string, unknown>;
  after: Record<string, unknown>;
};

export type ApproveRequest = {
  draft_version?: number;
  selected_character_change_indexes?: number[];
  selected_foreshadow_change_indexes?: number[];
};
```

- [ ] **Step 2: Add approve client helper**

In `frontend/src/api/client.ts`, import `ApproveRequest` and add after `getApprovalReadiness()`:

```ts
export function approveChapter(chapterId: number, data: ApproveRequest = {}) {
  return apiRequest<ChapterPipelineResponse>(`/chapters/${chapterId}/approve`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
```

- [ ] **Step 3: Add selection state and initialization**

In `frontend/src/studio/StudioPage.tsx`, import `approveChapter`. Add state:

```ts
const [selectedCharacterChangeIndexes, setSelectedCharacterChangeIndexes] = useState<number[]>([]);
const [selectedForeshadowChangeIndexes, setSelectedForeshadowChangeIndexes] = useState<number[]>([]);
```

Add helpers near `isViewingLatestDraft()`:

```ts
function previewIndex(change: { change_index?: number }, fallback: number): number {
  return typeof change.change_index === 'number' ? change.change_index : fallback;
}

function toggleIndex(values: number[], index: number): number[] {
  return values.includes(index) ? values.filter((value) => value !== index) : [...values, index].sort((a, b) => a - b);
}

function initializeApprovalSelection(preview: ApprovalPreviewResponse) {
  setSelectedCharacterChangeIndexes(preview.character_changes.map((change, index) => previewIndex(change, index)));
  setSelectedForeshadowChangeIndexes(preview.foreshadow_changes.map((change, index) => previewIndex(change, index)));
}
```

After loading preview in `refreshReviewStudioPanels()`, call `initializeApprovalSelection(preview)`. When preview load fails, clear both selection arrays.

- [ ] **Step 4: Submit selected indexes**

Change `approveDraft()` to call:

```ts
await approveChapter(draft.chapter_id, {
  draft_version: resolveDraftVersion(draft),
  selected_character_change_indexes: selectedCharacterChangeIndexes,
  selected_foreshadow_change_indexes: selectedForeshadowChangeIndexes,
});
onApproved(await apiRequest<WorldOverview>(`/worlds/${world.id}/overview`));
```

- [ ] **Step 5: Render selectable preview**

Replace preview change `<p>` rows with checkbox labels:

```tsx
const totalPreviewChanges = approvalPreview.character_changes.length + approvalPreview.foreshadow_changes.length;
const selectedPreviewChanges = selectedCharacterChangeIndexes.length + selectedForeshadowChangeIndexes.length;
```

Use those counts in the preview section and render:

```tsx
<label key={`character-${change.change_index ?? index}`} className="flex items-start gap-3 rounded-xl bg-white/45 p-3 manuscript text-sm">
  <input
    type="checkbox"
    className="mt-1 accent-amber-800"
    checked={selectedCharacterChangeIndexes.includes(previewIndex(change, index))}
    onChange={() => setSelectedCharacterChangeIndexes((values) => toggleIndex(values, previewIndex(change, index)))}
  />
  <span>角色：{change.name} · {String(change.before.status ?? '未设置')} → {String(change.after.status ?? '未设置')}</span>
</label>
```

Use the same pattern for foreshadows with `selectedForeshadowChangeIndexes`.

- [ ] **Step 6: Run frontend GREEN tests**

Run:

```bash
npm run test -- src/studio/StudioPage.test.tsx
```

Expected: StudioPage tests pass.

---

### Task 6: Inline self-review and targeted verification

**Files:** all modified files

- [ ] **Step 1: Review diff inline**

Run:

```bash
git diff -- backend/app/narrative/schemas.py backend/app/narrative/router.py backend/app/narrative/service.py backend/tests/test_narrative_approval.py frontend/src/api/types.ts frontend/src/api/client.ts frontend/src/studio/StudioPage.tsx frontend/src/studio/StudioPage.test.tsx docs/superpowers/specs/2026-05-31-mvp10-approval-change-set-review-design.md docs/superpowers/plans/2026-05-31-mvp10-approval-change-set-review.md
```

Check manually:

- No dynamic workflow or subagent artifacts.
- No accidental push or unrelated edits.
- Backend `chapter_approved` payload records `applied_changes`, not full unselected `proposed_changes`.
- Old no-body approval path still applies all changes.
- Frontend approve button remains disabled for historical drafts.

- [ ] **Step 2: Run backend targeted tests**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_approval.py tests/test_narrative_draft_versioning.py tests/test_story_bible_management.py -v'
```

Expected: all selected backend tests pass.

- [ ] **Step 3: Run frontend targeted tests**

Run:

```bash
npm run test -- src/studio/StudioPage.test.tsx src/api/client.test.ts
```

Expected: all selected frontend tests pass.

- [ ] **Step 4: Run frontend build**

Run:

```bash
npm run build
```

Expected: TypeScript and Vite build succeed.

---

### Task 7: Commit and merge locally without pushing

**Files:** all modified files

- [ ] **Step 1: Check status**

Run:

```bash
git status --short --branch
```

Expected: on `feat/mvp10-approval-change-set-review` with only MVP10 files modified.

- [ ] **Step 2: Commit**

Run:

```bash
git add docs/superpowers/specs/2026-05-31-mvp10-approval-change-set-review-design.md docs/superpowers/plans/2026-05-31-mvp10-approval-change-set-review.md backend/app/narrative/schemas.py backend/app/narrative/router.py backend/app/narrative/service.py backend/tests/test_narrative_approval.py frontend/src/api/types.ts frontend/src/api/client.ts frontend/src/studio/StudioPage.tsx frontend/src/studio/StudioPage.test.tsx
git commit -m "feat: add approval change set review" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

Expected: commit succeeds.

- [ ] **Step 3: Merge to main**

Run:

```bash
git switch main
git merge feat/mvp10-approval-change-set-review
```

Expected: fast-forward merge succeeds.

- [ ] **Step 4: Verify merged state**

Run:

```bash
git status --short --branch
```

Expected: on `main`, clean working tree, ahead of `origin/main` by 6 commits. Do not push.

## Plan self-review

- Spec coverage: every backend, frontend, EventLog, compatibility, stale/version conflict, and historical draft requirement maps to Tasks 2-6.
- Placeholder scan: no TBD/TODO/fill-in-later placeholders remain.
- Type consistency: `ApproveRequest`, `change_index`, `selected_by_default`, `selected_character_change_indexes`, and `selected_foreshadow_change_indexes` are named consistently across backend schema, frontend types, tests, and implementation tasks.
- TDD check: backend and frontend tests are explicitly added and run RED before implementation steps.
