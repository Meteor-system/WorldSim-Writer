# MVP Milestone #2: Export & Snapshot Foundation Design

Date: 2026-05-30
Status: Draft for review

## 1. Goal

Add the first read-only archive foundation for WorldSim-Writer:

1. Markdown/Obsidian-style export of the current formal world archive.
2. World snapshot APIs for freezing the current `world_version` state.
3. Narrative Control Center controls for creating a snapshot and exporting the world archive.

This milestone intentionally avoids rollback, branch worlds, server-side Obsidian vault writes, and local filesystem synchronization.

## 2. Confirmed Decisions

- Export behavior: return Markdown contents in JSON only.
- Export API shape: `files: [{ path, content }]`.
- The backend must not write Markdown files to the server filesystem in this milestone.
- Snapshot creation captures the current `world_version` and a frozen payload.
- Snapshot creation does not roll back, branch, or mutate the formal world state.
- Frontend controls live in the Narrative Control Center.
- No dynamic workflows.
- Code-review subagent is skipped because it is unavailable in this environment.

## 3. Existing Foundations to Reuse

- `World.current_characters`
- `World.current_foreshadows`
- `World.current_relations`
- `World.story_arc`
- `EventLog`
- Approved chapter history/detail patterns from `app.narrative_control_center`
- Owner authorization through `require_owned_world`
- Narrative Control Center area in `frontend/src/world/WorldPage.tsx`

## 4. Architecture Choice

Use a dedicated backend domain module:

```text
backend/app/snapshot_export/
  models.py
  schemas.py
  service.py
  router.py
```

Rationale:

- Snapshot/export is an archive/read-model capability, not part of formal world-state mutation.
- It should not further enlarge the `world` module.
- It can later evolve into rollback, branch-world, or Obsidian vault writer support without coupling to the Narrative Control Center UI.
- The same Markdown bundle renderer can later be reused by a filesystem/vault export adapter.

## 5. Product Boundaries

### In scope

- Create snapshot for a world at the current `world_version`.
- List snapshots for a world.
- View snapshot payload.
- Export current formal world state as Markdown bundle JSON.
- Export includes:
  - world overview
  - approved chapter history
  - character cards
  - foreshadow ledger
  - relation ledger
  - event timeline
- Frontend buttons:
  - `创建世界快照`
  - `导出世界档案`
- Frontend success/error/loading states.

### Out of scope

- Snapshot rollback.
- Branch worlds.
- Writing Markdown files to server disk.
- Obsidian plugin integration.
- Automatic local folder sync.
- Exporting rejected/pending drafts as approved chapter history.
- LLM-polished exports.

## 6. Backend Data Model

Add `WorldSnapshot`:

```python
class WorldSnapshot(Base):
    __tablename__ = "world_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[int] = mapped_column(
        ForeignKey("worlds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    world_version: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str | None] = mapped_column(String(160), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
```

Migration requirements:

- Create `world_snapshots` table.
- Add index on `world_id`.
- Preserve cascade delete when a world is deleted.

## 7. Snapshot Payload Contract

Snapshot payload should freeze the current formal state:

```json
{
  "world": {
    "id": 1,
    "name": "...",
    "description": "...",
    "genre": "...",
    "world_version": 7,
    "story_arc": []
  },
  "characters": [],
  "relations": [],
  "foreshadows": [],
  "approved_chapters": [],
  "events": []
}
```

Rules:

- `world.world_version` and snapshot `world_version` must match at creation time.
- Snapshot payload must be frozen. Later world changes must not mutate previous snapshot payloads.
- Snapshot creation must not increment `world.world_version`.
- Snapshot creation must not refresh projections.
- Snapshot creation must not approve/reject drafts.

## 8. Backend API Contracts

All routes require authentication.

### 8.1 Create snapshot

```http
POST /api/worlds/{world_id}/snapshots
```

Request:

```json
{
  "label": "Before Chapter 4",
  "note": "Manual checkpoint before a major reveal"
}
```

Response:

```json
{
  "id": 12,
  "world_id": 1,
  "world_version": 7,
  "label": "Before Chapter 4",
  "note": "Manual checkpoint before a major reveal",
  "created_at": "2026-05-30T00:00:00Z"
}
```

Authorization:

- Must call `require_owned_world(db, user, world_id)`.

### 8.2 List snapshots

```http
GET /api/worlds/{world_id}/snapshots
```

Response:

```json
{
  "world_id": 1,
  "snapshots": [
    {
      "id": 12,
      "world_id": 1,
      "world_version": 7,
      "label": "Before Chapter 4",
      "note": "Manual checkpoint before a major reveal",
      "created_at": "2026-05-30T00:00:00Z"
    }
  ]
}
```

Rules:

- Must only list snapshots belonging to owned world.
- Sort by newest first, preferably `id desc` or `created_at desc`.

### 8.3 View snapshot detail

```http
GET /api/snapshots/{snapshot_id}
```

Response:

```json
{
  "id": 12,
  "world_id": 1,
  "world_version": 7,
  "label": "Before Chapter 4",
  "note": "Manual checkpoint before a major reveal",
  "created_at": "2026-05-30T00:00:00Z",
  "payload": {
    "world": {},
    "characters": [],
    "relations": [],
    "foreshadows": [],
    "approved_chapters": [],
    "events": []
  }
}
```

Authorization:

- Must verify that the snapshot belongs to a world owned by the current user.

### 8.4 Export Markdown archive

```http
POST /api/worlds/{world_id}/export/markdown
```

Response:

```json
{
  "world_id": 1,
  "world_version": 7,
  "generated_at": "2026-05-30T00:00:00Z",
  "files": [
    {
      "path": "World.md",
      "content": "# World Name\n..."
    }
  ]
}
```

Rules:

- Must call `require_owned_world(db, user, world_id)`.
- Must not write files to disk.
- Must not create a snapshot.
- Must not increment `world.world_version`.
- Must not mutate formal world state.

## 9. Markdown Bundle Structure

Recommended paths:

```text
World.md
Characters/{character-name-or-id}.md
Relations.md
Foreshadows/{foreshadow-id-or-title}.md
Chapters/Chapter-{number-or-id}.md
Timeline/Events.md
```

Path generation should be deterministic and safe:

- Prefer readable slugs from names/titles.
- Fall back to stable IDs when names are missing.
- Remove or replace path separators and unsafe filename characters.

## 10. Markdown Contents

### 10.1 `World.md`

Include:

- world name
- genre
- description
- current `world_version`
- story arc
- character index
- foreshadow index
- approved chapter index
- timeline link

Example:

```markdown
# The Brass Archive

- Genre: Steampunk Mystery
- World Version: 7

## Description

...

## Story Arc

- ...

## Characters

- [[Characters/Ada]]

## Foreshadows

- [[Foreshadows/Foreshadow-1]]

## Approved Chapters

- [[Chapters/Chapter-1]]

## Timeline

- [[Timeline/Events]]
```

### 10.2 `Characters/*.md`

Each current character receives a card.

Include fields available from current projections, such as:

- name
- role
- status
- location
- description
- traits
- notes
- related relations

### 10.3 `Relations.md`

Include a table over `current_relations`:

```markdown
# Character Relations

| Source | Target | Type | Intensity | Notes |
|---|---|---|---:|---|
| Ada | Bruno | ally | 7 | ... |
```

### 10.4 `Foreshadows/*.md`

Each current foreshadow receives a ledger page.

Include fields available from current projections, such as:

- title or ID
- status
- description
- payoff target
- related character IDs/names when available
- notes

### 10.5 `Chapters/*.md`

Only approved chapters are exported.

Include:

- title
- status
- approved version
- base world version
- world version after, when derivable from event logs
- approved content
- applied world changes summary, when derivable from event logs

Rejected and pending drafts must not appear as approved chapter files.

### 10.6 `Timeline/Events.md`

Include event log timeline:

```markdown
# Event Timeline

| ID | Version | Type | Source | Chapter | Created |
|---:|---|---|---|---|---|
| 1 | 0 → 1 | CHAPTER_APPROVED | narrative | 1 | 2026-05-30 |
```

Also include compact payload summaries where useful.

## 11. Backend Service Design

Suggested service functions:

```python
def build_world_archive_payload(db: Session, world: World) -> dict: ...

def create_world_snapshot(
    db: Session,
    user: User,
    world_id: int,
    data: WorldSnapshotCreate,
) -> dict: ...

def list_world_snapshots(db: Session, user: User, world_id: int) -> dict: ...

def get_world_snapshot_detail(db: Session, user: User, snapshot_id: int) -> dict: ...

def export_world_markdown(db: Session, user: User, world_id: int) -> dict: ...
```

Suggested helper boundaries:

- `build_world_archive_payload()` gathers formal state.
- `render_markdown_bundle(payload)` converts payload to files.
- Authorization is performed before payload/export operations.

## 12. Frontend Design

Add a focused component:

```text
frontend/src/world/WorldArchivePanel.tsx
```

Responsibilities:

- Render archive controls inside Narrative Control Center.
- Trigger snapshot creation.
- Trigger Markdown export.
- Display loading, success, and error states.
- Display generated file count and paths after export.

Recommended copy:

- Section title: `World Archive`
- Button: `创建世界快照`
- Button: `导出世界档案`
- Snapshot success: `快照已创建：版本 {world_version}`
- Export success: `导出成功：{files.length} 个 Markdown 文件已生成`
- Snapshot error: `创建快照失败`
- Export error: `导出世界档案失败`

`WorldPage.tsx` should render this component inside the Narrative Control Center section, near `NextChapterPrepPanel` and `ChapterHistoryPanel`.

## 13. Frontend API Types

Add to `frontend/src/api/types.ts`:

```ts
export type WorldSnapshotSummary = {
  id: number;
  world_id: number;
  world_version: number;
  label: string | null;
  note: string | null;
  created_at: string;
};

export type WorldSnapshotListResponse = {
  world_id: number;
  snapshots: WorldSnapshotSummary[];
};

export type WorldSnapshotPayload = {
  world: Record<string, unknown>;
  characters: unknown[];
  relations: unknown[];
  foreshadows: unknown[];
  approved_chapters: unknown[];
  events: unknown[];
};

export type WorldSnapshotDetailResponse = WorldSnapshotSummary & {
  payload: WorldSnapshotPayload;
};

export type MarkdownExportFile = {
  path: string;
  content: string;
};

export type WorldMarkdownExportResponse = {
  world_id: number;
  world_version: number;
  generated_at: string;
  files: MarkdownExportFile[];
};
```

Add to `frontend/src/api/client.ts`:

```ts
export function createWorldSnapshot(worldId: number, data = {}) { ... }
export function listWorldSnapshots(worldId: number) { ... }
export function getWorldSnapshot(snapshotId: number) { ... }
export function exportWorldArchiveMarkdown(worldId: number) { ... }
```

## 14. Backend TDD Sequence

### Step 1: Snapshot create RED

Add backend test proving:

- authenticated owner can create snapshot
- response includes current `world_version`
- `world.world_version` remains unchanged
- payload includes `world`, `characters`, `relations`, `foreshadows`, `approved_chapters`, and `events`

### Step 2: Snapshot create GREEN

Implement:

- model
- migration
- schema
- router route
- service create function
- model import registration if needed

### Step 3: Snapshot list/detail RED

Add tests proving:

- owner can list snapshots for a world
- owner can fetch snapshot detail
- detail returns frozen payload
- another user cannot list/fetch

### Step 4: Snapshot list/detail GREEN

Implement list/detail service and routes.

### Step 5: Markdown export RED

Add tests proving export returns Markdown files including:

- `World.md`
- `Timeline/Events.md`
- at least one `Characters/...` file when characters exist
- at least one `Foreshadows/...` file when foreshadows exist
- at least one `Chapters/...` file when approved chapters exist

Also prove:

- export does not mutate `world_version`
- export does not create snapshot rows

### Step 6: Markdown export GREEN

Implement payload builder and Markdown renderer.

### Step 7: Authorization/regression RED

Add tests proving:

- unauthenticated calls are rejected
- non-owner calls are rejected
- rejected drafts do not appear in exported approved chapters
- rejected drafts do not appear in snapshot approved chapter payload

### Step 8: Authorization/regression GREEN

Implement or adjust owner checks and approved-only filtering.

## 15. Frontend TDD Sequence

### Step 9: Archive panel RED

Add `frontend/src/world/WorldArchivePanel.test.tsx` proving:

- buttons render
- snapshot loading/success/error states work
- export loading/success/error states work
- generated file paths render after export success

### Step 10: Archive panel GREEN

Implement `WorldArchivePanel.tsx`.

### Step 11: API client/types GREEN

Add API methods and types required by the component.

### Step 12: WorldPage integration RED/GREEN

Add or update test coverage as appropriate to prove the Narrative Control Center renders the archive controls.

Then integrate `WorldArchivePanel` into `WorldPage.tsx`.

### Step 13: Refactor and verify

Refactor helpers without changing behavior.

Run targeted and full verification:

Backend:

```bash
cd /opt/WorldSim-Writer/backend && pytest tests/test_snapshot_export.py -v
cd /opt/WorldSim-Writer/backend && pytest -v
```

Frontend:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldArchivePanel.test.tsx
cd /opt/WorldSim-Writer/frontend && npm run test
cd /opt/WorldSim-Writer/frontend && npm run build
```

## 16. Acceptance Criteria

Backend:

- Snapshot model and migration exist.
- Owner can create/list/view snapshots.
- Non-owner cannot access snapshots.
- Snapshot payload is frozen at creation time.
- Snapshot creation does not increment `world_version`.
- Markdown export returns deterministic file paths and contents.
- Markdown export includes world overview, approved chapters, character cards, foreshadow ledger, relations, and event timeline.
- Markdown export does not write server files.
- Markdown export does not mutate `world_version`.
- Rejected drafts remain excluded from approved chapter export/snapshot payload.

Frontend:

- Narrative Control Center includes `创建世界快照` and `导出世界档案` controls.
- Snapshot button shows loading, success, and error states.
- Export button shows loading, success, and error states.
- Export success shows file count and generated paths.

Process:

- Implementation follows RED-GREEN-REFACTOR.
- Dynamic workflows are not used.
- Code-review subagent is skipped.
