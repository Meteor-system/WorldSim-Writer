# MVP39 Tag View Summary 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This repository run is explicitly inline-only: do not use dynamic workflows, subagents, or the code-review subagent.

**Goal:** Add a compact local summary of the active tag-list view so users can understand combined search, filter, sort, and visible-count state at a glance.

**Architecture:** Frontend-only enhancement in `WorldTagsPanel`. Helper functions convert local filter/sort values into user-facing labels, and a derived summary string renders below the existing tag-list controls. No backend route, schema, database, canon, world-version, or EventLog behavior changes.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, Vite; existing FastAPI pytest tag/search suites for regression verification.

---

## File structure

- Modify `frontend/src/world/WorldTagsPanel.test.tsx` — add RED/GREEN coverage for tag-list view summary text.
- Modify `frontend/src/world/WorldTagsPanel.tsx` — add label helpers, derived summary text, and summary UI.
- Create `docs/superpowers/specs/2026-05-31-mvp39-tag-view-summary-design.md` — MVP39 design spec.
- Create `docs/superpowers/plans/2026-05-31-mvp39-tag-view-summary.md` — implementation plan.

---

### Task 1: Frontend tag-view summary TDD

**Files:**
- Test: `frontend/src/world/WorldTagsPanel.test.tsx`
- Modify: `frontend/src/world/WorldTagsPanel.tsx`

- [ ] **Step 1: Write failing frontend tests**

In `frontend/src/world/WorldTagsPanel.test.tsx`, add these tests before the existing `shows counts in tag-list object type filter options` test:

```tsx
it('summarizes active tag-list search filter and sort state', async () => {
  const user = userEvent.setup();
  renderPanel({ onListTags: vi.fn().mockResolvedValue(sortableListResponse) });

  await screen.findByText('灯塔线');
  await user.type(screen.getByLabelText('搜索标签'), '档');
  await user.selectOptions(screen.getByLabelText('标签对象类型'), 'foreshadow');
  await user.selectOptions(screen.getByLabelText('标签排序'), 'name');

  expect(screen.getByLabelText('标签视图摘要')).toHaveTextContent('显示 1 / 3 个标签 · 搜索「档」 · 类型：伏笔 · 排序：名称 A-Z');
});

it('resets tag-list view summary with tag view reset', async () => {
  const user = userEvent.setup();
  renderPanel({ onListTags: vi.fn().mockResolvedValue(sortableListResponse) });

  await screen.findByText('灯塔线');
  await user.type(screen.getByLabelText('搜索标签'), '档');
  await user.selectOptions(screen.getByLabelText('标签对象类型'), 'empty');
  await user.selectOptions(screen.getByLabelText('标签排序'), 'count');
  expect(screen.getByLabelText('标签视图摘要')).toHaveTextContent('显示 1 / 3 个标签 · 搜索「档」 · 类型：无对象 · 排序：对象数最多');

  await user.click(screen.getByRole('button', { name: '重置标签视图' }));

  expect(screen.getByLabelText('标签视图摘要')).toHaveTextContent('显示 3 / 3 个标签 · 未搜索 · 类型：全部标签 · 排序：默认排序');
});
```

- [ ] **Step 2: Run frontend RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx
```

Expected: new tests fail because the `标签视图摘要` element does not exist.

- [ ] **Step 3: Add local label helpers**

In `frontend/src/world/WorldTagsPanel.tsx`, add these helpers after `tagTypeFilterCount()`:

```ts
function tagTypeFilterLabel(value: string): string {
  if (value === 'all') return '全部标签';
  if (value === 'empty') return '无对象';
  return OBJECT_TYPES.find((item) => item.value === value)?.label ?? value;
}

function tagSortLabel(value: string): string {
  if (value === 'name') return '名称 A-Z';
  if (value === 'count') return '对象数最多';
  if (value === 'created') return '最新创建';
  return '默认排序';
}
```

- [ ] **Step 4: Add derived summary text**

In `frontend/src/world/WorldTagsPanel.tsx`, add this after `visibleTagIdsKey`:

```ts
const tagViewSummary = [
  `显示 ${visibleTags.length} / ${tags.length} 个标签`,
  normalizedTagSearchQuery ? `搜索「${tagSearchQuery.trim()}」` : '未搜索',
  `类型：${tagTypeFilterLabel(tagObjectTypeFilter)}`,
  `排序：${tagSortLabel(tagSortMode)}`,
].join(' · ');
```

- [ ] **Step 5: Render summary below tag-list controls**

In `frontend/src/world/WorldTagsPanel.tsx`, replace the current tag-list controls block wrapper:

```tsx
{tags.length > 0 && (
  <div className="grid gap-3 md:grid-cols-[1fr_12rem_14rem_auto]">
```

with:

```tsx
{tags.length > 0 && (
  <div className="space-y-2">
    <div className="grid gap-3 md:grid-cols-[1fr_12rem_14rem_auto]">
```

Then add this immediately after the reset button and before closing the new wrapper:

```tsx
    </div>
    <p className="ink-muted text-xs" aria-label="标签视图摘要">{tagViewSummary}</p>
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
- Modified frontend panel files and MVP39 docs.

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

Append implementation status sections to the MVP39 spec and plan after verification, recording RED/GREEN and command results.

- [ ] **Step 5: Commit**

Run:

```bash
git -C /opt/WorldSim-Writer status --short
git -C /opt/WorldSim-Writer add frontend/src/world/WorldTagsPanel.tsx frontend/src/world/WorldTagsPanel.test.tsx docs/superpowers/specs/2026-05-31-mvp39-tag-view-summary-design.md docs/superpowers/plans/2026-05-31-mvp39-tag-view-summary.md
git -C /opt/WorldSim-Writer commit -m "feat: summarize tag view state"
```

- [ ] **Step 6: Fast-forward merge to main without push**

Run:

```bash
git -C /opt/WorldSim-Writer checkout main
git -C /opt/WorldSim-Writer merge --ff-only feat/mvp39-tag-view-summary
```

Do not push.

- [ ] **Step 7: Post-merge verification**

Repeat backend targeted tests, frontend targeted tests, and frontend build from Steps 1-3 on `main`.

Expected: all pass after merge.

## Self-review

- This plan covers all MVP39 acceptance criteria.
- No placeholders remain.
- Types and labels are consistent with the existing component and tests.
- Tag-view summary only reads local view state; it does not call write APIs.
- No backend, database, canon, world-version, or EventLog behavior changes are introduced.

## Execution status

Implemented on `feat/mvp39-tag-view-summary` using TDD. RED was observed in `WorldTagsPanel.test.tsx` for the missing tag-view summary element; GREEN was observed after adding label helpers, derived summary text, and summary UI below the tag-list controls. Pre-merge backend targeted tests, frontend targeted tests, and frontend build passed. An initial frontend command failed from the backend directory with missing `package.json`; rerunning from `/opt/WorldSim-Writer/frontend` passed.
