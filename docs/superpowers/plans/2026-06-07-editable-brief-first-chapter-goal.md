# Editable Brief First Chapter Goal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. This session must execute inline because the user explicitly forbids subagents, agents, code-review subagents, and dynamic workflows.

**Goal:** Let users review and edit the one-sentence draft's first chapter goal before creating the world and auto-starting Studio.

**Architecture:** Keep this frontend-only. `WorldCreationForm` already receives and stores `first_chapter_goal`; expose that stored value as an editable field inside the successful brief draft review panel, then keep submitting the edited value through `WorldCreationOptions.firstChapterGoal`. Do not change backend APIs, world creation payloads, Studio generation, approval behavior, world version, or EventLog writes.

**Tech Stack:** React, TypeScript, Vitest, React Testing Library.

---

### Task 1: Add editable first-chapter-goal review field

**Files:**
- Modify: `frontend/src/world/WorldCreationForm.test.tsx`
- Modify: `frontend/src/world/WorldCreationForm.tsx`

- [ ] **Step 1: Write the failing test**

Add a test that expands a one-sentence brief, edits the displayed `第一章草稿目标`, submits the world, and expects `onCreate` to receive the edited value in `WorldCreationOptions.firstChapterGoal`.

- [ ] **Step 2: Run RED verification**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldCreationForm.test.tsx --run
```

Expected: fail because `第一章草稿目标` is not currently rendered as an editable field.

- [ ] **Step 3: Implement the minimal UI change**

In `WorldCreationForm.tsx`, render an editable textarea inside the brief success panel when `briefDraftApplied` is true. Bind it to `briefFirstChapterGoal` and keep the existing submit trimming/fallback behavior.

- [ ] **Step 4: Run GREEN verification**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldCreationForm.test.tsx --run
```

Expected: all tests in the file pass.

### Task 2: Verify related MVP loop and commit

- [ ] **Step 1: Run related frontend tests**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldCreationForm.test.tsx src/world/WorldPage.test.tsx src/studio/StudioPage.test.tsx --run
```

Expected: all related tests pass.

- [ ] **Step 2: Run frontend build**

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: TypeScript and Vite build complete successfully.

- [ ] **Step 3: Run diff checks**

```bash
git -C /opt/WorldSim-Writer diff --check
git -C /opt/WorldSim-Writer diff --cached --check
```

Expected: no output.

- [ ] **Step 4: Inspect status and commit**

```bash
git -C /opt/WorldSim-Writer status --short --branch
git -C /opt/WorldSim-Writer log --oneline -5
git -C /opt/WorldSim-Writer add docs/superpowers/plans/2026-06-07-editable-brief-first-chapter-goal.md frontend/src/world/WorldCreationForm.test.tsx frontend/src/world/WorldCreationForm.tsx
git -C /opt/WorldSim-Writer commit -m "fix: make brief chapter goal editable"
```

Expected: commit on current branch. Do not push or merge.
