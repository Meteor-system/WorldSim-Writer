# First Chapter Candidate Reference Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clarify the first-chapter launchpad imported-reference count as candidate writing references.

**Architecture:** Frontend-only copy update in `WorldPage.tsx`. Change the visible count sentence only; keep material reference details, Studio launch payloads, story arc behavior, and canon behavior unchanged.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/world/WorldPage.test.tsx`
  - Update the first-chapter launchpad imported-reference count assertion.
  - Assert the old ambiguous count sentence is not exposed.
- Modify: `frontend/src/world/WorldPage.tsx`
  - Replace the visible count sentence in the launchpad import-reference section.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only.

---

### Task 1: First-chapter launchpad labels imports as candidate writing references

**Files:**
- Modify: `frontend/src/world/WorldPage.test.tsx`
- Modify: `frontend/src/world/WorldPage.tsx`

- [ ] **Step 1: Write the failing test**

In the test that renders the first-chapter launchpad with imported references, replace:

```ts
expect(await screen.findByText('已准备 1 条导入素材参考。')).toBeInTheDocument();
```

With:

```ts
expect(await screen.findByText('已准备 1 条候选素材写作参考。')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('已准备 1 条导入素材参考。');
```

- [ ] **Step 2: Run test to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx -t "passes imported material references into the first chapter Studio launch context"
```

Expected: FAIL because production still renders `已准备 1 条导入素材参考。`.

- [ ] **Step 3: Write minimal implementation**

In `WorldPage.tsx`, change:

```tsx
<p className="manuscript mt-1 text-sm">已准备 {materialReferences.length} 条导入素材参考。</p>
```

To:

```tsx
<p className="manuscript mt-1 text-sm">已准备 {materialReferences.length} 条候选素材写作参考。</p>
```

- [ ] **Step 4: Run test to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx -t "passes imported material references into the first chapter Studio launch context"
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
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx src/studio/StudioPage.test.tsx src/world/WorldImportPanel.test.tsx src/world/NextChapterPrepPanel.test.tsx src/world/ChapterHistoryPanel.test.tsx
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

Review diff for clearer candidate-reference wording, unchanged Studio launch payloads, preserved imported-reference safety, and no formal canon mutation, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-first-chapter-candidate-reference-copy-design.md docs/superpowers/plans/2026-06-04-first-chapter-candidate-reference-copy.md frontend/src/world/WorldPage.tsx frontend/src/world/WorldPage.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: clarify first chapter import references"
```

Do not push. Do not merge main.
