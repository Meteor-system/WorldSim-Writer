# Archived NCC Actions Design

## Goal

Prevent archived novels from launching Studio or selecting next-chapter writing goals through the Narrative Control Center while keeping read-only context visible.

## Why this is the next small MVP

Recent archive work made archived novels visible on the bookshelf, prevented auto-opening a single archived novel, added a paused-state card, and added direct restore from the bookshelf. One remaining gap is the Narrative Control Center: an opened archived world no longer shows the main overview `进入创作台`, but the `下一章准备台` panel can still show `用作下一章目标` and `进入创作台并使用此目标`.

That creates a mixed model: the top of the page says writing is paused, while a lower panel still invites writing continuation. This fix makes archived worlds consistently read-only until restored.

## Scope

### In scope

- For archived worlds, keep Narrative Control Center read-only panels visible.
- Hide `下一章准备台` writing action buttons for archived worlds.
- Show a short paused/read-only hint near the Narrative Control Center.
- Keep active worlds unchanged.
- Do not change backend behavior.

### Out of scope

- Backend authorization or endpoint changes.
- Hiding the whole Narrative Control Center.
- Disabling all manager tabs globally.
- Changing archive status semantics.
- New routing or persisted state.

## UX behavior

When `world.status === 'archived'` on the overview tab:

- The paused card remains the primary callout.
- Narrative Control Center panels still load so users can inspect history, health, open threads, and next-chapter context.
- A read-only notice appears near the Narrative Control Center heading:
  - `已归档小说为只读模式；恢复写作后才能把建议带入创作台。`
- `NextChapterPrepPanel` still displays suggested context, priority characters, priority foreshadows, and warnings.
- `NextChapterPrepPanel` does not render:
  - `用作下一章目标`
  - `进入创作台并使用此目标`

For active worlds, the existing NCC buttons and selected-goal behavior remain unchanged.

## Implementation notes

- In `WorldPage.tsx`, derive `const isArchivedWorld = world.status === 'archived'` after `nextStoryArcChapter`.
- Use `isArchivedWorld` for existing archived/active conditionals.
- In the Narrative Control Center heading block, render the read-only notice when archived.
- Pass `undefined` for `onUseContext` and `onEnterStudioWithContext` to `NextChapterPrepPanel` when archived.
- No changes are needed in `NextChapterPrepPanel` because it already hides buttons when handlers are absent.

## TDD plan

Add one regression test in `frontend/src/world/WorldPage.test.tsx`:

1. Open an archived world from the bookshelf.
2. Assert the archived read-only notice appears near NCC.
3. Assert `下一章准备台` still renders.
4. Assert `用作下一章目标` and `进入创作台并使用此目标` are not visible.
5. Assert the existing `恢复写作` action is visible.

Run RED, implement the minimal conditional handler changes, then run GREEN.

## Acceptance criteria

- Archived worlds cannot launch Studio from NCC actions.
- Archived worlds still expose read-only NCC context.
- Active-world NCC behavior remains unchanged.
- Targeted WorldPage tests, frontend build, full frontend tests, and `git diff --check` pass before commit.
