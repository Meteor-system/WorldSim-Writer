# Single-World Bookshelf Gateway Design

## Goal

Close a usability gap in the bookshelf/archive MVP: when a user has exactly one world, the app auto-opens it, but the current world page hides `返回作品书架`. That preserves the old single-world happy path, but it also prevents a cold-start user from reaching the bookshelf to create a second novel or manage the current one from the shelf.

This MVP keeps single-world auto-open behavior while adding a lightweight bookshelf gateway from the opened world.

## Why this is the next best slice

- README now documents `Return to 作品书架` as part of pausing/switching novels.
- `WorldSim-Writer.md` emphasizes first-day usability and workflows that answer what the user should do next.
- Current code only renders `返回作品书架` on the world page when `worlds.length > 1`, so a user with one auto-opened world cannot discover the bookshelf or create another novel without an indirect path.
- The fix is frontend-only, low-risk, and directly strengthens the already-committed bookshelf/archive MVP.

## Scope

### In scope

- Always expose a `返回作品书架` control from the current world overview when at least one world exists.
- Preserve single-world auto-open on initial load.
- On the bookshelf, keep the existing `创建新小说` entry so the single-world user can create a second novel after returning.
- Keep archive/restore, Story Arc, First Chapter Launchpad, NCC, Studio, snapshots, and export behavior unchanged.
- Add regression tests covering the single-world gateway and creation path from the returned bookshelf.

### Out of scope

- Changing the initial auto-open behavior for a single world.
- Adding routing or URL state.
- Backend/API changes.
- Changing archive semantics.
- Changing bookshelf grouping rules.

## UX

In the `书架归档` card on the world overview, show `返回作品书架` whenever `worlds.length > 0`.

Existing multi-world behavior remains unchanged. For a single-world account:

1. App auto-opens the one world.
2. User sees `返回作品书架` in the archive card.
3. Clicking it shows `作品书架` with the one active world and `创建新小说`.
4. Clicking `创建新小说` opens the existing creation form.
5. The creation form still offers `返回作品书架` because `worlds.length > 0`.

## Implementation notes

Current code in `frontend/src/world/WorldPage.tsx` uses:

```tsx
{worlds.length > 1 && <button className="secondary-button" type="button" onClick={returnToBookshelf}>返回作品书架</button>}
```

Change the condition to `worlds.length > 0`. This is intentionally small and avoids changing the data model.

## TDD plan

Add tests in `frontend/src/world/WorldPage.test.tsx` before implementation:

1. `returns from a single auto-opened world to the bookshelf`
   - Use default single-world mock.
   - Assert auto-open still happens.
   - Click `返回作品书架`.
   - Assert `作品书架` appears and the world card is visible.

2. `opens the creation form from a single-world bookshelf`
   - Use default single-world mock.
   - Click `返回作品书架`.
   - Click `创建新小说`.
   - Assert `创建世界工坊` and `返回作品书架` appear.

Run RED, implement minimal condition change, then run GREEN.

## Acceptance criteria

- Single-world accounts still auto-open the world.
- Single-world accounts can return to `作品书架` from the opened world.
- From that bookshelf, users can start creating another novel.
- Multi-world bookshelf behavior remains green.
- Targeted `WorldPage` tests, frontend build, full frontend tests, and `git diff --check` pass before commit.
