# Studio Settlement Candidate Reference Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clarify in the Studio approval settlement that imported materials were candidate writing references.

**Architecture:** Frontend-only copy update in `StudioPage.tsx`. Change the settlement sentence formatter only; keep approval behavior, world refresh, material reference title extraction, and canon behavior unchanged.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/studio/StudioPage.test.tsx`
  - Update the world progression settlement assertion.
  - Assert the older ambiguous sentence is not exposed.
- Modify: `frontend/src/studio/StudioPage.tsx`
  - Update `materialReferenceSentence()` for non-empty imported reference titles.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only.

---

### Task 1: Settlement sentence marks imports as candidate writing references

**Files:**
- Modify: `frontend/src/studio/StudioPage.test.tsx`
- Modify: `frontend/src/studio/StudioPage.tsx`

- [ ] **Step 1: Write the failing test**

In `shows world progression settlement after approval before returning to overview`, replace:

```ts
expect(screen.getByText('本章参考了 1 条导入素材：雨夜审讯。')).toBeInTheDocument();
```

With:

```ts
expect(screen.getByText('本章使用 1 条候选素材作为写作参考：雨夜审讯。')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('本章参考了 1 条导入素材：雨夜审讯。');
```

- [ ] **Step 2: Run test to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx -t "world progression settlement"
```

Expected: FAIL because production still renders the older settlement sentence.

- [ ] **Step 3: Write minimal implementation**

In `StudioPage.tsx`, change:

```ts
return `本章参考了 ${titles.length} 条导入素材：${titles.join('、')}。`;
```

To:

```ts
return `本章使用 ${titles.length} 条候选素材作为写作参考：${titles.join('、')}。`;
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

Review diff for safer candidate-reference wording, unchanged approval payloads, preserved imported-reference safety, and no formal canon mutation, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-studio-settlement-candidate-reference-copy-design.md docs/superpowers/plans/2026-06-04-studio-settlement-candidate-reference-copy.md frontend/src/studio/StudioPage.tsx frontend/src/studio/StudioPage.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: clarify settlement import references"
```

Do not push. Do not merge main.
