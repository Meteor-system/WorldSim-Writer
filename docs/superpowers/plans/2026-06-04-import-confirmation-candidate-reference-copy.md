# Import Confirmation Candidate Reference Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clarify the import confirmation success state as candidate writing references for later creation.

**Architecture:** Frontend-only copy update in `WorldImportPanel.tsx`. Change the visible success sentence only; keep import payloads, preview/confirm behavior, asset counts, recent batches, and canon behavior unchanged.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
  - Update the import confirmation success-copy assertion.
  - Assert the older generic sentence is not exposed.
  - Preserve batch ID and raw enum/count hiding assertions.
- Modify: `frontend/src/world/WorldImportPanel.tsx`
  - Replace the visible import confirmation sentence.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only.

---

### Task 1: Import confirmation labels imports as candidate writing references

**Files:**
- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
- Modify: `frontend/src/world/WorldImportPanel.tsx`

- [ ] **Step 1: Write the failing test**

In the import confirmation test, replace:

```ts
expect(screen.getByText('这些素材会作为创作参考出现在下一章准备区，不会自动改写正式设定。')).toBeInTheDocument();
```

With:

```ts
expect(screen.getByText('这些候选素材会作为写作参考出现在下一章准备区，不会自动改写正式设定。')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('这些素材会作为创作参考出现在下一章准备区，不会自动改写正式设定。');
```

- [ ] **Step 2: Run test to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx -t "submits preview and confirm payloads"
```

Expected: FAIL because production still renders the older success sentence.

- [ ] **Step 3: Write minimal implementation**

In `WorldImportPanel.tsx`, change:

```tsx
<p className="mt-1 font-normal">这些素材会作为创作参考出现在下一章准备区，不会自动改写正式设定。</p>
```

To:

```tsx
<p className="mt-1 font-normal">这些候选素材会作为写作参考出现在下一章准备区，不会自动改写正式设定。</p>
```

- [ ] **Step 4: Run test to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx -t "submits preview and confirm payloads"
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
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx src/world/NextChapterPrepPanel.test.tsx src/world/WorldPage.test.tsx src/studio/StudioPage.test.tsx src/world/ChapterHistoryPanel.test.tsx
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

Review diff for clearer candidate-reference wording, unchanged import payloads, preserved imported-reference safety, and no formal canon mutation, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-import-confirmation-candidate-reference-copy-design.md docs/superpowers/plans/2026-06-04-import-confirmation-candidate-reference-copy.md frontend/src/world/WorldImportPanel.tsx frontend/src/world/WorldImportPanel.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: clarify import confirmation references"
```

Do not push. Do not merge main.
