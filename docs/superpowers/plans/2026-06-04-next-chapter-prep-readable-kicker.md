# Next Chapter Prep Readable Kicker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the English Next Chapter Prep kicker with readable Chinese copy.

**Architecture:** Frontend-only copy update in `NextChapterPrepPanel.tsx`. Change the visible kicker text only; keep callbacks, execution context construction, imported material references, API payloads, and canon behavior unchanged.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/world/NextChapterPrepPanel.test.tsx`
  - Add readable kicker expectations.
  - Assert the old English label is not exposed.
- Modify: `frontend/src/world/NextChapterPrepPanel.tsx`
  - Replace the visible kicker text.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only.

---

### Task 1: Next chapter prep kicker is readable Chinese

**Files:**
- Modify: `frontend/src/world/NextChapterPrepPanel.test.tsx`
- Modify: `frontend/src/world/NextChapterPrepPanel.tsx`

- [ ] **Step 1: Write the failing test**

In `renders next chapter prep signals and uses suggested goal callback`, add:

```ts
expect(screen.getByText('下一章写作准备')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('Next Chapter Prep');
```

Keep the existing callback assertions to prove behavior and imported references still pass through unchanged.

- [ ] **Step 2: Run test to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/NextChapterPrepPanel.test.tsx -t "renders next chapter prep signals"
```

Expected: FAIL because production still renders `Next Chapter Prep`.

- [ ] **Step 3: Write minimal implementation**

In `NextChapterPrepPanel.tsx`, change:

```tsx
<p className="chapter-kicker">Next Chapter Prep</p>
```

To:

```tsx
<p className="chapter-kicker">下一章写作准备</p>
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
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/NextChapterPrepPanel.test.tsx src/world/WorldPage.test.tsx src/world/WorldImportPanel.test.tsx src/studio/StudioPage.test.tsx src/world/ChapterHistoryPanel.test.tsx
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

Review diff for Chinese writing-prep copy, unchanged callback payloads, preserved imported-reference safety, and no formal canon mutation, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-next-chapter-prep-readable-kicker-design.md docs/superpowers/plans/2026-06-04-next-chapter-prep-readable-kicker.md frontend/src/world/NextChapterPrepPanel.tsx frontend/src/world/NextChapterPrepPanel.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: localize next chapter prep kicker"
```

Do not push. Do not merge main.
