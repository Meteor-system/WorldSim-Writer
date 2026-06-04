# First Chapter Launchpad Readable Label Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the English first-chapter launchpad label with readable Chinese copy.

**Architecture:** Frontend-only copy update in `WorldPage.tsx`. Change the visible kicker text only; keep story arc planning, Studio launch context, imported candidate material references, API calls, and canon behavior unchanged.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/world/WorldPage.test.tsx`
  - Update first-chapter launchpad expectations to `第一章启动台`.
  - Assert `First Chapter Launchpad` is not exposed.
- Modify: `frontend/src/world/WorldPage.tsx`
  - Replace the visible launchpad kicker text.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only.

---

### Task 1: First chapter launchpad label is readable Chinese

**Files:**
- Modify: `frontend/src/world/WorldPage.test.tsx`
- Modify: `frontend/src/world/WorldPage.tsx`

- [ ] **Step 1: Write the failing test**

In the first-chapter launchpad tests, replace `First Chapter Launchpad` expectations with `第一章启动台`, and add:

```ts
expect(document.body).not.toHaveTextContent('First Chapter Launchpad');
```

- [ ] **Step 2: Run test to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx -t "first chapter launchpad"
```

Expected: FAIL because production still renders `First Chapter Launchpad`.

- [ ] **Step 3: Write minimal implementation**

In `WorldPage.tsx`, change:

```tsx
<p className="chapter-kicker">First Chapter Launchpad</p>
```

To:

```tsx
<p className="chapter-kicker">第一章启动台</p>
```

- [ ] **Step 4: Run test to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx -t "first chapter launchpad"
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
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx src/world/WorldImportPanel.test.tsx src/world/NextChapterPrepPanel.test.tsx src/studio/StudioPage.test.tsx src/world/ChapterHistoryPanel.test.tsx
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

Review diff for Chinese onboarding copy, unchanged Studio context payloads, preserved Import Node candidate safety, and no formal canon mutation, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-first-chapter-launchpad-readable-label-design.md docs/superpowers/plans/2026-06-04-first-chapter-launchpad-readable-label.md frontend/src/world/WorldPage.tsx frontend/src/world/WorldPage.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: localize first chapter launchpad"
```

Do not push. Do not merge main.
