# Import Node Candidate Record Intro Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking. This run explicitly forbids subagents and workflows.

**Goal:** Replace remaining visible Import Node intro batch terminology with candidate-material record wording.

**Architecture:** Frontend-only copy update in `WorldImportPanel`. Tests cover the Import Node intro guidance so the UI explains confirmation as candidate-material record creation, while API payloads, TypeScript type names, persistence, and canon behavior remain unchanged.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
  - Add an expectation for the clearer intro sentence.
  - Assert old internal batch-audit wording is not visible.
  - Preserve raw ID/enum/slug hiding assertions.
- Modify: `frontend/src/world/WorldImportPanel.tsx`
  - Replace the visible intro sentence only.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only and do not mutate canon/world version.

---

### Task 1: Import Node intro uses candidate-material record wording

**Files:**
- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
- Modify: `frontend/src/world/WorldImportPanel.tsx`

- [ ] **Step 1: Write the failing test**

In `WorldImportPanel.test.tsx`, inside `previews imported material as grouped candidate assets with canon safety copy`, after:

```ts
expect(screen.getByText('导入素材会先进入候选素材池，不会自动改写正式设定。')).toBeInTheDocument();
```

Add:

```ts
expect(screen.getByText('系统会先解析、分类、清洗并提示冲突，确认后只写入候选素材记录，不会改动正式设定。')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('导入批次审计记录');
```

- [ ] **Step 2: Run tests to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx -t "grouped candidate assets"
```

Expected: FAIL because production still renders `确认后只写入候选素材和导入批次审计记录。` and the old phrase `导入批次审计记录` is still visible.

- [ ] **Step 3: Write minimal implementation**

In `WorldImportPanel.tsx`, replace:

```tsx
<p className="manuscript mt-1 text-sm text-[#5e3b1c]">系统会先解析、分类、清洗并提示冲突，确认后只写入候选素材和导入批次审计记录。</p>
```

With:

```tsx
<p className="manuscript mt-1 text-sm text-[#5e3b1c]">系统会先解析、分类、清洗并提示冲突，确认后只写入候选素材记录，不会改动正式设定。</p>
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

Review diff for candidate-record wording, unchanged import/canon behavior, and preserved raw ID/enum hiding, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-import-node-candidate-record-intro-copy-design.md docs/superpowers/plans/2026-06-04-import-node-candidate-record-intro-copy.md frontend/src/world/WorldImportPanel.tsx frontend/src/world/WorldImportPanel.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: clarify import intro record copy"
```

Do not push. Do not merge main.
