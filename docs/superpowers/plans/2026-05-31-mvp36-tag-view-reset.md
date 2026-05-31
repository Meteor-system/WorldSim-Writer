# MVP36 Tag View Reset Controls 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This repository run is explicitly inline-only: do not use dynamic workflows, subagents, or the code-review subagent.

**Goal:** Add local reset controls for tag-list and selected-tag object views so users can quickly return accumulated search/filter/sort state to defaults.

**Architecture:** Frontend-only view enhancement in `WorldTagsPanel`. Reset buttons call local React state setters; no backend route, schema, database, canon, world-version, or EventLog behavior changes.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, Vite; existing FastAPI pytest tag/search suites for regression verification.

---

## File structure

- Modify `frontend/src/world/WorldTagsPanel.test.tsx` — add RED/GREEN coverage for local tag view reset controls.
- Modify `frontend/src/world/WorldTagsPanel.tsx` — add reset handlers and reset buttons.
- Create `docs/superpowers/specs/2026-05-31-mvp36-tag-view-reset-design.md` — MVP36 design spec.
- Create `docs/superpowers/plans/2026-05-31-mvp36-tag-view-reset.md` — implementation plan.

---

### Task 1: Frontend tag view reset TDD

**Files:**
- Test: `frontend/src/world/WorldTagsPanel.test.tsx`
- Modify: `frontend/src/world/WorldTagsPanel.tsx`

- [ ] **Step 1: Write failing frontend tests**

In `frontend/src/world/WorldTagsPanel.test.tsx`, add these tests before the existing empty/error state test:

```tsx
it('resets tag-list search and sort controls', async () => {
  const user = userEvent.setup();
  renderPanel({ onListTags: vi.fn().mockResolvedValue(sortableListResponse) });

  await screen.findByText('灯塔线');
  await user.type(screen.getByLabelText('搜索标签'), '档');
  await user.selectOptions(screen.getByLabelText('标签排序'), 'name');
  expect(screen.getByLabelText('搜索标签')).toHaveValue('档');
  expect(screen.getByLabelText('标签排序')).toHaveValue('name');

  await user.click(screen.getByRole('button', { name: '重置标签视图' }));

  expect(screen.getByLabelText('搜索标签')).toHaveValue('');
  expect(screen.getByLabelText('标签排序')).toHaveValue('default');
  const tagButtons = screen.getAllByRole('button', { name: /查看 / });
  expect(tagButtons.map((button) => button.textContent)).toEqual([
    '主线归档总数 0无对象',
    '灯塔线总数 3character 1 · chapter 2',
    '阿尔法档案总数 1foreshadow 1',
  ]);
  expect(screen.getByText('显示 3 / 3 个标签')).toBeInTheDocument();
});

it('resets selected tag object filter search and sort controls', async () => {
  const user = userEvent.setup();
  renderPanel({ onLoadTag: vi.fn().mockResolvedValue(mixedDetailResponse) });

  await screen.findByText('灯塔线');
  await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
  await screen.findByText('黑匣子脉冲');
  await user.click(screen.getByRole('button', { name: '只看章节 1' }));
  await user.type(screen.getByLabelText('搜索当前标签对象'), '许');
  await user.selectOptions(screen.getByLabelText('对象排序'), 'id');
  expect(screen.getByText('显示 1 / 3 个对象')).toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: '重置对象视图' }));

  expect(screen.getByRole('button', { name: '查看全部对象 3' })).toHaveClass('ring-2');
  expect(screen.getByLabelText('搜索当前标签对象')).toHaveValue('');
  expect(screen.getByLabelText('对象排序')).toHaveValue('default');
  expect(screen.getByText('显示 3 / 3 个对象')).toBeInTheDocument();
  expect(screen.getByText('许砚')).toBeInTheDocument();
  expect(screen.getByText('黑匣子脉冲')).toBeInTheDocument();
  expect(screen.getByText('第一章 灯塔低鸣')).toBeInTheDocument();
});

it('keeps selected tag detail when resetting tag-list controls', async () => {
  const user = userEvent.setup();
  renderPanel({
    onListTags: vi.fn().mockResolvedValue(sortableListResponse),
    onLoadTag: vi.fn().mockResolvedValue(detailResponse),
  });

  await screen.findByText('灯塔线');
  await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
  expect(await screen.findByText('许砚')).toBeInTheDocument();
  await user.selectOptions(screen.getByLabelText('标签排序'), 'name');

  await user.click(screen.getByRole('button', { name: '重置标签视图' }));

  expect(screen.getByText('当前标签')).toBeInTheDocument();
  expect(screen.getByText('许砚')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run frontend RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx
```

Expected: new tests fail because the reset buttons do not exist.

- [ ] **Step 3: Add reset handlers**

In `frontend/src/world/WorldTagsPanel.tsx`, add these local handlers before `submitTag()`:

```ts
function resetTagView() {
  setTagSearchQuery('');
  setTagSortMode('default');
}

function resetDetailView() {
  setDetailObjectTypeFilter('all');
  setDetailSearchQuery('');
  setDetailSortMode('default');
}
```

- [ ] **Step 4: Add tag-list reset button**

Inside the existing tag search/sort grid, after the `标签排序` label, add:

```tsx
<button className="secondary-button self-end" type="button" onClick={resetTagView}>重置标签视图</button>
```

Update the grid class from `md:grid-cols-[1fr_14rem]` to `md:grid-cols-[1fr_14rem_auto]`.

- [ ] **Step 5: Add selected-tag object reset button**

Inside the existing selected-tag object search/sort grid, after the `对象排序` label, add:

```tsx
<button className="secondary-button self-end" type="button" onClick={resetDetailView}>重置对象视图</button>
```

Update the grid class from `md:grid-cols-[1fr_14rem]` to `md:grid-cols-[1fr_14rem_auto]` for that selected-tag object controls grid.

- [ ] **Step 6: Run frontend GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx
```

Expected: all panel tests pass.

---

### Task 2: Final verification, docs status, commit, and merge

**Files:**
- Modified frontend panel files and MVP36 docs.

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

Append implementation status sections to the MVP36 spec and plan after verification, recording RED/GREEN and command results.

- [ ] **Step 5: Commit**

Run:

```bash
git -C /opt/WorldSim-Writer status --short
git -C /opt/WorldSim-Writer add frontend/src/world/WorldTagsPanel.tsx frontend/src/world/WorldTagsPanel.test.tsx docs/superpowers/specs/2026-05-31-mvp36-tag-view-reset-design.md docs/superpowers/plans/2026-05-31-mvp36-tag-view-reset.md
git -C /opt/WorldSim-Writer commit -m "feat: reset tag views"
```

- [ ] **Step 6: Fast-forward merge to main without push**

Run:

```bash
git -C /opt/WorldSim-Writer checkout main
git -C /opt/WorldSim-Writer merge --ff-only feat/mvp36-tag-view-reset
```

Do not push.

- [ ] **Step 7: Post-merge verification**

Repeat backend targeted tests, frontend targeted tests, and frontend build from Steps 1-3 on `main`.

Expected: all pass after merge.

## Self-review

- This plan covers all MVP36 acceptance criteria.
- No placeholders remain.
- Types and labels are consistent with the existing component and tests.
- Reset controls only update local state; they do not call write APIs.
- No backend, database, canon, world-version, or EventLog behavior changes are introduced.

## Execution status

Implemented on `feat/mvp36-tag-view-reset` using TDD. RED was observed in `WorldTagsPanel.test.tsx` for missing reset buttons; GREEN was observed after adding local tag-list and selected-tag object reset handlers/buttons. Pre-merge backend targeted tests, frontend targeted tests, and frontend build passed. An initial frontend command failed from the backend directory with missing `package.json`; rerunning from `/opt/WorldSim-Writer/frontend` passed.
