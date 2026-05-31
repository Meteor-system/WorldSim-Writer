# MVP28 Tag Editing 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use sequential inline execution for this repository request because the user explicitly chose inline execution, no subagents, no dynamic workflows, and skip code-review subagent. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users edit an existing tag’s name and color while preserving assignments and metadata-only invariants.

**Architecture:** Add a partial tag update request schema, service function, and `PATCH /worlds/{world_id}/tags/{tag_id}` route in the existing tag module. Wire a small edit form into `WorldTagsPanel`, backed by a new `updateWorldTag()` API client helper and `WorldPage` prop. Use strict TDD: backend failing tests first, then backend implementation; frontend failing tests first, then frontend implementation.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, React, TypeScript, Vite, Vitest, Testing Library.

---

## File map

- Create: `docs/superpowers/specs/2026-05-31-mvp28-tag-editing-design.md` — design spec.
- Create: `docs/superpowers/plans/2026-05-31-mvp28-tag-editing.md` — this implementation plan.
- Modify: `backend/tests/test_tags.py` — RED/GREEN backend coverage for tag editing.
- Modify: `backend/app/tags/schemas.py` — add `TagUpdateRequest`.
- Modify: `backend/app/tags/service.py` — add `update_tag()`.
- Modify: `backend/app/tags/router.py` — add PATCH route.
- Modify: `frontend/src/api/types.ts` — add `TagUpdateRequest` type.
- Modify: `frontend/src/api/client.ts` — add `updateWorldTag()` helper.
- Modify: `frontend/src/world/WorldTagsPanel.test.tsx` — RED/GREEN UI coverage for editing.
- Modify: `frontend/src/world/WorldTagsPanel.tsx` — add edit form and update flow.
- Modify: `frontend/src/world/WorldPage.tsx` — pass `updateWorldTag` into `WorldTagsPanel`.

---

### Task 1: Backend RED tests

**Files:**
- Modify: `backend/tests/test_tags.py`

- [ ] **Step 1: Add failing backend tests**

Add these tests after `test_create_and_list_world_tags` in `backend/tests/test_tags.py`:

```python
def test_update_tag_name_and_color_preserves_assignments(client):
    token = register(client, 'tags-update@example.com')
    world = create_world(client, token)
    overview = client.get(f"/worlds/{world['id']}/overview", headers=auth(token)).json()
    tag = client.post(f"/worlds/{world['id']}/tags", headers=auth(token), json={'name': '旧标签', 'color': 'gray'}).json()
    client.post(
        f"/worlds/{world['id']}/tags/{tag['id']}/objects",
        headers=auth(token),
        json={'object_type': 'character', 'object_id': overview['characters'][0]['id']},
    )

    response = client.patch(
        f"/worlds/{world['id']}/tags/{tag['id']}",
        headers=auth(token),
        json={'name': ' 新标签 ', 'color': ' amber '},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['name'] == '新标签'
    assert payload['slug'] == '新标签'
    assert payload['color'] == 'amber'
    detail = client.get(f"/worlds/{world['id']}/tags/{tag['id']}", headers=auth(token)).json()
    assert detail['tag']['name'] == '新标签'
    assert detail['tag']['assignment_count'] == 1
    assert detail['objects'][0]['object_type'] == 'character'
    assert detail['objects'][0]['object_id'] == overview['characters'][0]['id']


def test_update_tag_duplicate_name_is_rejected_per_world(client):
    token = register(client, 'tags-update-duplicate@example.com')
    world = create_world(client, token)
    first = client.post(f"/worlds/{world['id']}/tags", headers=auth(token), json={'name': '主线'}).json()
    second = client.post(f"/worlds/{world['id']}/tags", headers=auth(token), json={'name': '支线'}).json()

    response = client.patch(
        f"/worlds/{world['id']}/tags/{second['id']}",
        headers=auth(token),
        json={'name': ' 主线 '},
    )

    assert response.status_code == 409
    assert response.json()['detail'] == 'TAG_ALREADY_EXISTS'
    unchanged = client.get(f"/worlds/{world['id']}/tags/{second['id']}", headers=auth(token)).json()
    assert unchanged['tag']['name'] == '支线'
    assert first['slug'] == '主线'


def test_update_tag_can_clear_color_without_incrementing_world_version(client):
    token = register(client, 'tags-update-version@example.com')
    world = create_world(client, token)
    overview = client.get(f"/worlds/{world['id']}/overview", headers=auth(token)).json()
    tag = client.post(f"/worlds/{world['id']}/tags", headers=auth(token), json={'name': '临时标签', 'color': 'red'}).json()

    response = client.patch(
        f"/worlds/{world['id']}/tags/{tag['id']}",
        headers=auth(token),
        json={'color': '   '},
    )
    after = client.get(f"/worlds/{world['id']}/overview", headers=auth(token)).json()
    events = client.get(f"/worlds/{world['id']}/events", headers=auth(token)).json()

    assert response.status_code == 200
    assert response.json()['color'] is None
    assert after['world_version'] == overview['world_version']
    assert events['summary']['event_type_counts'] == {'WORLD_CREATED': 1}
```

- [ ] **Step 2: Run backend RED test**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_tags.py::test_update_tag_name_and_color_preserves_assignments tests/test_tags.py::test_update_tag_duplicate_name_is_rejected_per_world tests/test_tags.py::test_update_tag_can_clear_color_without_incrementing_world_version -q
```

Expected: FAIL with `405 Method Not Allowed` or route-not-found behavior because the PATCH endpoint is not implemented yet.

---

### Task 2: Backend GREEN implementation

**Files:**
- Modify: `backend/app/tags/schemas.py`
- Modify: `backend/app/tags/service.py`
- Modify: `backend/app/tags/router.py`

- [ ] **Step 1: Add the update request schema**

In `backend/app/tags/schemas.py`, after `TagCreateRequest`, add:

```python
class TagUpdateRequest(BaseModel):
    name: str | None = None
    color: str | None = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _strip_required(value)

    @field_validator('color')
    @classmethod
    def normalize_color(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None
```

- [ ] **Step 2: Add the service function**

In `backend/app/tags/service.py`, update the schema import:

```python
from app.tags.schemas import ObjectTagAssignRequest, ObjectTagBulkAssignRequest, TagCreateRequest, TagUpdateRequest
```

Then add this function after `create_tag()`:

```python
def update_tag(db: Session, user: User, world_id: int, tag_id: int, data: TagUpdateRequest) -> Tag:
    world = require_owned_world(db, user, world_id)
    tag = _require_tag(db, world.id, tag_id)
    if data.name is not None:
        name = data.name.strip()
        tag.name = name
        tag.slug = _slugify(name)
    if 'color' in data.model_fields_set:
        tag.color = data.color
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='TAG_ALREADY_EXISTS') from exc
    db.refresh(tag)
    return tag
```

- [ ] **Step 3: Add the route**

In `backend/app/tags/router.py`, import `TagUpdateRequest` and `update_tag`.

Change the schemas import block to include:

```python
    TagUpdateRequest,
```

Change the service import to:

```python
from app.tags.service import assign_tag, bulk_assign_tag, create_tag, delete_tag, get_tag_detail, list_tags, unassign_tag, update_tag
```

Add this route after `create_world_tag()`:

```python
@router.patch('/worlds/{world_id}/tags/{tag_id}', response_model=TagResponse)
def update_world_tag(
    world_id: int,
    tag_id: int,
    data: TagUpdateRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> TagResponse:
    return TagResponse.model_validate(update_tag(db, current_user, world_id, tag_id, data))
```

- [ ] **Step 4: Run backend GREEN tests**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_tags.py::test_update_tag_name_and_color_preserves_assignments tests/test_tags.py::test_update_tag_duplicate_name_is_rejected_per_world tests/test_tags.py::test_update_tag_can_clear_color_without_incrementing_world_version -q
```

Expected: PASS.

---

### Task 3: Frontend RED tests

**Files:**
- Modify: `frontend/src/world/WorldTagsPanel.test.tsx`

- [ ] **Step 1: Add frontend failing tests**

Update the type import at the top of `frontend/src/world/WorldTagsPanel.test.tsx` to include `TagUpdateRequest` if that type already exists after Task 4, or keep the inline object shape before implementation. Add these tests before `it('shows empty and error states', ...)`:

```tsx
  it('edits the selected tag name and clears color', async () => {
    const user = userEvent.setup();
    const updatedTag: TagResponse = { ...tag, name: '主线压力', slug: '主线压力', color: null };
    const updatedDetail: TagDetailResponse = {
      ...detailResponse,
      tag: { ...detailResponse.tag, name: '主线压力', slug: '主线压力', color: null },
    };
    const onUpdateTag = vi.fn().mockResolvedValue(updatedTag);
    const onLoadTag = vi.fn()
      .mockResolvedValueOnce(detailResponse)
      .mockResolvedValueOnce(updatedDetail);
    renderPanel({ onUpdateTag, onLoadTag });

    await screen.findByText('灯塔线');
    await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
    expect(await screen.findByText('编辑标签')).toBeInTheDocument();

    await user.clear(screen.getByLabelText('编辑标签名称'));
    await user.type(screen.getByLabelText('编辑标签名称'), ' 主线压力 ');
    await user.clear(screen.getByLabelText('编辑标签颜色'));
    await user.click(screen.getByRole('button', { name: '保存标签修改' }));

    expect(onUpdateTag).toHaveBeenCalledWith(7, 3, { name: '主线压力', color: null });
    expect(await screen.findByText('标签已更新。')).toBeInTheDocument();
    await waitFor(() => expect(onLoadTag).toHaveBeenLastCalledWith(7, 3));
  });

  it('requires a name before updating a tag', async () => {
    const user = userEvent.setup();
    const onUpdateTag = vi.fn().mockResolvedValue(tag);
    renderPanel({ onUpdateTag });

    await screen.findByText('灯塔线');
    await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
    await screen.findByText('编辑标签');
    await user.clear(screen.getByLabelText('编辑标签名称'));
    await user.click(screen.getByRole('button', { name: '保存标签修改' }));

    expect(onUpdateTag).not.toHaveBeenCalled();
    expect(await screen.findByRole('alert')).toHaveTextContent('请输入标签名称');
  });
```

Also update `renderPanel()` to pass an `onUpdateTag` default once the prop exists:

```tsx
      onUpdateTag={vi.fn().mockResolvedValue(tag)}
```

- [ ] **Step 2: Run frontend RED test**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx
```

Expected: FAIL because `WorldTagsPanel` has no `onUpdateTag` prop and no edit UI.

---

### Task 4: Frontend GREEN implementation

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/world/WorldTagsPanel.tsx`
- Modify: `frontend/src/world/WorldPage.tsx`

- [ ] **Step 1: Add frontend API type**

In `frontend/src/api/types.ts`, after `TagResponse`, add:

```ts
export type TagUpdateRequest = {
  name?: string;
  color?: string | null;
};
```

- [ ] **Step 2: Add API client helper**

In `frontend/src/api/client.ts`, import `TagUpdateRequest` from `./types`, then add this function after `createWorldTag()`:

```ts
export function updateWorldTag(worldId: number, tagId: number, data: TagUpdateRequest) {
  return apiRequest<TagResponse>(`/worlds/${worldId}/tags/${tagId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}
```

- [ ] **Step 3: Update WorldTagsPanel props and state**

In `frontend/src/world/WorldTagsPanel.tsx`, import `TagUpdateRequest` and add the prop:

```ts
onUpdateTag: (worldId: number, tagId: number, data: TagUpdateRequest) => Promise<TagResponse>;
```

Update the function signature to include `onUpdateTag`.

Add state near the existing tag form state:

```ts
  const [editTagName, setEditTagName] = useState('');
  const [editTagColor, setEditTagColor] = useState('');
  const [editNotice, setEditNotice] = useState('');
```

- [ ] **Step 4: Initialize edit fields when loading details**

In `loadTag(tagId)`, replace `setDetail(await onLoadTag(worldId, tagId));` with:

```ts
      const loaded = await onLoadTag(worldId, tagId);
      setDetail(loaded);
      setEditTagName(loaded.tag.name);
      setEditTagColor(loaded.tag.color ?? '');
      setEditNotice('');
```

- [ ] **Step 5: Add submit handler**

Add this function before `submitAssignment()`:

```ts
  async function submitTagUpdate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedTagId === null) return;
    const name = editTagName.trim();
    if (!name) {
      setError('请输入标签名称');
      return;
    }
    setSaving(true);
    setError('');
    setEditNotice('');
    try {
      await onUpdateTag(worldId, selectedTagId, { name, color: editTagColor.trim() || null });
      await loadTags();
      await loadTag(selectedTagId);
      setEditNotice('标签已更新。');
    } catch (err) {
      setError(err instanceof Error ? err.message : '更新标签失败');
    } finally {
      setSaving(false);
    }
  }
```

- [ ] **Step 6: Add edit form UI**

Inside the `detail && (...)` block, after the current tag header and before the object assignment form, add:

```tsx
          <form className="grid gap-3 rounded-2xl bg-amber-50/60 p-4 md:grid-cols-[1fr_1fr_auto]" onSubmit={submitTagUpdate}>
            <p className="text-sm font-black text-[#3b2511] md:col-span-3">编辑标签</p>
            <label className="text-sm font-bold text-[#3b2511]">
              编辑标签名称
              <input className="paper-input mt-1" value={editTagName} onChange={(event) => setEditTagName(event.target.value)} />
            </label>
            <label className="text-sm font-bold text-[#3b2511]">
              编辑标签颜色
              <input className="paper-input mt-1" value={editTagColor} onChange={(event) => setEditTagColor(event.target.value)} placeholder="留空清除颜色" />
            </label>
            <button className="primary-button self-end" disabled={saving} type="submit">保存标签修改</button>
            {editNotice && <p className="ink-muted text-sm md:col-span-3">{editNotice}</p>}
          </form>
```

- [ ] **Step 7: Wire WorldPage**

In `frontend/src/world/WorldPage.tsx`, add `updateWorldTag` to the API import list and pass it into `WorldTagsPanel`:

```tsx
                onUpdateTag={updateWorldTag}
```

- [ ] **Step 8: Run frontend GREEN tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx
```

Expected: PASS.

---

### Task 5: Targeted verification, commit, and fast-forward merge

**Files:**
- Verify all MVP28 modified files.

- [ ] **Step 1: Run backend targeted regression**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_tags.py tests/test_world_search.py -q
```

Expected: PASS.

- [ ] **Step 2: Run frontend targeted tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx src/world/WorldSearchPanel.test.tsx src/world/WorldPage.test.tsx src/api/client.test.ts
```

Expected: PASS.

- [ ] **Step 3: Run frontend build**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: PASS.

- [ ] **Step 4: Inspect git status and diff**

Run:

```bash
git status --short --branch && git diff --stat
```

Expected: branch is `feat/mvp28-tag-editing`; changed files are limited to MVP28 docs, tag backend files/tests, API client/types, and world tag UI wiring/tests.

- [ ] **Step 5: Commit**

Run:

```bash
git add docs/superpowers/specs/2026-05-31-mvp28-tag-editing-design.md docs/superpowers/plans/2026-05-31-mvp28-tag-editing.md backend/tests/test_tags.py backend/app/tags/schemas.py backend/app/tags/service.py backend/app/tags/router.py frontend/src/api/types.ts frontend/src/api/client.ts frontend/src/world/WorldTagsPanel.test.tsx frontend/src/world/WorldTagsPanel.tsx frontend/src/world/WorldPage.tsx
git commit -m "feat: add tag editing" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

Expected: commit succeeds.

- [ ] **Step 6: Fast-forward merge to main without pushing**

Run:

```bash
git checkout main
git merge --ff-only feat/mvp28-tag-editing
git status --short --branch
git log --oneline -4
```

Expected: main fast-forwards to the MVP28 commit, working tree stays clean, no push is performed.

---

## Self-review

- Spec coverage: backend update route, duplicate handling, assignment preservation, metadata-only invariants, frontend edit form, WorldPage wiring, tests, and verification are all mapped to tasks.
- Placeholder scan: no TBD/TODO/fill-in placeholders remain.
- Type consistency: backend uses `TagUpdateRequest`; frontend uses `TagUpdateRequest`, `updateWorldTag`, and `onUpdateTag` consistently.
- Scope remains limited to tag name/color editing; tag merge, palette UX, assignment changes, migrations, and canon writes are excluded.
