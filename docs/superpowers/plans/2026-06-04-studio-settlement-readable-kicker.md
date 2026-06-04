# Studio Settlement Readable Kicker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the English Studio settlement kicker with readable Chinese copy.

**Architecture:** Frontend-only copy update in `StudioPage.tsx`. Change the visible settlement kicker text only; keep approval behavior, imported material reference copy, world refresh, and canon behavior unchanged.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/studio/StudioPage.test.tsx`
  - Add settlement kicker expectations.
  - Assert the old English kicker is not exposed.
- Modify: `frontend/src/studio/StudioPage.tsx`
  - Replace the visible settlement kicker text.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only.

---

### Task 1: Settlement kicker is readable Chinese

**Files:**
- Modify: `frontend/src/studio/StudioPage.test.tsx`
- Modify: `frontend/src/studio/StudioPage.tsx`

- [ ] **Step 1: Write the failing test**

In `shows world progression settlement after approval before returning to overview`, add these assertions near the settlement heading checks:

```ts
expect(screen.getByText('正史结算')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('Canon Settlement');
```

- [ ] **Step 2: Run test to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx -t "world progression settlement"
```

Expected: FAIL because production still renders `Canon Settlement`.

- [ ] **Step 3: Write minimal implementation**

In `StudioPage.tsx`, change:

```tsx
<p className="chapter-kicker">Canon Settlement</p>
```

To:

```tsx
<p className="chapter-kicker">正史结算</p>
```

- [ ] **Step 4: Run test to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx -t "world progression settlement"
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
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx src/world/WorldImportPanel.test.tsx src/world/NextChapterPrepPanel.test.tsx src/world/WorldPage.test.tsx src/world/ChapterHistoryPanel.test.tsx
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

Review diff for Chinese settlement copy, unchanged approval payloads, preserved imported-reference safety, and no formal canon mutation, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-studio-settlement-readable-kicker-design.md docs/superpowers/plans/2026-06-04-studio-settlement-readable-kicker.md frontend/src/studio/StudioPage.tsx frontend/src/studio/StudioPage.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: localize studio settlement kicker"
```

Do not push. Do not merge main.
