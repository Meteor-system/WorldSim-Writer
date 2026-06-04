# Import Node Readable Audit Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Import Node preview and audit copy Chinese-readable and hide raw pool/conflict enum wording.

**Architecture:** Frontend-only presentation change in `WorldImportPanel`. Existing backend payloads remain unchanged; UI maps/sanitizes backend values before rendering.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for safety regression.

---

## File Structure

- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
  - Add/adjust expectations for Chinese pool/count/conflict copy and absence of raw enum wording.
- Modify: `frontend/src/world/WorldImportPanel.tsx`
  - Add readable labels and conflict display helper.
- Verify: `backend/tests/test_import_node.py`
  - Existing backend safety tests prove import confirmation remains candidate/audit only.

---

### Task 1: WorldImportPanel readable import labels

**Files:**
- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
- Modify: `frontend/src/world/WorldImportPanel.tsx`

- [ ] **Step 1: Write the failing test**

Update the preview test to expect:

```ts
expect(await screen.findByText('正式设定候选')).toBeInTheDocument();
expect(screen.getByText('角色候选')).toBeInTheDocument();
expect(screen.getByText('灵感候选')).toBeInTheDocument();
expect(screen.getByText('这份素材可能和已有正式设定重叠：青岚城')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('canon 候选');
expect(document.body).not.toHaveTextContent('canon 1');
expect(document.body).not.toHaveTextContent('canon_overlap');
expect(document.body).not.toHaveTextContent('导入内容提到已有 canon 关键词');
```

Update the confirm test to expect:

```ts
expect(within(audit).getByText('正式设定 1 · 角色 1 · 灵感 1')).toBeInTheDocument();
expect(within(audit).queryByText('canon 1 · 角色 1 · 灵感 1')).not.toBeInTheDocument();
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx -t "previews imported material"
```

Expected: FAIL because the UI still displays `canon 候选`, `canon 1`, and raw backend conflict message.

- [ ] **Step 3: Write minimal implementation**

In `WorldImportPanel.tsx`:

```ts
const POOL_LABELS: Record<ImportCandidateAssetPreview['asset_pool'], string> = {
  canon: '正式设定候选',
  character: '角色候选',
  inspiration: '灵感候选',
};

function countText(counts: Record<string, number>) {
  return `正式设定 ${counts.canon ?? 0} · 角色 ${counts.character ?? 0} · 灵感 ${counts.inspiration ?? 0}`;
}

function conflictText(conflict: ImportPreviewResponse['conflicts'][number]): string {
  const matched = conflict.matched_text ? `：${conflict.matched_text}` : '';
  if (conflict.category === 'canon_overlap') return `这份素材可能和已有正式设定重叠${matched}`;
  if (conflict.category === 'character_duplicate') return `这份素材可能和已有角色设定重叠${matched}`;
  return conflict.message.replaceAll('canon', '正式设定');
}
```

Render conflicts with `conflictText(conflict)`.

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

Review diff, ensure no raw enum/id copy is introduced, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-import-node-readable-audit-copy-design.md docs/superpowers/plans/2026-06-04-import-node-readable-audit-copy.md frontend/src/world/WorldImportPanel.tsx frontend/src/world/WorldImportPanel.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: localize import audit copy"
```

Do not push. Do not merge main.
