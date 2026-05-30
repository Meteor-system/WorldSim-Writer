# MVP #5 Approval Readiness Dashboard 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only approval readiness endpoint and Studio panel that summarize whether a draft is ready, needs review, or is blocked before approval.

**Architecture:** Keep readiness as a deterministic read-only aggregation separate from approval preview and approval mutation. Backend computes checks from persisted chapter/draft/world/review data; frontend fetches and displays the response without changing approve/reject/edit behavior.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, React, TypeScript, Vitest, Vite.

---

## File structure

- Modify `backend/app/narrative/schemas.py`: add readiness response schemas.
- Modify `backend/app/narrative/service.py`: add `get_approval_readiness` and small helpers.
- Modify `backend/app/narrative/router.py`: add `GET /chapters/{chapter_id}/approval-readiness`.
- Modify `backend/tests/test_narrative_approval.py`: add endpoint/service coverage.
- Modify `frontend/src/api/types.ts`: add readiness TypeScript types.
- Modify `frontend/src/api/client.ts`: add `getApprovalReadiness`.
- Create `frontend/src/studio/ApprovalReadinessPanel.tsx`: focused display component.
- Modify `frontend/src/studio/StudioPage.tsx`: fetch and render readiness panel.
- Modify `frontend/src/studio/StudioPage.test.tsx`: add readiness mocks and assertions.

## Task 1: Backend readiness API with tests

- [ ] Add tests to `backend/tests/test_narrative_approval.py`:
  - `test_approval_readiness_ready_when_all_checks_pass`
  - `test_approval_readiness_blocks_world_version_mismatch`
  - `test_approval_readiness_needs_review_for_missing_reports_and_uncovered_priorities`
  - `test_approval_readiness_reports_high_risk_items`
- [ ] Run `PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_approval.py -v'` and verify the new tests fail because the endpoint does not exist.
- [ ] Add Pydantic schemas in `backend/app/narrative/schemas.py`:
  - `ApprovalReadinessWorldVersion`
  - `ApprovalReadinessCheck`
  - `ApprovalReadinessResponse`
- [ ] Add `get_approval_readiness` in `backend/app/narrative/service.py`:
  - load owned chapter, latest draft, and world;
  - build checks for world version, execution context, priority coverage, continuity warnings, Critic high issues, character arc high risks, and proposed changes;
  - set `blocked` if any check is `fail`, `needs_review` if any check is `warning`, else `ready`;
  - never write or commit to the database.
- [ ] Add route in `backend/app/narrative/router.py`:
  - import `ApprovalReadinessResponse` and `get_approval_readiness`;
  - expose `GET /chapters/{chapter_id}/approval-readiness` with existing auth/db dependencies.
- [ ] Re-run the backend test file and verify it passes.

## Task 2: Frontend readiness types, client, panel, and Studio integration with tests

- [ ] Update `frontend/src/studio/StudioPage.test.tsx` mock module:
  - import and mock `getApprovalReadiness`;
  - return a default `needs_review` readiness payload after drafting;
  - add assertions for panel title, status, checklist, and unchanged approve button.
- [ ] Run `cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx` and verify readiness assertions fail.
- [ ] Add readiness types in `frontend/src/api/types.ts`:
  - `ApprovalReadinessStatus = 'ready' | 'needs_review' | 'blocked'`
  - `ApprovalReadinessCheckStatus = 'pass' | 'warning' | 'fail'`
  - `ApprovalReadinessCheck`
  - `ApprovalReadinessResponse`
- [ ] Add `getApprovalReadiness(chapterId)` in `frontend/src/api/client.ts` and import its response type.
- [ ] Create `frontend/src/studio/ApprovalReadinessPanel.tsx`:
  - render badge labels `审批准备就绪`, `建议复核后批准`, `暂不可批准`;
  - render summary, world version, checks, and high-risk items;
  - apply simple existing Tailwind classes consistent with Studio panels.
- [ ] Update `frontend/src/studio/StudioPage.tsx`:
  - import `getApprovalReadiness`, `ApprovalReadinessResponse`, and `ApprovalReadinessPanel`;
  - add `approvalReadiness` state;
  - fetch readiness in `refreshReviewStudioPanels` after approval preview;
  - refresh after Critic and character arc generation;
  - clear readiness when creating a new chapter session or rerunning outline.
- [ ] Re-run the Studio test file and verify it passes.

## Task 3: Full verification, commit, and merge

- [ ] Run backend targeted tests:
  - `PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_approval.py -v'`
- [ ] Run backend full tests:
  - `PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest -v'`
- [ ] Run frontend targeted test:
  - `cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx`
- [ ] Run frontend full tests:
  - `cd /opt/WorldSim-Writer/frontend && npm run test`
- [ ] Run frontend build:
  - `cd /opt/WorldSim-Writer/frontend && npm run build`
- [ ] Check git status and review changed files.
- [ ] Commit on `feat/mvp5-approval-readiness` with message `feat: add approval readiness dashboard`.
- [ ] Switch to `main` and merge `feat/mvp5-approval-readiness`.
- [ ] Do not push.
