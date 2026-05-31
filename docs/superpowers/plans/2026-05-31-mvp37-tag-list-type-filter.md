# MVP37 Tag List Type Filter 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This repository run is explicitly inline-only: do not use dynamic workflows, subagents, or the code-review subagent.

**Goal:** Add a local tag-list object-type filter so users can show all tags, empty tags, or tags assigned to characters, foreshadows, chapters, or events.

**Architecture:** Frontend-only view enhancement in `WorldTagsPanel`. A new local state value filters loaded tag summaries by `assignment_count` and `object_type_counts` before existing text search and sort logic. No backend route, schema, database, canon, world-version, or EventLog behavior changes.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, Vite; existing FastAPI pytest tag/search suites for regression verification.

---

## File structure

- Modify `frontend/src/world/WorldTagsPanel.test.tsx` — add RED/GREEN coverage for local tag-list object-type filtering.
- Modify `frontend/src/world/WorldTagsPanel.tsx` — add tag-list type-filter state, derivation, reset integration, and select UI.
- Create `docs/superpowers/specs/2026-05-31-mvp37-tag-list-type-filter-design.md` — MVP37 design spec.
- Create `docs/superpowers/plans/2026-05-31-mvp37-tag-list-type-filter.md` — implementation plan.

---

### Task 1: Frontend tag-list type-filter TDD

**Files:**
- Test: `frontend/src/world/WorldTagsPanel.test.tsx`
- Modify: `frontend/src/world/WorldTagsPanel.tsx`

- [ ] **Step 1: Write failing frontend tests**

In `frontend/src/world/WorldTagsPanel.test.tsx`, add these tests before the existing `resets tag-list search and sort controls` test:

```tsx
it('filters visible tags by assigned object type', async () => {
  const user = userEvent.setup();
  renderPanel({ onListTags: vi.fn().mockResolvedValue(sortableListResponse) });

  await screen.findByText('灯塔线');
  await user.selectOptions(screen.getByLabelText('标签对象类型'), 'foreshadow');

  const tagButtons = screen.getAllByRole('button', { name: /查看 / });
  expect(tagButtons.map((button) => button.textContent)).toEqual([
    '阿尔法档案总数 1foreshadow 1',
  ]);
  expect(screen.getByText('显示 1 / 3 个标签')).toBeInTheDocument();
});

it('resets tag-list object type filtering with tag view reset', async () => {
  const user = userEvent.setup();
  renderPanel({ onListTags: vi.fn().mockResolvedValue(sortableListResponse) });

  await screen.findByText('灯塔线');
  await user.selectOptions(screen.getByLabelText('标签对象类型'), 'empty');
  expect(screen.getByText('主线归档')).toBeInTheDocument();
  expect(screen.queryByText('灯塔线')).not.toBeInTheDocument();
  expect(screen.getByLabelText('标签对象类型')).toHaveValue('empty');

  await user.click(screen.getByRole('button', { name: '重置标签视图' }));

  expect(screen.getByLabelText('标签对象类型')).toHaveValue('all');
  expect(screen.getByText('显示 3 / 3 个标签')).toBeInTheDocument();
  expect(screen.getByText('灯塔线')).toBeInTheDocument();
  expect(screen.getByText('阿尔法档案')).toBeInTheDocument();
});

it('clears selected tag detail when tag-list type filtering hides it', async () => {
  const user = userEvent.setup();
  renderPanel({
    onListTags: vi.fn().mockResolvedValue(sortableListResponse),
    onLoadTag: vi.fn().mockResolvedValue(detailResponse),
  });

  await screen.findByText('灯塔线');
  await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
  expect(await screen.findByText('许砚')).toBeInTheDocument();

  await user.selectOptions(screen.getByLabelText('标签对象类型'), 'foreshadow');

  expect(screen.queryByText('许砚')).not.toBeInTheDocument();
  expect(screen.queryByText('当前标签')).not.toBeInTheDocument();
});
```

- [ ] **Step 2: Run frontend RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx
```

Expected: new tests fail because the `标签对象类型` select does not exist.

- [ ] **Step 3: Add tag-list type-filter state and derivation**

In `frontend/src/world/WorldTagsPanel.tsx`, add state after `tagSearchQuery`:

```ts
const [tagObjectTypeFilter, setTagObjectTypeFilter] = useState('all');
```

Replace the current tag-list derivation that starts at `const normalizedTagSearchQuery = ...` with:

```ts
const typeFilteredTags = tagObjectTypeFilter === 'all'
  ? tags
  : tags.filter((tag) => {
      if (tagObjectTypeFilter === 'empty') return tag.assignment_count === 0;
      return (tag.object_type_counts[tagObjectTypeFilter] ?? 0) > 0;
    });
const normalizedTagSearchQuery = tagSearchQuery.trim().toLowerCase();
const searchedTags = normalizedTagSearchQuery
  ? typeFilteredTags.filter((tag) => {
      const haystack = [tag.name, tag.slug, tag.color ?? '', String(tag.assignment_count), countText(tag)].join(' ').toLowerCase();
      return haystack.includes(normalizedTagSearchQuery);
    })
  : typeFilteredTags;
```

Keep the existing `visibleTags` sort logic unchanged after `searchedTags`.

- [ ] **Step 4: Extend tag view reset**

Update `resetTagView()` in `frontend/src/world/WorldTagsPanel.tsx` to also restore the type filter:

```ts
function resetTagView() {
  setTagSearchQuery('');
  setTagObjectTypeFilter('all');
  setTagSortMode('default');
}
```

- [ ] **Step 5: Add tag-list type-filter UI**

In the tag-list controls grid, update the grid class from:

```tsx
<div className="grid gap-3 md:grid-cols-[1fr_14rem_auto]">
```

to:

```tsx
<div className="grid gap-3 md:grid-cols-[1fr_12rem_14rem_auto]">
```

Add this label between the `搜索标签` label and the `标签排序` label:

```tsx
<label className="block rounded-2xl bg-white/45 p-3 text-sm font-bold text-[#3b2511]">
  标签对象类型
  <select
    className="paper-input mt-1"
    aria-label="标签对象类型"
    value={tagObjectTypeFilter}
    onChange={(event) => setTagObjectTypeFilter(event.target.value)}
  >
    <option value="all">全部标签</option>
    <option value="empty">无对象</option>
    {OBJECT_TYPES.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
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
- Modified frontend panel files and MVP37 docs.

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

Append implementation status sections to the MVP37 spec and plan after verification, recording RED/GREEN and command results.

- [ ] **Step 5: Commit**

Run:

```bash
git -C /opt/WorldSim-Writer status --short
git -C /opt/WorldSim-Writer add frontend/src/world/WorldTagsPanel.tsx frontend/src/world/WorldTagsPanel.test.tsx docs/superpowers/specs/2026-05-31-mvp37-tag-list-type-filter-design.md docs/superpowers/plans/2026-05-31-mvp37-tag-list-type-filter.md
git -C /opt/WorldSim-Writer commit -m "feat: filter tag list by type"
```

- [ ] **Step 6: Fast-forward merge to main without push**

Run:

```bash
git -C /opt/WorldSim-Writer checkout main
git -C /opt/WorldSim-Writer merge --ff-only feat/mvp37-tag-list-type-filter
```

Do not push.

- [ ] **Step 7: Post-merge verification**

Repeat backend targeted tests, frontend targeted tests, and frontend build from Steps 1-3 on `main`.

Expected: all pass after merge.

## Self-review

- This plan covers all MVP37 acceptance criteria.
- No placeholders remain.
- Types and labels are consistent with the existing component and tests.
- Tag-list type filtering only updates local view state; it does not call write APIs.
- No backend, database, canon, world-version, or EventLog behavior changes are introduced.

## Execution status

Implemented on `feat/mvp37-tag-list-type-filter` using TDD. RED was observed in `WorldTagsPanel.test.tsx` for the missing tag-list object-type filter select; GREEN was observed after adding local tag-list type-filter state, filter-first/search-second/sort-last derivation, reset behavior, and filter UI. Pre-merge backend targeted tests, frontend targeted tests, and frontend build passed. An initial frontend command failed from the backend directory with missing `package.json`; rerunning from `/opt/WorldSim-Writer/frontend` passed.
