# MVP41 Tag Empty State Guidance 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This repository run is explicitly inline-only: do not use dynamic workflows, subagents, or the code-review subagent.

**Goal:** Make tag-list and selected-tag object filtered-empty states explain the active local search/filter constraints that caused zero visible results.

**Architecture:** Frontend-only enhancement in `WorldTagsPanel`. Existing local summary state and label helpers are reused to derive clearer empty-state guidance. No backend route, schema, database, canon, world-version, or EventLog behavior changes.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, Vite; existing FastAPI pytest tag/search suites for regression verification.

---

## File structure

- Modify `frontend/src/world/WorldTagsPanel.test.tsx` — add RED/GREEN coverage for tag-list and selected-tag object filtered-empty guidance.
- Modify `frontend/src/world/WorldTagsPanel.tsx` — add guidance helpers and replace generic filtered-empty copy.
- Create `docs/superpowers/specs/2026-06-01-mvp41-tag-empty-guidance-design.md` — MVP41 design spec.
- Create `docs/superpowers/plans/2026-06-01-mvp41-tag-empty-guidance.md` — implementation plan.

---

### Task 1: Frontend empty-state guidance TDD

**Files:**
- Test: `frontend/src/world/WorldTagsPanel.test.tsx`
- Modify: `frontend/src/world/WorldTagsPanel.tsx`

- [ ] **Step 1: Write failing frontend tests**

In `frontend/src/world/WorldTagsPanel.test.tsx`, add these tests near the existing tag-list and selected-tag object empty-state coverage:

```tsx
it('explains tag-list empty state using active object type filters', async () => {
  const user = userEvent.setup();
  renderPanel({ onListTags: vi.fn().mockResolvedValue(sortableListResponse) });

  await screen.findByText('灯塔线');
  await user.selectOptions(screen.getByLabelText('标签对象类型'), 'event');

  expect(screen.getByText('没有匹配类型：事件的标签。请重置标签视图或调整搜索与类型筛选。')).toBeInTheDocument();
  expect(screen.getByLabelText('标签视图摘要')).toHaveTextContent('显示 0 / 3 个标签 · 未搜索 · 类型：事件 · 排序：默认排序');
});

it('explains selected tag object empty state using active search and type filters', async () => {
  const user = userEvent.setup();
  renderPanel({ onLoadTag: vi.fn().mockResolvedValue(mixedDetailResponse) });

  await screen.findByText('灯塔线');
  await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
  await screen.findByText('黑匣子脉冲');
  await user.click(screen.getByRole('button', { name: '只看伏笔 1' }));
  await user.type(screen.getByLabelText('搜索当前标签对象'), '许');

  expect(screen.getByText('没有匹配搜索「许」，类型：伏笔的对象。请重置对象视图或调整搜索与类型筛选。')).toBeInTheDocument();
  expect(screen.getByLabelText('标签对象视图摘要')).toHaveTextContent('显示 0 / 3 个对象 · 搜索「许」 · 类型：伏笔 · 排序：默认排序');
});

it('keeps no-associated-objects empty state separate from filtered-empty guidance', async () => {
  const emptyDetail: TagDetailResponse = {
    tag: { ...tag, assignment_count: 0, object_type_counts: {} },
    objects: [],
  };
  renderPanel({ onLoadTag: vi.fn().mockResolvedValue(emptyDetail) });

  await screen.findByText('灯塔线');
  await userEvent.click(screen.getByRole('button', { name: '查看 灯塔线' }));

  expect(await screen.findByText('这个标签还没有关联对象。')).toBeInTheDocument();
  expect(screen.queryByText(/请重置对象视图/)).not.toBeInTheDocument();
});
```

- [ ] **Step 2: Run frontend RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx
```

Expected: the new guidance tests fail because the UI still renders generic empty-state copy.

- [ ] **Step 3: Add local empty-guidance helpers**

In `frontend/src/world/WorldTagsPanel.tsx`, add this helper after `detailSortLabel()`:

```ts
function constraintText(parts: string[]): string {
  return parts.length > 0 ? parts.join('，') : '当前条件';
}
```

- [ ] **Step 4: Add derived tag-list guidance text**

In `frontend/src/world/WorldTagsPanel.tsx`, add this immediately after `tagViewSummary`:

```ts
const tagEmptyGuidance = [
  normalizedTagSearchQuery ? `搜索「${tagSearchQuery.trim()}」` : '',
  tagObjectTypeFilter !== 'all' ? `类型：${tagTypeFilterLabel(tagObjectTypeFilter)}` : '',
].filter(Boolean);
const tagFilteredEmptyText = `没有匹配${constraintText(tagEmptyGuidance)}的标签。请重置标签视图或调整搜索与类型筛选。`;
```

- [ ] **Step 5: Add derived selected-tag object guidance text**

In `frontend/src/world/WorldTagsPanel.tsx`, add this immediately after `detailViewSummary`:

```ts
const detailEmptyGuidance = [
  normalizedDetailSearchQuery ? `搜索「${detailSearchQuery.trim()}」` : '',
  detailObjectTypeFilter !== 'all' ? `类型：${objectTypeFilterLabel(detailObjectTypeFilter)}` : '',
].filter(Boolean);
const detailFilteredEmptyText = `没有匹配${constraintText(detailEmptyGuidance)}的对象。请重置对象视图或调整搜索与类型筛选。`;
```

- [ ] **Step 6: Replace generic filtered-empty copy**

In `frontend/src/world/WorldTagsPanel.tsx`, replace:

```tsx
{tags.length > 0 && visibleTags.length === 0 && !error && <p className="ink-muted">当前搜索没有匹配标签。</p>}
```

with:

```tsx
{tags.length > 0 && visibleTags.length === 0 && !error && <p className="ink-muted">{tagFilteredEmptyText}</p>}
```

Then replace:

```tsx
) : filteredObjects.length === 0 ? (
  <p className="ink-muted">当前筛选下没有对象。</p>
) : (
```

with:

```tsx
) : filteredObjects.length === 0 ? (
  <p className="ink-muted">{detailFilteredEmptyText}</p>
) : (
```

- [ ] **Step 7: Run frontend GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx
```

Expected: all panel tests pass.

---

### Task 2: Final verification, docs status, commit, and merge

**Files:**
- Modified frontend panel files and MVP41 docs.

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

Append implementation status sections to the MVP41 spec and plan after verification, recording RED/GREEN and command results.

- [ ] **Step 5: Commit**

Run:

```bash
git -C /opt/WorldSim-Writer status --short
git -C /opt/WorldSim-Writer add frontend/src/world/WorldTagsPanel.tsx frontend/src/world/WorldTagsPanel.test.tsx docs/superpowers/specs/2026-06-01-mvp41-tag-empty-guidance-design.md docs/superpowers/plans/2026-06-01-mvp41-tag-empty-guidance.md
git -C /opt/WorldSim-Writer commit -m "feat: clarify tag empty states"
```

- [ ] **Step 6: Fast-forward merge to main without push**

Run:

```bash
git -C /opt/WorldSim-Writer checkout main
git -C /opt/WorldSim-Writer merge --ff-only feat/mvp41-tag-empty-guidance
```

Do not push.

- [ ] **Step 7: Post-merge verification**

Repeat backend targeted tests, frontend targeted tests, and frontend build from Steps 1-3 on `main`.

Expected: all pass after merge.

## Self-review

- This plan covers all MVP41 acceptance criteria.
- No placeholders remain.
- Types and labels are consistent with the existing component and tests.
- Empty-state guidance only reads local view state; it does not call write APIs.
- No backend, database, canon, world-version, or EventLog behavior changes are introduced.

## Execution status

Implemented on `feat/mvp41-tag-empty-guidance` using TDD. RED was observed in `WorldTagsPanel.test.tsx` for missing context-aware filtered-empty guidance; GREEN was observed after adding local constraint text derivation and replacing generic filtered-empty messages for tag-list and selected-tag object filtered-empty states. Pre-merge backend targeted tests, frontend targeted tests, and frontend build passed. An initial frontend verification command failed from the backend directory with missing `package.json`; rerunning from `/opt/WorldSim-Writer/frontend` passed.
