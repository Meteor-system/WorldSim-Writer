# Archived World Bible Read-Only Design

## Goal

Make opened archived worlds consistently read-only across World Bible manager tabs until the user restores writing.

## Why this is the next small MVP

Recent archive work blocked primary overview writing actions, made Narrative Control Center actions read-only, and provided restore paths from both the paused page and bookshelf. One remaining inconsistency is the World Bible manager tabs. If a user opens an archived novel and switches to characters, relations, or foreshadows, formal world-state edit actions can still appear.

That breaks the archive mental model: archived should mean paused/read-only, not just hidden Studio buttons. This small frontend-only fix keeps archived context inspectable while preventing accidental formal edits from the UI.

## Scope

### In scope

- Add a read-only mode to `CharacterManager`, `RelationManager`, and `ForeshadowManager`.
- For archived worlds, show a consistent read-only notice in each manager.
- Hide manager actions that formally mutate world state:
  - Character: `编辑`
  - Relation: `+ 新增关系`, relation `编辑`
  - Foreshadow: `+ 新增伏笔`, status advance, `编辑`, `放弃伏笔`, `删除`, drag/drop mutation
- Keep non-mutating inspection controls available, including foreshadow filters, list/kanban view, and timeline expansion.
- Pass read-only mode from `WorldPage` when `world.status === 'archived'`.

### Out of scope

- Backend authorization changes.
- Disabling snapshot/export/history/search read-only tools.
- Changing archive semantics or status values.
- Large component refactors.

## UX behavior

For archived worlds:

- Manager tabs still load and display current state.
- Each manager shows:
  - `已归档小说为只读模式；恢复写作后才能编辑世界资料。`
- No formal edit/create/delete/advance controls are visible.
- Foreshadow timeline expansion remains available because it is read-only.

For active worlds:

- Existing manager warnings and edit actions remain unchanged.

## Implementation notes

- Add an optional `readOnly?: boolean` prop to each manager component.
- In each component, render the archived read-only notice instead of the existing formal-edit warning when `readOnly` is true.
- Guard mutating controls with `!readOnly`.
- In `ForeshadowManager`, set `draggable={!readOnly}` and ignore `dropOnStatus()` when read-only.
- In `WorldPage.tsx`, pass `readOnly={isArchivedWorld}` to all three manager tabs.

## TDD plan

Add one regression test in `frontend/src/world/WorldPage.test.tsx`:

1. Open an archived world.
2. Switch to `角色管理` and assert:
   - read-only notice is visible;
   - `编辑` is not visible.
3. Switch to `关系管理` and assert:
   - read-only notice is visible;
   - `+ 新增关系` is not visible.
4. Switch to `伏笔账本` and assert:
   - read-only notice is visible;
   - `+ 新增伏笔`, `放弃伏笔`, and `删除` are not visible;
   - read-only `展开时间线` remains visible.

Run RED, implement minimal read-only props, then run GREEN.

## Acceptance criteria

- Archived worlds are read-only across World Bible manager tabs.
- Active-world manager behavior remains unchanged.
- Read-only inspection still works for archived worlds.
- Targeted WorldPage tests, frontend build, full frontend tests, and `git diff --check` pass before commit.
