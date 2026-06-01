# Bookshelf Archive Switch MVP Design

## Goal

Give users a safe way to pause one novel, preserve it through snapshot/export, return to a bookshelf, and open or create another novel without deleting data.

## Current Context

The backend already stores multiple `World` rows per user and `GET /worlds` returns the owned worlds. `World.status` already exists, so archive state can be represented by setting status to `archived` without a migration. Snapshot/export already exists through `WorldArchivePanel`: users can create immutable world snapshots and download a Markdown ZIP from `/worlds/{world_id}/export/markdown`.

## Recommended User Workflow

1. Open the current novel.
2. In `World Archive`, create a world snapshot.
3. Export the Markdown archive and download the ZIP.
4. Return to the bookshelf.
5. Archive the paused novel so it moves out of the active writing group but remains recoverable.
6. Create or open another novel and continue writing.

## Product Design

The frontend should no longer auto-open `worlds[0]` when more than one world exists. Instead it should show a `作品书架` view listing all owned novels. Users can open a specific novel, create a new one when needed, and return from a novel page to the bookshelf.

For a single existing world, preserve the current fast path and open it automatically to avoid regressing the MVP loop. For zero worlds, preserve the existing creation workshop.

Archive is a reversible status marker. It never deletes a world. Active and archived worlds are shown in separate bookshelf groups. The current novel page includes copy that reminds users to snapshot/export before archiving and a button to archive or restore the current world.

## API Design

Use the existing `World.status` field and add one minimal endpoint:

- `PATCH /worlds/{world_id}/status`
- Request: `{ "status": "active" | "archived" }`
- Response: existing `WorldResponse`

The service must enforce ownership through `require_owned_world`. Invalid statuses are rejected. Status changes do not increment `world_version`, do not create projection changes, and do not delete data.

## Frontend Design

Add a small bookshelf state to `WorldPage`:

- list owned worlds on load
- if zero worlds: show `WorldCreationForm`
- if one world: open it automatically, preserving current behavior
- if multiple worlds: show `作品书架`
- from bookshelf, `打开` loads a selected world overview and NCC data
- from world page, `返回作品书架` clears the selected world and shows the list
- `创建新小说` from bookshelf opens the existing creation form
- archive/restore action calls the new status endpoint and updates both current world and list state

Keep `Story Arc`, `Narrative Control Center`, Studio launch, snapshot, and export behavior unchanged once a world is opened.

## Documentation Design

Update README with a short product/user workflow section explaining the safe pause/switch flow:

- create snapshot
- export Markdown ZIP
- return to bookshelf
- archive paused novel
- create/open another novel
- archived means hidden/grouped, not deleted

## Test Design

Frontend tests cover:

- multiple worlds show the bookshelf instead of auto-opening `worlds[0]`
- user can open the second world
- user can return to bookshelf
- archive entry/copy is visible on current world page
- single world still auto-opens to preserve the existing MVP loop

Backend tests cover:

- owner can set status to `archived` and back to `active`
- archive does not delete the world
- invalid status is rejected
- non-owner cannot update status

## Out of Scope

No deletion, restore-from-snapshot, import-from-zip, branch worlds, collaboration, or dashboard redesign. Archive is intentionally a reversible status marker and list grouping only.
