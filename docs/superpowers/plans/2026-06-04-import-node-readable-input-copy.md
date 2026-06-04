# Import Node Readable Input Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Import Node technical input helper/error copy with simple Chinese first-use guidance.

**Architecture:** Frontend-only copy update in `WorldImportPanel.tsx`. Keep import source enum values and API payloads unchanged; only visible helper/error text changes.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
  - Add helper/error copy expectations first.
- Modify: `frontend/src/world/WorldImportPanel.tsx`
  - Replace the empty-content error and helper sentence.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only.

---

### Task 1: Import input copy is readable and non-technical

**Files:**
- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
- Modify: `frontend/src/world/WorldImportPanel.tsx`

- [ ] **Step 1: Write the failing tests**

In the empty-history test, add helper assertions:

```ts
expect(screen.getByText('当前一次只处理一份素材来源，粘贴正文后会先生成候选预览。')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('当前只处理单份 Markdown/txt 或粘贴文本。');
```

Add this validation test:

```ts
it('shows readable empty-content validation copy', async () => {
  const user = userEvent.setup();
  render(<WorldImportPanel worldId={7} onPreview={vi.fn()} onConfirm={vi.fn()} onListBatches={vi.fn().mockResolvedValue(emptyBatches)} />);

  await user.clear(screen.getByLabelText('素材正文'));
  await user.click(screen.getByRole('button', { name: '生成结构化预览' }));

  expect(await screen.findByRole('alert')).toHaveTextContent('请先粘贴一段素材正文。');
  expect(document.body).not.toHaveTextContent('请先粘贴 Markdown、txt 或文本素材。');
});
```

- [ ] **Step 2: Run tests to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx -t "readable"
```

Expected: FAIL because the panel still shows technical shorthand copy.

- [ ] **Step 3: Write minimal implementation**

In `WorldImportPanel.tsx`, change:

```ts
setError('请先粘贴 Markdown、txt 或文本素材。');
```

To:

```ts
setError('请先粘贴一段素材正文。');
```

And change:

```tsx
<span className="self-center text-xs ink-muted">当前只处理单份 Markdown/txt 或粘贴文本。</span>
```

To:

```tsx
<span className="self-center text-xs ink-muted">当前一次只处理一份素材来源，粘贴正文后会先生成候选预览。</span>
```

- [ ] **Step 4: Run tests to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx -t "readable"
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

Review diff for readable Chinese copy, no old shorthand on this surface, preserved Import Node safety, and no formal canon mutation, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-import-node-readable-input-copy-design.md docs/superpowers/plans/2026-06-04-import-node-readable-input-copy.md frontend/src/world/WorldImportPanel.tsx frontend/src/world/WorldImportPanel.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: clarify import input guidance"
```

Do not push. Do not merge main.
