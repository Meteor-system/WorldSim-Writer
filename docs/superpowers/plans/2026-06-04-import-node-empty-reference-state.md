# Import Node Empty Reference State Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the terse Import Node empty history state with safe-reference guidance for newcomers.

**Architecture:** Frontend-only copy update in `WorldImportPanel.tsx`. Change only the recent-import empty-state sentence; import API calls, payloads, preview/confirm behavior, and canon mutation behavior remain unchanged.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
  - Add an empty-history assertion first.
- Modify: `frontend/src/world/WorldImportPanel.tsx`
  - Replace the empty batch message.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only.

---

### Task 1: Empty import history explains safe references

**Files:**
- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
- Modify: `frontend/src/world/WorldImportPanel.tsx`

- [ ] **Step 1: Write the failing test**

Add this test in `WorldImportPanel.test.tsx`:

```ts
it('shows empty import history as safe reference guidance', async () => {
  render(<WorldImportPanel worldId={7} onPreview={vi.fn()} onConfirm={vi.fn()} onListBatches={vi.fn().mockResolvedValue(emptyBatches)} />);

  expect(await screen.findByText('还没有导入素材参考。导入后会先作为候选素材出现在下一章准备区，不会自动改写正式设定。')).toBeInTheDocument();
  expect(document.body).not.toHaveTextContent('还没有导入批次。');
});
```

- [ ] **Step 2: Run test to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx -t "shows empty import history"
```

Expected: FAIL because the panel still shows `还没有导入批次。`.

- [ ] **Step 3: Write minimal implementation**

In `WorldImportPanel.tsx`, change:

```tsx
<p className="text-sm ink-muted">还没有导入批次。</p>
```

To:

```tsx
<p className="text-sm ink-muted">还没有导入素材参考。导入后会先作为候选素材出现在下一章准备区，不会自动改写正式设定。</p>
```

- [ ] **Step 4: Run test to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx -t "shows empty import history"
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

Review diff for safe-reference wording, hidden terse empty state, preserved Import Node safety, and no formal canon mutation, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-import-node-empty-reference-state-design.md docs/superpowers/plans/2026-06-04-import-node-empty-reference-state.md frontend/src/world/WorldImportPanel.tsx frontend/src/world/WorldImportPanel.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: clarify import empty reference state"
```

Do not push. Do not merge main.
