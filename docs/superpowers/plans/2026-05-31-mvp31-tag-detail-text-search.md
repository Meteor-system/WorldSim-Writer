# MVP31 Tag Detail Text Search 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This repository run is explicitly inline-only: do not use dynamic workflows, subagents, or the code-review subagent.

**Goal:** Add local text search to selected tag details so users can quickly find assigned objects inside large tag collections.

**Architecture:** Frontend-only view enhancement in `WorldTagsPanel`. The component uses existing `TagDetailResponse.objects` and combines the new text query with MVP30's local object-type filter; no backend route, schema, database, canon, world-version, or EventLog behavior changes.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, Vite; existing FastAPI pytest tag/search suites for regression verification.

---

## File structure

- Modify `frontend/src/world/WorldTagsPanel.test.tsx` — add RED/GREEN coverage for local tag detail text search.
- Modify `frontend/src/world/WorldTagsPanel.tsx` — add search state, input, derived search filtering, visible count, and reset behavior.
- Create `docs/superpowers/specs/2026-05-31-mvp31-tag-detail-text-search-design.md` — MVP31 design spec.
- Create `docs/superpowers/plans/2026-05-31-mvp31-tag-detail-text-search.md` — implementation plan.

---

### Task 1: Frontend tag detail text search TDD

**Files:**
- Test: `frontend/src/world/WorldTagsPanel.test.tsx`
- Modify: `frontend/src/world/WorldTagsPanel.tsx`

- [ ] **Step 1: Write failing frontend tests**

In `frontend/src/world/WorldTagsPanel.test.tsx`, add these tests before the existing empty/error state test:

```tsx
it('searches selected tag objects by text', async () => {
  const user = userEvent.setup();
  renderPanel({ onLoadTag: vi.fn().mockResolvedValue(mixedDetailResponse) });

  await screen.findByText('灯塔线');
  await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
  expect(await screen.findByText('许砚')).toBeInTheDocument();
  expect(screen.getByText('黑匣子脉冲')).toBeInTheDocument();
  expect(screen.getByText('第一章 灯塔低鸣')).toBeInTheDocument();

  await user.type(screen.getByLabelText('搜索当前标签对象'), '未来');

  expect(screen.queryByText('许砚')).not.toBeInTheDocument();
  expect(screen.getByText('黑匣子脉冲')).toBeInTheDocument();
  expect(screen.queryByText('第一章 灯塔低鸣')).not.toBeInTheDocument();
  expect(screen.getByText('显示 1 / 3 个对象')).toBeInTheDocument();
});

it('combines tag object text search with object type filters', async () => {
  const user = userEvent.setup();
  renderPanel({ onLoadTag: vi.fn().mockResolvedValue(mixedDetailResponse) });

  await screen.findByText('灯塔线');
  await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
  await screen.findByText('黑匣子脉冲');

  await user.click(screen.getByRole('button', { name: '只看章节 1' }));
  await user.type(screen.getByLabelText('搜索当前标签对象'), '许砚');

  expect(screen.queryByText('黑匣子脉冲')).not.toBeInTheDocument();
  expect(screen.getByText('第一章 灯塔低鸣')).toBeInTheDocument();
  expect(screen.getByText('显示 1 / 3 个对象')).toBeInTheDocument();
});

it('resets tag object text search when loading another tag', async () => {
  const user = userEvent.setup();
  const targetDetail: TagDetailResponse = {
    tag: { ...targetTag, assignment_count: 1, object_type_counts: { character: 1 } },
    objects: [detailResponse.objects[0]],
  };
  const onLoadTag = vi.fn()
    .mockResolvedValueOnce(mixedDetailResponse)
    .mockResolvedValueOnce(targetDetail);
  renderPanel({ onLoadTag });

  await screen.findByText('灯塔线');
  await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
  await screen.findByText('黑匣子脉冲');
  await user.type(screen.getByLabelText('搜索当前标签对象'), '未来');
  expect(screen.queryByText('许砚')).not.toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: '查看 主线归档' }));

  expect(await screen.findByText('许砚')).toBeInTheDocument();
  expect(screen.getByLabelText('搜索当前标签对象')).toHaveValue('');
});
```

- [ ] **Step 2: Run frontend RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx
```

Expected: new tests fail because the `搜索当前标签对象` input and search-derived visible counts do not exist.

- [ ] **Step 3: Add search state and derived data**

In `frontend/src/world/WorldTagsPanel.tsx`, add state near existing detail filter state:

```ts
const [detailSearchQuery, setDetailSearchQuery] = useState('');
```

In `loadTag()`, after resetting `detailObjectTypeFilter`, add:

```ts
setDetailSearchQuery('');
```

Replace the existing `filteredObjects` derivation before the return statement with:

```ts
const normalizedDetailSearchQuery = detailSearchQuery.trim().toLowerCase();
const typeFilteredObjects = detail
  ? detailObjectTypeFilter === 'all'
    ? detail.objects
    : detail.objects.filter((item) => item.object_type === detailObjectTypeFilter)
  : [];
const filteredObjects = normalizedDetailSearchQuery
  ? typeFilteredObjects.filter((item) => {
      const haystack = [item.title, item.subtitle, item.snippet, item.object_type, String(item.object_id)].join(' ').toLowerCase();
      return haystack.includes(normalizedDetailSearchQuery);
    })
  : typeFilteredObjects;
```

- [ ] **Step 4: Add search UI**

In the selected tag detail panel, after the object-type filter block and before the assignment form, add:

```tsx
<label className="block rounded-2xl bg-white/45 p-3 text-sm font-bold text-[#3b2511]">
  搜索当前标签对象
  <input
    className="paper-input mt-1"
    value={detailSearchQuery}
    onChange={(event) => setDetailSearchQuery(event.target.value)}
    placeholder="按标题、摘要、类型或 ID 搜索"
  />
  <span className="ink-muted mt-2 block text-xs">显示 {filteredObjects.length} / {detail.tag.assignment_count} 个对象</span>
</label>
```

Keep object rendering pointed at `filteredObjects`; no assignment or mutation handlers change.

- [ ] **Step 5: Run frontend GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx
```

Expected: all panel tests pass.

---

### Task 2: Final verification, docs status, commit, and merge

**Files:**
- Modified frontend panel files and MVP31 docs.

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

- [ ] **Step 4: Update docs status**

Append implementation status sections to the MVP31 spec and plan after verification, recording RED/GREEN and command results.

- [ ] **Step 5: Commit**

Run:

```bash
git -C /opt/WorldSim-Writer/frontend status --short
git -C /opt/WorldSim-Writer/frontend add frontend/src/world/WorldTagsPanel.tsx frontend/src/world/WorldTagsPanel.test.tsx docs/superpowers/specs/2026-05-31-mvp31-tag-detail-text-search-design.md docs/superpowers/plans/2026-05-31-mvp31-tag-detail-text-search.md
git -C /opt/WorldSim-Writer/frontend commit -m "feat: search tag detail objects"
```

- [ ] **Step 6: Fast-forward merge to main without push**

Run:

```bash
git -C /opt/WorldSim-Writer/frontend checkout main
git -C /opt/WorldSim-Writer/frontend merge --ff-only feat/mvp31-tag-detail-search
```

Do not push.

- [ ] **Step 7: Post-merge verification**

Repeat backend targeted tests, frontend targeted tests, and frontend build from Steps 1-3 on `main`.

Expected: all pass after merge.

## Self-review

- This plan covers all MVP31 acceptance criteria.
- No placeholders remain.
- Types and labels are consistent with the existing component and tests.
- Search combines with type filtering without changing mutation handlers.
- No backend, database, canon, world-version, or EventLog behavior changes are introduced.

## Execution status

Implemented on `feat/mvp31-tag-detail-search` using TDD. RED was observed in `WorldTagsPanel.test.tsx` for the missing tag-detail search input; GREEN was observed after adding local search state, derived type-plus-text filtering, visible counts, and reset-on-tag-load behavior. Pre-merge backend targeted tests, frontend targeted tests, and frontend build passed.
