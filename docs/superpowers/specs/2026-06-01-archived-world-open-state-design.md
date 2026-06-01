# Archived World Open State Design

## Goal

When a user opens an archived novel, make its paused status obvious and give a clear restore-writing action before normal writing actions.

## Why this is the next small MVP

Recent work added bookshelf switching and fixed startup behavior for archived single-world accounts. A remaining UX gap is that an opened archived world still looks almost identical to an active world: the first visible actions include First Chapter Launchpad, `进入创作台`, and story arc generation. That weakens the archive mental model. Since archive is intended as a reversible pause marker, the UI should state that writing is paused and guide users to restore before continuing.

This is a frontend-only, low-risk clarification that preserves all existing capabilities while preventing accidental continuation of paused work.

## Scope

### In scope

- Add an archived-world pause banner/card near the top of the world overview.
- For archived worlds, show copy explaining that the novel is paused and no data is deleted.
- Provide a primary `恢复写作` button that reuses the existing archive toggle action.
- Keep `返回作品书架` visible.
- Keep the existing `取消归档当前小说` button in the archive card as a secondary path.
- For active worlds, keep the existing First Chapter Launchpad and writing buttons unchanged.

### Out of scope

- Backend/API changes.
- Disabling all writing code paths globally.
- Changing archive status semantics.
- Removing the ability to open archived worlds.
- URL routing or persisted preferences.

## UX behavior

On the overview tab:

- If `world.status === 'archived'`:
  - Show a warm parchment card titled `已归档：写作已暂停`.
  - Copy: `这本小说已从活跃创作中移出。快照、章节、伏笔和导出都还在。恢复写作后再进入创作台。`
  - Actions:
    - `返回作品书架`
    - `恢复写作`
  - Do not show First Chapter Launchpad or the main `进入创作台` / `生成故事大纲` action row in the primary overview column.
- If active:
  - Show First Chapter Launchpad and existing action row exactly as today.

The archive card remains below, so advanced users can still see the archive/export guidance and the existing archive toggle state.

## Implementation notes

- Add a small `ArchivedWorldPauseCard` component in `WorldPage.tsx`.
- Reuse existing `returnToBookshelf()` and `toggleWorldArchiveStatus()` handlers.
- In the overview render:
  - conditionally render `ArchivedWorldPauseCard` when archived;
  - otherwise render `FirstChapterLaunchpad` and the main writing buttons.

## TDD plan

Add tests in `frontend/src/world/WorldPage.test.tsx`:

1. Open an archived world from the bookshelf and assert:
   - archived pause card is visible;
   - `恢复写作` button is visible;
   - First Chapter Launchpad is not visible;
   - `进入创作台` is not visible.
2. Click `恢复写作` and assert:
   - `updateWorldStatus(7, { status: 'active' })` is called;
   - active-only First Chapter Launchpad returns.

Run RED, implement minimal UI, then run GREEN.

## Acceptance criteria

- Opened archived worlds clearly look paused.
- Users can restore writing from the primary archived-state card.
- Active worlds keep the existing launchpad and writing actions.
- Existing bookshelf/archive behavior remains green.
- Targeted WorldPage tests, frontend build, full frontend tests, and `git diff --check` pass before commit.
