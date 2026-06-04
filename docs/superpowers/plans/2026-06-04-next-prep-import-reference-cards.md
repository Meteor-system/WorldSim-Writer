# Next Chapter Prep Import Reference Cards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show imported candidate materials as safe, readable reference cards in Next Chapter Prep.

**Architecture:** Frontend-only rendering update in `NextChapterPrepPanel`. Existing `material_references` data and execution-context construction remain unchanged.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/world/NextChapterPrepPanel.test.tsx`
  - Update tests first for safe readable import reference cards.
- Modify: `frontend/src/world/NextChapterPrepPanel.tsx`
  - Render title/source/summary cards and Chinese safety copy.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only.

---

### Task 1: Next Chapter Prep shows safe imported material cards

**Files:**
- Modify: `frontend/src/world/NextChapterPrepPanel.test.tsx`
- Modify: `frontend/src/world/NextChapterPrepPanel.tsx`

- [ ] **Step 1: Write the failing test**

In `renders next chapter prep signals and uses suggested goal callback`, replace the simple material assertions with:

```ts
expect(screen.getByText('导入素材参考')).toBeInTheDocument();
expect(screen.getByText('雨夜审讯（来源：旧设定.md）')).toBeInTheDocument();
expect(screen.getByText('雨夜审讯从一盏坏灯开始。')).toBeInTheDocument();
expect(screen.getByText('这些素材只是下一章写作参考，不会自动改写正式设定。')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('正式 canon');
expect(document.body).not.toHaveTextContent('asset_id');
expect(document.body).not.toHaveTextContent('batch_id');
expect(document.body).not.toHaveTextContent('inspiration');
```

- [ ] **Step 2: Run test to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/NextChapterPrepPanel.test.tsx -t "renders next chapter prep"
```

Expected: FAIL because the title/source combined copy and `正式设定` safety wording are not present yet.

- [ ] **Step 3: Write minimal implementation**

In `NextChapterPrepPanel.tsx`, update the material reference block to render:

```tsx
{(prep.material_references ?? []).length > 0 && (
  <section className="rounded-2xl bg-white/35 p-4">
    <h3 className="font-black text-[#3b2511]">导入素材参考</h3>
    <p className="manuscript mt-2 text-sm text-[#5e3b1c]">这些素材只是下一章写作参考，不会自动改写正式设定。</p>
    <div className="mt-3 space-y-3">
      {(prep.material_references ?? []).map((reference) => (
        <article key={`${reference.source_title}-${reference.title}`} className="rounded-xl border border-amber-900/10 bg-amber-50/35 p-3">
          <p className="font-bold text-[#3b2511]">{reference.title}（来源：{reference.source_title}）</p>
          <p className="manuscript mt-1 text-sm">{reference.summary}</p>
        </article>
      ))}
    </div>
  </section>
)}
```

- [ ] **Step 4: Run test to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/NextChapterPrepPanel.test.tsx
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
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/NextChapterPrepPanel.test.tsx src/world/WorldImportPanel.test.tsx src/world/WorldPage.test.tsx src/studio/StudioPage.test.tsx
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

Review diff for safe copy, hidden raw IDs/enums, and no formal canon mutation, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-next-prep-import-reference-cards-design.md docs/superpowers/plans/2026-06-04-next-prep-import-reference-cards.md frontend/src/world/NextChapterPrepPanel.tsx frontend/src/world/NextChapterPrepPanel.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: show next prep import reference cards"
```

Do not push. Do not merge main.
