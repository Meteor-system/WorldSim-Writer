# Archived World Startup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This run explicitly forbids subagents and dynamic workflows, so execute inline with strict TDD.

**Goal:** Show the bookshelf instead of auto-opening a single archived world on startup.

**Architecture:** Frontend-only conditional change in `WorldPage.loadWorld()`. Reuse the existing bookshelf, archived grouping, and open-from-shelf behavior.

**Tech Stack:** React, TypeScript, Vite, Vitest, React Testing Library.

---

## File Structure

- Modify: `frontend/src/world/WorldPage.test.tsx`
  - Add a regression test for a single archived world startup.
- Modify: `frontend/src/world/WorldPage.tsx`
  - Change single-world auto-open logic to skip archived worlds.
- Create: `docs/superpowers/specs/2026-06-01-archived-world-startup-design.md`
  - Design spec for this MVP.
- Create: `docs/superpowers/plans/2026-06-01-archived-world-startup.md`
  - This plan.

---

### Task 1: Add RED test

**Files:**
- Modify: `frontend/src/world/WorldPage.test.tsx`

- [ ] **Step 1: Add archived startup test**

Add under `describe('WorldPage bookshelf', ...)`, near the single-world tests:

```ts
it('shows the bookshelf instead of auto-opening a single archived world', async () => {
  const user = userEvent.setup();
  vi.mocked(apiRequest).mockReset();
  vi.mocked(apiRequest)
    .mockResolvedValueOnce([
      { id: 7, title: '青岚城', genre_template: 'xianxia', truth_canon: '灵脉正在衰退。', truth_canon_version: 1, world_version: 2, status: 'archived', tone_profile: {}, current_characters: [], current_foreshadows: [], current_relations: [] },
    ])
    .mockResolvedValueOnce(archivedWorld);

  render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

  expect(await screen.findByText('作品书架')).toBeInTheDocument();
  expect(screen.queryByText('World Canon')).not.toBeInTheDocument();
  expect(screen.getByText('已归档')).toBeInTheDocument();
  expect(screen.getByText('青岚城')).toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: '打开 青岚城' }));

  expect(await screen.findByText('World Canon')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '取消归档当前小说' })).toBeInTheDocument();
});
```

- [ ] **Step 2: Run focused test and verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: the new test fails because `loadWorld()` auto-opens the sole archived world.

---

### Task 2: Implement minimal GREEN

**Files:**
- Modify: `frontend/src/world/WorldPage.tsx`

- [ ] **Step 1: Change single-world auto-open condition**

Replace:

```tsx
} else if (loadedWorlds.length === 1) {
  await openWorld(loadedWorlds[0].id);
} else {
  setWorld(null);
  setShowCreationForm(false);
}
```

with:

```tsx
} else if (loadedWorlds.length === 1 && loadedWorlds[0].status !== 'archived') {
  await openWorld(loadedWorlds[0].id);
} else {
  setWorld(null);
  setShowCreationForm(false);
}
```

- [ ] **Step 2: Run focused test and verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: `WorldPage.test.tsx` passes.

---

### Task 3: Verification and commit

**Files:**
- Verify changed docs, test, and implementation.

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

Expected: no whitespace errors. Do not stage `.hermes/plans/*` or `backend/worldsim-dev.db`.

- [ ] **Step 4: Commit relevant files only**

```bash
cd /opt/WorldSim-Writer && git add docs/superpowers/specs/2026-06-01-archived-world-startup-design.md docs/superpowers/plans/2026-06-01-archived-world-startup.md frontend/src/world/WorldPage.test.tsx frontend/src/world/WorldPage.tsx && git commit -m "fix: show bookshelf for archived single world"
```

Expected: commit succeeds. Do not push and do not merge.
