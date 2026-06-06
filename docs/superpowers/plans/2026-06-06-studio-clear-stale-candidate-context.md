# Studio Clear Stale Candidate Context Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking. This run explicitly forbids subagents and workflows.

**Goal:** Clear stale candidate-material execution context when continuing from an approved chapter into a fresh Studio chapter session.

**Architecture:** Frontend-only state reset in `StudioPage`. The launch execution context becomes local mutable state so `continueNextChapter()` can clear it after settlement. New manual chapter creation then uses the updated world overview and sends no candidate material references unless a new context is explicitly supplied.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/studio/StudioPage.test.tsx`
  - Add a RED regression test for approval → continue next chapter → create next chapter from a fresh manual context.
- Modify: `frontend/src/studio/StudioPage.tsx`
  - Change the execution context from immutable state to mutable state.
  - Clear it in `continueNextChapter()` after settlement.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only and do not mutate canon/world version.

---

### Task 1: Continuing after approval clears stale candidate context

**Files:**
- Modify: `frontend/src/studio/StudioPage.test.tsx`
- Modify: `frontend/src/studio/StudioPage.tsx`

- [ ] **Step 1: Write the failing test**

Add a test that launches Studio with `executionContext`, approves the chapter, clicks `继续下一章`, then verifies the next chapter creation uses a manual context with `material_references: []` and the updated world version.

- [ ] **Step 2: Run focused RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx -t "clears stale candidate references"
```

Expected: FAIL because the old launch context remains visible and the next create action still submits stale candidate material.

- [ ] **Step 3: Implement minimal GREEN**

In `StudioPage.tsx`, replace immutable execution context state with mutable state:

```ts
const [executionContext, setExecutionContext] = useState(launchContext?.executionContext);
```

In `continueNextChapter()`, add:

```ts
setExecutionContext(undefined);
```

- [ ] **Step 4: Run focused GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx -t "clears stale candidate references"
```

Expected: PASS.

---

### Task 2: Final verification and commit

- [ ] **Step 1: Run backend import safety tests**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 ./.venv/bin/pytest tests/test_import_node.py -v
```

Expected: PASS.

- [ ] **Step 2: Run frontend targeted tests**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx src/world/WorldPage.test.tsx src/world/WorldImportPanel.test.tsx src/world/NextChapterPrepPanel.test.tsx
```

Expected: PASS.

- [ ] **Step 3: Run frontend build**

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: PASS.

- [ ] **Step 4: Run diff check**

```bash
git -C /opt/WorldSim-Writer diff --check
```

Expected: no output.

- [ ] **Step 5: Inline self-review and commit**

Review diff for frontend-only scope, unchanged import/backend behavior, unchanged approval payload shape, fresh manual context after continuation, and preserved raw ID/enum hiding. Then stage the docs and source files and commit:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-06-studio-clear-stale-candidate-context-design.md docs/superpowers/plans/2026-06-06-studio-clear-stale-candidate-context.md frontend/src/studio/StudioPage.tsx frontend/src/studio/StudioPage.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "fix: clear stale studio candidate context"
```

Do not push. Do not merge main.
