# Import Node Recent Reference Cards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Surface confirmed candidate imported materials as safe writing references in recent import cards without mutating formal canon.

**Architecture:** Frontend-only rendering improvement in `WorldImportPanel`. Existing backend list data already includes batch assets, so no API or persistence changes are needed.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
  - Extend recent batch test with TDD assertions for safe reference display and hidden raw IDs/enums.
- Modify: `frontend/src/world/WorldImportPanel.tsx`
  - Render candidate asset references inside recent batch cards with Chinese labels and safety copy.
- Verify: `backend/tests/test_import_node.py`
  - Existing safety tests confirm imports remain candidate/audit only.

---

### Task 1: Recent import cards show safe writing references

**Files:**
- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
- Modify: `frontend/src/world/WorldImportPanel.tsx`

- [ ] **Step 1: Write the failing test**

In `loads recent import batches as source audit history`, add expectations:

```ts
expect(screen.getByText('可用创作参考')).toBeInTheDocument();
expect(screen.getByText('正式设定候选：青岚城密探规则')).toBeInTheDocument();
expect(screen.getByText('角色候选：沈微霜')).toBeInTheDocument();
expect(screen.getByText('灵感候选：雨夜审讯')).toBeInTheDocument();
expect(screen.getByText('密探必须隐藏真实姓名。')).toBeInTheDocument();
expect(screen.getByText('这些素材只是写作参考，不会自动改写正式设定。')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('batch #12');
expect(document.body).not.toHaveTextContent('asset #1');
expect(document.body).not.toHaveTextContent('inspiration');
expect(document.body).not.toHaveTextContent('character');
expect(document.body).not.toHaveTextContent('canon 候选');
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx -t "loads recent import batches"
```

Expected: FAIL because recent batch cards do not render the candidate reference titles yet.

- [ ] **Step 3: Write minimal implementation**

Add a helper:

```ts
function assetReferenceLabel(asset: ImportCandidateAssetPreview) {
  return `${POOL_LABELS[asset.asset_pool]}：${asset.title}`;
}
```

Inside each recent batch card, after the count text, render:

```tsx
{batch.assets.length > 0 && (
  <div className="mt-3 rounded-2xl bg-white/45 p-3">
    <p className="text-sm font-bold text-[#4a321e]">可用创作参考</p>
    <div className="mt-2 space-y-2">
      {batch.assets.map((asset, index) => (
        <article key={`${asset.title}-${index}`}>
          <p className="text-sm font-bold text-[#5e3b1c]">{assetReferenceLabel(asset)}</p>
          <p className="manuscript mt-1 text-sm text-[#5e3b1c]">{asset.summary}</p>
        </article>
      ))}
    </div>
    <p className="manuscript mt-3 text-sm font-bold text-[#5e3b1c]">这些素材只是写作参考，不会自动改写正式设定。</p>
  </div>
)}
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx
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
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx src/world/WorldPage.test.tsx src/world/NextChapterPrepPanel.test.tsx
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

Review diff for raw IDs/enums and safety invariant, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-import-node-recent-reference-cards-design.md docs/superpowers/plans/2026-06-04-import-node-recent-reference-cards.md frontend/src/world/WorldImportPanel.tsx frontend/src/world/WorldImportPanel.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: show import candidates as writing references"
```

Do not push. Do not merge main.
