# Bookshelf Direct Restore Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This run explicitly forbids subagents and dynamic workflows, so execute inline with strict TDD.

**Goal:** Add a direct restore-writing action to archived bookshelf cards.

**Architecture:** Frontend-only change in `WorldPage`. Add a handler that reuses `updateWorldStatus`, updates local bookshelf state, and renders a restore button in archived cards without opening the world.

**Tech Stack:** React, TypeScript, Vite, Vitest, React Testing Library.

---

## File Structure

- Modify: `frontend/src/world/WorldPage.test.tsx`
  - Add a bookshelf regression test for direct archived-world restore.
- Modify: `frontend/src/world/WorldPage.tsx`
  - Add `restoreArchivedWorldFromShelf()` and a restore button in archived shelf cards.
- Create: `docs/superpowers/specs/2026-06-01-bookshelf-direct-restore-design.md`
  - Design spec for this MVP.
- Create: `docs/superpowers/plans/2026-06-01-bookshelf-direct-restore.md`
  - This implementation plan.

---

### Task 1: Add RED test

**Files:**
- Modify: `frontend/src/world/WorldPage.test.tsx`

- [ ] **Step 1: Add bookshelf direct-restore test**

Add under `describe('WorldPage bookshelf', ...)`:

```ts
it('restores an archived world directly from the bookshelf', async () => {
  const user = userEvent.setup();
  vi.mocked(apiRequest).mockReset();
  vi.mocked(apiRequest).mockResolvedValueOnce([
    { id: 7, title: '青岚城', genre_template: 'xianxia', truth_canon: '灵脉正在衰退。', truth_canon_version: 1, world_version: 2, status: 'archived', tone_profile: {}, current_characters: [], current_foreshadows: [], current_relations: [] },
    { id: 8, title: '星舰余烬', genre_template: 'sci_fi', truth_canon: '星舰仍在航行。', truth_canon_version: 1, world_version: 1, status: 'active', tone_profile: {}, current_characters: [], current_foreshadows: [], current_relations: [] },
  ]);
  vi.mocked(updateWorldStatus).mockResolvedValueOnce({ ...archivedWorld, status: 'active' });

  render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

  expect(await screen.findByText('作品书架')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: '恢复写作 青岚城' }));

  expect(updateWorldStatus).toHaveBeenCalledWith(7, { status: 'active' });
  expect(await screen.findByText('v2 · xianxia · active')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '打开 青岚城' })).toBeInTheDocument();
  expect(screen.getByText('暂无归档小说。')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run focused test and verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: the new test fails because `恢复写作 青岚城` does not exist on archived bookshelf cards.

---

### Task 2: Implement minimal GREEN

**Files:**
- Modify: `frontend/src/world/WorldPage.tsx`

- [ ] **Step 1: Add restore handler after `openWorldFromShelf()`**

```tsx
async function restoreArchivedWorldFromShelf(worldId: number) {
  setArchiveLoading(true);
  setError('');
  try {
    const updated = await updateWorldStatus(worldId, { status: 'active' });
    setWorlds((current) => current.map((item) => (item.id === updated.id ? { ...item, status: updated.status } : item)));
  } catch (err) {
    setError(err instanceof Error ? err.message : '恢复写作失败');
  } finally {
    setArchiveLoading(false);
  }
}
```

- [ ] **Step 2: Add restore button to archived cards**

Inside `archivedWorlds.map(...)`, render:

```tsx
<div className="mt-3 flex flex-wrap gap-2">
  <button className="secondary-button" type="button" onClick={() => void openWorldFromShelf(item.id)}>打开 {item.title}</button>
  <button className="primary-button" type="button" disabled={archiveLoading} onClick={() => void restoreArchivedWorldFromShelf(item.id)}>恢复写作 {item.title}</button>
</div>
```

- [ ] **Step 3: Run focused test and verify GREEN**

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
cd /opt/WorldSim-Writer && git add docs/superpowers/specs/2026-06-01-bookshelf-direct-restore-design.md docs/superpowers/plans/2026-06-01-bookshelf-direct-restore.md frontend/src/world/WorldPage.test.tsx frontend/src/world/WorldPage.tsx && git commit -m "fix: restore archived worlds from bookshelf"
```

Expected: commit succeeds. Do not push and do not merge.
