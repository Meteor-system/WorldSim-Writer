# Archived World Startup Design

## Goal

Stabilize the bookshelf/archive MVP by respecting archive intent on app startup: if the user has exactly one world and it is archived, show the bookshelf instead of auto-opening that archived novel.

## Why this is the next MVP slice

The README pause/switch workflow says users should snapshot/export, return to `作品书架`, archive the paused novel, then create or open another novel. Current startup logic auto-opens any single world, including archived worlds. That makes an archived novel feel active again and hides the bookshelf entry point the user needs to create or restore another project.

This is a small frontend-only fix that strengthens the existing MVP loop without touching backend archive semantics.

## Scope

### In scope

- Keep auto-opening a single active world.
- Do not auto-open a single archived world.
- For a single archived world, show `作品书架` with the archived world in the `已归档` group and the `创建新小说` action visible.
- Keep opening archived worlds from the bookshelf possible.
- Keep archive/restore, First Chapter Launchpad, Story Arc, NCC, Studio, snapshots, and export behavior unchanged.

### Out of scope

- Backend changes.
- Changing `World.status` values.
- Hiding archived worlds entirely.
- Adding URL routing or persisted UI preferences.
- Changing multi-world bookshelf behavior.

## UX behavior

Startup rules after `/worlds` loads:

1. `loadedWorlds.length === 0`
   - Show creation form as today.
2. `loadedWorlds.length === 1 && loadedWorlds[0].status !== 'archived'`
   - Auto-open the one active world as today.
3. `loadedWorlds.length === 1 && loadedWorlds[0].status === 'archived'`
   - Show bookshelf instead of opening the world.
4. `loadedWorlds.length > 1`
   - Show bookshelf as today.

The single archived world card remains openable from the archived group. If user opens it, the existing archive card lets them `取消归档当前小说`.

## Implementation notes

Current code in `frontend/src/world/WorldPage.tsx`:

```tsx
} else if (loadedWorlds.length === 1) {
  await openWorld(loadedWorlds[0].id);
} else {
  setWorld(null);
  setShowCreationForm(false);
}
```

Change it to only auto-open when the sole world is not archived.

## TDD plan

Add tests to `frontend/src/world/WorldPage.test.tsx` under `WorldPage bookshelf`:

1. `shows the bookshelf instead of auto-opening a single archived world`
   - Mock `/worlds` as one `status: 'archived'` world.
   - Assert `作品书架` appears.
   - Assert `World Canon` is not present.
   - Assert the archived world appears in the `已归档` shelf and can still be opened.

2. Keep existing `still auto-opens a single existing world` test for active/non-archived world.

Run RED, implement the conditional change, then run GREEN.

## Acceptance criteria

- A single active world still auto-opens.
- A single archived world shows the bookshelf on startup.
- Archived single worlds remain openable from the bookshelf.
- Targeted `WorldPage` tests pass.
- Frontend build and full frontend tests pass before commit.
- `git diff --check` passes before commit.
