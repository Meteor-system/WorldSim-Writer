# MVP32 Tag Delete Confirmation 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This repository run is explicitly inline-only: do not use dynamic workflows, subagents, or the code-review subagent.

**Goal:** Add a two-step confirmation before deleting selected tags to prevent accidental metadata loss.

**Architecture:** Frontend-only safety enhancement in `WorldTagsPanel`. The component keeps the existing `onDeleteTag` prop and backend behavior, but only calls it after a local confirmation state is armed and confirmed; no backend route, schema, database, canon, world-version, or EventLog behavior changes.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, Vite; existing FastAPI pytest tag/search suites for regression verification.

---

## File structure

- Modify `frontend/src/world/WorldTagsPanel.test.tsx` — add RED/GREEN coverage for tag delete confirmation.
- Modify `frontend/src/world/WorldTagsPanel.tsx` — add confirmation state, warning UI, confirm/cancel behavior, and reset behavior.
- Create `docs/superpowers/specs/2026-05-31-mvp32-tag-delete-confirmation-design.md` — MVP32 design spec.
- Create `docs/superpowers/plans/2026-05-31-mvp32-tag-delete-confirmation.md` — implementation plan.

---

### Task 1: Frontend tag delete confirmation TDD

**Files:**
- Test: `frontend/src/world/WorldTagsPanel.test.tsx`
- Modify: `frontend/src/world/WorldTagsPanel.tsx`

- [ ] **Step 1: Write failing frontend tests**

In `frontend/src/world/WorldTagsPanel.test.tsx`, update the existing `creates, assigns, bulk assigns, unassigns, and deletes tags` test so the final delete step confirms deletion:

```tsx
await user.click(screen.getByRole('button', { name: '删除当前标签' }));
expect(onDeleteTag).not.toHaveBeenCalled();
expect(await screen.findByText('确认删除标签「灯塔线」？这会移除 1 个对象关联。')).toBeInTheDocument();
await user.click(screen.getByRole('button', { name: '确认删除标签' }));
expect(onDeleteTag).toHaveBeenCalledWith(7, 3);
```

Add these tests before the existing empty/error state test:

```tsx
it('cancels selected tag deletion before calling the API', async () => {
  const user = userEvent.setup();
  const onDeleteTag = vi.fn().mockResolvedValue(undefined);
  renderPanel({ onDeleteTag });

  await screen.findByText('灯塔线');
  await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
  await screen.findByText('许砚');
  await user.click(screen.getByRole('button', { name: '删除当前标签' }));
  expect(await screen.findByText('确认删除标签「灯塔线」？这会移除 1 个对象关联。')).toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: '取消删除' }));

  expect(onDeleteTag).not.toHaveBeenCalled();
  expect(screen.queryByText('确认删除标签「灯塔线」？这会移除 1 个对象关联。')).not.toBeInTheDocument();
});

it('resets pending tag deletion when loading another tag', async () => {
  const user = userEvent.setup();
  const targetDetail: TagDetailResponse = {
    tag: { ...targetTag, assignment_count: 0, object_type_counts: {} },
    objects: [],
  };
  const onLoadTag = vi.fn()
    .mockResolvedValueOnce(detailResponse)
    .mockResolvedValueOnce(targetDetail);
  const onDeleteTag = vi.fn().mockResolvedValue(undefined);
  renderPanel({ onLoadTag, onDeleteTag });

  await screen.findByText('灯塔线');
  await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
  await screen.findByText('许砚');
  await user.click(screen.getByRole('button', { name: '删除当前标签' }));
  expect(await screen.findByText('确认删除标签「灯塔线」？这会移除 1 个对象关联。')).toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: '查看 主线归档' }));

  expect(await screen.findByText('这个标签还没有关联对象。')).toBeInTheDocument();
  expect(screen.queryByText('确认删除标签「灯塔线」？这会移除 1 个对象关联。')).not.toBeInTheDocument();
  expect(onDeleteTag).not.toHaveBeenCalled();
});
```

- [ ] **Step 2: Run frontend RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx
```

Expected: tests fail because the current delete button calls `onDeleteTag` immediately and no confirmation UI exists.

- [ ] **Step 3: Add confirmation state and reset behavior**

In `frontend/src/world/WorldTagsPanel.tsx`, add state near other selected-detail UI state:

```ts
const [deleteConfirming, setDeleteConfirming] = useState(false);
```

In `loadTag()`, after clearing notices, add:

```ts
setDeleteConfirming(false);
```

In `deleteSelectedTag()`, after clearing detail, add:

```ts
setDeleteConfirming(false);
```

- [ ] **Step 4: Change delete button and add confirmation UI**

Replace the selected-tag header delete button:

```tsx
<button className="secondary-button" disabled={saving} onClick={deleteSelectedTag}>删除当前标签</button>
```

with:

```tsx
<button className="secondary-button" disabled={saving} onClick={() => setDeleteConfirming(true)}>删除当前标签</button>
```

After the selected-tag header and before the edit form, add:

```tsx
{deleteConfirming && (
  <div className="rounded-2xl border border-red-900/20 bg-red-50/70 p-4">
    <p className="text-sm font-bold text-red-900">确认删除标签「{detail.tag.name}」？这会移除 {detail.tag.assignment_count} 个对象关联。</p>
    <div className="mt-3 flex flex-wrap gap-2">
      <button className="secondary-button text-sm" disabled={saving} onClick={deleteSelectedTag}>确认删除标签</button>
      <button className="secondary-button text-sm" disabled={saving} onClick={() => setDeleteConfirming(false)}>取消删除</button>
    </div>
  </div>
)}
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
- Modified frontend panel files and MVP32 docs.

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

Append implementation status sections to the MVP32 spec and plan after verification, recording RED/GREEN and command results.

- [ ] **Step 5: Commit**

Run:

```bash
git -C /opt/WorldSim-Writer status --short
git -C /opt/WorldSim-Writer add frontend/src/world/WorldTagsPanel.tsx frontend/src/world/WorldTagsPanel.test.tsx docs/superpowers/specs/2026-05-31-mvp32-tag-delete-confirmation-design.md docs/superpowers/plans/2026-05-31-mvp32-tag-delete-confirmation.md
git -C /opt/WorldSim-Writer commit -m "feat: confirm tag deletion"
```

- [ ] **Step 6: Fast-forward merge to main without push**

Run:

```bash
git -C /opt/WorldSim-Writer checkout main
git -C /opt/WorldSim-Writer merge --ff-only feat/mvp32-tag-delete-confirmation
```

Do not push.

- [ ] **Step 7: Post-merge verification**

Repeat backend targeted tests, frontend targeted tests, and frontend build from Steps 1-3 on `main`.

Expected: all pass after merge.

## Self-review

- This plan covers all MVP32 acceptance criteria.
- No placeholders remain.
- Types and labels are consistent with the existing component and tests.
- Delete confirmation only delays the existing delete prop call; it does not change backend semantics.
- No backend, database, canon, world-version, or EventLog behavior changes are introduced.

## Execution status

Implemented on `feat/mvp32-tag-delete-confirmation` using TDD. RED was observed in `WorldTagsPanel.test.tsx` for immediate deletion without confirmation; GREEN was observed after adding confirmation state, warning text, explicit confirm/cancel actions, and reset behavior when switching tags. Pre-merge backend targeted tests, frontend targeted tests, and frontend build passed.
