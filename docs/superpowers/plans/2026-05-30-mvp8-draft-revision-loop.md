# MVP #8 Draft Revision Loop 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This MVP explicitly forbids dynamic workflows and subagents; use inline self-review instead of code-review subagents.

**Goal:** Add a Studio full-draft revision loop that generates a new draft version from the current draft, frozen context, review reports, approval readiness, and a user revision instruction without mutating formal world state.

**Architecture:** Add a backend `POST /chapters/{chapter_id}/draft/revise` endpoint that reuses `ChapterGeneration`, `_create_draft_version`, and existing ID validation. Add a read-only draft-version endpoint for lightweight version switching. Extend Studio with a revision instruction panel, version switching, parent version display, diff refresh, and historical-version approval guard.

**Tech Stack:** FastAPI + SQLAlchemy + Pydantic + Pytest backend; React + TypeScript + Vite + Vitest + Testing Library frontend.

---

## File Map

- Modify: `backend/app/llm/schemas.py` — reuse `ChapterGeneration`; no new schema expected unless implementation discovers a stronger need.
- Modify: `backend/app/llm/client.py` — add `revise_chapter(messages)` and mock revision output.
- Modify: `backend/app/narrative/schemas.py` — add `ReviseDraftRequest`.
- Modify: `backend/app/narrative/router.py` — add revise and read-version endpoints.
- Modify: `backend/app/narrative/service.py` — add revision prompt builder, revision service, exact draft lookup service.
- Modify: `backend/tests/test_narrative_draft_versioning.py` — backend RED/GREEN tests for full-draft revision and draft lookup.
- Modify: `frontend/src/api/types.ts` — add `ReviseDraftRequest`.
- Modify: `frontend/src/api/client.ts` — add `reviseDraft` and `getDraftVersion`.
- Modify: `frontend/src/api/client.test.ts` — client path/body tests if existing client tests cover path helpers.
- Modify: `frontend/src/studio/StudioPage.test.tsx` — frontend RED/GREEN tests for revision UI and version switching.
- Modify: `frontend/src/studio/StudioPage.tsx` — revision UI, mutation handler, version switch handler, historical approval guard.
- Create: `docs/superpowers/specs/2026-05-30-mvp8-draft-revision-loop-design.md` — already written from approved brainstorming.

## Domain Decisions

- Full-draft revision creates a new `ChapterDraft` row; it never mutates a previous draft row.
- `change_type` for model-assisted whole-draft revision is `revision`.
- `change_summary` stores the user instruction text, trimmed.
- `parent_draft_version` is the previous active draft version.
- Revision may update proposed changes, but those changes remain proposed until approval.
- Revision must not mutate `world_version`, projection tables, or event logs.
- Draft version switching is read-only. Viewing an old version does not restore it or make it approvable.
- Approval stays tied to the latest backend `chapter.draft_version`.

---

### Task 0: Prepare feature branch after spec/plan files exist

**Files:**
- Verify only: git status and branch state.

- [ ] **Step 1: Check branch and working tree**

Run:

```bash
cd /opt/WorldSim-Writer && git status --short --branch
```

Expected: `## main...origin/main [领先 3]` plus the new uncommitted MVP8 spec/plan files.

- [ ] **Step 2: Create feature branch carrying spec/plan changes**

Run:

```bash
cd /opt/WorldSim-Writer && git checkout -b feat/mvp8-draft-revision-loop
```

Expected: branch switches to `feat/mvp8-draft-revision-loop`; uncommitted spec/plan changes remain in the working tree.

---

### Task 1: Backend full-draft revision endpoint

**Files:**
- Modify: `backend/tests/test_narrative_draft_versioning.py`
- Modify: `backend/app/narrative/schemas.py`
- Modify: `backend/app/narrative/router.py`
- Modify: `backend/app/narrative/service.py`
- Modify: `backend/app/llm/client.py`

- [ ] **Step 1: Write failing backend revision test**

Add imports in `backend/tests/test_narrative_draft_versioning.py`:

```python
from app.event.models import EventLog
```

Extend `DraftVersioningLLMClient` with revision capture behavior:

```python
    revision_messages = []

    def revise_chapter(self, messages):
        self.revision_messages = messages
        joined = '\n'.join(message['content'] for message in messages)
        return ChapterGeneration(
            title='第一章 雨巷密谈（修订版）',
            draft_content=f'修订版正文：{joined[:24]}',
            context_summary='根据审稿意见强化林砚的试探过程。',
            review_hints=['确认修订后 Critic 高风险是否解除'],
            proposed_character_changes=[
                ProposedCharacterChange(character_id=1, status='谨慎试探沈微霜', current_goals=['验证湿信来源'])
            ],
            proposed_foreshadow_changes=[
                ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='修订版继续推进玉佩线索')
            ],
        )
```

Add this test:

```python
def test_full_draft_revision_creates_new_version_from_review_context_without_mutating_world(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    fake_client = DraftVersioningLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: fake_client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)
    chapter = db_session.get(Chapter, draft['chapter_id'])
    chapter.critique_report = {
        'chapter_id': chapter.id,
        'draft_version': 1,
        'current_draft_version': 1,
        'is_stale': False,
        'overall_score': 71,
        'summary': '人物信任转折过快。',
        'dimensions': {},
        'issues': [{'severity': 'high', 'dimension': 'character_consistency', 'message': '林砚突然信任沈微霜。', 'paragraph_index': 0, 'suggested_action': '补足试探。'}],
        'suggestions': ['增加试探动作。'],
        'created_at': '2026-05-30T00:00:00Z',
    }
    chapter.character_arc_report = {
        'chapter_id': chapter.id,
        'draft_version': 1,
        'current_draft_version': 1,
        'is_stale': False,
        'summary': '角色弧线需要补足选择铺垫。',
        'character_arcs': [{'character_id': 1, 'name': '林砚', 'continuity_risk': 'high', 'risk_reason': '选择缺少铺垫。', 'suggested_revision': '加入试探沈微霜。'}],
        'relationship_notes': [],
        'progression_hints': [],
        'created_at': '2026-05-30T00:00:00Z',
    }
    db_session.commit()

    response = client.post(
        f"/chapters/{draft['chapter_id']}/draft/revise",
        json={'instruction': '保留雨巷会面，但补足林砚试探沈微霜的过程。'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['draft_version'] == 2
    assert payload['parent_draft_version'] == 1
    assert payload['change_type'] == 'revision'
    assert payload['change_summary'] == '保留雨巷会面，但补足林砚试探沈微霜的过程。'
    assert payload['title'] == '第一章 雨巷密谈（修订版）'
    assert payload['proposed_changes']['characters'][0]['status'] == '谨慎试探沈微霜'

    db_session.expire_all()
    world = db_session.get(World, world_id)
    chapter = db_session.get(Chapter, draft['chapter_id'])
    drafts = get_drafts_for_chapter(db_session, draft['chapter_id'])
    event_count = db_session.query(EventLog).filter_by(world_id=world_id).count()

    assert world.world_version == 1
    assert chapter.draft_version == 2
    assert chapter.status == 'reviewing'
    assert [item.draft_version for item in drafts] == [1, 2]
    assert drafts[0].content == draft['content']
    assert drafts[1].change_type == 'revision'
    assert event_count == 0

    joined_messages = '\n'.join(message['content'] for message in fake_client.revision_messages)
    assert '保留雨巷会面，但补足林砚试探沈微霜的过程。' in joined_messages
    assert '人物信任转折过快。' in joined_messages
    assert '角色弧线需要补足选择铺垫。' in joined_messages
    assert '存在建议复核项，请确认后再批准。' in joined_messages
    assert '本章执行上下文' in joined_messages
```

- [ ] **Step 2: Run backend test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_draft_versioning.py::test_full_draft_revision_creates_new_version_from_review_context_without_mutating_world -v
```

Expected: FAIL with 404 or missing route for `/draft/revise`.

- [ ] **Step 3: Add backend schema and router hook**

In `backend/app/narrative/schemas.py`, add near `ParagraphDraftRequest`:

```python
class ReviseDraftRequest(BaseModel):
    instruction: str = Field(min_length=3)
```

In `backend/app/narrative/router.py`, import `ReviseDraftRequest` and `revise_chapter_draft`, then add:

```python
@router.post('/chapters/{chapter_id}/draft/revise', response_model=DraftResponse)
def revise_draft(
    chapter_id: int,
    payload: ReviseDraftRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> DraftResponse:
    return DraftResponse.model_validate(revise_chapter_draft(db, current_user, chapter_id, payload.instruction))
```

- [ ] **Step 4: Add LLM client revision method**

In `backend/app/llm/client.py`, add method after `generate_chapter`:

```python
    def revise_chapter(self, messages: list[dict[str, str]]) -> ChapterGeneration:
        if self.mock:
            mock_data = dict(MOCK_CHAPTER)
            mock_data['title'] = f"{mock_data['title']}（修订版）"
            mock_data['draft_content'] = f"修订版：{mock_data['draft_content']}"
            mock_data['context_summary'] = '根据审稿意见和人工指令完成整稿修订。'
            mock_data['review_hints'] = ['重新生成 Critic 报告确认修订效果']
            return ChapterGeneration.model_validate(mock_data)
        return parse_chapter_generation(self._post_json(messages, temperature=0.6))
```

- [ ] **Step 5: Add service prompt builder and revision implementation**

In `backend/app/narrative/service.py`, add helpers before `revise_chapter_paragraph`:

```python
def _jsonish(value) -> str:
    return str(value or {})


def _approval_readiness_for_revision(db: Session, user: User, chapter_id: int) -> dict:
    try:
        return get_approval_readiness(db, user, chapter_id)
    except HTTPException:
        return {}


def build_revision_messages(
    world: World,
    characters: list[Character],
    foreshadows: list[Foreshadow],
    chapter: Chapter,
    draft: ChapterDraft,
    approval_readiness: dict,
    instruction: str,
) -> list[dict[str, str]]:
    character_lines = '\n'.join(f'- {c.id}: {c.name}, status={c.status}, goals={c.current_goals}' for c in characters)
    foreshadow_lines = '\n'.join(f'- {f.id}: {f.title}, status={f.status}, urgency={f.urgency_level}, description={f.description}' for f in foreshadows)
    return [
        {
            'role': 'system',
            'content': (
                '你是 WorldSim-Writer 的 Draft Revision Agent。必须只返回合法 JSON，字段结构与 Writer Agent 相同：'
                '{"title":"章节标题","draft_content":"完整修订后正文","context_summary":"摘要",'
                '"review_hints":["提示"],'
                '"proposed_character_changes":[{"character_id":整数,"status":"新状态","current_goals":["目标"]}],'
                '"proposed_foreshadow_changes":[{"foreshadow_id":整数,"status":"advanced|resolved|expired","description_note":"备注"}]}。'
                '你必须输出完整新版正文，不要输出 diff、patch 或说明文字。'
                '拟提交变化只是草稿建议，不能自动提交世界状态。不要编造不存在的角色 ID 或伏笔 ID。'
            ),
        },
        {
            'role': 'user',
            'content': (
                f'世界设定：{world.truth_canon}\n'
                f'世界版本：{world.world_version}\n'
                f'角色：\n{character_lines}\n'
                f'伏笔：\n{foreshadow_lines}\n'
                f'章节标题：{chapter.title}\n'
                f'章节目标：{chapter.chapter_goal or chapter.title}\n'
                f'{format_execution_context_for_prompt(draft.execution_context or chapter.execution_context)}'
                f'Outliner上下文：{_jsonish(chapter.outline_context)}\n'
                f'Outliner节拍：{_jsonish(chapter.outline_beats)}\n'
                f'当前草稿版本：v{draft.draft_version}\n'
                f'当前草稿拟提交变化：{_jsonish(draft.proposed_changes)}\n'
                f'当前正文：\n{draft.content}\n'
                f'Critic报告：{_jsonish(chapter.critique_report)}\n'
                f'角色弧线报告：{_jsonish(chapter.character_arc_report)}\n'
                f'审批准备度：{_jsonish(approval_readiness)}\n'
                f'人工修订指令：{instruction.strip()}\n'
                '请根据人工修订指令、Critic问题、角色弧线风险和审批准备度，生成完整修订版章节正文。'
            ),
        },
    ]
```

Add service function:

```python
def revise_chapter_draft(
    db: Session,
    user: User,
    chapter_id: int,
    instruction: str,
    llm_client: LLMClient | None = None,
) -> dict:
    chapter = _require_owned_chapter(db, user, chapter_id)
    if chapter.status == 'approved':
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='ALREADY_APPROVED')
    draft = _latest_draft(db, chapter)
    if draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    world = db.get(World, chapter.world_id)
    assert world is not None
    characters, foreshadows = _load_world_context(db, world)
    readiness = _approval_readiness_for_revision(db, user, chapter.id)
    client = _model_client(llm_client)
    try:
        generation = client.revise_chapter(
            build_revision_messages(world, characters, foreshadows, chapter, draft, readiness, instruction)
        )
    except (TimeoutError, ValueError, RuntimeError) as exc:
        raise _map_model_error(exc) from exc
    validate_generation_ids(generation, characters, foreshadows)

    proposed_changes = {
        'characters': [change.model_dump(exclude_none=True) for change in generation.proposed_character_changes],
        'foreshadows': [change.model_dump(exclude_none=True) for change in generation.proposed_foreshadow_changes],
    }
    new_draft = _create_draft_version(db, chapter, draft, generation.draft_content, 'revision', instruction.strip())
    chapter.title = generation.title
    chapter.status = 'reviewing'
    new_draft.context_summary = generation.context_summary
    new_draft.review_hints = generation.review_hints
    new_draft.proposed_changes = proposed_changes
    db.commit()
    db.refresh(chapter)
    db.refresh(new_draft)
    return _draft_payload(chapter, new_draft)
```

- [ ] **Step 6: Run backend revision test to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_draft_versioning.py::test_full_draft_revision_creates_new_version_from_review_context_without_mutating_world -v
```

Expected: PASS.

---

### Task 2: Backend draft version lookup and edge cases

**Files:**
- Modify: `backend/tests/test_narrative_draft_versioning.py`
- Modify: `backend/app/narrative/router.py`
- Modify: `backend/app/narrative/service.py`

- [ ] **Step 1: Add failing tests for lookup and revision edge cases**

Add these tests:

```python
def test_get_exact_draft_version_returns_requested_version(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)
    edited_content = '第一段：林砚停在雨巷口，掌心的玉佩微微发烫。\n\n第二段：沈微霜递来一封湿透的信。\n\n第三段：远处城主府钟声响起。'
    client.put(
        f"/chapters/{draft['chapter_id']}/draft",
        json={'content': edited_content, 'change_summary': '强化第一段玉佩反应'},
        headers={'Authorization': f'Bearer {token}'},
    )

    first = client.get(f"/chapters/{draft['chapter_id']}/drafts/1", headers={'Authorization': f'Bearer {token}'})
    second = client.get(f"/chapters/{draft['chapter_id']}/drafts/2", headers={'Authorization': f'Bearer {token}'})
    missing = client.get(f"/chapters/{draft['chapter_id']}/drafts/99", headers={'Authorization': f'Bearer {token}'})

    assert first.status_code == 200
    assert first.json()['draft_version'] == 1
    assert first.json()['content'] == draft['content']
    assert second.status_code == 200
    assert second.json()['draft_version'] == 2
    assert second.json()['content'] == edited_content
    assert missing.status_code == 404


def test_revision_rejects_approved_chapter(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)
    approve = client.post(f"/chapters/{draft['chapter_id']}/approve", headers={'Authorization': f'Bearer {token}'})
    assert approve.status_code == 200

    response = client.post(
        f"/chapters/{draft['chapter_id']}/draft/revise",
        json={'instruction': '批准后不允许再修订。'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 409
    assert response.json()['detail'] == 'ALREADY_APPROVED'


def test_revision_rejects_model_changes_for_unknown_ids(client, monkeypatch):
    class InvalidRevisionLLM(DraftVersioningLLMClient):
        def revise_chapter(self, messages):
            return ChapterGeneration(
                title='错误修订版',
                draft_content='错误修订正文。',
                context_summary='包含不存在角色。',
                review_hints=[],
                proposed_character_changes=[ProposedCharacterChange(character_id=999, status='不存在')],
                proposed_foreshadow_changes=[],
            )

    token, world_id = register_and_create_world(client)
    invalid_client = InvalidRevisionLLM()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: invalid_client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)

    response = client.post(
        f"/chapters/{draft['chapter_id']}/draft/revise",
        json={'instruction': '触发非法角色 ID。'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 502
    assert response.json()['detail'] == 'MODEL_RESPONSE_INVALID'
```

- [ ] **Step 2: Run tests to verify RED for lookup endpoint**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_draft_versioning.py::test_get_exact_draft_version_returns_requested_version -v
```

Expected: FAIL with 404 or missing route.

- [ ] **Step 3: Implement exact draft lookup service and route**

In `backend/app/narrative/service.py`, add:

```python
def get_chapter_draft_version(db: Session, user: User, chapter_id: int, draft_version: int) -> dict:
    chapter = _require_owned_chapter(db, user, chapter_id)
    draft = db.scalar(
        select(ChapterDraft)
        .where(ChapterDraft.chapter_id == chapter.id)
        .where(ChapterDraft.draft_version == draft_version)
    )
    if draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    return _draft_payload(chapter, draft)
```

In `backend/app/narrative/router.py`, import `get_chapter_draft_version` and add before the diff endpoint:

```python
@router.get('/chapters/{chapter_id}/drafts/{draft_version}', response_model=DraftResponse)
def read_draft_version(
    chapter_id: int,
    draft_version: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> DraftResponse:
    return DraftResponse.model_validate(get_chapter_draft_version(db, current_user, chapter_id, draft_version))
```

- [ ] **Step 4: Run backend draft versioning tests**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_draft_versioning.py -v
```

Expected: PASS.

---

### Task 3: Frontend API client support

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/api/client.test.ts`

- [ ] **Step 1: Inspect existing client test style**

Read `frontend/src/api/client.test.ts` and follow its mocking style for new helper tests.

- [ ] **Step 2: Add failing client tests**

If `client.test.ts` mocks `fetch`, add tests equivalent to:

```typescript
it('posts a full-draft revision instruction', async () => {
  mockJsonResponse({ chapter_id: 11, draft_id: 102, draft_version: 2 });

  await reviseDraft(11, { instruction: '补足试探过程' });

  expect(fetch).toHaveBeenCalledWith(
    'http://localhost:8000/chapters/11/draft/revise',
    expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({ instruction: '补足试探过程' }),
    }),
  );
});

it('gets an exact draft version', async () => {
  mockJsonResponse({ chapter_id: 11, draft_id: 101, draft_version: 1 });

  await getDraftVersion(11, 1);

  expect(fetch).toHaveBeenCalledWith(
    'http://localhost:8000/chapters/11/drafts/1',
    expect.objectContaining({ method: undefined }),
  );
});
```

Adjust only the assertion shape to match existing helper utilities in the file.

- [ ] **Step 3: Run client tests to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts
```

Expected: FAIL because `reviseDraft` and `getDraftVersion` are missing.

- [ ] **Step 4: Add API types and functions**

In `frontend/src/api/types.ts`, add near `ParagraphReviseRequest`:

```typescript
export type ReviseDraftRequest = {
  instruction: string;
};
```

In `frontend/src/api/client.ts`, import `ReviseDraftRequest` and add after `reviseParagraph`:

```typescript
export function reviseDraft(chapterId: number, data: ReviseDraftRequest) {
  return apiRequest<DraftResponse>(`/chapters/${chapterId}/draft/revise`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function getDraftVersion(chapterId: number, draftVersion: number) {
  return apiRequest<DraftResponse>(`/chapters/${chapterId}/drafts/${draftVersion}`);
}
```

- [ ] **Step 5: Run client tests to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts
```

Expected: PASS.

---

### Task 4: Studio revision UI and version switching

**Files:**
- Modify: `frontend/src/studio/StudioPage.test.tsx`
- Modify: `frontend/src/studio/StudioPage.tsx`

- [ ] **Step 1: Add failing Studio tests**

In the mock import list in `StudioPage.test.tsx`, add `reviseDraft` and `getDraftVersion`.

In the `vi.mock('../api/client', ...)` object, add:

```typescript
  reviseDraft: vi.fn(async () => ({
    ...draftResponse,
    draft_id: 102,
    draft_version: 2,
    title: '第一章 雨巷密谈（修订版）',
    content: '修订版第一段：林砚没有立刻信任沈微霜，而是先以湿信试探她。\n\n第二段：沈微霜递来一封湿透的信。',
    context_summary: '修订版补足林砚试探过程。',
    review_hints: ['重新生成 Critic 报告确认高风险是否解除'],
    change_type: 'revision',
    change_summary: '补足林砚试探沈微霜的过程',
    parent_draft_version: 1,
  })),
  getDraftVersion: vi.fn(async (_chapterId: number, draftVersion: number) => (
    draftVersion === 1
      ? draftResponse
      : {
          ...draftResponse,
          draft_id: 102,
          draft_version: 2,
          title: '第一章 雨巷密谈（修订版）',
          content: '修订版第一段：林砚没有立刻信任沈微霜，而是先以湿信试探她。\n\n第二段：沈微霜递来一封湿透的信。',
          change_type: 'revision',
          change_summary: '补足林砚试探沈微霜的过程',
          parent_draft_version: 1,
        }
  )),
```

Add imported names to the top import:

```typescript
import { createChapter, generateCharacterArcReport, getApprovalReadiness, getDraftVersion, reviseDraft, writeChapter } from '../api/client';
```

Add test:

```typescript
it('generates a full-draft revision from review context and shows parent diff', async () => {
  const user = userEvent.setup();
  render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

  await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
  await user.click(screen.getByRole('button', { name: '创建章节' }));
  await user.click(await screen.findByRole('button', { name: '生成大纲' }));
  await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));

  expect(await screen.findByText('Draft Revision Loop')).toBeInTheDocument();
  await user.type(screen.getByLabelText('修订指令'), '补足林砚试探沈微霜的过程');
  await user.click(screen.getByRole('button', { name: '生成修订版' }));

  expect(reviseDraft).toHaveBeenCalledWith(11, { instruction: '补足林砚试探沈微霜的过程' });
  expect(await screen.findByText('第一章 雨巷密谈（修订版）')).toBeInTheDocument();
  expect(screen.getByText('当前草稿：v2')).toBeInTheDocument();
  expect(screen.getByText('父版本：v1')).toBeInTheDocument();
  expect(screen.getByText('最近修改：补足林砚试探沈微霜的过程')).toBeInTheDocument();
  expect(screen.getByText('v1 → v2')).toBeInTheDocument();
  expect(getApprovalReadiness).toHaveBeenCalledTimes(2);
});

it('switches to parent draft as a read-only historical version and disables approval', async () => {
  const user = userEvent.setup();
  render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

  await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
  await user.click(screen.getByRole('button', { name: '创建章节' }));
  await user.click(await screen.findByRole('button', { name: '生成大纲' }));
  await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));
  await user.type(screen.getByLabelText('修订指令'), '补足林砚试探沈微霜的过程');
  await user.click(screen.getByRole('button', { name: '生成修订版' }));

  await user.selectOptions(await screen.findByLabelText('草稿版本'), '1');

  expect(getDraftVersion).toHaveBeenCalledWith(11, 1);
  expect(await screen.findByText('第一段：林砚停在雨巷口。')).toBeInTheDocument();
  expect(screen.getByText('正在查看历史版本，切回最新版本后才能批准。')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '通过并更新世界' })).toBeDisabled();
});
```

- [ ] **Step 2: Run Studio test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx
```

Expected: FAIL because revision client imports/UI/handlers are missing.

- [ ] **Step 3: Implement Studio state and handlers**

In `StudioPage.tsx`, import `getDraftVersion` and `reviseDraft` from client.

Add state:

```typescript
const [latestDraftVersion, setLatestDraftVersion] = useState<number | null>(null);
const [revisionInstruction, setRevisionInstruction] = useState('');
```

Update `refreshReviewStudioPanels` to include parent version and latest version:

```typescript
const knownVersions = [version];
if (nextDraft.parent_draft_version) knownVersions.push(nextDraft.parent_draft_version);
setDraftVersions((versions) => Array.from(new Set([...versions, ...knownVersions])).sort((a, b) => a - b));
setLatestDraftVersion((current) => Math.max(current ?? version, version));
```

Add helper:

```typescript
function isViewingLatestDraft(): boolean {
  if (!draft) return false;
  return latestDraftVersion === null || resolveDraftVersion(draft) === latestDraftVersion;
}
```

Add revision handler:

```typescript
async function runFullDraftRevision() {
  if (!draft) return;
  const instruction = revisionInstruction.trim();
  if (instruction.length < 3) {
    setError('修订指令至少需要3个字符');
    return;
  }
  setWorking(true);
  setError('');
  try {
    const updated = normalizeDraft(await reviseDraft(draft.chapter_id, { instruction }));
    setDraft(updated);
    await refreshReviewStudioPanels(updated);
    setRevisionInstruction('');
    setCritique(null);
    setCharacterArcReport(null);
  } catch (err) {
    setError(err instanceof Error ? err.message : '生成修订版失败');
  } finally {
    setWorking(false);
  }
}
```

Add version switch handler:

```typescript
async function switchDraftVersion(value: string) {
  if (!draft) return;
  const selected = Number(value);
  if (!Number.isFinite(selected) || selected === resolveDraftVersion(draft)) return;
  setWorking(true);
  setError('');
  try {
    const selectedDraft = normalizeDraft(await getDraftVersion(draft.chapter_id, selected));
    setDraft(selectedDraft);
    if (selectedDraft.parent_draft_version) {
      try {
        setDraftDiff(await getDraftDiff(selectedDraft.chapter_id, selectedDraft.parent_draft_version, selectedDraft.draft_version));
      } catch {
        setDraftDiff(null);
      }
    } else if (latestDraftVersion && selectedDraft.draft_version !== latestDraftVersion) {
      try {
        setDraftDiff(await getDraftDiff(selectedDraft.chapter_id, selectedDraft.draft_version, latestDraftVersion));
      } catch {
        setDraftDiff(null);
      }
    } else {
      setDraftDiff(null);
    }
  } catch (err) {
    setError(err instanceof Error ? err.message : '切换草稿版本失败');
  } finally {
    setWorking(false);
  }
}
```

Update `runWriter` to set latest version:

```typescript
setLatestDraftVersion(nextDraft.draft_version);
```

- [ ] **Step 4: Implement Studio revision UI and approval guard**

Change draft version selector:

```tsx
<select className="paper-input mt-1" aria-label="草稿版本" value={resolveDraftVersion(draft)} onChange={(event) => void switchDraftVersion(event.target.value)}>
```

Add revision section after the version row:

```tsx
<section className="space-y-3 rounded-2xl border border-amber-900/15 bg-amber-50/45 p-4">
  <div>
    <p className="chapter-kicker">Draft Revision Loop</p>
    <h3 className="font-black text-[#3b2511]">整稿修订</h3>
    <p className="manuscript mt-2 text-sm">当前草稿：v{resolveDraftVersion(draft)}</p>
    {draft.parent_draft_version && <p className="manuscript mt-1 text-sm">父版本：v{draft.parent_draft_version}</p>}
    <p className="manuscript mt-1 text-sm">修订类型：{draft.change_type}</p>
  </div>
  <label className="block">
    <span className="text-sm font-semibold text-[#4a321e]">修订指令</span>
    <textarea
      className="paper-input mt-1 min-h-24"
      aria-label="修订指令"
      value={revisionInstruction}
      onChange={(event) => setRevisionInstruction(event.target.value)}
      placeholder="例如：保留雨巷会面，但补足林砚试探沈微霜的过程。"
      disabled={working || !isViewingLatestDraft()}
    />
  </label>
  <button className="secondary-button" disabled={working || !isViewingLatestDraft()} onClick={runFullDraftRevision}>生成修订版</button>
  {!isViewingLatestDraft() && <p className="paper-error">正在查看历史版本，切回最新版本后才能批准。</p>}
</section>
```

Change approve button:

```tsx
<button className="primary-button" disabled={working || !isViewingLatestDraft()} onClick={approveDraft}>通过并更新世界</button>
```

- [ ] **Step 5: Run Studio tests to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx
```

Expected: PASS.

---

### Task 5: Targeted verification and inline self-review

**Files:**
- Verify backend/frontend test/build output.
- Review changed files inline; do not use code-review subagent.

- [ ] **Step 1: Run backend targeted tests**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_draft_versioning.py tests/test_narrative_approval.py -v
```

Expected: all tests pass.

- [ ] **Step 2: Run frontend targeted tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx src/api/client.test.ts
```

Expected: all tests pass.

- [ ] **Step 3: Run frontend build**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: TypeScript and Vite build pass.

- [ ] **Step 4: Inline self-review checklist**

Review the diff manually and verify:

- Revision endpoint rejects approved chapters.
- Revision endpoint creates `revision` draft versions with parent version.
- Revision endpoint does not mutate world projection, `world_version`, or events.
- Model-proposed IDs are validated.
- Version switching is read-only.
- Approval is disabled while viewing historical versions.
- No dynamic workflows or subagents were used.
- No push was performed.

Run:

```bash
cd /opt/WorldSim-Writer && git diff -- backend/app/llm/client.py backend/app/narrative/schemas.py backend/app/narrative/router.py backend/app/narrative/service.py backend/tests/test_narrative_draft_versioning.py frontend/src/api/types.ts frontend/src/api/client.ts frontend/src/api/client.test.ts frontend/src/studio/StudioPage.tsx frontend/src/studio/StudioPage.test.tsx docs/superpowers/specs/2026-05-30-mvp8-draft-revision-loop-design.md docs/superpowers/plans/2026-05-30-mvp8-draft-revision-loop.md
```

Expected: only MVP8-related changes are present.

---

### Task 6: Commit, merge, and post-merge verification

**Files:**
- Commit and merge only; do not push.

- [ ] **Step 1: Check status**

Run:

```bash
cd /opt/WorldSim-Writer && git status --short --branch
```

Expected: on `feat/mvp8-draft-revision-loop` with MVP8 changes only.

- [ ] **Step 2: Commit feature branch**

Run:

```bash
cd /opt/WorldSim-Writer && git add docs/superpowers/specs/2026-05-30-mvp8-draft-revision-loop-design.md docs/superpowers/plans/2026-05-30-mvp8-draft-revision-loop.md backend/app/llm/client.py backend/app/narrative/schemas.py backend/app/narrative/router.py backend/app/narrative/service.py backend/tests/test_narrative_draft_versioning.py frontend/src/api/types.ts frontend/src/api/client.ts frontend/src/api/client.test.ts frontend/src/studio/StudioPage.tsx frontend/src/studio/StudioPage.test.tsx && git commit -m "feat: add draft revision loop" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

Expected: commit succeeds.

- [ ] **Step 3: Merge back to main without pushing**

Run:

```bash
cd /opt/WorldSim-Writer && git checkout main && git merge feat/mvp8-draft-revision-loop
```

Expected: merge succeeds. Do not run `git push`.

- [ ] **Step 4: Post-merge backend verification**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_draft_versioning.py tests/test_narrative_approval.py -v
```

Expected: all tests pass after merge.

- [ ] **Step 5: Post-merge frontend verification**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx src/api/client.test.ts && npm run build
```

Expected: targeted frontend tests and build pass after merge.

- [ ] **Step 6: Final status check**

Run:

```bash
cd /opt/WorldSim-Writer && git status --short --branch
```

Expected: on `main`, clean working tree, ahead of `origin/main` by 4 commits, no push performed.

## Self-Review

- Spec coverage: plan covers full-draft revision, review-context prompt inputs, draft-only semantics, parent version display, version switching, historical approval guard, tests, build, commit, merge, and no push.
- Placeholder scan: no TBD/TODO/fill-in placeholders remain; every task has exact files, commands, and expected outcomes.
- Type consistency: backend uses `ReviseDraftRequest`, `revise_chapter_draft`, and `get_chapter_draft_version`; frontend uses `ReviseDraftRequest`, `reviseDraft`, and `getDraftVersion` consistently.
