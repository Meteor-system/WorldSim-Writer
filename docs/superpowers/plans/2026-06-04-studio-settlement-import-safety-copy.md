# Studio Settlement Import Safety Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace raw canon wording in the Studio approval settlement with clear Chinese import-reference safety copy.

**Architecture:** Frontend-only copy update in the existing `StudioPage` settlement panel. Existing approval flow, world settlement state, event checks, export controls, and Studio handoff remain unchanged.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/studio/StudioPage.test.tsx`
  - Update the settlement test first.
- Modify: `frontend/src/studio/StudioPage.tsx`
  - Replace raw `canon` wording in the settlement copy.
- Verify: `backend/tests/test_import_node.py`
  - Existing backend import safety tests prove imports remain candidate/audit only.

---

### Task 1: Studio settlement uses safe Chinese import-reference copy

**Files:**
- Modify: `frontend/src/studio/StudioPage.test.tsx`
- Modify: `frontend/src/studio/StudioPage.tsx`

- [ ] **Step 1: Write the failing test**

In `shows world progression settlement after approval before returning to overview`, replace the current import-safety assertion with:

```ts
expect(screen.getByText('这一章已写入正式设定，后续章节会继承本次世界变化。')).toBeInTheDocument();
expect(screen.getByText('导入素材仍是本章创作参考，没有自动写入正式设定。')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('正式 canon');
expect(document.body).not.toHaveTextContent('正史 / canon');
expect(document.body).not.toHaveTextContent('asset_id');
expect(document.body).not.toHaveTextContent('batch_id');
expect(document.body).not.toHaveTextContent('inspiration');
```

Keep the existing assertions for:

```ts
expect(screen.getByText('本章参考了 1 条导入素材：雨夜审讯。')).toBeInTheDocument();
expect(screen.getByText('正式事件：章节已批准并写入世界历史。')).toBeInTheDocument();
expect(screen.queryByText('chapter_approved · 世界 1 → 2')).not.toBeInTheDocument();
```

- [ ] **Step 2: Run test to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx -t "shows world progression settlement"
```

Expected: FAIL because settlement still displays `正史 / canon` and `正式 canon` copy.

- [ ] **Step 3: Write minimal implementation**

In `StudioPage.tsx`, update the settlement copy:

```tsx
<p className="manuscript mt-2">这一章已写入正式设定，后续章节会继承本次世界变化。</p>
```

and:

```tsx
<p className="manuscript mt-2 text-sm">导入素材仍是本章创作参考，没有自动写入正式设定。</p>
```

- [ ] **Step 4: Run test to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx -t "shows world progression settlement"
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
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx src/world/ChapterHistoryPanel.test.tsx src/world/WorldPage.test.tsx src/world/WorldImportPanel.test.tsx src/world/NextChapterPrepPanel.test.tsx
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
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-studio-settlement-import-safety-copy-design.md docs/superpowers/plans/2026-06-04-studio-settlement-import-safety-copy.md frontend/src/studio/StudioPage.tsx frontend/src/studio/StudioPage.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: clarify studio settlement import safety"
```

Do not push. Do not merge main.
