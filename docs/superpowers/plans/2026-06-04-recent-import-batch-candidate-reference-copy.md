# Recent Import Batch Candidate Reference Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clarify recent confirmed import batches as candidate writing references.

**Architecture:** Frontend-only copy update in `WorldImportPanel.tsx`. Change the recent-batch visible label and guardrail sentence only; keep import payloads, preview/confirm behavior, batch listing, asset counts, candidate labels, and canon behavior unchanged.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
  - Update the recent import batch test to expect candidate-reference wording.
  - Assert the older generic wording is not exposed.
  - Preserve raw ID, slug, enum, and non-candidate label hiding assertions.
- Modify: `frontend/src/world/WorldImportPanel.tsx`
  - Replace the visible recent-batch reference label and guardrail sentence.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only.

---

### Task 1: Recent batch labels confirmed imports as candidate writing references

**Files:**
- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
- Modify: `frontend/src/world/WorldImportPanel.tsx`

- [ ] **Step 1: Write the failing test**

In the recent import batch test, replace:

```ts
expect(screen.getByText('可用创作参考')).toBeInTheDocument();
expect(screen.getByText('这些素材只是写作参考，不会自动改写正式设定。')).toBeInTheDocument();
```

With:

```ts
expect(screen.getByText('候选素材写作参考')).toBeInTheDocument();
expect(screen.getByText('这些候选素材只是写作参考，不会自动改写正式设定。')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('可用创作参考');
expect(document.body).not.toHaveTextContent('这些素材只是写作参考，不会自动改写正式设定。');
```

- [ ] **Step 2: Run test to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx -t "loads recent import batches"
```

Expected: FAIL because production still renders the older recent-batch label and sentence.

- [ ] **Step 3: Write minimal implementation**

In `WorldImportPanel.tsx`, change:

```tsx
<p className="text-sm font-bold text-[#4a321e]">可用创作参考</p>
```

To:

```tsx
<p className="text-sm font-bold text-[#4a321e]">候选素材写作参考</p>
```

And change:

```tsx
<p className="manuscript mt-3 text-sm font-bold text-[#5e3b1c]">这些素材只是写作参考，不会自动改写正式设定。</p>
```

To:

```tsx
<p className="manuscript mt-3 text-sm font-bold text-[#5e3b1c]">这些候选素材只是写作参考，不会自动改写正式设定。</p>
```

- [ ] **Step 4: Run test to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx -t "loads recent import batches"
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
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-recent-import-batch-candidate-reference-copy-design.md docs/superpowers/plans/2026-06-04-recent-import-batch-candidate-reference-copy.md frontend/src/world/WorldImportPanel.tsx frontend/src/world/WorldImportPanel.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: clarify recent import references"
```

Do not push. Do not merge main.
