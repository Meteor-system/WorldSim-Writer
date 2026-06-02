# Archived Snapshot Create Guard Design

## Brainstorming outcome

The next small high-value stability gap is archived-world snapshot creation. Archived worlds are now broadly read-only for narrative, story arc, tag, character, relation, and foreshadow writes, but `POST /worlds/{world_id}/snapshots` still creates a persisted `WorldSnapshot` row.

## Scope

- Reject creating a new world snapshot when `world.status == "archived"`.
- Preserve read/export behavior for archived worlds:
  - list snapshots,
  - snapshot detail,
  - snapshot compare,
  - Markdown ZIP export.
- Hide the create-snapshot button in the archived-world archive panel while keeping export/list/compare controls visible.

## API contract

Archived snapshot creation returns HTTP 409 with JSON detail `WORLD_ARCHIVED`, matching existing archived write guards.

## Frontend contract

`WorldArchivePanel` accepts a read-only flag. When read-only, it displays a short archived notice and hides only the snapshot creation action. Export and snapshot history controls remain available.

## Testing

- Backend regression test verifies archived snapshot creation returns 409 and does not insert a snapshot, while list and Markdown export still return 200.
- Frontend regression test verifies read-only archive panel hides `创建世界快照` but keeps `导出世界档案` and `加载快照列表`.
- WorldPage test verifies archived worlds pass read-only mode into the archive panel.
