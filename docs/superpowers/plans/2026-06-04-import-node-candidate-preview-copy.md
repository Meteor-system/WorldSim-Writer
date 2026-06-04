# Import Node Candidate Preview Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking. This run explicitly forbids subagents and workflows.

**Goal:** Replace technical Import Node preview wording with beginner-friendly candidate-material preview wording.

**Architecture:** Frontend-only copy update in `WorldImportPanel`. Tests cover the preview button, preview heading, and preview fallback error so the UI explains this step as candidate-material preview while preserving existing preview/confirm data flow and candidate-only canon safety.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
  - Update preview button expectations to `生成候选素材预览`.
  - Update preview heading expectation to `候选素材预览`.
  - Add fallback error coverage for `候选素材预览生成失败`.
  - Preserve raw ID/enum/slug hiding assertions.
- Modify: `frontend/src/world/WorldImportPanel.tsx`
  - Replace visible preview button, heading, and fallback error copy only.
- Modify: `frontend/src/world/WorldPage.test.tsx`
  - Update the import-refresh regression to click the renamed preview button.
  - Assert the old preview button copy is not visible in that flow.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only and do not mutate canon/world version.

---

### Task 1: Import Node preview uses candidate-material wording

**Files:**
- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
- Modify: `frontend/src/world/WorldImportPanel.tsx`
- Modify: `frontend/src/world/WorldPage.test.tsx`

- [ ] **Step 1: Write the failing tests**

In `WorldImportPanel.test.tsx`, in `shows readable empty-content validation copy`, replace:

```ts
await user.click(screen.getByRole('button', { name: '生成结构化预览' }));
```

With:

```ts
await user.click(screen.getByRole('button', { name: '生成候选素材预览' }));
expect(document.body).not.toHaveTextContent('生成结构化预览');
```

In `previews imported material as grouped candidate assets with canon safety copy`, replace both button clicks:

```ts
await user.click(screen.getByRole('button', { name: '生成结构化预览' }));
```

With:

```ts
await user.click(screen.getByRole('button', { name: '生成候选素材预览' }));
```

Then after the existing preview assertions, add:

```ts
expect(screen.getByText('候选素材预览')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('结构化预览');
```

Add this new test before `confirms preview assets and shows audit batch result`:

```ts
  it('shows candidate-material fallback copy when preview generation fails', async () => {
    const user = userEvent.setup();
    render(<WorldImportPanel worldId={7} onPreview={vi.fn().mockRejectedValue('preview down')} onConfirm={vi.fn()} onListBatches={vi.fn().mockResolvedValue(emptyBatches)} />);

    await user.type(screen.getByLabelText('素材正文'), '灵感：雨夜审讯从一盏坏灯开始。');
    await user.click(screen.getByRole('button', { name: '生成候选素材预览' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('候选素材预览生成失败');
    expect(document.body).not.toHaveTextContent('结构化预览生成失败');
  });
```

- [ ] **Step 2: Run tests to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx -t "empty-content|grouped candidate assets|fallback copy"
```

Expected: FAIL because production still renders `生成结构化预览`, `结构化预览`, and `结构化预览生成失败`.

- [ ] **Step 3: Write minimal implementation**

In `WorldImportPanel.tsx`, replace:

```ts
setError(err instanceof Error ? err.message : '结构化预览生成失败');
```

With:

```ts
setError(err instanceof Error ? err.message : '候选素材预览生成失败');
```

Replace:

```tsx
<button type="submit" className="primary-button motion-soft-lift" disabled={readOnly || loadingPreview}>{loadingPreview ? '解析中…' : '生成结构化预览'}</button>
```

With:

```tsx
<button type="submit" className="primary-button motion-soft-lift" disabled={readOnly || loadingPreview}>{loadingPreview ? '解析中…' : '生成候选素材预览'}</button>
```

Replace:

```tsx
<h3 className="text-xl font-black text-[#34210f]">结构化预览</h3>
```

With:

```tsx
<h3 className="text-xl font-black text-[#34210f]">候选素材预览</h3>
```

- [ ] **Step 4: Update broader WorldPage regression call site**

In `WorldPage.test.tsx`, inside `refreshes next chapter references after confirming imported material`, replace:

```ts
await user.click(screen.getByRole('button', { name: '生成结构化预览' }));
```

With:

```ts
expect(screen.queryByRole('button', { name: '生成结构化预览' })).not.toBeInTheDocument();
await user.click(screen.getByRole('button', { name: '生成候选素材预览' }));
```

- [ ] **Step 5: Run tests to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx -t "empty-content|grouped candidate assets|fallback copy"
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
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx src/world/WorldPage.test.tsx src/world/NextChapterPrepPanel.test.tsx src/studio/StudioPage.test.tsx src/world/ChapterHistoryPanel.test.tsx
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

Review diff for candidate-preview wording, unchanged import/canon behavior, unchanged preview/confirm behavior, and preserved raw ID/enum hiding, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-import-node-candidate-preview-copy-design.md docs/superpowers/plans/2026-06-04-import-node-candidate-preview-copy.md frontend/src/world/WorldImportPanel.tsx frontend/src/world/WorldImportPanel.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: clarify import preview copy"
```

Do not push. Do not merge main.
