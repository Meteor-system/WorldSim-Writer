# World Operations Terminology Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This task explicitly forbids subagents, so execute inline.

**Goal:** Polish key WorldPage/Studio terminology and waiting states so the UX update phase has a delivered P3 MVP.

**Architecture:** This is frontend-only copy and state polish. `StudioPage` reuses its existing `operationHint` state for more waiting paths; `WorldPage` reuses `arcLoading`; `docs/UX_UPDATE_PHASE.md` gets a completion record.

**Tech Stack:** React, TypeScript, Vite, Vitest, React Testing Library, Markdown docs.

---

## Files

- Create: `docs/superpowers/specs/2026-06-02-world-operations-terminology-polish-design.md`
  - Documents P3 terminology/waiting-copy scope.
- Create: `docs/superpowers/plans/2026-06-02-world-operations-terminology-polish.md`
  - Documents this TDD plan.
- Modify: `frontend/src/studio/StudioPage.test.tsx`
  - Add RED tests for polished terms and new waiting states.
- Modify: `frontend/src/studio/StudioPage.tsx`
  - Update visible terms and operation hints.
- Modify: `frontend/src/world/WorldPage.test.tsx`
  - Add RED test for story arc waiting copy.
- Modify: `frontend/src/world/WorldPage.tsx`
  - Update story arc loading copy and narrative console copy.
- Modify: `docs/UX_UPDATE_PHASE.md`
  - Add phase completion record including P0/P1/P2/P3 commits.

## Task 1: Add failing tests

- [ ] In `frontend/src/studio/StudioPage.test.tsx`, add a test asserting user-side terms after rendering/drafting:
  - `创作流程`
  - `世界进度：1`
  - `写入正史前确认`
  - `设定冲突检查`
  - button `写入正史并更新世界`
- [ ] In `frontend/src/studio/StudioPage.test.tsx`, add a pending outline test:
  - mock `generateOutline` with a pending Promise
  - create a chapter
  - click `生成大纲`
  - assert button `编剧室正在排布章节骨架…`
- [ ] In `frontend/src/studio/StudioPage.test.tsx`, add a pending Critic test:
  - mock `generateCriticReport` with a pending Promise
  - create chapter, generate outline, generate draft
  - click `生成 Critic 报告`
  - assert button `评论席正在检查节奏与设定…`
- [ ] In `frontend/src/world/WorldPage.test.tsx`, add a pending story arc test:
  - mock `generateStoryArc` with a pending Promise
  - click `生成第一轮故事弧线`
  - assert button `故事弧线规划中…`
- [ ] Run RED focused tests:
  ```bash
  cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx src/world/WorldPage.test.tsx
  ```
- [ ] Expected: new tests fail because the polished terms/waiting copy are not implemented yet.

## Task 2: Implement terminology and waiting copy

- [ ] In `frontend/src/studio/StudioPage.tsx`:
  - Change `Pipeline` heading to `创作流程`.
  - Change context label `世界版本：` to `世界进度：`.
  - In `runOutliner()`, set `operationHint` to `编剧室正在排布章节骨架…` before awaiting and clear in `finally`.
  - In `runCritic()`, set `operationHint` to `评论席正在检查节奏与设定…` before awaiting and clear in `finally`.
  - Render outline button as the outline operation hint when active.
  - Render Critic button as the critic operation hint when active.
  - Change `通过后将提交` to `写入正史前确认`.
  - Change approval preview world label to `世界进度：{before} → {after}`.
  - Change consistency heading to `设定冲突检查`.
  - Change approve button label to `写入正史并更新世界`, while still using `正在写入正史…` during approval.
- [ ] In `frontend/src/world/WorldPage.tsx`:
  - Change Story Arc loading text from `规划中...` to `故事弧线规划中…` for both launchpad and overview story-arc buttons.
  - Change narrative console description to mention `世界历史记录`.
- [ ] Run focused tests:
  ```bash
  cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx src/world/WorldPage.test.tsx
  ```
- [ ] Expected: focused tests pass after updating old expectations as needed for intentional copy changes.

## Task 3: Update UX phase documentation

- [ ] Modify `docs/UX_UPDATE_PHASE.md`:
  - Replace the outdated `第一轮实现范围` note with `阶段完成记录`.
  - Record P0 `f3ef8a2`, P1 `d6d7ed9`, P2 `ee8cc61`, and P3 `本轮提交：feat: polish world operations terminology`.
  - State all P0/P1/P2/P3 priorities now have MVP implementations.
- [ ] No backend tests are needed because this task is frontend/docs only.

## Task 4: Verify and commit

- [ ] Run focused tests:
  ```bash
  cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx src/world/WorldPage.test.tsx
  ```
- [ ] Run frontend build:
  ```bash
  cd /opt/WorldSim-Writer/frontend && npm run build
  ```
- [ ] Run whitespace check:
  ```bash
  git -C /opt/WorldSim-Writer diff --check
  ```
- [ ] Inspect status:
  ```bash
  git -C /opt/WorldSim-Writer status --short --branch
  ```
- [ ] Commit with message:
  ```text
  feat: polish world operations terminology
  ```
- [ ] Do not push and do not merge.

## Self-Review

- Spec coverage: covers 3+ user-side terms, 2+ new waiting prompts, doc completion record, focused tests, build, and commit.
- Placeholder scan: no TBD/TODO placeholders.
- Type consistency: all implementation uses existing `operationHint`, `arcLoading`, and local component props.
