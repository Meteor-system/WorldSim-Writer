# First Chapter Launchpad Import Reference Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show imported candidate material summaries as safe readable references in the First Chapter Launchpad.

**Architecture:** Frontend-only rendering update in `FirstChapterLaunchpad` inside `WorldPage.tsx`. Existing import candidate data, Next Chapter Prep loading, and Studio execution-context handoff remain unchanged.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/world/WorldPage.test.tsx`
  - Update the existing First Chapter Launchpad import-reference test first.
- Modify: `frontend/src/world/WorldPage.tsx`
  - Render launchpad material references as readable title/source/summary cards and replace `正式 canon` copy.
- Verify: `backend/tests/test_import_node.py`
  - Existing backend import safety tests prove imports remain candidate/audit only.

---

### Task 1: First Chapter Launchpad shows imported material summaries safely

**Files:**
- Modify: `frontend/src/world/WorldPage.test.tsx`
- Modify: `frontend/src/world/WorldPage.tsx`

- [ ] **Step 1: Write the failing test**

In `shows imported references in the first chapter launchpad and carries them into Studio context`, add summary and updated safety-copy assertions:

```ts
expect(await screen.findByText('已准备 1 条导入素材参考。')).toBeInTheDocument();
expect(screen.getAllByText('导入素材参考').length).toBeGreaterThan(0);
expect(screen.getAllByText('雨夜审讯（来源：旧设定.md）').length).toBeGreaterThan(0);
expect(screen.getAllByText('雨夜审讯从一盏坏灯开始。').length).toBeGreaterThan(0);
expect(screen.getByText('这些素材只会随下一章目标进入创作台，不会自动写入正式设定。')).toBeInTheDocument();
expect(document.body).not.toHaveTextContent('正式 canon');
expect(document.body).not.toHaveTextContent('asset_id');
expect(document.body).not.toHaveTextContent('batch_id');
expect(document.body).not.toHaveTextContent('inspiration');
```

- [ ] **Step 2: Run test to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx -t "shows imported references in the first chapter launchpad"
```

Expected: FAIL because the launchpad does not show the summary and still uses `正式 canon` copy.

- [ ] **Step 3: Write minimal implementation**

In `FirstChapterLaunchpad`, replace the plain imported-reference list with readable cards:

```tsx
{materialReferences.length > 0 && (
  <section className="rounded-2xl bg-white/45 p-3">
    <h3 className="font-black text-[#3b2511]">导入素材参考</h3>
    <p className="manuscript mt-1 text-sm">已准备 {materialReferences.length} 条导入素材参考。</p>
    <div className="mt-3 space-y-2">
      {materialReferences.map((reference) => (
        <article key={`${reference.source_title}-${reference.title}`} className="rounded-xl border border-amber-900/10 bg-amber-50/35 p-3">
          <p className="font-bold text-[#3b2511]">{reference.title}（来源：{reference.source_title}）</p>
          <p className="manuscript mt-1 text-sm">{reference.summary}</p>
        </article>
      ))}
    </div>
    <p className="manuscript mt-2 text-sm font-bold text-[#5e3b1c]">这些素材只会随下一章目标进入创作台，不会自动写入正式设定。</p>
  </section>
)}
```

- [ ] **Step 4: Run test to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx -t "shows imported references in the first chapter launchpad"
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
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx src/world/WorldImportPanel.test.tsx src/world/NextChapterPrepPanel.test.tsx src/studio/StudioPage.test.tsx
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

Review the diff for safe Chinese copy, hidden raw IDs/enums, and no formal canon mutation, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-launchpad-import-reference-summary-design.md docs/superpowers/plans/2026-06-04-launchpad-import-reference-summary.md frontend/src/world/WorldPage.tsx frontend/src/world/WorldPage.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: show launchpad import reference summaries"
```

Do not push. Do not merge main.
