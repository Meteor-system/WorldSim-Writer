# Studio Import Reference Cards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show imported material references as readable safe writing reference cards in Studio.

**Architecture:** Frontend-only rendering change in `StudioPage`. Existing `ChapterExecutionContext.material_references` data is already available before chapter creation and after drafting.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/studio/StudioPage.test.tsx`
  - Update tests first for safe readable Studio import references.
- Modify: `frontend/src/studio/StudioPage.tsx`
  - Add reusable material reference card renderer and replace one-line/raw copy.
- Verify: `backend/tests/test_import_node.py`
  - Existing backend safety tests prove imports remain candidate/audit only.

---

### Task 1: Studio shows safe imported material reference cards

**Files:**
- Modify: `frontend/src/studio/StudioPage.test.tsx`
- Modify: `frontend/src/studio/StudioPage.tsx`

- [ ] **Step 1: Write the failing tests**

In `shows launch execution context summary and submits edited context when creating chapter`, replace the raw safety assertion with:

```ts
expect(screen.getByText('导入素材参考：1 条')).toBeInTheDocument();
expect(screen.getByText('雨夜审讯（来源：旧设定.md）')).toBeInTheDocument();
expect(screen.getByText('雨夜审讯从一盏坏灯开始。')).toBeInTheDocument();
expect(screen.getByText('导入素材只是本章写作参考，不会自动改写正式设定。')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('正式 canon');
expect(document.body).not.toHaveTextContent('asset_id');
expect(document.body).not.toHaveTextContent('batch_id');
expect(document.body).not.toHaveTextContent('inspiration');
```

In `shows frozen execution context snapshot after drafting`, replace the one-line material assertion with:

```ts
expect(screen.getAllByText('雨夜审讯（来源：旧设定.md）').length).toBeGreaterThan(0);
expect(screen.getAllByText('雨夜审讯从一盏坏灯开始。').length).toBeGreaterThan(0);
expect(screen.getByText('素材参考不会自动改写正式设定。')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('素材参考不会自动改写正式 canon。');
```

- [ ] **Step 2: Run test to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx -t "launch execution context"
```

Expected: FAIL because Studio does not show the material summary/source card yet and still uses `正式 canon`.

- [ ] **Step 3: Write minimal implementation**

Add a small renderer in `StudioPage.tsx`:

```tsx
function MaterialReferenceCards({ context, compact = false }: { context?: ChapterExecutionContext | null; compact?: boolean }) {
  const references = context?.material_references ?? [];
  if (references.length === 0) return null;
  return (
    <div className={compact ? 'mt-3 space-y-2' : 'mt-3 rounded-2xl bg-white/45 p-3'}>
      {!compact && <p className="text-sm font-bold text-[#4a321e]">导入素材参考：{references.length} 条</p>}
      {references.map((reference) => (
        <article key={`${reference.source_title}-${reference.title}`} className="rounded-xl border border-amber-900/10 bg-amber-50/35 p-3">
          <p className="manuscript text-sm font-bold text-[#5e3b1c]">{reference.title}（来源：{reference.source_title}）</p>
          <p className="manuscript mt-1 text-sm text-[#5e3b1c]">{reference.summary}</p>
        </article>
      ))}
      <p className="manuscript text-sm font-bold text-[#5e3b1c]">{compact ? '素材参考不会自动改写正式设定。' : '导入素材只是本章写作参考，不会自动改写正式设定。'}</p>
    </div>
  );
}
```

Use it in `ExecutionContextSummary` and `ExecutionContextSnapshot`.

- [ ] **Step 4: Run test to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx
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
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx src/world/WorldImportPanel.test.tsx src/world/WorldPage.test.tsx src/world/NextChapterPrepPanel.test.tsx
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
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-studio-import-reference-cards-design.md docs/superpowers/plans/2026-06-04-studio-import-reference-cards.md frontend/src/studio/StudioPage.tsx frontend/src/studio/StudioPage.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: show studio import reference cards"
```

Do not push. Do not merge main.
