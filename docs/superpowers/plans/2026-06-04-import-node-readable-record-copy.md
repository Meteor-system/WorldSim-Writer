# Import Node Readable Record Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking. This run explicitly forbids subagents and workflows.

**Goal:** Replace visible Import Node batch terminology with candidate-material record wording.

**Architecture:** Frontend-only copy update in `WorldImportPanel`. Tests cover the recent record heading and fallback load-error copy. Existing import API payloads, TypeScript type names, callbacks, persistence, and canon behavior remain unchanged.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
  - Update recent record heading expectation.
  - Add a fallback error test for failed import record loading.
  - Preserve raw ID/enum/slug hiding assertions.
- Modify: `frontend/src/world/WorldImportPanel.tsx`
  - Replace visible recent-import heading and fallback load error copy.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only.

---

### Task 1: Recent import records use readable candidate-material copy

**Files:**
- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
- Modify: `frontend/src/world/WorldImportPanel.tsx`

- [ ] **Step 1: Write the failing tests**

In `WorldImportPanel.test.tsx`, in `loads recent import batches as source audit history`, replace:

```ts
expect(await screen.findByText('最近导入批次')).toBeInTheDocument();
```

With:

```ts
expect(await screen.findByText('最近候选素材记录')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('最近导入批次');
```

Then add this test before the recent records test:

```ts
  it('shows readable fallback copy when import records fail to load', async () => {
    render(<WorldImportPanel worldId={7} onPreview={vi.fn()} onConfirm={vi.fn()} onListBatches={vi.fn().mockRejectedValue('network down')} />);

    expect(await screen.findByRole('alert')).toHaveTextContent('导入记录加载失败');
    expect(document.body).not.toHaveTextContent('导入批次加载失败');
  });
```

- [ ] **Step 2: Run tests to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx -t "recent import batches|fallback copy"
```

Expected: FAIL because production still renders `最近导入批次` and non-Error load failures still fall back to `导入批次加载失败`.

- [ ] **Step 3: Write minimal implementation**

In `WorldImportPanel.tsx`, change the load error fallback:

```ts
if (!cancelled) setError(err instanceof Error ? err.message : '导入批次加载失败');
```

To:

```ts
if (!cancelled) setError(err instanceof Error ? err.message : '导入记录加载失败');
```

Then change the heading:

```tsx
<h3 className="text-lg font-black text-[#34210f]">最近导入批次</h3>
```

To:

```tsx
<h3 className="text-lg font-black text-[#34210f]">最近候选素材记录</h3>
```

- [ ] **Step 4: Run tests to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx -t "recent import batches|fallback copy"
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

Review diff for readable candidate-record wording, unchanged import/canon behavior, preserved raw ID/enum hiding, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-import-node-readable-record-copy-design.md docs/superpowers/plans/2026-06-04-import-node-readable-record-copy.md frontend/src/world/WorldImportPanel.tsx frontend/src/world/WorldImportPanel.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: clarify import record copy"
```

Do not push. Do not merge main.
