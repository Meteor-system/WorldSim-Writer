# Continuous Chapters MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Inline execution only for this task. Do not use subagents or dynamic workflows. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users reliably continue from an approved first chapter into second and third chapter drafting with frozen continuity context.

**Architecture:** Reuse the existing Narrative Control Center, chapter history, frozen `execution_context`, and Story Bible projections. Add previous-chapter summary to next-prep/context, keep Writer prompts sourced from current DB state, and make the Studio settlement CTA fetch fresh next-prep before starting the next chapter.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, Vite React, TypeScript, Vitest, React Testing Library.

---

## Constraints

- No dynamic workflows, no subagents/agents/code-review subagent.
- TDD: write failing tests before production edits.
- Do not run real LLM unless explicitly justified; default verification uses fake/mock LLM tests.
- No push, no merge. Commit after green verification.

## Tasks

### Task 1: Backend continuity context

**Files:**
- Modify: `backend/tests/test_narrative_control_center.py`
- Modify: `backend/tests/test_chapter_execution_context.py`
- Modify: `backend/app/narrative_control_center/schemas.py`
- Modify: `backend/app/narrative_control_center/service.py`
- Modify: `backend/app/narrative/schemas.py`
- Modify: `backend/app/narrative/service.py`

- [ ] Add failing tests that assert `next-chapter-prep` returns `previous_chapter_summary` and Writer prompts include `上一章摘要`.
- [ ] Run targeted tests to verify RED.
- [ ] Add `previous_chapter_summary` to backend schemas and populate it from latest approved draft `context_summary`, falling back to approved-content excerpt.
- [ ] Add the field to frozen execution context and prompt formatting.
- [ ] Run targeted tests to verify GREEN.

### Task 2: Backend two-chapter mock smoke and stale approval

**Files:**
- Modify: `backend/tests/test_narrative_pipeline.py`

- [ ] Add a fake-LLM continuous chapter test: chapter 1 approve, next-prep, edited chapter 2 goal, chapter 2 prompt assertions, chapter 2 approve.
- [ ] Assert chapter 2 prompt contains previous summary, latest canon, updated character state, open/advanced foreshadow, edited goal, and current `world_version`.
- [ ] Add stale third-draft approval assertion after a manual canon edit advances `world_version`.
- [ ] Run targeted tests to verify RED/GREEN.

### Task 3: Frontend next-prep/context display

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/world/chapterExecutionContext.ts`
- Modify: `frontend/src/world/chapterExecutionContext.test.ts`
- Modify: `frontend/src/world/NextChapterPrepPanel.tsx`
- Modify: `frontend/src/world/NextChapterPrepPanel.test.tsx`

- [ ] Add failing tests for copying and rendering previous chapter summary.
- [ ] Add frontend type field and copy it through `buildExecutionContextFromPrep()` / `withEditedGoal()`.
- [ ] Render Chinese “上一章摘要” copy without exposing internal field names.
- [ ] Run targeted Vitest to verify GREEN.

### Task 4: Frontend settlement continues into fresh editable next chapter

**Files:**
- Modify: `frontend/src/studio/StudioPage.tsx`
- Modify: `frontend/src/studio/StudioPage.test.tsx`

- [ ] Add failing test that clicks settlement “继续下一章”, fetches fresh next-prep, pre-fills editable goal, and submits edited goal/context.
- [ ] Add/adjust UI regression so `approvalPreview.version_conflict` disables approval and shows the existing mismatch warning.
- [ ] Import and use `getNextChapterPrep()` and `buildExecutionContextFromPrep()` in `StudioPage`.
- [ ] Make `continueNextChapter()` async, reset review state, seed fresh goal/context, and preserve manual fallback on prep fetch failure.
- [ ] Run targeted Vitest to verify GREEN.

### Task 5: Final verification and commit

- [ ] Run backend targeted pytest:
  ```bash
  cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 ./.venv/bin/pytest tests/test_narrative_control_center.py tests/test_chapter_execution_context.py tests/test_narrative_pipeline.py tests/test_narrative_approval.py tests/test_narrative_draft_versioning.py -q
  ```
- [ ] Run frontend targeted tests:
  ```bash
  cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/chapterExecutionContext.test.ts src/world/NextChapterPrepPanel.test.tsx src/studio/StudioPage.test.tsx --run
  ```
- [ ] Run frontend build:
  ```bash
  cd /opt/WorldSim-Writer/frontend && npm run build
  ```
- [ ] Run `git -C /opt/WorldSim-Writer diff --check` and staged diff check.
- [ ] Inline self-review for invariants, Chinese UI copy, no internal enum/id exposure in new copy, no real LLM, no push/merge.
- [ ] Commit local changes and stop for user acceptance.
