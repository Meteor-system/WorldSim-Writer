# MVP11 Continuity / Consistency Review 1.0 Design

## Summary

MVP11 upgrades approval from controllable submission to trusted submission. Before a draft is approved, WorldSim-Writer evaluates the selected approval change set for deterministic continuity and consistency risks. The system surfaces warnings in the approval preview, recalculates them when the selected change set changes, blocks clearly unsafe changes, and records the actual approval consistency summary in the approval EventLog.

This design builds directly on MVP10 Approval Change Set Review 1.0. MVP10 lets users select which proposed character and foreshadow changes are committed. MVP11 validates that selected subset before formal world projection changes are applied.

## Goals

- Show consistency warnings before approval.
- Evaluate the currently selected change set, not only the full proposed change set.
- Detect selected changes that conflict with the current world projection.
- Flag abrupt character status/current_goals shifts.
- Block illegal foreshadow status rollback, such as `resolved -> advanced`.
- Support warning severities: `info`, `warning`, and `blocking`.
- Prevent approval when blocking warnings exist.
- Allow approval when only warning/info items exist.
- Record the consistency summary for the actual approved selected change set in the `chapter_approved` EventLog payload.
- Preserve MVP10 compatibility: omitted selection means approve all, explicit empty arrays mean approve the chapter without applying object changes.

## Non-goals

- No automatic repair of proposed changes.
- No complex policy/rules engine.
- No multi-user approval workflow.
- No LLM-based autonomous approval or world-state edits.
- No editing of proposed change content.
- No changes to draft revision semantics.

## Recommended approach

Use a shared backend Consistency Evaluator and a selected consistency endpoint.

The evaluator is deterministic and is used by three places:

1. `GET /chapters/{chapter_id}/approval-preview` for the default all-selected preview.
2. `POST /chapters/{chapter_id}/approval-consistency` for recalculating warnings after checkbox selection changes.
3. `POST /chapters/{chapter_id}/approve` immediately before mutation, as the authoritative guard.

The frontend displays the preview consistency state, calls the selected consistency endpoint when checkbox selections change, disables approval for blocking states, and still relies on the backend approval guard for correctness.

## Data contracts

### ConsistencyWarning

Backend responses and frontend types should use this shape:

```json
{
  "severity": "info | warning | blocking",
  "category": "world_projection | character_jump | character_goal_shift | foreshadow_transition | selection",
  "message": "Human-readable warning message",
  "object_type": "character | foreshadow | chapter",
  "object_id": 1,
  "change_index": 0,
  "details": {}
}
```

Field rules:

- `severity` controls UX and approval blocking.
- `category` gives stable grouping for tests and future UI refinements.
- `object_type` identifies whether the warning belongs to a character, foreshadow, or chapter-level selection.
- `object_id` is `null` only for chapter-level warnings.
- `change_index` is the MVP10 zero-based index within its change type, or `null` for chapter-level warnings.
- `details` stores structured before/after context needed for audit and tests.

### ConsistencySummary

```json
{
  "status": "clear | needs_review | blocked",
  "total": 0,
  "info_count": 0,
  "warning_count": 0,
  "blocking_count": 0
}
```

Status derivation:

- `blocked` when `blocking_count > 0`.
- `needs_review` when no blocking warnings exist but `warning_count > 0`.
- `clear` when no blocking or warning items exist. Informational items may exist without changing the status from `clear`.

### Approval preview additions

`GET /chapters/{chapter_id}/approval-preview` returns the existing MVP10 payload plus:

```json
{
  "consistency_summary": {},
  "consistency_warnings": []
}
```

The preview uses the default MVP10 behavior: all proposed changes selected.

### Selected consistency endpoint

Add:

```http
POST /chapters/{chapter_id}/approval-consistency
```

Request body reuses `ApproveRequest`:

```json
{
  "draft_version": 1,
  "selected_character_change_indexes": [0],
  "selected_foreshadow_change_indexes": []
}
```

Response:

```json
{
  "chapter_id": 11,
  "draft_version": 1,
  "selected_change_indexes": {
    "characters": [0],
    "foreshadows": []
  },
  "consistency_summary": {},
  "consistency_warnings": []
}
```

Selection semantics match MVP10:

- Omitted selection body or omitted index lists means that change type is all selected.
- Explicit empty arrays mean no changes of that type are selected.
- Duplicate, negative, or out-of-range indexes return `INVALID_CHANGE_SELECTION`.
- A request `draft_version` that does not match the current draft returns `DRAFT_VERSION_MISMATCH`.

## Backend rules

### Existing hard guards stay unchanged

These are not replaced by consistency warnings:

- Stale world version: `409 WORLD_VERSION_MISMATCH`.
- Stale draft version selection: `409 DRAFT_VERSION_MISMATCH`.
- Invalid change selection: `400 INVALID_CHANGE_SELECTION`.
- Model-proposed IDs that do not exist or do not belong to the world: `502 MODEL_RESPONSE_INVALID`.

### Foreshadow status transition rules

Use this lifecycle order:

```text
planted -> advanced -> resolved -> expired
```

Rules:

- Forward movement is allowed without warning.
  - `planted -> advanced`
  - `advanced -> resolved`
  - `resolved -> expired`
- Same-state change is `info`.
  - Example: `advanced -> advanced` means no status transition, though a description note may still be appended.
- Backward movement is `blocking`.
  - `resolved -> advanced`
  - `resolved -> planted`
  - `expired -> resolved`
  - `expired -> advanced`
  - `advanced -> planted`
- Unknown before or after status is `blocking`.

A blocking foreshadow warning prevents approval if that foreshadow change remains selected.

### Character change rules

Character status and goals are free-form in the MVP, so MVP11 does not block character changes by content. It surfaces warning/info items instead.

Rules:

- If both `status` and `current_goals` change, and old/new non-empty goals have no overlap, emit `warning` with category `character_jump`.
- If old goals are non-empty and the selected change sets `current_goals` to an empty list, emit `warning` with category `character_goal_shift`.
- If the selected change produces no actual projection difference, emit `info` with category `world_projection`.

Warning-only character consistency findings do not block approval.

### Empty selected set

If no character or foreshadow changes are selected:

- Consistency summary is `clear` with zero warnings.
- Approval is allowed.
- World version still increments once, matching MVP10 behavior.
- Object projection tables are not changed.
- The `chapter_approved` EventLog records the empty applied changes and a clear consistency summary.

## Backend implementation shape

Create shared service helpers in `app.narrative.service` unless the file becomes too large during implementation. The MVP can keep the helpers near approval logic to minimize cross-file churn.

Suggested helpers:

```python
def _consistency_warning(...):
    ...


def _consistency_summary(warnings: list[dict]) -> dict:
    ...


def _evaluate_approval_consistency(character_changes: list[tuple], foreshadow_changes: list[tuple]) -> dict:
    ...


def _approval_change_set(db, world, draft, selection) -> dict:
    ...
```

`_approval_change_set` should centralize the logic that currently exists separately in preview and approve:

- read proposed character/foreshadow changes,
- resolve selected indexes,
- validate referenced objects,
- compute before/after projections,
- return selected indexes plus selected change tuples.

This keeps preview, consistency endpoint, and approval aligned.

## Approval mutation behavior

`approve_chapter()` flow becomes:

1. Load chapter, lock world, and load latest draft.
2. Check stale draft selection and stale world version.
3. Build selected change set using MVP10 selection semantics.
4. Evaluate consistency for the selected change set.
5. If `blocking_count > 0`, rollback and return `409 CONSISTENCY_BLOCKED` with structured summary and warnings in the error detail.
6. If no blocking items exist, apply selected changes exactly as MVP10 does.
7. Increment `world_version` once.
8. Write object events for selected changes only.
9. Write `chapter_approved` payload with:

```json
{
  "applied_changes": {
    "characters": [],
    "foreshadows": []
  },
  "applied_change_indexes": {
    "characters": [],
    "foreshadows": []
  },
  "consistency_summary": {},
  "consistency_warnings": []
}
```

Warning/info items are recorded for audit but do not block approval.

## Frontend design

### Types and API client

Add frontend types for:

- `ConsistencyWarning`
- `ConsistencySummary`
- `ApprovalConsistencyResponse`

Extend `ApprovalPreviewResponse` with consistency fields.

Add API helper:

```ts
checkApprovalConsistency(chapterId: number, data: ApproveRequest): Promise<ApprovalConsistencyResponse>
```

### Studio behavior

Studio maintains a separate current consistency state initialized from `approvalPreview`.

When approval preview loads:

- Initialize selected indexes from preview changes.
- Set current consistency summary/warnings from preview.

When a checkbox changes:

- Update local selected indexes.
- Call `checkApprovalConsistency()` with the new selected indexes and current `draft_version`.
- Replace the current consistency state from the response.
- If the request fails, show the error in the existing error area.

Approval button behavior:

- If viewing a historical draft, remain disabled as today.
- If current consistency summary is `blocked`, disable approval and show a blocking message.
- If status is `needs_review`, keep approval enabled.
- If status is `clear`, keep approval enabled.

The backend remains authoritative. Even if the frontend state is stale, `approve_chapter()` re-evaluates consistency and blocks unsafe approval.

### UI presentation

In the existing approval preview card, add a consistency section:

- Summary line:
  - `一致性检查通过`
  - `存在需复核项`
  - `存在阻塞项`
- Counts by severity.
- Warning list grouped or styled by severity:
  - `info`: neutral note.
  - `warning`: amber review warning.
  - `blocking`: red blocking warning.

Each warning should include the message. When helpful, include object type labels such as `角色` or `伏笔`.

## Error handling

Add one new error code:

- `CONSISTENCY_BLOCKED`

Recommended FastAPI error shape:

```json
{
  "detail": {
    "code": "CONSISTENCY_BLOCKED",
    "summary": {},
    "warnings": []
  }
}
```

The frontend can display a generic string if the central fetch wrapper converts non-2xx responses to text. Tests can assert the backend structured error directly.

Existing error codes remain unchanged.

## Testing plan

### Backend tests

Add targeted tests to `backend/tests/test_narrative_approval.py`:

1. Preview includes `consistency_summary` and `consistency_warnings`.
2. A selected foreshadow rollback such as `resolved -> advanced` produces a `blocking` warning.
3. The selected consistency endpoint recalculates warnings when the blocking change is unselected.
4. Approval with a selected blocking foreshadow rollback returns `409` with `CONSISTENCY_BLOCKED`.
5. A warning-only character jump can still approve.
6. `chapter_approved.payload` records the consistency summary/warnings for the actual selected set.
7. Existing MVP10 selection tests keep passing for no body, selected subset, empty arrays, invalid indexes, and stale draft version.

### Frontend tests

Add targeted tests to `frontend/src/studio/StudioPage.test.tsx`:

1. Approval preview renders consistency warnings.
2. Blocking consistency disables the approve button and shows a blocking message.
3. Warning-only consistency keeps approve enabled.
4. Unselecting a blocking change calls `checkApprovalConsistency()` with updated selected indexes and updates the displayed warning state.
5. Approval payload still includes selected indexes and current draft version.

Update `frontend/src/api/client.test.ts` only if needed to cover the new API helper.

### Verification commands

Backend targeted tests:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_approval.py -v
```

Frontend targeted tests:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx src/api/client.test.ts
```

Frontend build:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

## Acceptance criteria mapping

- Approval preview displays consistency warnings: preview response and Studio UI include warnings.
- Selected change set changes update warnings: new selected consistency endpoint and checkbox-triggered frontend refresh.
- Blocking item prevents approval: backend approval guard returns `CONSISTENCY_BLOCKED`; frontend disables approve when current consistency is blocked.
- Warning item can continue approval: evaluator records warnings but only blocks on `blocking` severity.
- EventLog records actual approval consistency summary: `chapter_approved.payload.consistency_summary` and `consistency_warnings` are written from the selected set evaluated during approval.
- MVP10 behavior remains compatible: selection parsing and applied subset semantics are reused.
- Tests/build pass: targeted backend/frontend tests and frontend build are required before commit/merge.
