# MVP #8 Draft Revision Loop 1.0 Design

## Goal

Add a full-draft revision loop to Studio so a writer can generate a new draft version from the current draft, frozen chapter goal, execution context, Critic report, character arc report, approval readiness summary, and a manual revision instruction.

The new draft is still only a draft. It must not mutate formal world projection state, increment `world_version`, or write event history. World-state changes remain proposed until the user manually approves the current draft.

## Current state

The codebase already has the core versioning primitives needed for MVP #8:

- `ChapterDraft` stores `draft_version`, `change_type`, `change_summary`, `parent_draft_version`, `source_world_version`, `proposed_changes`, and `execution_context`.
- `edit_chapter_draft`, `stash_chapter_draft`, and `revise_chapter_paragraph` already create new draft versions without mutating world state.
- `get_draft_diff` already compares two draft versions.
- Studio already shows a draft version selector, parent diff, approval preview, approval readiness, Critic report, and character arc report.
- Approval still uses the latest `chapter.draft_version` and is the only narrative operation that formally commits proposed world-state changes.

MVP #8 should extend these primitives instead of introducing a separate revision tree or branch-world model.

## Product decision

Use a backend first-class full-draft revision endpoint.

Rejected alternatives:

- Paragraph-only revision: too narrow; it cannot use whole-draft reports and approval readiness as revision context.
- Manual edit as revision: too weak; it does not generate a model-assisted revision.
- Version tree UI or restore workflow: out of scope for this MVP and would complicate approval semantics.

## Backend design

### New request schema

Add `ReviseDraftRequest` in `backend/app/narrative/schemas.py`:

- `instruction: str` with minimum length 3.

The endpoint returns the existing `DraftResponse` shape.

### New endpoint

Add `POST /chapters/{chapter_id}/draft/revise` in `backend/app/narrative/router.py`.

Behavior:

1. Require authentication and chapter ownership through the existing `_require_owned_chapter` service path.
2. Reject approved chapters with `409 ALREADY_APPROVED`.
3. Require an existing current draft.
4. Build a full-draft revision prompt from the current draft and review context.
5. Ask the LLM for a full `ChapterGeneration` response.
6. Validate proposed character and foreshadow IDs with existing validation.
7. Create a new `ChapterDraft` version:
   - `draft_version = chapter.draft_version + 1`,
   - `parent_draft_version = previous current version`,
   - `change_type = revision`,
   - `change_summary = instruction`,
   - `content/context_summary/review_hints/proposed_changes` from the model,
   - `source_world_version` inherited from the previous draft or current world when appropriate,
   - `execution_context` inherited from the previous draft.
8. Update `chapter.title` from the model response and `chapter.status` to `reviewing`.
9. Commit only the draft/chapter draft metadata changes.

Non-behavior:

- Do not update `World.world_version`.
- Do not call `refresh_world_projection`.
- Do not write `EventLog` rows.
- Do not approve or reject the chapter.
- Do not automatically regenerate Critic or character arc reports.

### Revision prompt inputs

`build_revision_messages(...)` should include:

- world truth canon and current world version,
- current characters and foreshadows,
- chapter title and chapter goal,
- frozen execution context,
- outline context and outline beats,
- current draft version and content,
- current draft proposed changes,
- Critic report summary, issues, and suggestions if present,
- character arc report summary, risky arcs/relationships, and suggested revisions if present,
- approval readiness status, summary, checks, and high-risk items,
- manual revision instruction.

The system prompt must tell the model:

- return a complete revised draft, not a patch or diff,
- preserve world-state discipline: proposed changes are suggestions only,
- do not invent character IDs or foreshadow IDs,
- return the same JSON shape as normal chapter generation.

### Approval readiness input

The revision service can call `get_approval_readiness(db, user, chapter_id)` before generating the new version. If readiness cannot be computed because the draft is missing, the revision path is already blocked by the current draft requirement. Existing warnings about stale reports and world-version mismatch are useful revision inputs.

### Draft version lookup

Add a small read endpoint for version switching:

- `GET /chapters/{chapter_id}/drafts/{draft_version}` returns `DraftResponse` for that exact version.

This is intentionally read-only. It does not make an older draft current. It exists so Studio can switch between current and parent draft content without adding restore semantics.

## Frontend design

### API client and types

Add:

- `ReviseDraftRequest` type with `instruction: string`.
- `reviseDraft(chapterId, data)` client function.
- `getDraftVersion(chapterId, draftVersion)` client function.

### Studio revision UI

Inside the existing draft card in `frontend/src/studio/StudioPage.tsx`, add a `Draft Revision Loop` section:

- show current draft version,
- show parent draft version when present,
- show current `change_type` and `change_summary`,
- textarea labelled `修订指令`,
- button `生成修订版`.

On submit:

1. Validate instruction length on the client for a clear message.
2. Call `reviseDraft(draft.chapter_id, { instruction })`.
3. Normalize and set the returned draft as the active draft.
4. Add the new version and parent version to the local version list.
5. Refresh approval preview and approval readiness.
6. Fetch and show the parent-to-child diff through the existing diff path.
7. Clear current in-memory Critic and character arc panels because reports from the previous version are no longer current.

### Version switching

Keep this MVP intentionally light:

- The selector lists the current known versions, plus the parent version when available.
- Selecting a version calls `getDraftVersion` and displays that version's content.
- Selecting an older version is view-only. It does not restore that draft or change `chapter.draft_version`.
- The approve button should only be enabled for the latest/current backend draft version. If a viewed draft version is not the latest known version, show copy such as `正在查看历史版本，切回最新版本后才能批准。`

This satisfies display/switch requirements without adding version tree or restore semantics.

## Error handling

- Model timeout, invalid model response, and model request failures map through the existing `_map_model_error` behavior.
- Invalid proposed character or foreshadow IDs return `MODEL_RESPONSE_INVALID`.
- Missing draft returns `NOT_FOUND` or `DRAFT_REQUIRED` according to the closest existing service convention.
- Approved chapters cannot be revised and return `ALREADY_APPROVED`.
- Frontend mutation errors render the existing `paper-error` message.
- If approval preview/readiness refresh fails after revision, the draft still displays and those panels degrade to absent.

## Testing plan

### Backend targeted tests

Extend `backend/tests/test_narrative_draft_versioning.py` for:

- full-draft revision creates a new version with parent version and `change_type = revision`,
- revision does not mutate `World.world_version`,
- revision prompt includes revision instruction, execution context, Critic report, character arc report, and approval readiness summary,
- approved chapter revision is rejected,
- invalid proposed IDs from the model are rejected,
- `GET /chapters/{chapter_id}/drafts/{draft_version}` returns the requested version and returns 404 for missing versions.

### Frontend targeted tests

Extend `frontend/src/studio/StudioPage.test.tsx` for:

- revision UI appears after a draft is generated,
- submitting a revision instruction calls `reviseDraft`, updates content to v2, shows parent v1, and refreshes approval readiness,
- diff displays v1 to v2 after revision,
- the draft selector can switch to parent draft content through `getDraftVersion`,
- approval is disabled while viewing a historical version.

Extend `frontend/src/api/client.test.ts` if needed to cover the new client functions.

## Verification

Run targeted backend tests:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_draft_versioning.py tests/test_narrative_approval.py -v
```

Run targeted frontend tests:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx src/api/client.test.ts
```

Run frontend build:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

After merge, rerun at least the targeted backend tests, frontend Studio tests, and frontend build.

## Non-goals

- No automatic approval.
- No automatic world-state repair.
- No formal projection mutation before manual approval.
- No rollback or restore endpoint.
- No branch-world semantics.
- No complex diff editor.
- No version tree UI.
- No multi-user review.
- No batch revision.
- No push.
- No dynamic workflows.
- No subagents.

## Self-review

- Placeholder scan: no TBD/TODO placeholders remain.
- Internal consistency: the endpoint creates new draft versions only; approval remains the sole formal world-state commit path.
- Scope check: focused on full-draft revision plus read-only version switching; no restore/tree/rollback semantics.
- Ambiguity check: older draft selection is explicitly view-only, and approving is limited to the latest current draft version.
