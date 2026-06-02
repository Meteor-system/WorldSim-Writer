# Post-Approval World Settlement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This project explicitly forbids subagents for this task, so execute inline.

**Goal:** Add a frontend-only post-approval settlement panel that shows the user how the world advanced after a chapter was written into canon.

**Architecture:** `StudioPage` will retain the post-approval overview in local settlement state instead of immediately calling `onApproved`. A small settlement section will render counts and CTA buttons from approval preview selections and refreshed world overview. Existing API functions will be reused.

**Tech Stack:** React, TypeScript, Vite, Vitest, React Testing Library.

---

## Files

- Modify: `frontend/src/studio/StudioPage.test.tsx`
  - Add RED tests for settlement rendering and CTA behavior.
  - Extend the existing API mock to include `exportWorldArchiveMarkdown` and a post-approval overview fixture.
- Modify: `frontend/src/studio/StudioPage.tsx`
  - Import `exportWorldArchiveMarkdown`.
  - Add settlement/local world state.
  - Change `approveDraft()` to show settlement after approval.
  - Add settlement rendering and CTA handlers.
- Existing docs: `docs/UX_UPDATE_PHASE.md`
  - Already written for the UX update roadmap.
- Create: `docs/superpowers/specs/2026-06-02-post-approval-world-settlement-design.md`
- Create: `docs/superpowers/plans/2026-06-02-post-approval-world-settlement.md`

## Task 1: Add failing frontend tests

- [ ] Add `exportWorldArchiveMarkdown` to the mocked imports and mock factory in `frontend/src/studio/StudioPage.test.tsx`.
- [ ] Add an `approvedWorld` fixture based on `world` with `world_version: 2`, `approved_chapter_count: 1`, and a `chapter_approved` recent event.
- [ ] Add a test named `shows world progression settlement after approval before returning to overview`.
- [ ] In the test, draft and approve a chapter, assert `onApproved` has not been called, assert settlement text and CTAs exist, then click `查看世界概览` and assert `onApproved(approvedWorld)`.
- [ ] Add a test named `exports the world archive from the settlement panel`.
- [ ] Add a test named `continues with a fresh chapter session from the settlement panel`.
- [ ] Run: `cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx`
- [ ] Expected: the new settlement tests fail because the panel and CTA handlers do not exist yet.

## Task 2: Implement minimal settlement state and rendering

- [ ] In `StudioPage.tsx`, import `exportWorldArchiveMarkdown`.
- [ ] Add a `localWorld` state initialized from `world`, and keep it synced when the prop changes.
- [ ] Add a `WorldSettlement` type holding before/after versions, committed counts, event evidence, overview, and export status text.
- [ ] In `approveDraft()`, after `approveChapter()`, fetch `/worlds/${world.id}/overview`, build settlement from the current preview/selected change counts plus refreshed overview, update local world, and do not call `onApproved` yet.
- [ ] Render a `世界推进结算` section when settlement exists.
- [ ] Add CTA handlers:
  - `查看世界概览` calls `onApproved(settlement.overview)`.
  - `导出世界档案` calls `exportWorldArchiveMarkdown(localWorld.id)` and stores success/error text.
  - `继续下一章` clears chapter, outline, draft, review, approval, critique, and settlement state; clears the goal; keeps `localWorld` as the updated overview.
- [ ] Run: `cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx`
- [ ] Expected: all `StudioPage` tests pass.

## Task 3: Verify and commit

- [ ] Run focused frontend test: `cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx`
- [ ] Run frontend build: `cd /opt/WorldSim-Writer/frontend && npm run build`
- [ ] Run whitespace check: `git -C /opt/WorldSim-Writer diff --check`
- [ ] Inspect changed files: `git -C /opt/WorldSim-Writer status --short` and `git -C /opt/WorldSim-Writer diff --stat`
- [ ] Commit only this UX update work with message `feat: add post-approval world settlement`.
- [ ] Do not push and do not merge.

## Self-Review

- Spec coverage: all requested P0 UX items map to the settlement panel and CTA tests.
- Placeholder scan: no placeholders or deferred behavior beyond explicitly out-of-scope future UX work.
- Type consistency: plan uses existing `WorldOverview`, `ApprovalPreviewResponse`, and `exportWorldArchiveMarkdown` names.
