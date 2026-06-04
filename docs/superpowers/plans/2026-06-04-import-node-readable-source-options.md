# Import Node Readable Source Options Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace terse Import Node source-option labels with readable Chinese labels while preserving API enum values.

**Architecture:** Frontend-only copy update in `WorldImportPanel.tsx`. Change only visible labels in `SOURCE_LABELS`; the select values and import request payloads stay unchanged.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
  - Add readable source-option expectations first.
- Modify: `frontend/src/world/WorldImportPanel.tsx`
  - Update `SOURCE_LABELS.markdown` and `SOURCE_LABELS.txt`.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only.

---

### Task 1: Source options are readable but payload values stay stable

**Files:**
- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
- Modify: `frontend/src/world/WorldImportPanel.tsx`

- [ ] **Step 1: Write the failing test**

In `previews imported material as grouped candidate assets with canon safety copy`, add source-option assertions before selecting `markdown`:

```ts
expect(screen.getByRole('option', { name: 'Markdown 文档' })).toBeInTheDocument();
expect(screen.getByRole('option', { name: '纯文本文件' })).toBeInTheDocument();
expect(screen.queryByRole('option', { name: 'txt' })).not.toBeInTheDocument();
```

Keep the existing `await user.selectOptions(screen.getByLabelText('素材类型'), 'markdown');` and payload assertion to prove enum values are unchanged.

- [ ] **Step 2: Run test to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx -t "previews imported material"
```

Expected: FAIL because the source selector still shows `Markdown` and `txt`.

- [ ] **Step 3: Write minimal implementation**

In `WorldImportPanel.tsx`, change:

```ts
markdown: 'Markdown',
txt: 'txt',
```

To:

```ts
markdown: 'Markdown 文档',
txt: '纯文本文件',
```

- [ ] **Step 4: Run test to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx -t "previews imported material"
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

Review diff for readable source labels, stable payload values, preserved Import Node safety, and no formal canon mutation, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-import-node-readable-source-options-design.md docs/superpowers/plans/2026-06-04-import-node-readable-source-options.md frontend/src/world/WorldImportPanel.tsx frontend/src/world/WorldImportPanel.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: clarify import source options"
```

Do not push. Do not merge main.
