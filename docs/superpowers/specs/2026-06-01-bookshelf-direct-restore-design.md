# Bookshelf Direct Restore Design

## Goal

Let users restore an archived novel directly from the bookshelf without first opening the paused novel page.

## Why this is the next small MVP

Recent archive work made archived novels visible, prevented auto-opening a single archived world, and clarified the paused state after opening one. A remaining friction point is the bookshelf itself: the empty active shelf says users can restore archived works, but each archived card only offers `打开`. Users must open the paused world, find the restore action, then return to active writing.

A direct `恢复写作` action on archived bookshelf cards closes that loop. It is small, frontend-only, and reinforces archive as a reversible status marker rather than a dead-end shelf.

## Scope

### In scope

- Add a `恢复写作 <title>` action to each archived bookshelf card.
- The action calls the existing `updateWorldStatus(worldId, { status: 'active' })` API client.
- After success, update the local `worlds` list so the novel moves from `已归档` to `正在创作` without opening it.
- Keep the existing `打开 <title>` action for users who want to inspect the paused world first.
- Reuse existing loading/error state where practical.

### Out of scope

- Backend/API changes.
- Automatically opening the restored novel.
- Changing archive semantics.
- Bulk restore/archive actions.
- New global routing or persisted UI state.

## UX behavior

On the bookshelf:

- Archived cards show two actions:
  - `打开 <title>`
  - `恢复写作 <title>`
- Clicking `恢复写作 <title>`:
  - disables restore/archive actions while the request is in flight;
  - calls `updateWorldStatus(id, { status: 'active' })`;
  - moves the card into the `正在创作` section;
  - does not open the world automatically.
- If the restore request fails, the existing bookshelf alert area shows the error message or `恢复写作失败`.

## Implementation notes

- Add a small `restoreArchivedWorldFromShelf(worldId)` handler in `WorldPage.tsx`.
- Use `setWorlds()` to update only the restored world's `status` in local state.
- Render the restore button beside the existing open button inside `archivedWorlds.map(...)`.
- Do not touch backend code.

## TDD plan

Add tests in `frontend/src/world/WorldPage.test.tsx`:

1. Render a bookshelf with one active and one archived world, click `恢复写作 青岚城`, and assert:
   - `updateWorldStatus(7, { status: 'active' })` was called;
   - the archived novel appears in `正在创作` with status `active`;
   - the archived section shows `暂无归档小说。`.
2. Keep existing archived-open tests green.

Run RED, implement minimal UI/handler, then run GREEN.

## Acceptance criteria

- Archived novels can be restored directly from the bookshelf.
- Restoring does not open the novel automatically.
- The card moves from archived to active in the current UI.
- Existing archive/open/pause behavior remains green.
- Targeted WorldPage tests, frontend build, full frontend tests, and `git diff --check` pass before commit.
