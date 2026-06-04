# Candidate Empty Reference Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking. This run explicitly forbids subagents and workflows.

**Goal:** Clarify no-reference empty states as candidate-material reference copy in Studio settlement and chapter history.

**Architecture:** Frontend-only copy update. Add focused tests for the empty reference path in `StudioPage` and `ChapterHistoryPanel`, then replace the two visible empty-state strings. Keep approval behavior, execution context payloads, world refresh, event history, and import persistence unchanged.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/studio/StudioPage.test.tsx`
  - Add a settlement test for approving a chapter whose execution context has no candidate material references.
  - Assert candidate-material empty-state copy and reject the older import-material empty string.
- Modify: `frontend/src/studio/StudioPage.tsx`
  - Replace the empty return value in `materialReferenceSentence()`.
- Modify: `frontend/src/world/ChapterHistoryPanel.test.tsx`
  - Add a detail test where `execution_context.material_references` is empty.
  - Assert candidate-material empty-state copy and reject the older import-material empty string.
- Modify: `frontend/src/world/ChapterHistoryPanel.tsx`
  - Replace the empty chapter-history reference sentence.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only.

---

### Task 1: Studio settlement empty state says candidate material

**Files:**
- Modify: `frontend/src/studio/StudioPage.test.tsx`
- Modify: `frontend/src/studio/StudioPage.tsx`

- [ ] **Step 1: Write the failing Studio test**

In `StudioPage.test.tsx`, add this test after `shows world progression settlement after approval before returning to overview`:

```ts
  it('shows candidate-material empty state when settlement used no imported references', async () => {
    const user = userEvent.setup();
    const contextWithoutReferences = { ...executionContext, material_references: [] };
    vi.mocked(createChapter).mockResolvedValueOnce({
      id: 11,
      world_id: 7,
      title: '推进雨巷密谈',
      status: 'drafting',
      draft_version: 1,
      approved_version: null,
      base_world_version: 1,
      approved_content: null,
      chapter_goal: '推进雨巷密谈',
      outline_beats: [],
      outline_context: {},
      critique_report: {},
      execution_context: contextWithoutReferences,
    });
    vi.mocked(writeChapter).mockResolvedValueOnce({
      ...draftResponse,
      execution_context: contextWithoutReferences,
    });
    vi.mocked(apiRequest).mockResolvedValueOnce(approvedWorld);

    render(<StudioPage world={world} onBack={vi.fn()} onApproved={vi.fn()} />);

    await user.type(screen.getByLabelText('章节目标'), '推进雨巷密谈');
    await user.click(screen.getByRole('button', { name: '创建章节' }));
    await user.click(await screen.findByRole('button', { name: '生成大纲' }));
    await user.click(await screen.findByRole('button', { name: '基于大纲生成正文' }));
    await user.click(screen.getByRole('button', { name: '写入正史并更新世界' }));

    expect(await screen.findByText('世界推进结算')).toBeInTheDocument();
    expect(screen.getByText('本章未使用候选素材参考。')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('本章未使用导入素材参考。');
    expect(screen.queryByText('候选素材仍是本章创作参考，没有自动写入正式设定。')).not.toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('asset_id');
    expect(document.body).not.toHaveTextContent('batch_id');
    expect(document.body).not.toHaveTextContent('inspiration');
  });
```

- [ ] **Step 2: Run Studio test to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx -t "candidate-material empty state"
```

Expected: FAIL because production still returns `本章未使用导入素材参考。`.

- [ ] **Step 3: Write minimal Studio implementation**

In `StudioPage.tsx`, change:

```ts
if (titles.length === 0) return '本章未使用导入素材参考。';
```

To:

```ts
if (titles.length === 0) return '本章未使用候选素材参考。';
```

- [ ] **Step 4: Run Studio test to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx -t "candidate-material empty state"
```

Expected: PASS.

---

### Task 2: Chapter history empty state says candidate material

**Files:**
- Modify: `frontend/src/world/ChapterHistoryPanel.test.tsx`
- Modify: `frontend/src/world/ChapterHistoryPanel.tsx`

- [ ] **Step 1: Write the failing chapter history test**

In `ChapterHistoryPanel.test.tsx`, add this test before the empty/loading/error state test:

```ts
  it('shows candidate-material empty state when chapter detail used no imported references', async () => {
    const user = userEvent.setup();
    const detailWithoutReferences: ApprovedChapterHistoryDetailResponse = {
      ...detail,
      execution_context: detail.execution_context
        ? { ...detail.execution_context, material_references: [] }
        : detail.execution_context,
    };
    const onLoadDetail = vi.fn(async () => detailWithoutReferences);

    render(<ChapterHistoryPanel history={history} loading={false} onLoadDetail={onLoadDetail} />);

    await user.click(screen.getByRole('button', { name: '查看详情' }));

    expect(await screen.findByText('章节详情')).toBeInTheDocument();
    expect(screen.getByText('本章未使用候选素材参考。')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('本章未使用导入素材参考。');
    expect(document.body).not.toHaveTextContent('正式 canon');
    expect(document.body).not.toHaveTextContent('asset_id');
    expect(document.body).not.toHaveTextContent('batch_id');
    expect(document.body).not.toHaveTextContent('inspiration');
    expect(document.body).not.toHaveTextContent('markdown');
  });
```

- [ ] **Step 2: Run chapter history test to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/ChapterHistoryPanel.test.tsx -t "candidate-material empty state"
```

Expected: FAIL because production still renders `本章未使用导入素材参考。`.

- [ ] **Step 3: Write minimal chapter history implementation**

In `ChapterHistoryPanel.tsx`, change:

```tsx
<p className="manuscript mt-1 text-sm">本章未使用导入素材参考。</p>
```

To:

```tsx
<p className="manuscript mt-1 text-sm">本章未使用候选素材参考。</p>
```

- [ ] **Step 4: Run chapter history test to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/ChapterHistoryPanel.test.tsx -t "candidate-material empty state"
```

Expected: PASS.

---

### Task 3: Final verification and commit

- [ ] **Step 1: Run backend import safety tests**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 ./.venv/bin/pytest tests/test_import_node.py -v
```

Expected: PASS.

- [ ] **Step 2: Run frontend targeted tests**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx src/world/ChapterHistoryPanel.test.tsx src/world/WorldImportPanel.test.tsx src/world/NextChapterPrepPanel.test.tsx src/world/WorldPage.test.tsx
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

Review diff for clearer candidate-reference empty-state wording, unchanged execution context and approval payloads, preserved imported-reference safety, and no formal canon mutation, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-candidate-empty-reference-copy-design.md docs/superpowers/plans/2026-06-04-candidate-empty-reference-copy.md frontend/src/studio/StudioPage.tsx frontend/src/studio/StudioPage.test.tsx frontend/src/world/ChapterHistoryPanel.tsx frontend/src/world/ChapterHistoryPanel.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: clarify candidate empty references"
```

Do not push. Do not merge main.
