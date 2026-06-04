# Chapter History Candidate Reference Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clarify chapter history imported-reference copy as candidate writing references.

**Architecture:** Frontend-only copy update in `ChapterHistoryPanel.tsx`. Change the visible material-reference heading and safety sentence only; keep chapter detail data, approval audit details, execution context details, and canon behavior unchanged.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/world/ChapterHistoryPanel.test.tsx`
  - Update material-reference heading and safety sentence assertions.
  - Preserve raw ID/enum hiding and formal approval audit assertions.
- Modify: `frontend/src/world/ChapterHistoryPanel.tsx`
  - Replace the visible section heading and explanatory sentence.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only.

---

### Task 1: Chapter history labels imports as candidate writing references

**Files:**
- Modify: `frontend/src/world/ChapterHistoryPanel.test.tsx`
- Modify: `frontend/src/world/ChapterHistoryPanel.tsx`

- [ ] **Step 1: Write the failing test**

In the chapter detail test, replace:

```ts
expect(screen.getByText('导入素材参考')).toBeInTheDocument();
```

With:

```ts
expect(screen.getByText('候选素材写作参考')).toBeInTheDocument();
```

Then replace:

```ts
expect(screen.getByText('这些导入素材只是本章创作参考，不代表已自动进入正式设定。')).toBeInTheDocument();
```

With:

```ts
expect(screen.getByText('这些候选素材只是本章创作参考，不代表已自动进入正式设定。')).toBeInTheDocument();
```

- [ ] **Step 2: Run test to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/ChapterHistoryPanel.test.tsx -t "loads chapter detail"
```

Expected: FAIL because production still renders `导入素材参考` and the older safety sentence.

- [ ] **Step 3: Write minimal implementation**

In `ChapterHistoryPanel.tsx`, change:

```tsx
<h5 className="font-black text-[#3b2511]">导入素材参考</h5>
```

To:

```tsx
<h5 className="font-black text-[#3b2511]">候选素材写作参考</h5>
```

Then change:

```tsx
<p className="manuscript text-sm font-bold text-[#5e3b1c]">这些导入素材只是本章创作参考，不代表已自动进入正式设定。</p>
```

To:

```tsx
<p className="manuscript text-sm font-bold text-[#5e3b1c]">这些候选素材只是本章创作参考，不代表已自动进入正式设定。</p>
```

- [ ] **Step 4: Run test to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/ChapterHistoryPanel.test.tsx -t "loads chapter detail"
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
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/ChapterHistoryPanel.test.tsx src/world/NextChapterPrepPanel.test.tsx src/world/WorldPage.test.tsx src/studio/StudioPage.test.tsx src/world/WorldImportPanel.test.tsx
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

Review diff for clearer candidate-reference wording, unchanged approval audit details, preserved imported-reference safety, and no formal canon mutation, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-chapter-history-candidate-reference-copy-design.md docs/superpowers/plans/2026-06-04-chapter-history-candidate-reference-copy.md frontend/src/world/ChapterHistoryPanel.tsx frontend/src/world/ChapterHistoryPanel.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: clarify chapter history import references"
```

Do not push. Do not merge main.
