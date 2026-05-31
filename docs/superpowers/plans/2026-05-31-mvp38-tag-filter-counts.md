# MVP38 Tag Filter Counts 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This repository run is explicitly inline-only: do not use dynamic workflows, subagents, or the code-review subagent.

**Goal:** Show local counts in the tag-list object-type filter options so users can see how many tags each option will match before selecting it.

**Architecture:** Frontend-only enhancement in `WorldTagsPanel`. A small helper derives counts from loaded tag summaries, and the existing `标签对象类型` option labels include those counts while keeping option values and filtering behavior unchanged. No backend route, schema, database, canon, world-version, or EventLog behavior changes.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, Vite; existing FastAPI pytest tag/search suites for regression verification.

---

## File structure

- Modify `frontend/src/world/WorldTagsPanel.test.tsx` — add RED/GREEN coverage for tag-list type-filter option counts.
- Modify `frontend/src/world/WorldTagsPanel.tsx` — add local count helper and count labels in filter options.
- Create `docs/superpowers/specs/2026-05-31-mvp38-tag-filter-counts-design.md` — MVP38 design spec.
- Create `docs/superpowers/plans/2026-05-31-mvp38-tag-filter-counts.md` — implementation plan.

---

### Task 1: Frontend tag-filter count TDD

**Files:**
- Test: `frontend/src/world/WorldTagsPanel.test.tsx`
- Modify: `frontend/src/world/WorldTagsPanel.tsx`

- [ ] **Step 1: Write failing frontend tests**

In `frontend/src/world/WorldTagsPanel.test.tsx`, add these tests before the existing `filters visible tags by assigned object type` test:

```tsx
it('shows counts in tag-list object type filter options', async () => {
  renderPanel({ onListTags: vi.fn().mockResolvedValue(sortableListResponse) });

  await screen.findByText('灯塔线');
  const typeFilter = screen.getByLabelText('标签对象类型');

  expect(within(typeFilter).getByRole('option', { name: '全部标签 3' })).toBeInTheDocument();
  expect(within(typeFilter).getByRole('option', { name: '无对象 1' })).toBeInTheDocument();
  expect(within(typeFilter).getByRole('option', { name: '角色 1' })).toBeInTheDocument();
  expect(within(typeFilter).getByRole('option', { name: '伏笔 1' })).toBeInTheDocument();
  expect(within(typeFilter).getByRole('option', { name: '章节 1' })).toBeInTheDocument();
  expect(within(typeFilter).getByRole('option', { name: '事件 0' })).toBeInTheDocument();
});

it('keeps tag-list object type counts based on all loaded tags while searching', async () => {
  const user = userEvent.setup();
  renderPanel({ onListTags: vi.fn().mockResolvedValue(sortableListResponse) });

  await screen.findByText('灯塔线');
  await user.type(screen.getByLabelText('搜索标签'), '档');

  const typeFilter = screen.getByLabelText('标签对象类型');
  expect(screen.getByText('显示 2 / 3 个标签')).toBeInTheDocument();
  expect(within(typeFilter).getByRole('option', { name: '全部标签 3' })).toBeInTheDocument();
  expect(within(typeFilter).getByRole('option', { name: '角色 1' })).toBeInTheDocument();
  expect(within(typeFilter).getByRole('option', { name: '伏笔 1' })).toBeInTheDocument();
});
```

- [ ] **Step 2: Run frontend RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx
```

Expected: new tests fail because the filter options do not include counts.

- [ ] **Step 3: Add tag type filter count helper**

In `frontend/src/world/WorldTagsPanel.tsx`, add this helper after `countText()`:

```ts
function tagTypeFilterCount(tags: TagSummaryResponse[], value: string): number {
  if (value === 'all') return tags.length;
  if (value === 'empty') return tags.filter((tag) => tag.assignment_count === 0).length;
  return tags.filter((tag) => (tag.object_type_counts[value] ?? 0) > 0).length;
}
```

- [ ] **Step 4: Add counts to type-filter options**

In the `标签对象类型` select in `frontend/src/world/WorldTagsPanel.tsx`, replace the current option labels:

```tsx
<option value="all">全部标签</option>
<option value="empty">无对象</option>
{OBJECT_TYPES.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
```

with:

```tsx
<option value="all">全部标签 {tagTypeFilterCount(tags, 'all')}</option>
<option value="empty">无对象 {tagTypeFilterCount(tags, 'empty')}</option>
{OBJECT_TYPES.map((item) => <option key={item.value} value={item.value}>{item.label} {tagTypeFilterCount(tags, item.value)}</option>)}
```

Do not change the option values.

- [ ] **Step 5: Run frontend GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx
```

Expected: all panel tests pass.

---

### Task 2: Final verification, docs status, commit, and merge

**Files:**
- Modified frontend panel files and MVP38 docs.

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

Append implementation status sections to the MVP38 spec and plan after verification, recording RED/GREEN and command results.

- [ ] **Step 5: Commit**

Run:

```bash
git -C /opt/WorldSim-Writer status --short
git -C /opt/WorldSim-Writer add frontend/src/world/WorldTagsPanel.tsx frontend/src/world/WorldTagsPanel.test.tsx docs/superpowers/specs/2026-05-31-mvp38-tag-filter-counts-design.md docs/superpowers/plans/2026-05-31-mvp38-tag-filter-counts.md
git -C /opt/WorldSim-Writer commit -m "feat: show tag filter counts"
```

- [ ] **Step 6: Fast-forward merge to main without push**

Run:

```bash
git -C /opt/WorldSim-Writer checkout main
git -C /opt/WorldSim-Writer merge --ff-only feat/mvp38-tag-filter-counts
```

Do not push.

- [ ] **Step 7: Post-merge verification**

Repeat backend targeted tests, frontend targeted tests, and frontend build from Steps 1-3 on `main`.

Expected: all pass after merge.

## Self-review

- This plan covers all MVP38 acceptance criteria.
- No placeholders remain.
- Types and labels are consistent with the existing component and tests.
- Tag-filter counts only read loaded local tag data; they do not call write APIs.
- No backend, database, canon, world-version, or EventLog behavior changes are introduced.

## Execution status

Implemented on `feat/mvp38-tag-filter-counts` using TDD. RED was observed in `WorldTagsPanel.test.tsx` for missing tag-list object-type option counts; GREEN was observed after adding the local `tagTypeFilterCount()` helper and count labels to `标签对象类型` options. Pre-merge backend targeted tests, frontend targeted tests, and frontend build passed. An initial frontend command failed from the backend directory with missing `package.json`; rerunning from `/opt/WorldSim-Writer/frontend` passed.
