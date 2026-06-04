# Studio Approval Candidate Reference Note Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking. This run explicitly forbids subagents and workflows.

**Goal:** Show candidate material references at the Studio approval checkpoint as safe writing references, not formal state changes.

**Architecture:** Frontend-only conditional note inside `StudioPage` near `写入正史前确认`. The note derives display text from the active draft/chapter/execution context and does not change create, draft, or approve payloads.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/studio/StudioPage.test.tsx`
  - Add RED assertion in an existing candidate-reference drafting flow for the approval checkpoint note.
  - Preserve raw ID/enum/slug hiding assertions.
- Modify: `frontend/src/studio/StudioPage.tsx`
  - Add a small display helper for candidate reference names.
  - Render the note only when approval preview exists and candidate references are available.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only and do not mutate canon/world version.

---

### Task 1: Approval checkpoint names candidate writing references

**Files:**
- Modify: `frontend/src/studio/StudioPage.test.tsx`
- Modify: `frontend/src/studio/StudioPage.tsx`

- [ ] **Step 1: Write the failing test**

In `StudioPage.test.tsx`, inside `renders version selector, stash, paragraph controls, diff, and approval preview after drafting`, after:

```ts
expect(screen.getByText('写入正史前确认')).toBeInTheDocument();
```

Add:

```ts
expect(screen.getByText('候选素材写作参考')).toBeInTheDocument();
expect(screen.getByText('本章参考候选素材：雨夜审讯。')).toBeInTheDocument();
expect(screen.getByText('候选素材只帮助生成正文，不会作为正式设定变化写入；只有下方勾选的角色或伏笔变化会更新世界。')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('asset_id');
expect(document.body).not.toHaveTextContent('batch_id');
expect(document.body).not.toHaveTextContent('inspiration');
expect(document.body).not.toHaveTextContent('正式 canon');
```

- [ ] **Step 2: Run tests to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx -t "renders version selector"
```

Expected: FAIL because the approval checkpoint does not yet render the candidate-reference note.

- [ ] **Step 3: Write minimal implementation**

In `StudioPage.tsx`, after `materialReferenceSentence`, add:

```ts
function materialReferenceListSentence(titles: string[]): string {
  return `本章参考候选素材：${titles.join('、')}。`;
}
```

Inside `StudioPage`, after `const approvalBlockedByConsistency = consistencySummary?.status === 'blocked';`, add:

```ts
const reviewMaterialReferenceTitles = materialReferenceTitles(draft?.execution_context ?? chapter?.execution_context ?? executionContext);
```

Inside the `approvalPreview` section, after the selected-change count paragraph, render:

```tsx
{reviewMaterialReferenceTitles.length > 0 && (
  <div className="rounded-xl bg-white/45 p-3">
    <h4 className="font-black text-[#3b2511]">候选素材写作参考</h4>
    <p className="manuscript mt-2 text-sm">{materialReferenceListSentence(reviewMaterialReferenceTitles)}</p>
    <p className="manuscript mt-1 text-sm">候选素材只帮助生成正文，不会作为正式设定变化写入；只有下方勾选的角色或伏笔变化会更新世界。</p>
  </div>
)}
```

- [ ] **Step 4: Run tests to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx -t "renders version selector"
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
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx src/world/WorldPage.test.tsx src/world/WorldImportPanel.test.tsx src/world/NextChapterPrepPanel.test.tsx
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

Review diff for frontend-only scope, unchanged create/draft/approval payloads, unchanged import/canon behavior, unchanged approval transaction behavior, and preserved raw ID/enum hiding. Then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-05-studio-approval-candidate-reference-note-design.md docs/superpowers/plans/2026-06-05-studio-approval-candidate-reference-note.md frontend/src/studio/StudioPage.tsx frontend/src/studio/StudioPage.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: clarify approval candidate references"
```

Do not push. Do not merge main.
