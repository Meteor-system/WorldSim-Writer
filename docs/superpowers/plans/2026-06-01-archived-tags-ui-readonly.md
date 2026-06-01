# Archived Tags UI Read-Only Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline execution only for this session. Do not use dynamic workflows, subagents, or code-review subagent. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hide tag write controls for archived worlds while preserving tag/search read access.

**Architecture:** Add `readOnly?: boolean` props to `WorldTagsPanel` and `WorldSearchPanel`; pass `isArchivedWorld` from `WorldPage`; conditionally render write controls only for active worlds.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI backend compatibility tests.

---

## File Structure

- Modify: `frontend/src/world/WorldTagsPanel.tsx`
  - Add read-only prop and notice.
  - Hide create/edit/merge/delete/assign/bulk/unassign controls when read-only.
- Modify: `frontend/src/world/WorldTagsPanel.test.tsx`
  - Add failing read-only test first.
- Modify: `frontend/src/world/WorldSearchPanel.tsx`
  - Add read-only prop and hide search-results bulk tagging form when read-only.
- Modify: `frontend/src/world/WorldSearchPanel.test.tsx`
  - Add failing read-only search test first.
- Modify: `frontend/src/world/WorldPage.tsx`
  - Pass `isArchivedWorld` to both panels.

---

### Task 1: Add failing WorldTagsPanel read-only test

**Files:**
- Modify: `frontend/src/world/WorldTagsPanel.test.tsx`

- [ ] **Step 1: Write the failing test**

Add this test near the active write-control tests:

```tsx
it('keeps archived tag collections read-only while preserving tag detail browsing', async () => {
  const user = userEvent.setup();
  const onCreateTag = vi.fn().mockResolvedValue(tag);
  const onUpdateTag = vi.fn().mockResolvedValue(tag);
  const onMergeTag = vi.fn().mockResolvedValue(mergeResponse);
  const onAssignTag = vi.fn().mockResolvedValue(assignment);
  const onBulkAssignTag = vi.fn().mockResolvedValue(bulkAssignment);
  const onUnassignTag = vi.fn().mockResolvedValue(undefined);
  const onDeleteTag = vi.fn().mockResolvedValue(undefined);
  const onLoadTag = vi.fn().mockResolvedValue(detailResponse);

  renderPanel({
    readOnly: true,
    onCreateTag,
    onUpdateTag,
    onMergeTag,
    onAssignTag,
    onBulkAssignTag,
    onUnassignTag,
    onDeleteTag,
    onLoadTag,
  });

  expect(await screen.findByText('灯塔线')).toBeInTheDocument();
  expect(screen.getByText('已归档小说为只读模式；恢复写作后才能编辑标签和对象关联。')).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '创建标签' })).not.toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));

  expect(await screen.findByText('许砚')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '查看全部对象 1' })).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '删除当前标签' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '保存标签修改' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '合并当前标签' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '添加对象标签' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '批量添加对象标签' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '移除标签' })).not.toBeInTheDocument();

  expect(onLoadTag).toHaveBeenCalledWith(7, 3);
  expect(onCreateTag).not.toHaveBeenCalled();
  expect(onUpdateTag).not.toHaveBeenCalled();
  expect(onMergeTag).not.toHaveBeenCalled();
  expect(onAssignTag).not.toHaveBeenCalled();
  expect(onBulkAssignTag).not.toHaveBeenCalled();
  expect(onUnassignTag).not.toHaveBeenCalled();
  expect(onDeleteTag).not.toHaveBeenCalled();
});
```

- [ ] **Step 2: Verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx -t "keeps archived tag collections read-only"
```

Expected: FAIL because `readOnly` is not yet a prop and write controls still render.

---

### Task 2: Add failing WorldSearchPanel read-only test

**Files:**
- Modify: `frontend/src/world/WorldSearchPanel.test.tsx`

- [ ] **Step 1: Write the failing test**

Add a test proving archived search still works while bulk tagging is hidden:

```tsx
it('hides search-result bulk tagging in read-only mode while preserving search results', async () => {
  const user = userEvent.setup();
  const onSearch = vi.fn().mockResolvedValue(searchResponse);
  const onListTags = vi.fn().mockResolvedValue(tagListResponse);
  const onBulkAssignTag = vi.fn().mockResolvedValue(characterBulkResponse);

  render(<WorldSearchPanel worldId={7} readOnly onSearch={onSearch} onListTags={onListTags} onBulkAssignTag={onBulkAssignTag} />);

  await user.type(screen.getByLabelText('搜索世界资料'), '灯塔');
  await user.click(screen.getByRole('button', { name: '搜索' }));

  expect(await screen.findByText('许砚')).toBeInTheDocument();
  expect(screen.getByText('灯塔线 · 1')).toBeInTheDocument();
  expect(screen.queryByText('搜索结果批量打标')).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '给搜索结果打标签' })).not.toBeInTheDocument();
  expect(onBulkAssignTag).not.toHaveBeenCalled();
});
```

- [ ] **Step 2: Verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldSearchPanel.test.tsx -t "hides search-result bulk tagging"
```

Expected: FAIL because `readOnly` is not yet a prop and bulk tagging still renders.

---

### Task 3: Implement read-only props and wiring

**Files:**
- Modify: `frontend/src/world/WorldTagsPanel.tsx`
- Modify: `frontend/src/world/WorldSearchPanel.tsx`
- Modify: `frontend/src/world/WorldPage.tsx`

- [ ] **Step 1: Add `readOnly?: boolean` to both panel prop types and destructuring.**

- [ ] **Step 2: In `WorldTagsPanel`, render the notice and wrap all write controls in `!readOnly` conditions.**

Keep read-only browsing controls visible.

- [ ] **Step 3: In `WorldSearchPanel`, render search-result bulk tagging only when `!readOnly`.**

- [ ] **Step 4: Pass `readOnly={isArchivedWorld}` from `WorldPage` to both panels.**

- [ ] **Step 5: Run focused tests.**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx src/world/WorldSearchPanel.test.tsx
```

Expected: PASS.

---

### Task 4: Verify and commit

- [ ] **Step 1: Run WorldPage targeted tests.**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: PASS.

- [ ] **Step 2: Run frontend build.**

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: PASS.

- [ ] **Step 3: Run backend tag guard tests.**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/pytest tests/test_tags.py -q
```

Expected: PASS.

- [ ] **Step 4: Check untracked files and diff hygiene.**

```bash
cd /opt/WorldSim-Writer && git status --short && git diff --check
```

Expected: no whitespace errors. Preserve unrelated untracked files, especially `backend/worldsim-dev.db`.

- [ ] **Step 5: Stage relevant files only and commit.**

```bash
cd /opt/WorldSim-Writer && git add frontend/src/world/WorldTagsPanel.tsx frontend/src/world/WorldTagsPanel.test.tsx frontend/src/world/WorldSearchPanel.tsx frontend/src/world/WorldSearchPanel.test.tsx frontend/src/world/WorldPage.tsx docs/superpowers/specs/2026-06-01-archived-tags-ui-readonly-design.md docs/superpowers/plans/2026-06-01-archived-tags-ui-readonly.md && git commit -m "fix: keep archived tag UI read-only"
```

Expected: commit created. Do not push. Do not merge.
