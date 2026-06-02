# Archived World Open State Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This run explicitly forbids subagents and dynamic workflows, so execute inline with strict TDD.

**Goal:** Make opened archived worlds visibly paused and provide a primary restore-writing action before normal writing actions.

**Architecture:** Frontend-only UI state in `WorldPage`. Add a small archived pause card and conditionally hide active writing launch actions while `world.status === 'archived'`; reuse existing `toggleWorldArchiveStatus()` and `returnToBookshelf()` handlers.

**Tech Stack:** React, TypeScript, Vite, Vitest, React Testing Library.

---

## File Structure

- Modify: `frontend/src/world/WorldPage.test.tsx`
  - Add archived open-state tests under `WorldPage bookshelf`.
- Modify: `frontend/src/world/WorldPage.tsx`
  - Add `ArchivedWorldPauseCard` and conditionally render it for archived worlds.
- Create: `docs/superpowers/specs/2026-06-01-archived-world-open-state-design.md`
  - Design spec for this MVP.
- Create: `docs/superpowers/plans/2026-06-01-archived-world-open-state.md`
  - This implementation plan.

---

### Task 1: Add RED tests

**Files:**
- Modify: `frontend/src/world/WorldPage.test.tsx`

- [ ] **Step 1: Add archived-open paused-state test**

Add under `describe('WorldPage bookshelf', ...)`:

```ts
it('shows a paused state when opening an archived world', async () => {
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
  expect(screen.getByText('这本小说已从活跃创作中移出。快照、章节、伏笔和导出都还在。恢复写作后再进入创作台。')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '恢复写作' })).toBeInTheDocument();
  expect(screen.queryByText('First Chapter Launchpad')).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '进入创作台' })).not.toBeInTheDocument();
});
```

- [ ] **Step 2: Add restore-writing test**

```ts
it('restores writing from the archived paused state', async () => {
  const user = userEvent.setup();
  vi.mocked(apiRequest).mockReset();
  vi.mocked(apiRequest)
    .mockResolvedValueOnce([
      { id: 7, title: '青岚城', genre_template: 'xianxia', truth_canon: '灵脉正在衰退。', truth_canon_version: 1, world_version: 2, status: 'archived', tone_profile: {}, current_characters: [], current_foreshadows: [], current_relations: [] },
    ])
    .mockResolvedValueOnce(archivedWorld);
  vi.mocked(updateWorldStatus).mockResolvedValueOnce({ ...world, status: 'active' });

  render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

  await user.click(await screen.findByRole('button', { name: '打开 青岚城' }));
  await user.click(await screen.findByRole('button', { name: '恢复写作' }));

  expect(updateWorldStatus).toHaveBeenCalledWith(7, { status: 'active' });
  expect(await screen.findByText('First Chapter Launchpad')).toBeInTheDocument();
  expect(screen.queryByText('已归档：写作已暂停')).not.toBeInTheDocument();
});
```

- [ ] **Step 3: Run focused test and verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: new tests fail because the archived pause card does not exist and active writing actions still show.

---

### Task 2: Implement minimal GREEN

**Files:**
- Modify: `frontend/src/world/WorldPage.tsx`

- [ ] **Step 1: Add `ArchivedWorldPauseCard` above `WorldPage`**

Add:

```tsx
type ArchivedWorldPauseCardProps = {
  archiveLoading: boolean;
  onReturnToBookshelf: () => void;
  onRestoreWriting: () => void;
};

function ArchivedWorldPauseCard({ archiveLoading, onReturnToBookshelf, onRestoreWriting }: ArchivedWorldPauseCardProps) {
  return (
    <article className="mt-8 rounded-2xl border border-amber-900/15 bg-amber-100/70 p-4 shadow-sm">
      <p className="chapter-kicker">Archived Novel</p>
      <h2 className="mt-2 text-2xl font-black text-[#34210f]">已归档：写作已暂停</h2>
      <p className="manuscript mt-2 text-sm text-[#5e3b1c]">这本小说已从活跃创作中移出。快照、章节、伏笔和导出都还在。恢复写作后再进入创作台。</p>
      <div className="mt-4 flex flex-wrap gap-2">
        <button className="secondary-button" type="button" onClick={onReturnToBookshelf}>返回作品书架</button>
        <button className="primary-button" type="button" disabled={archiveLoading} onClick={onRestoreWriting}>
          {archiveLoading ? '恢复中...' : '恢复写作'}
        </button>
      </div>
    </article>
  );
}
```

- [ ] **Step 2: Conditionally render active vs archived action area**

Replace the unconditional `FirstChapterLaunchpad` with:

```tsx
{world.status === 'archived' ? (
  <ArchivedWorldPauseCard
    archiveLoading={archiveLoading}
    onReturnToBookshelf={returnToBookshelf}
    onRestoreWriting={toggleWorldArchiveStatus}
  />
) : (
  <FirstChapterLaunchpad
    world={world}
    nextChapter={nextStoryArcChapter}
    arcLoading={arcLoading}
    onGenerateArc={runStoryArcPlanner}
    onLaunchChapter={launchStoryArcChapter}
  />
)}
```

Wrap the main action row so it only appears for active worlds:

```tsx
{world.status !== 'archived' && (
  <div className="mt-8 flex flex-wrap gap-3">
    ...existing buttons...
  </div>
)}
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
cd /opt/WorldSim-Writer && git add docs/superpowers/specs/2026-06-01-archived-world-open-state-design.md docs/superpowers/plans/2026-06-01-archived-world-open-state.md frontend/src/world/WorldPage.test.tsx frontend/src/world/WorldPage.tsx && git commit -m "fix: clarify opened archived world state"
```

Expected: commit succeeds. Do not push and do not merge.
