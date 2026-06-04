# Chapter History Import Reference Cards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show imported candidate materials as safe readable reference cards in approved chapter history.

**Architecture:** Frontend-only rendering update in `ChapterHistoryPanel`. Existing chapter history API data, detail loading, approval event labels, and formal change rendering remain unchanged.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/world/ChapterHistoryPanel.test.tsx`
  - Update the existing detail-view test first.
- Modify: `frontend/src/world/ChapterHistoryPanel.tsx`
  - Render imported references as title/source/summary cards and replace `正式 canon` safety copy.
- Verify: `backend/tests/test_import_node.py`
  - Existing backend import safety tests prove imports remain candidate/audit only.

---

### Task 1: Chapter history settlement shows safe imported material cards

**Files:**
- Modify: `frontend/src/world/ChapterHistoryPanel.test.tsx`
- Modify: `frontend/src/world/ChapterHistoryPanel.tsx`

- [ ] **Step 1: Write the failing test**

In `renders approved chapter list and loads detail view with changes`, replace the current one-line import reference assertions with:

```ts
expect(screen.getByText('导入素材参考')).toBeInTheDocument();
expect(screen.getByText('雨夜审讯（来源：旧设定.md）')).toBeInTheDocument();
expect(screen.getByText('雨夜审讯从一盏坏灯开始。')).toBeInTheDocument();
expect(screen.getByText('这些导入素材只是本章创作参考，不代表已自动进入正式设定。')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('正式 canon');
expect(document.body).not.toHaveTextContent('asset_id');
expect(document.body).not.toHaveTextContent('batch_id');
expect(document.body).not.toHaveTextContent('inspiration');
expect(document.body).not.toHaveTextContent('markdown');
```

- [ ] **Step 2: Run test to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/ChapterHistoryPanel.test.tsx -t "renders approved chapter list"
```

Expected: FAIL because the summary card and `正式设定` safety wording are not present yet.

- [ ] **Step 3: Write minimal implementation**

In `ChapterHistoryPanel.tsx`, update the approval settlement material-reference block:

```tsx
{(selectedDetail.execution_context?.material_references ?? []).length > 0 ? (
  <div className="mt-3 space-y-2">
    <h5 className="font-black text-[#3b2511]">导入素材参考</h5>
    {selectedDetail.execution_context?.material_references.map((reference) => (
      <article key={`${reference.source_title}-${reference.title}`} className="rounded-xl border border-amber-900/10 bg-amber-50/35 p-3">
        <p className="font-bold text-[#3b2511]">{reference.title}（来源：{reference.source_title}）</p>
        <p className="manuscript mt-1 text-sm">{reference.summary}</p>
      </article>
    ))}
    <p className="manuscript text-sm font-bold text-[#5e3b1c]">这些导入素材只是本章创作参考，不代表已自动进入正式设定。</p>
  </div>
) : (
  <p className="manuscript mt-1 text-sm">本章未使用导入素材参考。</p>
)}
```

- [ ] **Step 4: Run test to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/ChapterHistoryPanel.test.tsx
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
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/ChapterHistoryPanel.test.tsx src/world/WorldPage.test.tsx src/world/WorldImportPanel.test.tsx src/world/NextChapterPrepPanel.test.tsx src/studio/StudioPage.test.tsx
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

Review diff for safe Chinese copy, hidden raw IDs/enums/slugs, and no formal canon mutation, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-chapter-history-import-reference-cards-design.md docs/superpowers/plans/2026-06-04-chapter-history-import-reference-cards.md frontend/src/world/ChapterHistoryPanel.tsx frontend/src/world/ChapterHistoryPanel.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: show history import reference cards"
```

Do not push. Do not merge main.
