# MVP40 Tag Detail View Summary 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This repository run is explicitly inline-only: do not use dynamic workflows, subagents, or the code-review subagent.

**Goal:** Add a compact local summary of the selected-tag object view so users can understand combined object filter, search, sort, and visible-count state at a glance.

**Architecture:** Frontend-only enhancement in `WorldTagsPanel`. Helper functions convert local object filter/sort values into user-facing labels, and a derived summary string renders below the existing selected-tag object controls. No backend route, schema, database, canon, world-version, or EventLog behavior changes.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, Vite; existing FastAPI pytest tag/search suites for regression verification.

---

## File structure

- Modify `frontend/src/world/WorldTagsPanel.test.tsx` — add RED/GREEN coverage for selected-tag object view summary text.
- Modify `frontend/src/world/WorldTagsPanel.tsx` — add detail label helpers, derived summary text, and summary UI.
- Create `docs/superpowers/specs/2026-05-31-mvp40-tag-detail-summary-design.md` — MVP40 design spec.
- Create `docs/superpowers/plans/2026-05-31-mvp40-tag-detail-summary.md` — implementation plan.

---

### Task 1: Frontend tag-detail summary TDD

**Files:**
- Test: `frontend/src/world/WorldTagsPanel.test.tsx`
- Modify: `frontend/src/world/WorldTagsPanel.tsx`

- [ ] **Step 1: Write failing frontend tests**

In `frontend/src/world/WorldTagsPanel.test.tsx`, add these tests before the existing `resets selected tag object filter search and sort controls` test:

```tsx
it('summarizes active selected tag object filter search and sort state', async () => {
  const user = userEvent.setup();
  renderPanel({ onLoadTag: vi.fn().mockResolvedValue(mixedDetailResponse) });

  await screen.findByText('灯塔线');
  await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
  await screen.findByText('黑匣子脉冲');
  await user.click(screen.getByRole('button', { name: '只看章节 1' }));
  await user.type(screen.getByLabelText('搜索当前标签对象'), '许');
  await user.selectOptions(screen.getByLabelText('对象排序'), 'id');

  expect(screen.getByLabelText('标签对象视图摘要')).toHaveTextContent('显示 1 / 3 个对象 · 搜索「许」 · 类型：章节 · 排序：ID 从小到大');
});

it('resets selected tag object view summary with object view reset', async () => {
  const user = userEvent.setup();
  renderPanel({ onLoadTag: vi.fn().mockResolvedValue(mixedDetailResponse) });

  await screen.findByText('灯塔线');
  await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
  await screen.findByText('黑匣子脉冲');
  await user.click(screen.getByRole('button', { name: '只看章节 1' }));
  await user.type(screen.getByLabelText('搜索当前标签对象'), '许');
  await user.selectOptions(screen.getByLabelText('对象排序'), 'id');
  expect(screen.getByLabelText('标签对象视图摘要')).toHaveTextContent('显示 1 / 3 个对象 · 搜索「许」 · 类型：章节 · 排序：ID 从小到大');

  await user.click(screen.getByRole('button', { name: '重置对象视图' }));

  expect(screen.getByLabelText('标签对象视图摘要')).toHaveTextContent('显示 3 / 3 个对象 · 未搜索 · 类型：全部对象 · 排序：默认排序');
});
```

- [ ] **Step 2: Run frontend RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx
```

Expected: new tests fail because the `标签对象视图摘要` element does not exist.

- [ ] **Step 3: Add local detail label helpers**

In `frontend/src/world/WorldTagsPanel.tsx`, add these helpers after `tagSortLabel()`:

```ts
function objectTypeFilterLabel(value: string): string {
  if (value === 'all') return '全部对象';
  return OBJECT_TYPES.find((item) => item.value === value)?.label ?? value;
}

function detailSortLabel(value: string): string {
  if (value === 'title') return '标题 A-Z';
  if (value === 'type') return '类型 A-Z';
  if (value === 'id') return 'ID 从小到大';
  return '默认排序';
}
```

- [ ] **Step 4: Add derived detail summary text**

In `frontend/src/world/WorldTagsPanel.tsx`, add this after `filteredObjects`:

```ts
const detailViewSummary = detail
  ? [
      `显示 ${filteredObjects.length} / ${detail.tag.assignment_count} 个对象`,
      normalizedDetailSearchQuery ? `搜索「${detailSearchQuery.trim()}」` : '未搜索',
      `类型：${objectTypeFilterLabel(detailObjectTypeFilter)}`,
      `排序：${detailSortLabel(detailSortMode)}`,
    ].join(' · ')
  : '';
```

- [ ] **Step 5: Render summary below selected-tag object controls**

In `frontend/src/world/WorldTagsPanel.tsx`, replace the current selected-tag object search/sort/reset controls block wrapper:

```tsx
<div className="grid gap-3 md:grid-cols-[1fr_14rem_auto]">
```

with:

```tsx
<div className="space-y-2">
  <div className="grid gap-3 md:grid-cols-[1fr_14rem_auto]">
```

Then add this immediately after the reset button and before closing the new wrapper:

```tsx
  </div>
  <p className="ink-muted text-xs" aria-label="标签对象视图摘要">{detailViewSummary}</p>
</div>
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
- Modified frontend panel files and MVP40 docs.

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

Append implementation status sections to the MVP40 spec and plan after verification, recording RED/GREEN and command results.

- [ ] **Step 5: Commit**

Run:

```bash
git -C /opt/WorldSim-Writer status --short
git -C /opt/WorldSim-Writer add frontend/src/world/WorldTagsPanel.tsx frontend/src/world/WorldTagsPanel.test.tsx docs/superpowers/specs/2026-05-31-mvp40-tag-detail-summary-design.md docs/superpowers/plans/2026-05-31-mvp40-tag-detail-summary.md
git -C /opt/WorldSim-Writer commit -m "feat: summarize tag detail view state"
```

- [ ] **Step 6: Fast-forward merge to main without push**

Run:

```bash
git -C /opt/WorldSim-Writer checkout main
git -C /opt/WorldSim-Writer merge --ff-only feat/mvp40-tag-detail-summary
```

Do not push.

- [ ] **Step 7: Post-merge verification**

Repeat backend targeted tests, frontend targeted tests, and frontend build from Steps 1-3 on `main`.

Expected: all pass after merge.

## Self-review

- This plan covers all MVP40 acceptance criteria.
- No placeholders remain.
- Types and labels are consistent with the existing component and tests.
- Tag-detail summary only reads local view state; it does not call write APIs.
- No backend, database, canon, world-version, or EventLog behavior changes are introduced.

## Execution status

Implemented on `feat/mvp40-tag-detail-summary` using TDD. RED was observed in `WorldTagsPanel.test.tsx` for the missing selected-tag object view summary element; GREEN was observed after adding detail label helpers, derived summary text, and summary UI below the selected-tag object controls. Pre-merge backend targeted tests, frontend targeted tests, and frontend build passed. An initial frontend command failed from the backend directory with missing `package.json`; rerunning from `/opt/WorldSim-Writer/frontend` passed.
