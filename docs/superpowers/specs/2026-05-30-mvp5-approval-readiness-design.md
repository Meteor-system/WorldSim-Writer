# MVP #5 Approval Readiness Dashboard 1.0 Design

## Goal

Add a read-only approval readiness dashboard for the existing Studio review flow. The dashboard helps the writer decide whether a draft is safe to approve by aggregating existing signals from the current world version, frozen execution context, proposed changes, continuity warnings, Critic report, and character arc report.

The feature must not approve, reject, repair, mutate world state, or call a new LLM. Existing approval behavior remains the source of truth and continues to reject stale drafts on world-version mismatch.

## Recommended approach

Use a standalone endpoint and frontend panel:

- Backend: `GET /chapters/{chapter_id}/approval-readiness` computes readiness from persisted data only.
- Frontend: Studio fetches the readiness response after draft/review changes and renders an Approval Readiness panel near the draft review controls.

This keeps readiness separate from approval preview. Approval preview explains what approval would commit; readiness explains what should be reviewed before approval.

## Backend design

### Response shape

Add schemas in `backend/app/narrative/schemas.py`:

- `ApprovalReadinessStatus`: `ready | needs_review | blocked`
- `ApprovalReadinessCheckStatus`: `pass | warning | fail`
- `ApprovalReadinessCheck`: key, label, status, message, details
- `ApprovalReadinessWorldVersion`: source/current versions and match flag
- `ApprovalReadinessResponse`: chapter id, draft version, overall status, summary, world version, checks, high-risk items

### Service behavior

Add `get_approval_readiness(db, user, chapter_id)` in `backend/app/narrative/service.py`.

The function loads the owned chapter, latest draft, and world. It performs only reads and returns a deterministic checklist:

1. **World version match**
   - Pass when `draft.source_world_version == world.world_version`.
   - Fail when versions differ.
   - Any fail makes overall status `blocked`.

2. **Execution context coverage**
   - Pass when draft or chapter execution context exists and includes a source world version.
   - Warning when execution context is missing or incomplete.

3. **Priority character, foreshadow, and progression hint coverage**
   - Compare execution context priority character IDs against proposed character changes.
   - Compare execution context priority foreshadow IDs against proposed foreshadow changes.
   - Compare progression hint related character/foreshadow IDs against proposed changes when related IDs exist.
   - Warning when priority items exist but are not covered by proposed changes.
   - Pass when there are no priority items, or all priority IDs are covered.

4. **Continuity warnings**
   - Warning when execution context contains continuity warnings.
   - Pass when none exist.

5. **Critic high-risk issues**
   - Warning when no Critic report has been generated.
   - Warning when the stored Critic report is stale for the latest draft.
   - Warning and high-risk item entries for issues with `severity == "high"`.
   - Pass when a current report exists without high issues.

6. **Character arc continuity risks**
   - Warning when no character arc report has been generated.
   - Warning when the stored character arc report is stale.
   - Warning and high-risk item entries for character arcs with `continuity_risk == "high"` and relationship notes with `risk_level == "high"`.
   - Pass when a current report exists without high risks.

7. **Proposed changes presence**
   - Pass when the latest draft proposes at least one character or foreshadow change.
   - Warning when there are no proposed changes. This is not blocking because approval can still commit the chapter and increment the world version, but the writer should confirm that no world-state projection changes are expected.

Overall status rule:

- Any `fail` check => `blocked`.
- Else any `warning` check => `needs_review`.
- Else => `ready`.

### Router

Expose the service through `GET /chapters/{chapter_id}/approval-readiness` in `backend/app/narrative/router.py`, protected by the existing `require_user` dependency.

## Frontend design

### API types and client

Add matching TypeScript types in `frontend/src/api/types.ts` and a `getApprovalReadiness(chapterId)` helper in `frontend/src/api/client.ts`.

### Panel

Add `frontend/src/studio/ApprovalReadinessPanel.tsx`.

The panel displays:

- Status badge:
  - `ready`: `审批准备就绪`
  - `needs_review`: `建议复核后批准`
  - `blocked`: `暂不可批准`
- Summary text from the backend.
- World version line.
- Checklist rows with pass/warning/fail styling.
- High-risk items when present.

The panel is informational only. It does not disable or hide approve/reject/edit controls.

### Studio integration

`StudioPage` stores `approvalReadiness` state and refreshes it after:

- writer draft generation,
- manual edit save,
- stash,
- paragraph revision,
- Critic report generation,
- character arc report generation.

If the readiness request fails, Studio clears or hides the panel without blocking the main draft flow.

## Testing plan

### Backend tests

Add tests for:

1. `ready` when versions match, execution context is present, priorities are covered, current Critic and character arc reports have no high risks, and proposed changes exist.
2. `blocked` when the draft source world version no longer matches the current world version.
3. `needs_review` when priority IDs are uncovered or review reports are missing.
4. `needs_review` with high-risk items when Critic and character arc reports include high-risk findings.

### Frontend tests

Add or extend Studio tests for:

1. Rendering the Approval Readiness panel after draft generation.
2. Displaying blocked status and version mismatch copy.
3. Refreshing readiness after Critic or character arc report generation.
4. Keeping the existing approve button behavior unchanged.

## Non-goals

- Do not change `approve_chapter` behavior.
- Do not auto-fix drafts.
- Do not call a new LLM.
- Do not auto-approve or mutate world state.
- Do not add a global dashboard, rollback system, or branch-world feature.
- Do not push to a remote repository.
