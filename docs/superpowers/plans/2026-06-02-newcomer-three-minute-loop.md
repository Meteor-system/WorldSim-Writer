# Newcomer Three-Minute Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This task explicitly forbids subagents, so execute inline.

**Goal:** Add a frontend-only newcomer 3-minute loop MVP that guides empty-state users from world embryo selection to first chapter generation, canon approval, and visible world changes.

**Architecture:** Existing world creation, seed library, Studio generation, and settlement flows stay intact. The implementation adds onboarding copy/cards to `WorldCreationForm`, `SeedLibraryPanel`, and `FirstChapterLaunchpad`, plus minimal Studio waiting-copy state so users understand what is happening during generation/approval.

**Tech Stack:** React, TypeScript, Vite, Vitest, React Testing Library.

---

## Files

- Modify: `frontend/src/world/WorldPage.test.tsx`
  - Add RED tests for the newcomer guide, high-tension embryo card behavior, and first-chapter launchpad loop copy.
- Modify: `frontend/src/studio/StudioPage.test.tsx`
  - Add RED tests for improved generation/approval waiting copy.
- Modify: `frontend/src/world/WorldCreationForm.tsx`
  - Add the `3 分钟开始运营你的故事世界` guide and four-step loop.
- Modify: `frontend/src/world/SeedLibraryPanel.tsx`
  - Update seed library language to `高张力世界胚胎` and clarify embryo copy is a starting prompt.
- Modify: `frontend/src/world/WorldPage.tsx`
  - Update `FirstChapterLaunchpad` copy/button waiting text to align with the P1 loop.
- Modify: `frontend/src/studio/StudioPage.tsx`
  - Add minimal operation-stage state to show `导演正在拆场景…` during writing and `正在写入正史…` during approval.
- Create: `docs/superpowers/specs/2026-06-02-newcomer-three-minute-loop-design.md`
- Create: `docs/superpowers/plans/2026-06-02-newcomer-three-minute-loop.md`

## Task 1: Add failing frontend tests

- [ ] In `WorldPage.test.tsx`, add a test that renders the no-world creation state and asserts:
  - `3 分钟开始运营你的故事世界`
  - `选世界胚胎`
  - `生成第一章`
  - `写入正史`
  - `查看世界变化`
  - `高张力世界胚胎`
- [ ] In `WorldPage.test.tsx`, add a seed creation test that clicks `直接创建此胚胎`, asserts `createWorldFromSeed('forgotten-sun-city')`, and asserts the seed hook is not displayed as generated chapter content such as `Writer Draft` or `世界推进结算`.
- [ ] In `WorldPage.test.tsx`, add a launchpad test that asserts the no-arc state explains `生成第一章 → 写入正史 → 查看世界变化`.
- [ ] In `StudioPage.test.tsx`, add tests for `导演正在拆场景…` while the write request is pending and `正在写入正史…` while approval is pending.
- [ ] Run: `cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx src/studio/StudioPage.test.tsx`
- [ ] Expected: new tests fail because the copy/state does not exist yet.

## Task 2: Implement minimal newcomer loop UI

- [ ] In `WorldCreationForm.tsx`, insert an onboarding section above the existing title with the four-step loop and story-world operation framing.
- [ ] In `SeedLibraryPanel.tsx`, change the heading/copy to use `高张力世界胚胎` and clarify the embryo is only a starting prompt.
- [ ] In `WorldPage.tsx`, update `FirstChapterLaunchpad` no-arc copy and button copy to use the 3-minute loop language.
- [ ] Run: `cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx`
- [ ] Expected: WorldPage tests pass.

## Task 3: Implement minimal Studio waiting copy

- [ ] In `StudioPage.tsx`, add `operationHint` state.
- [ ] Set `operationHint` to `导演正在拆场景…` during `runWriter()` and clear it in `finally`.
- [ ] Set `operationHint` to `正在写入正史…` during `approveDraft()` and clear it in `finally`.
- [ ] Render `operationHint` in the primary write/approval button labels while `working` is true.
- [ ] Run: `cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx`
- [ ] Expected: StudioPage tests pass.

## Task 4: Verify and commit

- [ ] Run focused tests: `cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx src/studio/StudioPage.test.tsx`
- [ ] Run frontend build: `cd /opt/WorldSim-Writer/frontend && npm run build`
- [ ] Run whitespace check: `git -C /opt/WorldSim-Writer diff --check`
- [ ] Inspect status: `git -C /opt/WorldSim-Writer status --short --branch`
- [ ] Commit with message `feat: add newcomer three-minute loop`.
- [ ] Do not push and do not merge.

## Self-Review

- Spec coverage: the plan covers empty-state guide, embryo entry, loop alignment, waiting copy, tests, build, and commit.
- Placeholder scan: no TBD/TODO placeholders.
- Type consistency: all changed components and functions already exist in the current frontend.
