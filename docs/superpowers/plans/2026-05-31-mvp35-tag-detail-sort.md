# MVP35 Tag Detail Object Sort 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This repository run is explicitly inline-only: do not use dynamic workflows, subagents, or the code-review subagent.

**Goal:** Add local sort controls over selected-tag objects so users can order tag detail results after filtering or searching.

**Architecture:** Frontend-only view enhancement in `WorldTagsPanel`. The component type-filters selected-tag objects, text-filters the result, then sorts the visible objects by the selected local sort mode; no backend route, schema, database, canon, world-version, or EventLog behavior changes.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, Vite; existing FastAPI pytest tag/search suites for regression verification.

---

## File structure

- Modify `frontend/src/world/WorldTagsPanel.test.tsx` — add RED/GREEN coverage for local selected-tag object sorting.
- Modify `frontend/src/world/WorldTagsPanel.tsx` — add detail sort state, sorted filtered objects, reset behavior, and sort UI.
- Create `docs/superpowers/specs/2026-05-31-mvp35-tag-detail-sort-design.md` — MVP35 design spec.
- Create `docs/superpowers/plans/2026-05-31-mvp35-tag-detail-sort.md` — implementation plan.

---

### Task 1: Frontend selected-tag object sort TDD

**Files:**
- Test: `frontend/src/world/WorldTagsPanel.test.tsx`
- Modify: `frontend/src/world/WorldTagsPanel.tsx`

- [ ] **Step 1: Write failing frontend tests**

In `frontend/src/world/WorldTagsPanel.test.tsx`, add these tests before the existing tag-list sort tests:

```tsx
it('sorts selected tag objects by title', async () => {
  const user = userEvent.setup();
  renderPanel({ onLoadTag: vi.fn().mockResolvedValue(mixedDetailResponse) });

  await screen.findByText('灯塔线');
  await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
  await screen.findByText('许砚');

  await user.selectOptions(screen.getByLabelText('对象排序'), 'title');

  const objectCards = screen.getAllByRole('article');
  expect(objectCards.map((card) => card.textContent)).toEqual([
    '第一章 灯塔低鸣chapter #11移除标签Chapter · approved · world v1许砚调查灯塔异常。',
    '许砚character #1移除标签Character · protagonist · active查明灯塔异常',
    '黑匣子脉冲foreshadow #2移除标签Foreshadow · planted · urgency 4废弃黑匣子收到来自未来的求救信号。',
  ]);
});

it('sorts searched selected tag objects by id', async () => {
  const user = userEvent.setup();
  renderPanel({ onLoadTag: vi.fn().mockResolvedValue(mixedDetailResponse) });

  await screen.findByText('灯塔线');
  await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
  await screen.findByText('黑匣子脉冲');

  await user.type(screen.getByLabelText('搜索当前标签对象'), '章');
  await user.selectOptions(screen.getByLabelText('对象排序'), 'id');

  const objectCards = screen.getAllByRole('article');
  expect(objectCards.map((card) => card.textContent)).toEqual([
    '许砚character #1移除标签Character · protagonist · active查明灯塔异常',
    '第一章 灯塔低鸣chapter #11移除标签Chapter · approved · world v1许砚调查灯塔异常。',
  ]);
  expect(screen.getByText('显示 2 / 3 个对象')).toBeInTheDocument();
});

it('resets selected tag object sort when loading another tag', async () => {
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
  await user.selectOptions(screen.getByLabelText('对象排序'), 'title');
  expect(screen.getByLabelText('对象排序')).toHaveValue('title');

  await user.click(screen.getByRole('button', { name: '查看 主线归档' }));

  expect(await screen.findByText('许砚')).toBeInTheDocument();
  expect(screen.getByLabelText('对象排序')).toHaveValue('default');
});
```

- [ ] **Step 2: Run frontend RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx
```

Expected: new tests fail because the `对象排序` select does not exist.

- [ ] **Step 3: Add detail sort state and reset behavior**

In `frontend/src/world/WorldTagsPanel.tsx`, add state near the existing selected-detail filter/search state:

```ts
const [detailSortMode, setDetailSortMode] = useState('default');
```

In `loadTag()`, after resetting `detailSearchQuery`, add:

```ts
setDetailSortMode('default');
```

- [ ] **Step 4: Add sorted selected-tag object derivation**

Replace the current `filteredObjects` derivation with:

```ts
const normalizedDetailSearchQuery = detailSearchQuery.trim().toLowerCase();
const typeFilteredObjects = detail
  ? detailObjectTypeFilter === 'all'
    ? detail.objects
    : detail.objects.filter((item) => item.object_type === detailObjectTypeFilter)
  : [];
const searchedObjects = normalizedDetailSearchQuery
  ? typeFilteredObjects.filter((item) => {
      const haystack = [item.title, item.subtitle, item.snippet, item.object_type, String(item.object_id)].join(' ').toLowerCase();
      return haystack.includes(normalizedDetailSearchQuery);
    })
  : typeFilteredObjects;
const filteredObjects = [...searchedObjects].sort((left, right) => {
  if (detailSortMode === 'title') return left.title.localeCompare(right.title) || left.object_type.localeCompare(right.object_type) || left.object_id - right.object_id;
  if (detailSortMode === 'type') return left.object_type.localeCompare(right.object_type) || left.title.localeCompare(right.title) || left.object_id - right.object_id;
  if (detailSortMode === 'id') return left.object_id - right.object_id || left.object_type.localeCompare(right.object_type);
  return 0;
});
```

- [ ] **Step 5: Add selected-tag object sort UI**

Wrap the existing `搜索当前标签对象` label in a two-column grid and add this sort label beside it:

```tsx
<label className="block rounded-2xl bg-white/45 p-3 text-sm font-bold text-[#3b2511]">
  对象排序
  <select
    className="paper-input mt-1"
    aria-label="对象排序"
    value={detailSortMode}
    onChange={(event) => setDetailSortMode(event.target.value)}
  >
    <option value="default">默认排序</option>
    <option value="title">标题 A-Z</option>
    <option value="type">类型 A-Z</option>
    <option value="id">ID 从小到大</option>
  </select>
</label>
```

- [ ] **Step 6: Run frontend GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx
```

Expected: all panel tests pass.

---

### Task 2: Final verification, docs status, commit, and merge

**Files:**
- Modified frontend panel files and MVP35 docs.

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

Append implementation status sections to the MVP35 spec and plan after verification, recording RED/GREEN and command results.

- [ ] **Step 5: Commit**

Run:

```bash
git -C /opt/WorldSim-Writer status --short
git -C /opt/WorldSim-Writer add frontend/src/world/WorldTagsPanel.tsx frontend/src/world/WorldTagsPanel.test.tsx docs/superpowers/specs/2026-05-31-mvp35-tag-detail-sort-design.md docs/superpowers/plans/2026-05-31-mvp35-tag-detail-sort.md
git -C /opt/WorldSim-Writer commit -m "feat: sort tag detail objects"
```

- [ ] **Step 6: Fast-forward merge to main without push**

Run:

```bash
git -C /opt/WorldSim-Writer checkout main
git -C /opt/WorldSim-Writer merge --ff-only feat/mvp35-tag-detail-sort
```

Do not push.

- [ ] **Step 7: Post-merge verification**

Repeat backend targeted tests, frontend targeted tests, and frontend build from Steps 1-3 on `main`.

Expected: all pass after merge.

## Self-review

- This plan covers all MVP35 acceptance criteria.
- No placeholders remain.
- Types and labels are consistent with the existing component and tests.
- Selected-tag object sorting only orders already-loaded data; it does not call write APIs.
- No backend, database, canon, world-version, or EventLog behavior changes are introduced.

## Execution status

Implemented on `feat/mvp35-tag-detail-sort` using TDD. RED was observed in `WorldTagsPanel.test.tsx` for the missing selected-tag object sort select; GREEN was observed after adding local detail sort state, reset behavior when loading another tag, default/title/type/id modes, and sort UI. Pre-merge backend targeted tests, frontend targeted tests, and frontend build passed. An initial frontend command failed from the backend directory with missing `package.json`; rerunning from `/opt/WorldSim-Writer/frontend` passed.
