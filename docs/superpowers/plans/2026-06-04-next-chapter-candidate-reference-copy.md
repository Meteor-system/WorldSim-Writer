# Next Chapter Candidate Reference Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clarify next-chapter imported-reference copy as candidate writing references.

**Architecture:** Frontend-only copy update in `NextChapterPrepPanel.tsx`. Change the visible material-reference section heading and safety sentence only; keep reference details, context payloads, buttons, prep behavior, and canon behavior unchanged.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/world/NextChapterPrepPanel.test.tsx`
  - Update material-reference heading and safety sentence assertions.
  - Preserve raw ID/enum hiding and context payload assertions.
- Modify: `frontend/src/world/WorldPage.test.tsx`
  - Update the import-confirmation regression assertion that renders the same next-chapter prep safety sentence.
- Modify: `frontend/src/world/NextChapterPrepPanel.tsx`
  - Replace the visible section heading and explanatory sentence.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only.

---

### Task 1: Next-chapter prep labels imports as candidate writing references

**Files:**
- Modify: `frontend/src/world/NextChapterPrepPanel.test.tsx`
- Modify: `frontend/src/world/NextChapterPrepPanel.tsx`

- [ ] **Step 1: Write the failing test**

In `renders next chapter prep signals with readable labels and builds execution context`, replace:

```ts
expect(screen.getByText('导入素材参考')).toBeInTheDocument();
```

With:

```ts
expect(screen.getByText('候选素材写作参考')).toBeInTheDocument();
```

Then replace:

```ts
expect(screen.getByText('这些素材只是下一章写作参考，不会自动改写正式设定。')).toBeInTheDocument();
```

With:

```ts
expect(screen.getByText('这些候选素材只是下一章写作参考，不会自动改写正式设定。')).toBeInTheDocument();
```

- [ ] **Step 2: Run test to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/NextChapterPrepPanel.test.tsx -t "renders next chapter prep signals"
```

Expected: FAIL because production still renders `导入素材参考` and the older safety sentence.

- [ ] **Step 3: Write minimal implementation**

In `NextChapterPrepPanel.tsx`, change:

```tsx
<h3 className="font-black text-[#3b2511]">导入素材参考</h3>
<p className="manuscript mt-2 text-sm text-[#5e3b1c]">这些素材只是下一章写作参考，不会自动改写正式设定。</p>
```

To:

```tsx
<h3 className="font-black text-[#3b2511]">候选素材写作参考</h3>
<p className="manuscript mt-2 text-sm text-[#5e3b1c]">这些候选素材只是下一章写作参考，不会自动改写正式设定。</p>
```

- [ ] **Step 4: Run test to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/NextChapterPrepPanel.test.tsx -t "renders next chapter prep signals"
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
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/NextChapterPrepPanel.test.tsx src/world/WorldPage.test.tsx src/studio/StudioPage.test.tsx src/world/WorldImportPanel.test.tsx src/world/ChapterHistoryPanel.test.tsx
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

Review diff for clearer candidate-reference wording, unchanged context payloads, preserved imported-reference safety, and no formal canon mutation, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-next-chapter-candidate-reference-copy-design.md docs/superpowers/plans/2026-06-04-next-chapter-candidate-reference-copy.md frontend/src/world/NextChapterPrepPanel.tsx frontend/src/world/NextChapterPrepPanel.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: clarify next chapter import references"
```

Do not push. Do not merge main.
