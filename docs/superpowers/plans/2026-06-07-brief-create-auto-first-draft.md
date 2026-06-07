# Brief-Created World Auto First Draft Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Inline execution only for this run. Do not use subagents, agents, code-review subagents, or dynamic workflows. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After a user fills the world form from a one-sentence brief and confirms creation, open Studio and automatically generate the first chapter draft for review.

**Architecture:** Keep the feature frontend-only by threading an optional creation intent from `WorldCreationForm` to `WorldPage`, then passing an auto-start launch context into `StudioPage`. `StudioPage` will run the existing chapter creation, outline, and write APIs in sequence, then stop at the review UI. Approval remains manual, so no 正史/canon/EventLog change happens until the existing approval button.

**Tech Stack:** React, TypeScript, Vite, Vitest, Testing Library.

---

## File Structure

- Modify `frontend/src/api/types.ts`
  - Extend `StudioLaunchContext` with an optional `autoStartFirstDraft` flag.
- Modify `frontend/src/world/WorldCreationForm.tsx`
  - Track whether the editable form came from one-sentence expansion.
  - When the user clicks the existing create action after brief autofill, pass `{ autoStartFirstDraft: true }` to `onCreate`.
  - Keep normal template/seed/manual creation behavior unchanged.
- Modify `frontend/src/world/WorldCreationForm.test.tsx`
  - Add RED tests that brief-autofilled confirmation passes the auto-start intent, while manual creation does not.
- Modify `frontend/src/world/WorldPage.tsx`
  - Accept the optional creation intent in `submitWorld`.
  - After the backend creates the world and overview loads, call `onEnterStudio(overview, { autoStartFirstDraft: true, initialChapterGoal: ..., executionContext: ... })` instead of staying on the world overview when the intent is present.
  - Use a safe first-chapter goal built from the created world’s title/truth/first protagonist if no story arc exists.
- Modify `frontend/src/world/WorldPage.test.tsx`
  - Add RED tests for brief-created world entering Studio with auto-start context and for sample/seed/manual creation not auto-entering Studio.
- Modify `frontend/src/studio/StudioPage.tsx`
  - Add guarded auto-run effect for `launchContext.autoStartFirstDraft`.
  - Reuse the existing API helpers in sequence: create chapter, generate outline, write draft.
  - Show clear Chinese progress/error copy.
  - Stop at draft review and never call approval.
- Modify `frontend/src/studio/StudioPage.test.tsx`
  - Add RED tests that auto-start creates chapter, generates outline, writes draft, shows draft review, and does not approve.
  - Add RED test that an auto-start failure leaves a friendly retry path.

## Tasks

### Task 1: Add launch intent tests and types

- [ ] Add failing tests in `WorldCreationForm.test.tsx`:
  - Brief autofill then `创建自定义世界` calls `onCreate(payload, { autoStartFirstDraft: true })`.
  - Manual `创建自定义世界` calls `onCreate(payload)` without auto-start intent.
- [ ] Run `npm run test -- src/world/WorldCreationForm.test.tsx --run` from `frontend/` and confirm RED.
- [ ] Extend the form prop type and local state minimally to make the tests pass.
- [ ] Run the same test and confirm GREEN.

### Task 2: Route brief-created worlds into Studio

- [ ] Add failing tests in `WorldPage.test.tsx`:
  - Brief autofill + confirmed creation calls `createWorld`, loads overview, then calls `onEnterStudio(overview, context)` with `autoStartFirstDraft: true`.
  - The context contains a Chinese first-chapter goal and a manual execution context based on world version 1.
  - Sample and seed creation still load the overview without entering Studio automatically.
- [ ] Run `npm run test -- src/world/WorldPage.test.tsx --run` from `frontend/` and confirm RED.
- [ ] Update `WorldPage` to accept the optional create options and invoke `onEnterStudio` only for the brief-created path.
- [ ] Run the same test and confirm GREEN.

### Task 3: Auto-generate the first draft in Studio

- [ ] Add failing tests in `StudioPage.test.tsx`:
  - With `launchContext.autoStartFirstDraft`, Studio automatically calls `createChapter`, `generateOutline`, and `writeChapter`, then renders `Writer Draft` and `写入正史前确认`.
  - It does not call `approveChapter`.
  - If auto-start fails, Studio shows a friendly Chinese error and leaves the existing manual create button available.
- [ ] Run `npm run test -- src/studio/StudioPage.test.tsx --run` from `frontend/` and confirm RED.
- [ ] Implement a guarded auto-start effect in `StudioPage` using a ref so it runs once per mount/context.
- [ ] Run the same test and confirm GREEN.

### Task 4: Verification and commit

- [ ] Run targeted tests:
  - `npm run test -- src/world/WorldCreationForm.test.tsx src/world/WorldPage.test.tsx src/studio/StudioPage.test.tsx --run`
- [ ] Run full frontend tests:
  - `npm run test -- --run`
- [ ] Run frontend build:
  - `npm run build`
- [ ] Run repository whitespace check:
  - `git -C /opt/WorldSim-Writer diff --check`
- [ ] Inspect diff and status.
- [ ] Commit with a clear message on the current feature branch.
- [ ] Do not push. Do not merge.

## Self-Review

- Scope stays MVP Next-3 and frontend-only.
- The feature only starts a draft for review after the user confirms world creation.
- It does not approve the draft, write 正史/canon, create EventLog directly, or advance world version.
- All new production behavior has failing tests first.
- No raw schema names, backend IDs, or implementation jargon are required in new user-facing copy.
