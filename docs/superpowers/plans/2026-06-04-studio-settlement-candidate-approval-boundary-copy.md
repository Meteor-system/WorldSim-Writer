# Studio Settlement Candidate Approval Boundary Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking. This run explicitly forbids subagents and workflows.

**Goal:** Clarify in the Studio approval settlement that candidate materials stayed writing references while approval wrote the chapter and formal world changes.

**Architecture:** Frontend-only copy update in `StudioPage`. Tests cover the post-approval settlement copy so the later review surface reinforces the candidate-only boundary without changing approval transactions, import persistence, event history, or world projection behavior.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import and approval safety regression.

---

## File Structure

- Modify: `frontend/src/studio/StudioPage.test.tsx`
  - Update the candidate-reference settlement test to expect the clearer approval-boundary note.
  - Assert the old note is not visible.
  - Preserve raw ID/enum/slug hiding assertions.
- Modify: `frontend/src/studio/StudioPage.tsx`
  - Replace the visible settlement candidate-material note only.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only and do not mutate canon/world version.
- Verify: `backend/tests/test_narrative_approval.py`
  - Existing approval tests prove formal world changes still require chapter approval.

---

### Task 1: Studio settlement uses approval-boundary candidate copy

**Files:**
- Modify: `frontend/src/studio/StudioPage.test.tsx`
- Modify: `frontend/src/studio/StudioPage.tsx`

- [ ] **Step 1: Write the failing test**

In `StudioPage.test.tsx`, inside the settlement test that currently asserts candidate references after approval, replace:

```ts
expect(screen.getByText('候选素材仍是本章创作参考，没有自动写入正式设定。')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('导入素材仍是本章创作参考，没有自动写入正式设定。');
```

With:

```ts
expect(screen.getByText('候选素材仍只是本章写作参考；本次批准只写入章节正文和世界变化。')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('候选素材仍是本章创作参考，没有自动写入正式设定。');
expect(document.body).not.toHaveTextContent('导入素材仍是本章创作参考，没有自动写入正式设定。');
```

- [ ] **Step 2: Run tests to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx -t "world progress settlement"
```

Expected: FAIL because production still renders `候选素材仍是本章创作参考，没有自动写入正式设定。`.

- [ ] **Step 3: Write minimal implementation**

In `StudioPage.tsx`, replace:

```tsx
<p className="manuscript mt-2 text-sm">候选素材仍是本章创作参考，没有自动写入正式设定。</p>
```

With:

```tsx
<p className="manuscript mt-2 text-sm">候选素材仍只是本章写作参考；本次批准只写入章节正文和世界变化。</p>
```

- [ ] **Step 4: Run tests to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx -t "world progress settlement"
```

Expected: PASS.

---

### Task 2: Final verification and commit

- [ ] **Step 1: Run backend import and approval safety tests**

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 ./.venv/bin/pytest tests/test_import_node.py tests/test_narrative_approval.py -v
```

Expected: PASS.

- [ ] **Step 2: Run frontend targeted tests**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx src/world/ChapterHistoryPanel.test.tsx src/world/WorldPage.test.tsx src/world/WorldImportPanel.test.tsx src/world/NextChapterPrepPanel.test.tsx
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

Review diff for approval-boundary settlement wording, unchanged import/canon behavior, unchanged approval behavior, and preserved raw ID/enum hiding, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-studio-settlement-candidate-approval-boundary-copy-design.md docs/superpowers/plans/2026-06-04-studio-settlement-candidate-approval-boundary-copy.md frontend/src/studio/StudioPage.tsx frontend/src/studio/StudioPage.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: clarify candidate settlement boundary"
```

Do not push. Do not merge main.
