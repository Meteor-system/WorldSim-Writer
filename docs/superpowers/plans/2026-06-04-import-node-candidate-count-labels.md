# Import Node Candidate Count Labels Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Import Node count summaries explicitly label imported materials as candidate/reference buckets.

**Architecture:** Frontend-only copy update in `WorldImportPanel.tsx`. Change the shared `countText()` helper so preview, confirmation, and recent batch summaries all use candidate labels without changing import payloads, callbacks, or canon mutation behavior.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
  - Update existing Import Node tests first to expect candidate count labels.
- Modify: `frontend/src/world/WorldImportPanel.tsx`
  - Change `countText()` copy only.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only.

---

### Task 1: Import count summaries say candidate buckets

**Files:**
- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
- Modify: `frontend/src/world/WorldImportPanel.tsx`

- [ ] **Step 1: Write the failing test**

In `previews imported material as grouped candidate assets with canon safety copy`, after the preview appears, assert:

```ts
expect(screen.getByText('正式设定候选 1 · 角色候选 1 · 灵感候选 1，需确认后才写入候选资产。')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('正式设定 1 · 角色 1 · 灵感 1，需确认后才写入候选资产。');
```

In `confirms preview assets and shows audit batch result`, replace the audit count assertion with:

```ts
expect(within(audit).getByText('正式设定候选 1 · 角色候选 1 · 灵感候选 1')).toBeInTheDocument();
expect(within(audit).queryByText('正式设定 1 · 角色 1 · 灵感 1')).not.toBeInTheDocument();
```

In `loads recent import batches as source audit history`, assert the recent batch also uses the candidate count:

```ts
expect(screen.getByText('正式设定候选 1 · 角色候选 1 · 灵感候选 1')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('正式设定 1 · 角色 1 · 灵感 1');
```

- [ ] **Step 2: Run test to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx
```

Expected: FAIL because `countText()` still uses ambiguous non-candidate labels.

- [ ] **Step 3: Write minimal implementation**

In `WorldImportPanel.tsx`, change:

```ts
return `正式设定 ${counts.canon ?? 0} · 角色 ${counts.character ?? 0} · 灵感 ${counts.inspiration ?? 0}`;
```

To:

```ts
return `正式设定候选 ${counts.canon ?? 0} · 角色候选 ${counts.character ?? 0} · 灵感候选 ${counts.inspiration ?? 0}`;
```

- [ ] **Step 4: Run test to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx
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

Review diff for candidate/reference wording, hidden ambiguous count labels, preserved Import Node safety, and no formal canon mutation, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-import-node-candidate-count-labels-design.md docs/superpowers/plans/2026-06-04-import-node-candidate-count-labels.md frontend/src/world/WorldImportPanel.tsx frontend/src/world/WorldImportPanel.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: label import counts as candidates"
```

Do not push. Do not merge main.
