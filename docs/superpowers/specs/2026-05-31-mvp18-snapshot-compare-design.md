# MVP18 Snapshot Compare / Archive Diff 1.0 Design

## Roadmap analysis

MVP17 completed the Narrative Health Dashboard and rounded out the read-only Narrative Control Center. The product now has a strong local MVP loop: create/customize a world, generate and approve chapters, manage world-bible entities, inspect continuity/foreshadow/health signals, search globally, browse timelines, and export or snapshot the archive.

Three viable next MVP candidates:

1. **Snapshot Compare / Archive Diff 1.0 — recommended**
   - Build on existing world snapshots from the archive/export subsystem.
   - Let users compare two frozen world versions and see what changed across world metadata, characters, relations, foreshadows, approved chapters, and events.
   - Low infrastructure risk: no new tables, no LLM calls, no state mutation.
   - High product value: turns snapshots from passive backups into a usable version-inspection workflow.

2. **Tagging / Collections 1.0**
   - Add lightweight tags to characters, foreshadows, chapters, and events for organization and search refinement.
   - Valuable after global search, but requires schema and UX decisions around tag creation, normalization, and object coverage.

3. **Import / Restore Preview 1.0**
   - Preview a Markdown/archive import or snapshot restore before applying changes.
   - Powerful, but riskier because it touches state mutation, conflict handling, and rollback semantics. It should follow after users can inspect snapshot differences.

## Recommendation

Implement **Snapshot Compare / Archive Diff 1.0** as MVP18. It is the next smallest stable step after snapshots/export/search/health because it uses already persisted frozen payloads and stays read-only. It strengthens trust in the formal writing loop by showing exactly how approved chapters and formal edits changed the world over time.

## Goals

- Add a read-only backend endpoint to compare two snapshots owned by the same user.
- Return structured counts and changed items grouped by object domain.
- Add frontend API types/helper for snapshot comparison.
- Extend the World Archive panel so users can load snapshots, choose two, and view a concise diff summary.
- Preserve the core invariant: comparison must never mutate world state, create events, increment `world_version`, or call the LLM.

## Non-goals

- No snapshot restore or rollback.
- No Markdown import.
- No visual line-by-line prose diff for chapter text.
- No cross-world comparison.
- No new database tables or Alembic migrations.
- No full audit/reconciliation engine.

## Backend design

### Endpoint

Add:

```http
GET /snapshots/{base_snapshot_id}/compare/{target_snapshot_id}
```

Response model:

```python
WorldSnapshotCompareResponse
```

The endpoint will:

1. Load the base snapshot by id.
2. Verify the current user owns the base snapshot world via `require_owned_world()`.
3. Load the target snapshot by id.
4. Verify the target snapshot belongs to the same world as the base snapshot.
5. Reject missing snapshots with `404 NOT_FOUND`.
6. Reject cross-world or unauthorized access with `403 FORBIDDEN`.
7. Return a deterministic read-only diff.

### Diff shape

Response fields:

- `world_id`
- `base_snapshot`: summary
- `target_snapshot`: summary
- `summary`: counts by domain and total change count
- `changes`: grouped lists of changed items

Change item fields:

- `object_type`: `world | character | relation | foreshadow | chapter | event`
- `object_id`: integer or null
- `change_type`: `added | removed | changed`
- `title`: human-readable title
- `fields_changed`: list of field names
- `before`: frozen value before the change
- `after`: frozen value after the change

### Domain comparison rules

- `world`: compare `title`, `genre_template`, `truth_canon`, `truth_canon_version`, `world_version`, `status`, `tone_profile`, and `story_arc` from `payload['world']`.
- `characters`: compare by `id`.
- `relations`: compare by `id`.
- `foreshadows`: compare by `id`.
- `approved_chapters`: compare by `id` and expose as `chapter` changes.
- `events`: compare by `id` and expose as `event` changes.

Objects only in target are `added`; objects only in base are `removed`; objects in both with changed values are `changed` with a field-level list.

## Frontend design

### API

Add types:

- `WorldSnapshotCompareChange`
- `WorldSnapshotCompareSummary`
- `WorldSnapshotCompareResponse`

Add helper:

```ts
compareWorldSnapshots(baseSnapshotId: number, targetSnapshotId: number)
```

It calls:

```http
GET /snapshots/{baseSnapshotId}/compare/{targetSnapshotId}
```

### UI

Extend `WorldArchivePanel` props:

- `onListSnapshots: () => Promise<WorldSnapshotListResponse>`
- `onCompareSnapshots: (baseSnapshotId: number, targetSnapshotId: number) => Promise<WorldSnapshotCompareResponse>`

Panel behavior:

- A new “快照对比” section loads existing snapshots.
- Users select a base snapshot and a target snapshot.
- Compare button is disabled until two different snapshots are selected.
- On success, show:
  - snapshot version range
  - total change count
  - counts by object type
  - grouped changed item cards with before/after snippets
- On failure, show a localized error.

`WorldPage` will pass the new helpers to `WorldArchivePanel`.

## Testing plan

Backend TDD:

- Compare two snapshots after mutating world projection and creating a second snapshot; expect grouped added/changed changes.
- Compare identical snapshots; expect zero total changes.
- Reject cross-world snapshot comparison.
- Require authentication.

Frontend TDD:

- API helper builds the correct compare URL.
- `WorldArchivePanel` loads snapshots, disables compare until two different choices are made, calls compare helper, and renders summary/change cards.
- `WorldPage` passes snapshot list/compare helpers into `WorldArchivePanel`.

## Risks and mitigations

- **Large JSON diffs can become noisy.** MVP18 returns object-level before/after plus changed field names, not deep nested diffs.
- **Snapshot payloads may have missing keys from older data.** Diff helpers should default missing lists to empty and missing world metadata to empty dict.
- **Cross-world comparisons could leak data.** Require ownership on base and same-world match for target; cross-world returns `403 FORBIDDEN`.

## Self-review

- No placeholders remain.
- Scope is limited to read-only compare.
- No mutation, migration, or model-call requirement is included.
- Backend and frontend contracts use explicit names and deterministic routes.
