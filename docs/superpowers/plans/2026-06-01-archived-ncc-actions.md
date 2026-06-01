# Archived NCC Actions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This run explicitly forbids subagents and dynamic workflows, so execute inline with strict TDD.

**Goal:** Hide Narrative Control Center writing actions for archived worlds while keeping read-only context visible.

**Architecture:** Frontend-only conditional rendering in `WorldPage`. Reuse `NextChapterPrepPanel`'s existing optional handlers by omitting action callbacks when the world is archived.

**Tech Stack:** React, TypeScript, Vite, Vitest, React Testing Library.

---

## File Structure

- Modify: `frontend/src/world/WorldPage.test.tsx`
  - Add an archived-world NCC read-only regression test.
- Modify: `frontend/src/world/WorldPage.tsx`
  - Derive `isArchivedWorld`, show a read-only notice, and omit NCC write-action callbacks while archived.
- Create: `docs/superpowers/specs/2026-06-01-archived-ncc-actions-design.md`
  - Design spec for this MVP.
- Create: `docs/superpowers/plans/2026-06-01-archived-ncc-actions.md`
  - This implementation plan.

---

### Task 1: Add RED test

**Files:**
- Modify: `frontend/src/world/WorldPage.test.tsx`

- [ ] **Step 1: Add archived NCC read-only test**

Add under `describe('WorldPage Narrative Control Center', ...)`:

```ts
it('keeps Narrative Control Center read-only for archived worlds', async () => {
  const user = userEvent.setup();
  vi.mocked(apiRequest).mockReset();
  vi.mocked(apiRequest)
    .mockResolvedValueOnce([
      { id: 7, title: '青岚城', genre_template: 'xianxia', truth_canon: '灵脉正在衰退。', truth_canon_version: 1, world_version: 2, status: 'archived', tone_profile: {}, current_characters: [], current_foreshadows: [], current_relations: [] },
    ])
    .mockResolvedValueOnce(archivedWorld);

  render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

  await user.click(await screen.findByRole('button', { name: '打开 青岚城' }));

  expect(await screen.findByText('已归档：写作已暂停')).toBeInTheDocument();
  expect(await screen.findByText('Narrative Control Center')).toBeInTheDocument();
  expect(screen.getByText('已归档小说为只读模式；恢复写作后才能把建议带入创作台。')).toBeInTheDocument();
  expect(screen.getByText('下一章准备台')).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '用作下一章目标' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '进入创作台并使用此目标' })).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: '恢复写作' })).toBeInTheDocument();
});
```

- [ ] **Step 2: Run focused test and verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: the new test fails because archived worlds still expose NCC action buttons and no read-only notice exists.

---

### Task 2: Implement minimal GREEN

**Files:**
- Modify: `frontend/src/world/WorldPage.tsx`

- [ ] **Step 1: Derive archived-world boolean**

After `nextStoryArcChapter`, add:

```tsx
const isArchivedWorld = world?.status === 'archived';
```

- [ ] **Step 2: Replace repeated archived status checks**

Use `isArchivedWorld` in the overview action conditionals:

```tsx
{isArchivedWorld ? (...pause card...) : (...launchpad...)}
{!isArchivedWorld && (...main action row...)}
```

- [ ] **Step 3: Add NCC read-only notice**

Inside the Narrative Control Center heading block, after the description copy, add:

```tsx
{isArchivedWorld && (
  <p className="mt-3 rounded-2xl bg-amber-100/70 p-3 text-sm font-bold text-[#5e3b1c]">
    已归档小说为只读模式；恢复写作后才能把建议带入创作台。
  </p>
)}
```

- [ ] **Step 4: Omit NextChapterPrepPanel action callbacks while archived**

Change:

```tsx
onUseContext={setSelectedExecutionContext}
onEnterStudioWithContext={(context) => onEnterStudio(world, {
  initialChapterGoal: context.goal,
  executionContext: context,
})}
```

to:

```tsx
onUseContext={isArchivedWorld ? undefined : setSelectedExecutionContext}
onEnterStudioWithContext={isArchivedWorld ? undefined : (context) => onEnterStudio(world, {
  initialChapterGoal: context.goal,
  executionContext: context,
})}
```

- [ ] **Step 5: Run focused test and verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: all `WorldPage` tests pass.

---

### Task 3: Verification and commit

**Files:**
- Verify changed docs, tests, and implementation.

- [ ] **Step 1: Run frontend build**

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 2: Run full frontend tests**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test
```

Expected: all frontend tests pass.

- [ ] **Step 3: Run diff check and status review**

```bash
cd /opt/WorldSim-Writer && git diff --check && git status --short && git diff --stat
```

Expected: no whitespace errors; do not stage `backend/worldsim-dev.db` or unrelated `.hermes/plans/*`.

- [ ] **Step 4: Commit relevant files only**

```bash
cd /opt/WorldSim-Writer && git add docs/superpowers/specs/2026-06-01-archived-ncc-actions-design.md docs/superpowers/plans/2026-06-01-archived-ncc-actions.md frontend/src/world/WorldPage.test.tsx frontend/src/world/WorldPage.tsx && git commit -m "fix: keep archived ncc actions read-only"
```

Expected: commit succeeds. Do not push and do not merge.
