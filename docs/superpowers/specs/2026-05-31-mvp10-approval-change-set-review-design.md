# MVP #10 Approval Change Set Review 1.0 Design

## Goal

Let writers review and select individual proposed character and foreshadow changes before approving a chapter draft, while preserving the core invariant that generated drafts only propose formal world-state changes and user approval decides what is committed.

## Current state

The approval flow already has a preview and readiness surface, but it is all-or-nothing:

- `GET /chapters/{chapter_id}/approval-preview` returns `character_changes` and `foreshadow_changes` derived from the latest draft's `proposed_changes`.
- `POST /chapters/{chapter_id}/approve` accepts no meaningful request body and applies every proposed character and foreshadow change.
- `approve_chapter()` increments `world_version` once, refreshes projections, writes per-object events, writes a `world_version_increment` event, and writes a `chapter_approved` event.
- `StudioPage` renders approval preview as read-only text and posts `{}` to approve.
- MVP #8 already prevents historical draft approval in the UI by disabling approval controls when the user views a non-latest draft.

MVP #10 turns the preview into an explicit change-set review surface.

## Product decision

Use **draft-version-scoped index selection**.

The approval preview exposes a stable index for each proposed change within the latest draft version:

- `character_changes[].change_index`
- `foreshadow_changes[].change_index`

The approve request may include:

```json
{
  "draft_version": 2,
  "selected_character_change_indexes": [0, 2],
  "selected_foreshadow_change_indexes": [1]
}
```

Selection semantics:

- If the request body is omitted, or both selection fields are omitted, approval remains backward compatible and applies all proposed changes.
- If either selection field is provided, the provided list controls that change type exactly.
- An explicitly empty list means "approve the chapter but apply no changes of this type."
- `draft_version`, when provided, must match the current latest draft version.
- Indexes are zero-based and scoped to the corresponding latest draft's proposed-change list.
- Duplicate, negative, or out-of-range indexes are rejected.

This avoids ambiguity when a draft contains multiple proposed changes for the same character or foreshadow.

## Invariants

1. Approval still approves exactly the latest draft for a chapter.
2. Historical and non-latest drafts remain non-approvable.
3. Approval still blocks when `draft.source_world_version != world.world_version`.
4. Approval still increments `world_version` exactly once per successful approval.
5. Approval still records chapter approval and world-version history in one transaction.
6. Only selected character and foreshadow changes mutate formal projection tables.
7. Unselected changes do not mutate characters, foreshadows, projection JSON, lifecycle history, or object EventLog rows.
8. EventLog payloads record the applied subset, not the full unselected proposal set.
9. Existing clients that approve without a selection keep approve-all behavior.
10. Draft revision, Critic, Character Arc, and approval readiness logic are not redesigned in this MVP.

## Backend design

### Request schema

Add an optional approve payload schema in `backend/app/narrative/schemas.py`:

```python
class ApproveRequest(BaseModel):
    draft_version: int | None = None
    selected_character_change_indexes: list[int] | None = None
    selected_foreshadow_change_indexes: list[int] | None = None
```

The router accepts `ApproveRequest | None` for `POST /chapters/{chapter_id}/approve` and passes it to the service.

### Preview response

`get_approval_preview()` keeps the existing response shape and adds fields to each change:

```json
{
  "change_index": 0,
  "selected_by_default": true
}
```

This is additive and keeps existing frontend consumers compatible.

### Selection validation

`approve_chapter()` accepts an optional selection object or primitive parameters derived from the request schema.

Validation rules:

- If `draft_version` is provided and does not equal the latest draft's `draft_version`, return `409 DRAFT_VERSION_MISMATCH`.
- If any selected index is negative, duplicated, or outside the available list length, return `400 INVALID_CHANGE_SELECTION`.
- If no selection lists are provided, use all indexes for both change types.
- If only one selection list is provided, that type is controlled exactly and the omitted type defaults to all indexes for backward compatibility within partial payloads.

The partial-payload rule preserves the intuitive meaning of sending only the type the client currently manages.

### Approval application

The service should split proposed changes into:

- all proposed character changes,
- all proposed foreshadow changes,
- selected character changes,
- selected foreshadow changes.

Only selected changes are validated against world-owned entities, transformed into before/after tuples, applied, and logged.

If the selected subset is empty for both types, the chapter can still be approved. The approval still increments `world_version` once because the approved chapter itself becomes formal history.

### Event history

For a successful approval:

- `character_change` events are written only for selected character changes.
- `foreshadow_change` events are written only for selected foreshadow changes.
- Foreshadow lifecycle events are written only for selected foreshadow changes.
- `world_version_increment` is written once.
- `chapter_approved` payload records only applied changes, for example:

```json
{
  "commit_group_id": "...",
  "chapter_id": 11,
  "chapter_title": "第一章 雨巷密谈",
  "approved_version": 2,
  "applied_changes": {
    "characters": [{ "character_id": 1, "status": "开始调查密信" }],
    "foreshadows": []
  },
  "applied_change_indexes": {
    "characters": [0],
    "foreshadows": []
  }
}
```

Do not store unselected proposed changes in the approval event payload.

## Frontend design

### API types and client

Add an `ApproveRequest` type:

```ts
export type ApproveRequest = {
  draft_version?: number;
  selected_character_change_indexes?: number[];
  selected_foreshadow_change_indexes?: number[];
};
```

Add an `approveChapter(chapterId, data?)` client helper. If `data` is omitted, it posts `{}` and preserves legacy approve-all behavior.

### StudioPage state

Maintain selected indexes beside the approval preview:

- `selectedCharacterChangeIndexes: number[]`
- `selectedForeshadowChangeIndexes: number[]`

When a fresh approval preview loads, initialize both lists from preview indexes so all changes are selected by default.

### Approval preview UI

The approval preview becomes the canonical change review panel:

- Each character change renders a checkbox.
- Each foreshadow change renders a checkbox.
- Labels include the existing before/after summary.
- Checkboxes default to checked.
- Users can uncheck any proposed change.
- The panel shows a selected count so the approval consequence is clear.
- Version-conflict warning remains visible.

The existing raw `draft.proposed_changes` display can remain as supporting data if already present, but the selectable preview is the authority for approval submission.

### Approval submission

`approveDraft()` sends:

```ts
{
  draft_version: draft.draft_version,
  selected_character_change_indexes: selectedCharacterChangeIndexes,
  selected_foreshadow_change_indexes: selectedForeshadowChangeIndexes,
}
```

The approve button remains disabled for historical/non-latest drafts through the existing `isViewingLatestDraft()` guard.

## Error handling

Backend error details remain explicit:

- `409 WORLD_VERSION_MISMATCH` for stale source world version.
- `409 DRAFT_VERSION_MISMATCH` for a payload that names a non-current draft version.
- `400 INVALID_CHANGE_SELECTION` for negative, duplicate, or out-of-range indexes.
- `502 MODEL_RESPONSE_INVALID` for malformed selected model-proposed changes that reference missing or cross-world entities.

Frontend displays existing request errors through the Studio error alert and does not mutate local world state optimistically.

## Testing plan

### Backend targeted tests

Add approval tests covering:

1. Approval preview exposes `change_index` and `selected_by_default` for character and foreshadow changes.
2. No-body approval keeps approve-all behavior.
3. Selected subset approval mutates only selected character/foreshadow projection rows.
4. Explicit empty selections approve the chapter but do not apply character or foreshadow changes.
5. `world_version` increments exactly once per successful approval.
6. EventLog object events and `chapter_approved.payload.applied_changes` include only the applied subset.
7. Invalid indexes return `400 INVALID_CHANGE_SELECTION`.
8. Stale `draft_version` returns `409 DRAFT_VERSION_MISMATCH`.
9. Existing world-version mismatch behavior still returns `409 WORLD_VERSION_MISMATCH`.

### Frontend targeted tests

Update Studio tests covering:

1. Approval preview changes render with checkboxes and default selected state.
2. Unchecking a character or foreshadow change changes the approve request selection payload.
3. Approve request includes current `draft_version`.
4. Historical draft approval remains disabled.
5. Approval preview version-conflict warning still renders.

## Non-goals

- No complex diff editor.
- No editing proposed change content.
- No multi-user approval workflow.
- No automatic repair or regeneration of proposed changes.
- No approval policy engine.
- No batch approval across chapters.
- No draft revision logic changes.
- No relation change-set approval.
- No character/foreshadow creation or deletion from approval proposed changes.
- No dynamic workflows.
- No subagent execution.

## Self-review

- Placeholder scan: no TBD/TODO/fill-in-later placeholders remain.
- Internal consistency: preview indexes, approve payload, service validation, UI checkboxes, and EventLog payload all use the same draft-version-scoped index model.
- Scope check: this is one approval-flow slice spanning existing backend narrative service/router/schema and StudioPage/API types; it does not require decomposition.
- Ambiguity check: omitted selection, explicit empty selection, partial selection payloads, invalid indexes, version mismatch, and empty selected subset semantics are explicit.
