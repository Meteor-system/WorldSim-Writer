# Studio Frozen Context Source Label Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the raw Studio frozen execution-context source slug with a readable Chinese source label.

**Architecture:** Frontend-only copy update in `ExecutionContextSummary` inside `StudioPage.tsx`. Use the existing `sourceLabel()` helper; imported reference cards, frozen context data, Studio generation, and approval behavior remain unchanged.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/studio/StudioPage.test.tsx`
  - Update the frozen-context test first.
- Modify: `frontend/src/studio/StudioPage.tsx`
  - Use `sourceLabel(context.source)` in the frozen banner.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only.

---

### Task 1: Studio frozen context banner hides source slug

**Files:**
- Modify: `frontend/src/studio/StudioPage.test.tsx`
- Modify: `frontend/src/studio/StudioPage.tsx`

- [ ] **Step 1: Write the failing test**

In `shows launch execution context summary and submits edited context when creating chapter`, replace the post-create frozen banner assertion with:

```ts
expect(await screen.findByText('已冻结执行上下文：下一章准备台 · v2')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('已冻结执行上下文：next_chapter_prep · v2');
```

Keep the existing imported material reference assertions.

- [ ] **Step 2: Run test to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx -t "shows launch execution context summary"
```

Expected: FAIL because the frozen banner still shows `next_chapter_prep`.

- [ ] **Step 3: Write minimal implementation**

In `ExecutionContextSummary`, change:

```tsx
{frozen && <p className="mt-2 text-sm font-bold text-[#5e3b1c]">已冻结执行上下文：{context.source} · v{context.source_world_version}</p>}
```

To:

```tsx
{frozen && <p className="mt-2 text-sm font-bold text-[#5e3b1c]">已冻结执行上下文：{sourceLabel(context.source)} · v{context.source_world_version}</p>}
```

- [ ] **Step 4: Run test to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx -t "shows launch execution context summary"
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
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx src/world/WorldPage.test.tsx src/world/NextChapterPrepPanel.test.tsx src/world/WorldImportPanel.test.tsx src/world/ChapterHistoryPanel.test.tsx
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

Review diff for readable Chinese copy, hidden source slug, preserved import-reference safety, and no formal canon mutation, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-studio-frozen-context-source-label-design.md docs/superpowers/plans/2026-06-04-studio-frozen-context-source-label.md frontend/src/studio/StudioPage.tsx frontend/src/studio/StudioPage.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: localize studio frozen context source"
```

Do not push. Do not merge main.
