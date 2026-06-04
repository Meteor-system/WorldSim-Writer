# Import Node Conflict Candidate Guidance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking. This run explicitly forbids subagents and workflows.

**Goal:** Clarify Import Node conflict hints as candidate-material review guidance that never auto-merges or rewrites formal settings.

**Architecture:** Frontend-only copy update in `WorldImportPanel`. Tests cover the conflict heading and safety note while preserving existing raw slug/id hiding and candidate-only import behavior.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
  - In the preview-with-conflict test, expect `候选素材冲突提示` and the new safety note.
  - Assert the old generic standalone heading is not present.
  - Preserve raw ID/enum/slug hiding assertions.
- Modify: `frontend/src/world/WorldImportPanel.tsx`
  - Replace the conflict heading copy and add one short note.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only and do not mutate canon/world version.

---

### Task 1: Import conflict hints use candidate-material safety guidance

**Files:**
- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
- Modify: `frontend/src/world/WorldImportPanel.tsx`

- [ ] **Step 1: Write the failing test**

In `WorldImportPanel.test.tsx`, inside `previews imported material as grouped candidate assets with canon safety copy`, after:

```ts
expect(screen.getByText('这份素材可能和已有正式设定重叠：青岚城')).toBeInTheDocument();
```

Add:

```ts
expect(screen.getByText('候选素材冲突提示')).toBeInTheDocument();
expect(screen.getByText('这些提示只帮助你审阅候选素材，不会自动合并或改写正式设定。')).toBeInTheDocument();
expect(screen.queryByText('冲突提示', { exact: true })).not.toBeInTheDocument();
```

- [ ] **Step 2: Run tests to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx -t "grouped candidate assets"
```

Expected: FAIL because production still renders `冲突提示` and does not render the candidate-material safety note.

- [ ] **Step 3: Write minimal implementation**

In `WorldImportPanel.tsx`, replace:

```tsx
<h4 className="font-black text-[#4a321e]">冲突提示</h4>
<ul className="mt-2 space-y-2 text-sm text-[#5e3b1c]">
```

With:

```tsx
<h4 className="font-black text-[#4a321e]">候选素材冲突提示</h4>
<p className="manuscript mt-1 text-sm font-bold text-[#5e3b1c]">这些提示只帮助你审阅候选素材，不会自动合并或改写正式设定。</p>
<ul className="mt-2 space-y-2 text-sm text-[#5e3b1c]">
```

- [ ] **Step 4: Run tests to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx -t "grouped candidate assets"
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
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx src/world/WorldPage.test.tsx src/world/NextChapterPrepPanel.test.tsx src/studio/StudioPage.test.tsx src/world/ChapterHistoryPanel.test.tsx
```

Expected: PASS.

- [ ] **Step 3: Run frontend build**

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: PASS.

- [ ] **Step 4: Run diff checks**

```bash
git -C /opt/WorldSim-Writer diff --check
```

Expected: no output.

- [ ] **Step 5: Inline self-review and commit**

Review diff for conflict-copy scope, unchanged import/canon behavior, unchanged preview/confirm behavior, and preserved raw ID/enum hiding, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-import-node-conflict-candidate-guidance-design.md docs/superpowers/plans/2026-06-04-import-node-conflict-candidate-guidance.md frontend/src/world/WorldImportPanel.tsx frontend/src/world/WorldImportPanel.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: clarify import conflict guidance"
```

Do not push. Do not merge main.
