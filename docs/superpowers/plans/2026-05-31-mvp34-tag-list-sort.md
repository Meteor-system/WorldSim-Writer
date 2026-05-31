# MVP34 Tag List Sort 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This repository run is explicitly inline-only: do not use dynamic workflows, subagents, or the code-review subagent.

**Goal:** Add local sort controls over the tag list so users can order visible tags after searching or browsing.

**Architecture:** Frontend-only view enhancement in `WorldTagsPanel`. The component filters the loaded `TagListResponse.tags` array locally, then sorts the filtered list by the selected local sort mode; no backend route, schema, database, canon, world-version, or EventLog behavior changes.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, Vite; existing FastAPI pytest tag/search suites for regression verification.

---

## File structure

- Modify `frontend/src/world/WorldTagsPanel.test.tsx` — add RED/GREEN coverage for local tag-list sorting.
- Modify `frontend/src/world/WorldTagsPanel.tsx` — add sort state, sorted visible tags, and sort UI.
- Create `docs/superpowers/specs/2026-05-31-mvp34-tag-list-sort-design.md` — MVP34 design spec.
- Create `docs/superpowers/plans/2026-05-31-mvp34-tag-list-sort.md` — implementation plan.

---

### Task 1: Frontend tag-list sort TDD

**Files:**
- Test: `frontend/src/world/WorldTagsPanel.test.tsx`
- Modify: `frontend/src/world/WorldTagsPanel.tsx`

- [ ] **Step 1: Write failing frontend tests**

In `frontend/src/world/WorldTagsPanel.test.tsx`, add an extra tag fixture and these tests before the existing empty/error state test:

```tsx
const olderTag: TagResponse = {
  id: 5,
  world_id: 7,
  name: '阿尔法档案',
  slug: '阿尔法档案',
  color: 'green',
  created_at: '2026-05-30T00:00:00Z',
};

const sortableListResponse: TagListResponse = {
  world_id: 7,
  tags: [
    { ...targetTag, assignment_count: 0, object_type_counts: {} },
    { ...tag, assignment_count: 3, object_type_counts: { character: 1, chapter: 2 } },
    { ...olderTag, assignment_count: 1, object_type_counts: { foreshadow: 1 } },
  ],
};
```

```tsx
it('sorts visible tags by assignment count', async () => {
  const user = userEvent.setup();
  renderPanel({ onListTags: vi.fn().mockResolvedValue(sortableListResponse) });

  await screen.findByText('灯塔线');
  await user.selectOptions(screen.getByLabelText('标签排序'), 'count');

  const tagButtons = screen.getAllByRole('button', { name: /查看 / });
  expect(tagButtons.map((button) => button.textContent)).toEqual([
    '灯塔线总数 3character 1 · chapter 2',
    '阿尔法档案总数 1foreshadow 1',
    '主线归档总数 0无对象',
  ]);
});

it('sorts searched tags by name', async () => {
  const user = userEvent.setup();
  renderPanel({ onListTags: vi.fn().mockResolvedValue(sortableListResponse) });

  await screen.findByText('灯塔线');
  await user.type(screen.getByLabelText('搜索标签'), '档');
  await user.selectOptions(screen.getByLabelText('标签排序'), 'name');

  const tagButtons = screen.getAllByRole('button', { name: /查看 / });
  expect(tagButtons.map((button) => button.textContent)).toEqual([
    '阿尔法档案总数 1foreshadow 1',
    '主线归档总数 0无对象',
  ]);
  expect(screen.getByText('显示 2 / 3 个标签')).toBeInTheDocument();
});

it('keeps selected tag detail when only sorting changes', async () => {
  const user = userEvent.setup();
  renderPanel({
    onListTags: vi.fn().mockResolvedValue(sortableListResponse),
    onLoadTag: vi.fn().mockResolvedValue(detailResponse),
  });

  await screen.findByText('灯塔线');
  await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
  expect(await screen.findByText('许砚')).toBeInTheDocument();

  await user.selectOptions(screen.getByLabelText('标签排序'), 'name');

  expect(screen.getByText('当前标签')).toBeInTheDocument();
  expect(screen.getByText('许砚')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run frontend RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx
```

Expected: new tests fail because the `标签排序` select does not exist.

- [ ] **Step 3: Add tag sort state and sorted visible tags**

In `frontend/src/world/WorldTagsPanel.tsx`, add state near the existing tag search state:

```ts
const [tagSortMode, setTagSortMode] = useState('default');
```

Replace the current `visibleTags` derivation with search-then-sort logic:

```ts
const normalizedTagSearchQuery = tagSearchQuery.trim().toLowerCase();
const searchedTags = normalizedTagSearchQuery
  ? tags.filter((tag) => {
      const haystack = [tag.name, tag.slug, tag.color ?? '', String(tag.assignment_count), countText(tag)].join(' ').toLowerCase();
      return haystack.includes(normalizedTagSearchQuery);
    })
  : tags;
const visibleTags = [...searchedTags].sort((left, right) => {
  if (tagSortMode === 'name') return left.name.localeCompare(right.name) || left.id - right.id;
  if (tagSortMode === 'count') return right.assignment_count - left.assignment_count || left.name.localeCompare(right.name) || left.id - right.id;
  if (tagSortMode === 'created') return right.created_at.localeCompare(left.created_at) || right.id - left.id;
  return 0;
});
const visibleTagIdsKey = visibleTags.map((tag) => tag.id).join(',');
```

- [ ] **Step 4: Add tag-list sort UI**

After the tag-list search label, add:

```tsx
<label className="block rounded-2xl bg-white/45 p-3 text-sm font-bold text-[#3b2511]">
  标签排序
  <select
    className="paper-input mt-1"
    aria-label="标签排序"
    value={tagSortMode}
    onChange={(event) => setTagSortMode(event.target.value)}
  >
    <option value="default">默认排序</option>
    <option value="name">名称 A-Z</option>
    <option value="count">对象数最多</option>
    <option value="created">最新创建</option>
  </select>
</label>
```

- [ ] **Step 5: Run frontend GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx
```

Expected: all panel tests pass.

---

### Task 2: Final verification, docs status, commit, and merge

**Files:**
- Modified frontend panel files and MVP34 docs.

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

Append implementation status sections to the MVP34 spec and plan after verification, recording RED/GREEN and command results.

- [ ] **Step 5: Commit**

Run:

```bash
git -C /opt/WorldSim-Writer status --short
git -C /opt/WorldSim-Writer add frontend/src/world/WorldTagsPanel.tsx frontend/src/world/WorldTagsPanel.test.tsx docs/superpowers/specs/2026-05-31-mvp34-tag-list-sort-design.md docs/superpowers/plans/2026-05-31-mvp34-tag-list-sort.md
git -C /opt/WorldSim-Writer commit -m "feat: sort tag list"
```

- [ ] **Step 6: Fast-forward merge to main without push**

Run:

```bash
git -C /opt/WorldSim-Writer checkout main
git -C /opt/WorldSim-Writer merge --ff-only feat/mvp34-tag-list-sort
```

Do not push.

- [ ] **Step 7: Post-merge verification**

Repeat backend targeted tests, frontend targeted tests, and frontend build from Steps 1-3 on `main`.

Expected: all pass after merge.

## Self-review

- This plan covers all MVP34 acceptance criteria.
- No placeholders remain.
- Types and labels are consistent with the existing component and tests.
- Tag-list sorting only orders already-loaded data; it does not call write APIs.
- No backend, database, canon, world-version, or EventLog behavior changes are introduced.

## Execution status

Implemented on `feat/mvp34-tag-list-sort` using TDD. RED was observed in `WorldTagsPanel.test.tsx` for the missing tag-list sort select; GREEN was observed after adding local sort state, search-then-sort derivation, default/name/count/created modes, and sort UI. Pre-merge backend targeted tests, frontend targeted tests, and frontend build passed. An initial frontend command failed from the backend directory with missing `package.json`; rerunning from `/opt/WorldSim-Writer/frontend` passed.
