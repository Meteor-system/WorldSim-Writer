# MVP Milestone #2: Export & Snapshot Foundation Implementation Plan

Date: 2026-05-30
Spec: `docs/superpowers/specs/2026-05-30-export-snapshot-foundation-design.md`
Status: Draft for implementation approval

## Process Rules

- Follow TDD RED-GREEN-REFACTOR.
- Execute steps sequentially.
- Do not use dynamic workflows.
- Skip code-review subagent because it is unavailable in this environment.
- Preserve the core writing-loop invariant: generated or exported data may observe/propose state, but only explicit user approval/manual governance commits formal world-state changes.
- Snapshot/export operations must not increment `world_version`.
- Markdown export must return JSON contents only and must not write server files.

## Target Files

Backend:

```text
backend/app/snapshot_export/__init__.py
backend/app/snapshot_export/models.py
backend/app/snapshot_export/schemas.py
backend/app/snapshot_export/service.py
backend/app/snapshot_export/router.py
backend/app/api/router.py
backend/app/core/database.py
backend/alembic/versions/<revision>_add_world_snapshots.py
backend/tests/test_snapshot_export.py
```

Frontend:

```text
frontend/src/api/types.ts
frontend/src/api/client.ts
frontend/src/world/WorldArchivePanel.tsx
frontend/src/world/WorldArchivePanel.test.tsx
frontend/src/world/WorldPage.tsx
```

## Step 1 — RED: Backend snapshot creation test

Create `backend/tests/test_snapshot_export.py` with a failing test for snapshot creation.

Test intent:

- Register/login or reuse existing test helpers.
- Create sample world.
- Capture `world_version` before snapshot.
- Call `POST /api/worlds/{world_id}/snapshots`.
- Assert response includes:
  - `id`
  - `world_id`
  - `world_version`
  - `label`
  - `note`
  - `created_at`
- Reload world and assert `world_version` did not change.
- Fetch snapshot row directly or via detail once available later; for this step, response-level proof is enough.

Expected initial failure:

- Route does not exist or model/table does not exist.

Target command:

```bash
cd /opt/WorldSim-Writer/backend && pytest tests/test_snapshot_export.py::test_create_snapshot_freezes_current_world_version_without_mutating_world -v
```

## Step 2 — GREEN: Implement snapshot model, migration, create API

Add backend domain module `app.snapshot_export`.

### Model

Create `backend/app/snapshot_export/models.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WorldSnapshot(Base):
    __tablename__ = 'world_snapshots'

    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[int] = mapped_column(ForeignKey('worlds.id', ondelete='CASCADE'), nullable=False, index=True)
    world_version: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str | None] = mapped_column(String(160), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
```

### Database metadata registration

Update `backend/app/core/database.py` `import_models()` to import `app.snapshot_export.models`.

### Migration

Create Alembic revision adding `world_snapshots` with:

- `id`
- `world_id`
- `world_version`
- `label`
- `note`
- `payload`
- `created_at`
- index on `world_id`
- FK to `worlds.id` with cascade delete

### Schemas

Create `backend/app/snapshot_export/schemas.py`:

```python
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class WorldSnapshotCreate(BaseModel):
    label: str | None = Field(default=None, max_length=160)
    note: str | None = None


class WorldSnapshotSummary(BaseModel):
    id: int
    world_id: int
    world_version: int
    label: str | None
    note: str | None
    created_at: datetime


class WorldSnapshotListResponse(BaseModel):
    world_id: int
    snapshots: list[WorldSnapshotSummary]


class WorldSnapshotDetailResponse(WorldSnapshotSummary):
    payload: dict[str, Any]
```

### Service

Implement a minimal payload builder and create function:

```python
def build_world_archive_payload(db: Session, world: World) -> dict[str, Any]:
    return {
        'world': {
            'id': world.id,
            'name': world.name,
            'description': world.description,
            'genre': world.genre,
            'world_version': world.world_version,
            'story_arc': world.story_arc,
        },
        'characters': world.current_characters,
        'relations': world.current_relations,
        'foreshadows': world.current_foreshadows,
        'approved_chapters': [],
        'events': [],
    }
```

Then insert `WorldSnapshot` and commit.

### Router

Create `backend/app/snapshot_export/router.py` with:

```python
@router.post('/worlds/{world_id}/snapshots', response_model=WorldSnapshotSummary)
def create_snapshot(...): ...
```

Update `backend/app/api/router.py` to include the router.

Rerun Step 1 test until green.

## Step 3 — RED: Backend snapshot list/detail tests

Extend `backend/tests/test_snapshot_export.py`.

Tests:

1. `test_list_snapshots_returns_only_owned_world_snapshots`
   - Create two worlds/snapshots if helper support allows.
   - Assert list response contains snapshots for requested owned world only.

2. `test_get_snapshot_detail_returns_frozen_payload`
   - Create snapshot.
   - Mutate world formally if existing helper/API supports a simple manual edit, or directly update world projection in DB for test isolation.
   - Fetch detail.
   - Assert payload still reflects original `world_version` and original projection.

3. `test_snapshot_detail_rejects_non_owner`
   - User A creates world/snapshot.
   - User B attempts `GET /api/snapshots/{snapshot_id}`.
   - Assert 403 or 404 consistent with existing ownership behavior.

Target command:

```bash
cd /opt/WorldSim-Writer/backend && pytest tests/test_snapshot_export.py -v
```

## Step 4 — GREEN: Implement snapshot list/detail

Service functions:

```python
def list_world_snapshots(db: Session, user: User, world_id: int) -> dict: ...
def get_world_snapshot_detail(db: Session, user: User, snapshot_id: int) -> WorldSnapshot: ...
```

Routes:

```python
@router.get('/worlds/{world_id}/snapshots', response_model=WorldSnapshotListResponse)
def list_snapshots(...): ...

@router.get('/snapshots/{snapshot_id}', response_model=WorldSnapshotDetailResponse)
def get_snapshot(...): ...
```

Implementation details:

- Use `require_owned_world()` for world-scoped list.
- For snapshot detail, select snapshot, then call `require_owned_world(db, user, snapshot.world_id)`.
- Sort list newest-first by `WorldSnapshot.id.desc()`.
- Return frozen `payload` exactly as persisted.

Rerun backend snapshot tests until green.

## Step 5 — RED: Backend Markdown export tests

Add tests for `POST /api/worlds/{world_id}/export/markdown`.

Tests:

1. `test_export_markdown_returns_world_archive_files`
   - Create sample world.
   - Call export endpoint.
   - Assert response includes:
     - `world_id`
     - `world_version`
     - `generated_at`
     - `files`
   - Assert paths include:
     - `World.md`
     - `Relations.md`
     - `Timeline/Events.md`
     - at least one `Characters/...`
     - at least one `Foreshadows/...`

2. `test_export_markdown_does_not_mutate_world_or_create_snapshot`
   - Capture `world_version` and snapshot count.
   - Export.
   - Assert version and snapshot count unchanged.

3. Approved chapter inclusion test, if existing narrative approval helper flow is practical:
   - Approve a chapter.
   - Export.
   - Assert at least one `Chapters/...` file exists and contains approved content.

Expected initial failure:

- Export route missing.

Target command:

```bash
cd /opt/WorldSim-Writer/backend && pytest tests/test_snapshot_export.py -v
```

## Step 6 — GREEN: Implement Markdown export

### Schemas

Add:

```python
class MarkdownExportFile(BaseModel):
    path: str
    content: str


class WorldMarkdownExportResponse(BaseModel):
    world_id: int
    world_version: int
    generated_at: datetime
    files: list[MarkdownExportFile]
```

### Service helpers

Implement:

```python
def export_world_markdown(db: Session, user: User, world_id: int) -> dict: ...
def render_markdown_bundle(payload: dict[str, Any]) -> list[dict[str, str]]: ...
def safe_markdown_slug(value: str | None, fallback: str) -> str: ...
```

Payload builder should now include:

- approved chapters from `Chapter` where:
  - `world_id == world.id`
  - `status == 'approved'`
  - `approved_content is not None`
  - `approved_version is not None`
- events from `EventLog` for world ordered by `id`

Renderer files:

- `World.md`
- `Relations.md`
- one file per current character
- one file per current foreshadow
- one file per approved chapter
- `Timeline/Events.md`

### Router

Add:

```python
@router.post('/worlds/{world_id}/export/markdown', response_model=WorldMarkdownExportResponse)
def export_markdown(...): ...
```

Rerun Step 5 tests until green.

## Step 7 — RED: Backend authorization and regression tests

Add tests:

1. Unauthenticated calls are rejected for:
   - create snapshot
   - list snapshots
   - get snapshot detail
   - export markdown

2. Non-owner calls are rejected for:
   - create snapshot
   - list snapshots
   - get snapshot detail
   - export markdown

3. Rejected drafts exclusion:
   - Create or simulate rejected chapter/draft using existing narrative APIs/helpers.
   - Export and snapshot.
   - Assert rejected content is not included in `approved_chapters` payload or `Chapters/...` files.

Target command:

```bash
cd /opt/WorldSim-Writer/backend && pytest tests/test_snapshot_export.py -v
```

## Step 8 — GREEN/REFACTOR: Complete backend behavior

- Ensure every route uses existing auth dependency and owner boundary.
- Ensure approved chapter query excludes rejected/pending chapters.
- Ensure Markdown rendering handles empty lists gracefully.
- Ensure JSON payload is serializable in SQLite test environment.
- Refactor repeated payload formatting helpers.
- Keep behavior aligned with current code naming/comment density.

Run:

```bash
cd /opt/WorldSim-Writer/backend && pytest tests/test_snapshot_export.py -v
cd /opt/WorldSim-Writer/backend && pytest -v
```

## Step 9 — RED: Frontend archive panel tests

Create `frontend/src/world/WorldArchivePanel.test.tsx`.

Tests:

1. `renders archive controls`
   - Assert `创建世界快照` button exists.
   - Assert `导出世界档案` button exists.

2. `shows snapshot success state`
   - Mock `onCreateSnapshot` resolving with `{ id, world_version, created_at }`.
   - Click button.
   - Assert loading then success text.

3. `shows snapshot error state`
   - Mock reject.
   - Click button.
   - Assert `创建快照失败`.

4. `shows export success state with generated files`
   - Mock `onExportMarkdown` resolving with files.
   - Click button.
   - Assert file count and paths.

5. `shows export error state`
   - Mock reject.
   - Assert `导出世界档案失败`.

Target command:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldArchivePanel.test.tsx
```

## Step 10 — GREEN: Implement `WorldArchivePanel`

Create `frontend/src/world/WorldArchivePanel.tsx`.

Props:

```ts
type WorldArchivePanelProps = {
  onCreateSnapshot: () => Promise<WorldSnapshotSummary>;
  onExportMarkdown: () => Promise<WorldMarkdownExportResponse>;
};
```

Behavior:

- Maintain independent loading/error/success state for snapshot and export.
- Disable relevant button while request is in flight.
- Show generated file paths after export success.
- Match existing UI style from Narrative Control Center panels.

## Step 11 — GREEN: Add frontend API types and client methods

Update `frontend/src/api/types.ts` with:

- `WorldSnapshotSummary`
- `WorldSnapshotListResponse`
- `WorldSnapshotPayload`
- `WorldSnapshotDetailResponse`
- `MarkdownExportFile`
- `WorldMarkdownExportResponse`

Update `frontend/src/api/client.ts` with:

```ts
export function createWorldSnapshot(worldId: number, data = {}) { ... }
export function listWorldSnapshots(worldId: number) { ... }
export function getWorldSnapshot(snapshotId: number) { ... }
export function exportWorldArchiveMarkdown(worldId: number) { ... }
```

Use existing API wrapper conventions.

## Step 12 — RED/GREEN: Integrate into `WorldPage` Narrative Control Center

Add or update frontend test coverage if existing setup supports it.

Implementation:

- Import `WorldArchivePanel`.
- Import `createWorldSnapshot` and `exportWorldArchiveMarkdown`.
- Render panel in the Narrative Control Center section near `NextChapterPrepPanel` and `ChapterHistoryPanel`.
- Pass closures bound to selected `world.id`:

```tsx
<WorldArchivePanel
  onCreateSnapshot={() => createWorldSnapshot(world.id)}
  onExportMarkdown={() => exportWorldArchiveMarkdown(world.id)}
/>
```

If the local `WorldPage.tsx` has manual integration conflicts from prior work, keep the change minimal and report exact conflict rather than repeatedly retrying broad edits.

## Step 13 — Final verification

Run backend targeted tests:

```bash
cd /opt/WorldSim-Writer/backend && pytest tests/test_snapshot_export.py -v
```

Run backend full regression:

```bash
cd /opt/WorldSim-Writer/backend && pytest -v
```

Run frontend targeted tests:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldArchivePanel.test.tsx
```

Run frontend full regression/build:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test
cd /opt/WorldSim-Writer/frontend && npm run build
```

Report:

- test commands executed
- pass/fail status
- any failures with exact output summary
- files changed
- whether acceptance criteria are satisfied

## Commit Plan

After tests pass, commit in logical chunks if requested by the user:

1. Backend snapshot/export foundation.
2. Frontend archive controls.
3. Verification/doc updates if needed.

Do not commit unless explicitly asked.
