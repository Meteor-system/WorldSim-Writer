# MVP29 Tag Merge 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This repository run is explicitly inline-only: do not use dynamic workflows, subagents, or the code-review subagent.

**Goal:** Add a safe metadata-only tag merge flow that moves assignments from one tag into another, deduplicates overlaps, deletes the source tag, and exposes the action in the Tools Workspace UI.

**Architecture:** Extend the existing tag domain without a migration. The backend adds a small request/response schema, service function, and router endpoint; the frontend adds one API helper and a compact merge form to `WorldTagsPanel`, wired through `WorldPage`.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic v2, pytest, React, TypeScript, Vitest, Testing Library, Vite.

---

## File structure

- Modify `backend/tests/test_tags.py` — backend RED/GREEN coverage for merge semantics and metadata-only invariant.
- Modify `backend/app/tags/schemas.py` — add `TagMergeRequest` and `TagMergeResponse`.
- Modify `backend/app/tags/service.py` — add `merge_tag()` using existing ownership, tag lookup, and assignment models.
- Modify `backend/app/tags/router.py` — add `POST /worlds/{world_id}/tags/{source_tag_id}/merge`.
- Modify `frontend/src/api/types.ts` — add merge request/response types.
- Modify `frontend/src/api/client.ts` — add `mergeWorldTag()` helper.
- Modify `frontend/src/api/client.test.ts` — verify merge helper URL/method/body.
- Modify `frontend/src/world/WorldTagsPanel.tsx` — add merge form for selected tag.
- Modify `frontend/src/world/WorldTagsPanel.test.tsx` — frontend RED/GREEN coverage for merge UI.
- Modify `frontend/src/world/WorldPage.tsx` — wire real helper into panel.
- Modify `frontend/src/world/WorldPage.test.tsx` — update API mocks for required prop.

---

### Task 1: Backend merge endpoint TDD

**Files:**
- Test: `backend/tests/test_tags.py`
- Modify: `backend/app/tags/schemas.py`
- Modify: `backend/app/tags/service.py`
- Modify: `backend/app/tags/router.py`

- [ ] **Step 1: Write failing backend tests**

Add these tests to `backend/tests/test_tags.py` after the MVP28 update-tag tests:

```python
def test_merge_tag_moves_assignments_deduplicates_and_deletes_source(client):
    token = register(client, 'tags-merge@example.com')
    world = create_world(client, token)
    overview = client.get(f"/worlds/{world['id']}/overview", headers=auth(token)).json()
    character_id = overview['characters'][0]['id']
    foreshadow_id = overview['foreshadows'][0]['id']
    source = client.post(f"/worlds/{world['id']}/tags", headers=auth(token), json={'name': '灯塔旧线'}).json()
    target = client.post(f"/worlds/{world['id']}/tags", headers=auth(token), json={'name': '灯塔线'}).json()
    client.post(f"/worlds/{world['id']}/tags/{source['id']}/objects", headers=auth(token), json={'object_type': 'character', 'object_id': character_id})
    client.post(f"/worlds/{world['id']}/tags/{source['id']}/objects", headers=auth(token), json={'object_type': 'foreshadow', 'object_id': foreshadow_id})
    client.post(f"/worlds/{world['id']}/tags/{target['id']}/objects", headers=auth(token), json={'object_type': 'character', 'object_id': character_id})

    response = client.post(
        f"/worlds/{world['id']}/tags/{source['id']}/merge",
        headers=auth(token),
        json={'target_tag_id': target['id']},
    )

    assert response.status_code == 200
    assert response.json() == {
        'world_id': world['id'],
        'source_tag_id': source['id'],
        'target_tag_id': target['id'],
        'moved_count': 1,
        'already_assigned_count': 1,
        'deleted_source_tag': True,
    }
    assert client.get(f"/worlds/{world['id']}/tags/{source['id']}", headers=auth(token)).status_code == 404
    detail = client.get(f"/worlds/{world['id']}/tags/{target['id']}", headers=auth(token)).json()
    assert detail['tag']['assignment_count'] == 2
    assert detail['tag']['object_type_counts'] == {'character': 1, 'foreshadow': 1}
    assert {(item['object_type'], item['object_id']) for item in detail['objects']} == {
        ('character', character_id),
        ('foreshadow', foreshadow_id),
    }


def test_merge_tag_rejects_self_merge_without_deleting_source(client):
    token = register(client, 'tags-merge-self@example.com')
    world = create_world(client, token)
    tag = client.post(f"/worlds/{world['id']}/tags", headers=auth(token), json={'name': '自合并'}).json()

    response = client.post(
        f"/worlds/{world['id']}/tags/{tag['id']}/merge",
        headers=auth(token),
        json={'target_tag_id': tag['id']},
    )

    assert response.status_code == 422
    assert response.json()['detail'] == 'TAG_MERGE_TARGET_REQUIRED'
    detail = client.get(f"/worlds/{world['id']}/tags/{tag['id']}", headers=auth(token)).json()
    assert detail['tag']['name'] == '自合并'


def test_merge_tag_does_not_increment_world_version(client):
    token = register(client, 'tags-merge-version@example.com')
    world = create_world(client, token)
    overview = client.get(f"/worlds/{world['id']}/overview", headers=auth(token)).json()
    source = client.post(f"/worlds/{world['id']}/tags", headers=auth(token), json={'name': '旧归档'}).json()
    target = client.post(f"/worlds/{world['id']}/tags", headers=auth(token), json={'name': '新归档'}).json()
    client.post(
        f"/worlds/{world['id']}/tags/{source['id']}/objects",
        headers=auth(token),
        json={'object_type': 'character', 'object_id': overview['characters'][0]['id']},
    )

    response = client.post(
        f"/worlds/{world['id']}/tags/{source['id']}/merge",
        headers=auth(token),
        json={'target_tag_id': target['id']},
    )
    after = client.get(f"/worlds/{world['id']}/overview", headers=auth(token)).json()
    events = client.get(f"/worlds/{world['id']}/events", headers=auth(token)).json()

    assert response.status_code == 200
    assert after['world_version'] == overview['world_version']
    assert events['summary']['event_type_counts'] == {'WORLD_CREATED': 1}
```

Also update `test_tag_endpoints_require_login()` to include:

```python
merge_response = client.post('/worlds/1/tags/1/merge', json={'target_tag_id': 2})
assert merge_response.status_code == 401
```

- [ ] **Step 2: Run backend RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_tags.py::test_merge_tag_moves_assignments_deduplicates_and_deletes_source tests/test_tags.py::test_merge_tag_rejects_self_merge_without_deleting_source tests/test_tags.py::test_merge_tag_does_not_increment_world_version -q
```

Expected: tests fail with `405 Method Not Allowed` or missing route because merge is not implemented.

- [ ] **Step 3: Add backend schemas**

In `backend/app/tags/schemas.py`, add after `TagUpdateRequest`:

```python
class TagMergeRequest(BaseModel):
    target_tag_id: int

    @field_validator('target_tag_id')
    @classmethod
    def validate_target_tag_id(cls, value: int) -> int:
        if value <= 0:
            raise ValueError('target_tag_id must be positive')
        return value


class TagMergeResponse(BaseModel):
    world_id: int
    source_tag_id: int
    target_tag_id: int
    moved_count: int
    already_assigned_count: int
    deleted_source_tag: bool
```

- [ ] **Step 4: Add service function**

In `backend/app/tags/service.py`, import `TagMergeRequest` and add:

```python
def merge_tag(db: Session, user: User, world_id: int, source_tag_id: int, data: TagMergeRequest) -> dict:
    world = require_owned_world(db, user, world_id)
    source_tag = _require_tag(db, world.id, source_tag_id)
    target_tag = _require_tag(db, world.id, data.target_tag_id)
    if source_tag.id == target_tag.id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail='TAG_MERGE_TARGET_REQUIRED')

    source_assignments = list(db.scalars(select(ObjectTag).where(ObjectTag.tag_id == source_tag.id).order_by(ObjectTag.id)))
    target_assignments = set(
        db.execute(
            select(ObjectTag.object_type, ObjectTag.object_id).where(ObjectTag.tag_id == target_tag.id)
        ).all()
    )
    moved_count = 0
    already_assigned_count = 0
    for assignment in source_assignments:
        key = (assignment.object_type, assignment.object_id)
        if key in target_assignments:
            db.delete(assignment)
            already_assigned_count += 1
        else:
            assignment.tag_id = target_tag.id
            target_assignments.add(key)
            moved_count += 1

    db.delete(source_tag)
    db.commit()
    return {
        'world_id': world.id,
        'source_tag_id': source_tag_id,
        'target_tag_id': target_tag.id,
        'moved_count': moved_count,
        'already_assigned_count': already_assigned_count,
        'deleted_source_tag': True,
    }
```

- [ ] **Step 5: Add router endpoint**

In `backend/app/tags/router.py`, import `TagMergeRequest`, `TagMergeResponse`, and `merge_tag`, then add before the detail route:

```python
@router.post('/worlds/{world_id}/tags/{source_tag_id}/merge', response_model=TagMergeResponse)
def merge_world_tag(
    world_id: int,
    source_tag_id: int,
    data: TagMergeRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> TagMergeResponse:
    return TagMergeResponse.model_validate(merge_tag(db, current_user, world_id, source_tag_id, data))
```

- [ ] **Step 6: Run backend GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_tags.py -q
```

Expected: all tag tests pass.

---

### Task 2: Frontend API and panel TDD

**Files:**
- Modify `frontend/src/api/types.ts`
- Modify `frontend/src/api/client.ts`
- Modify `frontend/src/api/client.test.ts`
- Test: `frontend/src/world/WorldTagsPanel.test.tsx`
- Modify `frontend/src/world/WorldTagsPanel.tsx`
- Modify `frontend/src/world/WorldPage.tsx`
- Modify `frontend/src/world/WorldPage.test.tsx`

- [ ] **Step 1: Write frontend panel failing tests**

In `frontend/src/world/WorldTagsPanel.test.tsx`, update imports to include `TagMergeResponse`. Add a second tag in test fixtures:

```ts
const targetTag: TagResponse = {
  id: 4,
  world_id: 7,
  name: '主线归档',
  slug: '主线归档',
  color: 'blue',
  created_at: '2026-05-31T00:00:00Z',
};

const listResponse: TagListResponse = {
  world_id: 7,
  tags: [
    { ...tag, assignment_count: 1, object_type_counts: { character: 1 } },
    { ...targetTag, assignment_count: 0, object_type_counts: {} },
  ],
};

const mergeResponse: TagMergeResponse = {
  world_id: 7,
  source_tag_id: 3,
  target_tag_id: 4,
  moved_count: 1,
  already_assigned_count: 1,
  deleted_source_tag: true,
};
```

Update `renderPanel()` to pass:

```tsx
onMergeTag={vi.fn().mockResolvedValue(mergeResponse)}
```

Add tests:

```tsx
it('merges the selected tag into another tag and loads the target detail', async () => {
  const user = userEvent.setup();
  const targetDetail: TagDetailResponse = {
    ...detailResponse,
    tag: { ...targetTag, assignment_count: 2, object_type_counts: { character: 1, foreshadow: 1 } },
  };
  const onMergeTag = vi.fn().mockResolvedValue(mergeResponse);
  const onLoadTag = vi.fn()
    .mockResolvedValueOnce(detailResponse)
    .mockResolvedValueOnce(targetDetail);
  renderPanel({ onMergeTag, onLoadTag });

  await screen.findByText('灯塔线');
  await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
  expect(await screen.findByText('合并标签')).toBeInTheDocument();

  await user.selectOptions(screen.getByLabelText('合并到标签'), '4');
  await user.click(screen.getByRole('button', { name: '合并当前标签' }));

  expect(onMergeTag).toHaveBeenCalledWith(7, 3, { target_tag_id: 4 });
  expect(await screen.findByText('标签已合并：移动 1，跳过重复 1。')).toBeInTheDocument();
  await waitFor(() => expect(onLoadTag).toHaveBeenLastCalledWith(7, 4));
});

it('explains that another tag is required before merging', async () => {
  renderPanel({ onListTags: vi.fn().mockResolvedValue({ world_id: 7, tags: [{ ...tag, assignment_count: 1, object_type_counts: { character: 1 } }] }) });

  await screen.findByText('灯塔线');
  await userEvent.click(screen.getByRole('button', { name: '查看 灯塔线' }));

  expect(await screen.findByText('需要至少另一个标签才能合并当前标签。')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run frontend RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx
```

Expected: tests fail because `onMergeTag` prop/types and merge UI do not exist.

- [ ] **Step 3: Add frontend types and API helper**

In `frontend/src/api/types.ts`, add after `TagUpdateRequest`:

```ts
export type TagMergeRequest = {
  target_tag_id: number;
};

export type TagMergeResponse = {
  world_id: number;
  source_tag_id: number;
  target_tag_id: number;
  moved_count: number;
  already_assigned_count: number;
  deleted_source_tag: boolean;
};
```

In `frontend/src/api/client.ts`, import `TagMergeRequest` and `TagMergeResponse`, then add after `updateWorldTag()`:

```ts
export function mergeWorldTag(worldId: number, sourceTagId: number, data: TagMergeRequest) {
  return apiRequest<TagMergeResponse>(`/worlds/${worldId}/tags/${sourceTagId}/merge`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
```

In `frontend/src/api/client.test.ts`, import `mergeWorldTag`, add a mocked merge response after `updateWorldTag`, call:

```ts
await mergeWorldTag(7, 3, { target_tag_id: 4 });
```

and expect:

```ts
expect(fetchMock).toHaveBeenNthCalledWith(4, 'http://localhost:8000/worlds/7/tags/3/merge', expect.objectContaining({ method: 'POST', body: JSON.stringify({ target_tag_id: 4 }) }));
```

Shift later call numbers by one.

- [ ] **Step 4: Add panel merge UI**

In `frontend/src/world/WorldTagsPanel.tsx`:

- Import `TagMergeRequest` and `TagMergeResponse`.
- Add prop:

```ts
onMergeTag: (worldId: number, sourceTagId: number, data: TagMergeRequest) => Promise<TagMergeResponse>;
```

- Add state:

```ts
const [mergeTargetTagId, setMergeTargetTagId] = useState('');
const [mergeNotice, setMergeNotice] = useState('');
```

- Add helper:

```ts
function availableMergeTargets(sourceTagId: number | null = selectedTagId) {
  return tags.filter((tag) => tag.id !== sourceTagId);
}
```

- In `loadTag()`, after setting edit fields:

```ts
const firstTarget = tags.find((tag) => tag.id !== loaded.tag.id);
setMergeTargetTagId(firstTarget ? String(firstTarget.id) : '');
setMergeNotice('');
```

- Add submit handler:

```ts
async function submitTagMerge(event: FormEvent<HTMLFormElement>) {
  event.preventDefault();
  if (selectedTagId === null) return;
  const targetTagId = Number(mergeTargetTagId);
  if (!Number.isInteger(targetTagId) || targetTagId <= 0 || targetTagId === selectedTagId) {
    setError('请选择要合并到的目标标签');
    return;
  }
  setSaving(true);
  setError('');
  setMergeNotice('');
  try {
    const result = await onMergeTag(worldId, selectedTagId, { target_tag_id: targetTagId });
    await loadTags();
    await loadTag(targetTagId);
    setMergeNotice(`标签已合并：移动 ${result.moved_count}，跳过重复 ${result.already_assigned_count}。`);
  } catch (err) {
    setError(err instanceof Error ? err.message : '合并标签失败');
  } finally {
    setSaving(false);
  }
}
```

- Render after edit form:

```tsx
{availableMergeTargets().length === 0 ? (
  <p className="ink-muted text-sm">需要至少另一个标签才能合并当前标签。</p>
) : (
  <form className="grid gap-3 rounded-2xl bg-white/45 p-4 md:grid-cols-[1fr_auto]" onSubmit={submitTagMerge}>
    <p className="text-sm font-black text-[#3b2511] md:col-span-2">合并标签</p>
    <label className="text-sm font-bold text-[#3b2511]">
      合并到标签
      <select className="paper-input mt-1" value={mergeTargetTagId} onChange={(event) => setMergeTargetTagId(event.target.value)}>
        {availableMergeTargets().map((tag) => <option key={tag.id} value={tag.id}>{tag.name}</option>)}
      </select>
    </label>
    <button className="secondary-button self-end" disabled={saving} type="submit">合并当前标签</button>
    {mergeNotice && <p className="ink-muted text-sm md:col-span-2">{mergeNotice}</p>}
  </form>
)}
```

- [ ] **Step 5: Wire through WorldPage**

In `frontend/src/world/WorldPage.tsx`, import `mergeWorldTag` and pass `onMergeTag={mergeWorldTag}` to `WorldTagsPanel`.

In `frontend/src/world/WorldPage.test.tsx`, add `mergeWorldTag` to the client mock, reset it in `beforeEach`, and provide a default resolved value matching `TagMergeResponse`.

- [ ] **Step 6: Run frontend GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx src/api/client.test.ts src/world/WorldPage.test.tsx
```

Expected: targeted frontend tests pass.

---

### Task 3: Final verification, commit, and merge

**Files:**
- All modified files above.

- [ ] **Step 1: Run targeted backend verification**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_tags.py tests/test_world_search.py -q
```

Expected: all selected backend tests pass.

- [ ] **Step 2: Run targeted frontend verification**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx src/world/WorldSearchPanel.test.tsx src/world/WorldPage.test.tsx src/api/client.test.ts
```

Expected: all selected frontend tests pass.

- [ ] **Step 3: Run frontend build**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 4: Review git status and commit**

Run:

```bash
git -C /opt/WorldSim-Writer/frontend status --short
```

Commit:

```bash
git -C /opt/WorldSim-Writer/frontend add backend/app/tags/schemas.py backend/app/tags/service.py backend/app/tags/router.py backend/tests/test_tags.py frontend/src/api/types.ts frontend/src/api/client.ts frontend/src/api/client.test.ts frontend/src/world/WorldTagsPanel.tsx frontend/src/world/WorldTagsPanel.test.tsx frontend/src/world/WorldPage.tsx frontend/src/world/WorldPage.test.tsx docs/superpowers/specs/2026-05-31-mvp29-tag-merge-design.md docs/superpowers/plans/2026-05-31-mvp29-tag-merge.md

git -C /opt/WorldSim-Writer/frontend commit -m "feat: add tag merge"
```

- [ ] **Step 5: Fast-forward merge to main without push**

Run:

```bash
git -C /opt/WorldSim-Writer/frontend checkout main
git -C /opt/WorldSim-Writer/frontend merge --ff-only feat/mvp29-tag-merge
```

Do not push.

- [ ] **Step 6: Post-merge verification**

Repeat backend targeted tests, frontend targeted tests, and frontend build from Steps 1-3 on `main`.

Expected: all pass after merge.

## Self-review

- This plan covers all spec acceptance criteria.
- No placeholders remain.
- Types and function names are consistent: `TagMergeRequest`, `TagMergeResponse`, `mergeWorldTag`, `merge_tag`, `onMergeTag`.
- No schema migration is needed.
- Merge remains metadata-only and does not touch canon or event history.

## Execution status

Implemented on `feat/mvp29-tag-merge` using TDD. RED was observed for missing backend merge behavior and missing frontend merge UI; GREEN was observed for targeted backend tag tests and targeted frontend panel/API/Page tests. Pre-merge targeted backend pytest, frontend Vitest, and frontend build passed.
