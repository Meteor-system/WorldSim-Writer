# Studio Candidate Reference Label Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clarify the Studio imported-reference count label as candidate material references.

**Architecture:** Frontend-only copy update in `StudioPage.tsx`. Change the visible material-reference count label only; keep execution context payloads, approval behavior, imported reference details, world refresh, and canon behavior unchanged.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/studio/StudioPage.test.tsx`
  - Update the execution context summary assertion.
  - Assert the old ambiguous count label is not exposed.
- Modify: `frontend/src/studio/StudioPage.tsx`
  - Replace the visible count label in `MaterialReferenceCards`.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only.

---

### Task 1: Studio labels imported references as candidate material

**Files:**
- Modify: `frontend/src/studio/StudioPage.test.tsx`
- Modify: `frontend/src/studio/StudioPage.tsx`

- [ ] **Step 1: Write the failing test**

In `shows launch execution context summary and submits edited context when creating chapter`, replace:

```ts
expect(screen.getByText('导入素材参考：1 条')).toBeInTheDocument();
```

With:

```ts
expect(screen.getByText('候选素材参考：1 条')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('导入素材参考：1 条');
```

- [ ] **Step 2: Run test to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx -t "launch execution context summary"
```

Expected: FAIL because production still renders `导入素材参考：1 条`.

- [ ] **Step 3: Write minimal implementation**

In `StudioPage.tsx`, change:

```tsx
<p className="text-sm font-bold text-[#4a321e]">导入素材参考：{references.length} 条</p>
```

To:

```tsx
<p className="text-sm font-bold text-[#4a321e]">候选素材参考：{references.length} 条</p>
```

- [ ] **Step 4: Run test to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx -t "launch execution context summary"
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

Review diff for clearer candidate-reference wording, unchanged execution context payloads, preserved imported-reference safety, and no formal canon mutation, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-studio-candidate-reference-label-design.md docs/superpowers/plans/2026-06-04-studio-candidate-reference-label.md frontend/src/studio/StudioPage.tsx frontend/src/studio/StudioPage.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: clarify studio candidate references"
```

Do not push. Do not merge main.
