# Import Panel Candidate Material Wording Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace technical user-facing `候选资产` import-panel wording with lower-cognitive `候选素材` wording.

**Architecture:** Frontend-only copy update in `WorldImportPanel.tsx`. Change visible strings only; keep import payloads, TypeScript types, preview/confirm behavior, batch listing, candidate pool labels, and canon behavior unchanged.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
  - Update import panel expectations from `候选资产` to `候选素材` where the user sees import flow status.
  - Assert older `候选资产` wording is not exposed in covered rendered states.
  - Preserve raw ID, slug, enum, and non-candidate label hiding assertions.
- Modify: `frontend/src/world/WorldImportPanel.tsx`
  - Replace visible `候选资产` strings with `候选素材` strings.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only.

---

### Task 1: Import panel uses candidate material wording

**Files:**
- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
- Modify: `frontend/src/world/WorldImportPanel.tsx`

- [ ] **Step 1: Write the failing test**

In `WorldImportPanel.test.tsx`, update visible copy assertions:

```ts
expect(screen.getByText('导入素材会先进入候选素材池，不会自动改写正式设定。')).toBeInTheDocument();
expect(screen.getByText('正式设定候选 1 · 角色候选 1 · 灵感候选 1，需确认后才写入候选素材。')).toBeInTheDocument();
expect(screen.getByRole('button', { name: '确认写入候选素材' })).toBeInTheDocument();
expect(screen.getByText('候选素材 3 项')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('候选资产');
```

Keep existing raw ID, slug, enum, and canon-safety assertions.

- [ ] **Step 2: Run tests to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx
```

Expected: FAIL because production still renders `候选资产` wording.

- [ ] **Step 3: Write minimal implementation**

In `WorldImportPanel.tsx`, change only visible copy:

```tsx
导入素材会先进入候选素材池，不会自动改写正式设定。
系统会先解析、分类、清洗并提示冲突，确认后只写入候选素材和导入批次审计记录。
正式设定候选 1 · 角色候选 1 · 灵感候选 1，需确认后才写入候选素材。
确认写入候选素材
候选素材写入失败
候选素材 3 项
```

Do not rename TypeScript types or API fields.

- [ ] **Step 4: Run tests to verify GREEN**

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
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx src/world/NextChapterPrepPanel.test.tsx src/world/WorldPage.test.tsx src/studio/StudioPage.test.tsx src/world/ChapterHistoryPanel.test.tsx
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

Review diff for clearer candidate-material wording, unchanged import payloads, preserved imported-reference safety, and no formal canon mutation, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-import-panel-candidate-material-wording-design.md docs/superpowers/plans/2026-06-04-import-panel-candidate-material-wording.md frontend/src/world/WorldImportPanel.tsx frontend/src/world/WorldImportPanel.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: clarify import candidate material wording"
```

Do not push. Do not merge main.
