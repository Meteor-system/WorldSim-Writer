# Bookshelf Archive Switch MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal bookshelf so users can snapshot/export a paused novel, archive it without deleting data, and open/create another novel.

**Architecture:** Reuse existing multi-world backend list and `World.status`. Add a tiny status PATCH endpoint, a frontend bookshelf state inside `WorldPage`, and README usage docs. Keep existing world overview, Story Arc, NCC, snapshot/export, and Studio launch flows unchanged after a world opens.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, Vite React, TypeScript, Vitest/React Testing Library.

---

## File Structure

- Modify `README.md` — add user workflow docs for snapshot/export/bookshelf/archive/switching.
- Modify `backend/app/world/schemas.py` — add `WorldStatusUpdateRequest` with `active | archived` validation.
- Modify `backend/app/world/service.py` — add `update_world_status()` that uses ownership checks and never deletes data.
- Modify `backend/app/world/router.py` — add `PATCH /worlds/{world_id}/status`.
- Test `backend/tests/test_world_routes.py` or create it if absent — cover archive/restore, invalid status, non-owner rejection.
- Modify `frontend/src/api/types.ts` — add `WorldSummary` and `WorldStatusUpdateRequest` types.
- Modify `frontend/src/api/client.ts` — add `updateWorldStatus()`.
- Modify `frontend/src/world/WorldPage.tsx` — add bookshelf/list selection, return-to-bookshelf, create-new entry, archive/restore action.
- Modify `frontend/src/world/WorldPage.test.tsx` — TDD coverage for multi-world select, return bookshelf, archive entry/status, single-world auto-open.

## Task 1: Document the pause/switch workflow

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add user workflow docs**

Insert after the markdown export response paragraph:

```markdown
## Pausing one novel and switching to another

Recommended flow when you are not ready to continue the current novel:

1. Open the current novel from the bookshelf.
2. In `World Archive`, click `创建世界快照` to freeze the current world version.
3. Click `导出世界档案` and download the Markdown ZIP for an offline copy.
4. Return to `作品书架`.
5. Archive the paused novel. Archiving is a reversible status marker; it never deletes the world, chapters, snapshots, or exports.
6. Create a new novel or open another active novel and continue writing.
```

- [ ] **Step 2: No test required**

This is documentation-only. Verify by reading the inserted section.

## Task 2: Backend archive status endpoint with TDD

**Files:**
- Modify: `backend/app/world/schemas.py`
- Modify: `backend/app/world/service.py`
- Modify: `backend/app/world/router.py`
- Test: `backend/tests/test_world_routes.py`

- [ ] **Step 1: Write failing backend tests**

Add tests covering:

```python
def test_world_owner_can_archive_and_restore_world(client, db_session):
    token = client.post('/auth/register', json={'email': 'archive-owner@example.com', 'password': 'strongpass123'}).json()['access_token']
    world = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {token}'}).json()

    archived = client.patch(
        f"/worlds/{world['id']}/status",
        json={'status': 'archived'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert archived.status_code == 200
    assert archived.json()['status'] == 'archived'
    assert client.get(f"/worlds/{world['id']}", headers={'Authorization': f'Bearer {token}'}).json()['status'] == 'archived'

    restored = client.patch(
        f"/worlds/{world['id']}/status",
        json={'status': 'active'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert restored.status_code == 200
    assert restored.json()['status'] == 'active'
    assert db_session.get(World, world['id']) is not None


def test_world_status_update_rejects_invalid_status(client):
    token = client.post('/auth/register', json={'email': 'archive-invalid@example.com', 'password': 'strongpass123'}).json()['access_token']
    world = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {token}'}).json()

    response = client.patch(
        f"/worlds/{world['id']}/status",
        json={'status': 'deleted'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 422


def test_world_status_update_rejects_non_owner(client):
    owner_token = client.post('/auth/register', json={'email': 'archive-real-owner@example.com', 'password': 'strongpass123'}).json()['access_token']
    other_token = client.post('/auth/register', json={'email': 'archive-other@example.com', 'password': 'strongpass123'}).json()['access_token']
    world = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {owner_token}'}).json()

    response = client.patch(
        f"/worlds/{world['id']}/status",
        json={'status': 'archived'},
        headers={'Authorization': f'Bearer {other_token}'},
    )

    assert response.status_code == 403
```

- [ ] **Step 2: Run backend RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 conda run -n worldsim pytest tests/test_world_routes.py -v
```

Expected: FAIL because `PATCH /worlds/{world_id}/status` does not exist.

- [ ] **Step 3: Implement minimal backend endpoint**

Add schema:

```python
class WorldStatusUpdateRequest(BaseModel):
    status: str

    @field_validator('status')
    @classmethod
    def validate_status(cls, value: str) -> str:
        if value not in {'active', 'archived'}:
            raise ValueError('status must be active or archived')
        return value
```

Add service:

```python
def update_world_status(db: Session, user: User, world_id: int, next_status: str) -> World:
    world = require_owned_world(db, user, world_id)
    world.status = next_status
    db.commit()
    db.refresh(world)
    return world
```

Add router:

```python
@router.patch('/{world_id}/status', response_model=WorldResponse)
def update_status(
    world_id: int,
    data: WorldStatusUpdateRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> WorldResponse:
    return WorldResponse.model_validate(update_world_status(db, current_user, world_id, data.status))
```

- [ ] **Step 4: Run backend GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 conda run -n worldsim pytest tests/test_world_routes.py -v
```

Expected: PASS.

## Task 3: Frontend bookshelf with TDD

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/world/WorldPage.tsx`
- Test: `frontend/src/world/WorldPage.test.tsx`

- [ ] **Step 1: Write failing frontend tests**

Add tests covering:

```ts
const secondWorld: WorldOverview = { ...world, id: 8, title: '星舰余烬', status: 'active', truth_canon: '星舰仍在航行。' };

it('shows a bookshelf for multiple worlds and opens the selected second world', async () => {
  const user = userEvent.setup();
  vi.mocked(apiRequest).mockReset();
  vi.mocked(apiRequest).mockResolvedValueOnce([
    { id: 7, title: '青岚城', genre_template: 'xianxia', truth_canon: '灵脉正在衰退。', truth_canon_version: 1, world_version: 2, status: 'active', tone_profile: {}, current_characters: [], current_foreshadows: [], current_relations: [] },
    { id: 8, title: '星舰余烬', genre_template: 'sci_fi', truth_canon: '星舰仍在航行。', truth_canon_version: 1, world_version: 1, status: 'active', tone_profile: {}, current_characters: [], current_foreshadows: [], current_relations: [] },
  ]);
  vi.mocked(apiRequest).mockResolvedValueOnce(secondWorld);

  render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

  expect(await screen.findByText('作品书架')).toBeInTheDocument();
  expect(screen.queryByText('World Canon')).not.toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: '打开 星舰余烬' }));

  expect(await screen.findByText('星舰余烬')).toBeInTheDocument();
  expect(apiRequest).toHaveBeenNthCalledWith(2, '/worlds/8/overview');
});

it('returns from an open world to the bookshelf', async () => {
  const user = userEvent.setup();
  vi.mocked(apiRequest).mockReset();
  vi.mocked(apiRequest)
    .mockResolvedValueOnce([{ id: 7 }, { id: 8 }])
    .mockResolvedValueOnce(world);

  render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

  await user.click(await screen.findByRole('button', { name: '打开 青岚城' }));
  expect(await screen.findByText('World Canon')).toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: '返回作品书架' }));

  expect(screen.getByText('作品书架')).toBeInTheDocument();
});

it('shows archive entry copy on the current world page', async () => {
  render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

  expect(await screen.findByText('归档前建议先创建世界快照并导出 Markdown ZIP。')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '归档当前小说' })).toBeInTheDocument();
});

it('still auto-opens a single existing world', async () => {
  render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

  expect(await screen.findByText('World Canon')).toBeInTheDocument();
  expect(screen.queryByText('作品书架')).not.toBeInTheDocument();
});
```

- [ ] **Step 2: Run frontend RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: FAIL because the bookshelf UI and archive entry do not exist.

- [ ] **Step 3: Implement frontend client/types**

Add `WorldSummary` type matching `WorldResponse`. Add `WorldStatusUpdateRequest`. Add:

```ts
export function updateWorldStatus(worldId: number, data: WorldStatusUpdateRequest) {
  return apiRequest<WorldSummary>(`/worlds/${worldId}/status`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}
```

- [ ] **Step 4: Implement bookshelf UI**

In `WorldPage`, keep a `worlds` list and `showCreationForm` state. Load list first. If multiple worlds exist, show a `作品书架` section with active and archived groups. Each item has `打开 <title>`. Current world page has `返回作品书架`, archive guidance copy, and archive/restore button.

- [ ] **Step 5: Run frontend GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: PASS.

## Task 4: Verification and commit

**Files:**
- All modified docs/backend/frontend files.

- [ ] **Step 1: Run targeted backend tests**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 conda run -n worldsim pytest tests/test_world_routes.py tests/test_snapshot_export.py -v
```

- [ ] **Step 2: Run focused frontend tests**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx src/world/WorldArchivePanel.test.tsx
```

- [ ] **Step 3: Run frontend build**

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

- [ ] **Step 4: Inspect git status**

```bash
cd /opt/WorldSim-Writer && git status --short && git diff --stat
```

Confirm untracked `.hermes/plans/*` and `backend/worldsim-dev.db` are not staged.

- [ ] **Step 5: Commit**

```bash
cd /opt/WorldSim-Writer && git add README.md docs/superpowers/specs/2026-06-01-bookshelf-archive-switch-design.md docs/superpowers/plans/2026-06-01-bookshelf-archive-switch.md backend/app/world/schemas.py backend/app/world/service.py backend/app/world/router.py backend/tests/test_world_routes.py frontend/src/api/types.ts frontend/src/api/client.ts frontend/src/world/WorldPage.tsx frontend/src/world/WorldPage.test.tsx && git commit -m "feat: add bookshelf archive switching" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

Do not merge or push.

## Self-Review

- Spec coverage: docs, bookshelf, multi-world select, return to shelf, archive marker, single-world no regression, snapshot/export preservation, backend ownership all covered.
- Placeholder scan: no TBD/TODO placeholders.
- Type consistency: frontend `WorldSummary` maps to backend `WorldResponse`; archive statuses are `active | archived`.
