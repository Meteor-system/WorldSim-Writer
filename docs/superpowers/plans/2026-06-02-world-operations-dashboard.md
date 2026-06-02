# World Operations Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This task explicitly forbids subagents, so execute inline.

**Goal:** Add a frontend-only world operations dashboard that tells authors what the current story world needs today.

**Architecture:** Reuse existing `WorldOverview` data inside `WorldPage.tsx`. Add small pure helper functions plus a local `WorldOperationsDashboard` component near the top of the overview tab; no backend calls or routing changes are needed.

**Tech Stack:** React, TypeScript, Vite, Vitest, React Testing Library.

---

## Files

- Create: `docs/superpowers/specs/2026-06-02-world-operations-dashboard-design.md`
  - Documents the P2 dashboard MVP design.
- Create: `docs/superpowers/plans/2026-06-02-world-operations-dashboard.md`
  - Documents this TDD implementation plan.
- Modify: `frontend/src/world/WorldPage.test.tsx`
  - Add RED tests for dashboard metrics, recommendations, summaries, and no hardcoded generated prose.
- Modify: `frontend/src/world/WorldPage.tsx`
  - Add helper functions and `WorldOperationsDashboard` component; render it in the overview tab.

## Task 1: Add failing dashboard tests

- [ ] Add a `WorldPage operations dashboard` describe block to `frontend/src/world/WorldPage.test.tsx` with tests that render `<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />` and assert:
  - `世界运营仪表盘`
  - `世界进度 v2`
  - `已写入正史章节：1`
  - `近期世界历史记录：0`
  - `待处理悬念/伏笔：1`
  - recommendation cards `继续下一章` and `回收或推进悬念/伏笔`
  - summary headings `活跃角色` and `紧迫悬念/伏笔`
  - fixture data `林砚：追查湿信来源` and `裂纹玉佩：advanced · 紧迫度 4`
  - absence of generated mock prose such as `第一章 雨巷密谈` inside the dashboard test's production overview assertions.
- [ ] Run focused RED command:
  ```bash
  cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
  ```
- [ ] Expected: new tests fail because `世界运营仪表盘` does not exist yet.

## Task 2: Implement minimal dashboard UI

- [ ] In `frontend/src/world/WorldPage.tsx`, add pure helpers near `describeEvent()`:
  - `isOpenForeshadow(status: string): boolean`
  - `openForeshadows(world: WorldOverview)` sorted by `urgency_level` descending.
  - `dashboardActions(world: WorldOverview, isArchivedWorld: boolean)` returning user-facing labels/details derived only from `WorldOverview`.
- [ ] Add a `WorldOperationsDashboard` component that accepts:
  ```ts
  {
    world: WorldOverview;
    isArchivedWorld: boolean;
    onContinue: () => void;
    onShowForeshadows: () => void;
  }
  ```
- [ ] Render metrics, recommended actions, active role summary, urgent foreshadow summary, and recent world history summary. Keep lists to the first three items.
- [ ] Wire CTA buttons:
  - `继续下一章` calls `onContinue` and is hidden/disabled for archived worlds.
  - `查看悬念/伏笔账本` calls `onShowForeshadows`.
  - `查看章节历史` links to `#chapter-history`.
- [ ] Render the dashboard in the overview tab after truth canon and before archived/launchpad content.
- [ ] Run focused GREEN command:
  ```bash
  cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
  ```
- [ ] Expected: `WorldPage.test.tsx` passes.

## Task 3: Verify and commit

- [ ] Run focused tests:
  ```bash
  cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
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
- [ ] Commit all P2 files with message:
  ```text
  feat: add world operations dashboard
  ```
- [ ] Do not push and do not merge.

## Self-Review

- Spec coverage: covers dashboard title/metrics, recommendations, active roles, urgent foreshadows, recent history, CTA alignment, frontend-only scope, tests, build, and commit.
- Placeholder scan: no TBD/TODO placeholders.
- Type consistency: all props use existing `WorldOverview`; CTA callbacks are local `WorldPage` state/action callbacks.
