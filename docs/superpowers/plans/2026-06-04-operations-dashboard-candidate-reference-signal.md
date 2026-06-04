# Operations Dashboard Candidate Reference Signal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking. This run explicitly forbids subagents and workflows.

**Goal:** Show candidate material reference availability in the World Operations Dashboard as safe next-chapter writing context.

**Architecture:** Frontend-only change in `WorldPage`. `WorldOperationsDashboard` receives existing next-prep material references and renders one optional operations metric plus safety note when references exist.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/world/WorldPage.test.tsx`
  - Add a dashboard regression for candidate material reference count and safety copy.
  - Assert raw ID/enum/slug terms stay hidden.
- Modify: `frontend/src/world/WorldPage.tsx`
  - Extend `WorldOperationsDashboard` props with `materialReferences`.
  - Render the optional candidate-reference metric and note.
  - Pass `nextPrep?.material_references ?? []` from the overview.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only and do not mutate canon/world version.

---

### Task 1: Operations dashboard shows safe candidate-reference signal

**Files:**
- Modify: `frontend/src/world/WorldPage.test.tsx`
- Modify: `frontend/src/world/WorldPage.tsx`

- [ ] **Step 1: Write the failing test**

In `WorldPage.test.tsx`, inside `describe('WorldPage operations dashboard', () => {`, add this test after `shows world operations metrics in user language`:

```ts
  it('shows candidate material references as safe operations context', async () => {
    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    const dashboard = within(await screen.findByLabelText('世界运营仪表盘'));
    expect(dashboard.getByText('候选素材参考：1 条')).toBeInTheDocument();
    expect(dashboard.getByText('只作为下一章写作参考，不会自动写入正式设定。')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('asset_id');
    expect(document.body).not.toHaveTextContent('batch_id');
    expect(document.body).not.toHaveTextContent('inspiration');
  });
```

This relies on the existing default `getNextChapterPrep` mock containing one `material_references` item.

- [ ] **Step 2: Run tests to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx -t "candidate material references as safe operations context"
```

Expected: FAIL because the dashboard does not yet render the candidate-reference operations signal.

- [ ] **Step 3: Write minimal implementation**

In `WorldPage.tsx`, update the import type usage if needed and change `WorldOperationsDashboard` signature from:

```ts
function WorldOperationsDashboard({ world, isArchivedWorld, onContinue, onShowForeshadows }: { world: WorldOverview; isArchivedWorld: boolean; onContinue: () => void; onShowForeshadows: () => void }) {
```

To:

```ts
function WorldOperationsDashboard({ world, isArchivedWorld, materialReferences, onContinue, onShowForeshadows }: { world: WorldOverview; isArchivedWorld: boolean; materialReferences: ImportMaterialReference[]; onContinue: () => void; onShowForeshadows: () => void }) {
```

Inside the metrics grid, after the foreshadow metric, add:

```tsx
{materialReferences.length > 0 && (
  <p className="rounded-2xl bg-white/65 p-4 font-black text-[#3b2511]">候选素材参考：{materialReferences.length} 条</p>
)}
```

After the metrics grid, add:

```tsx
{materialReferences.length > 0 && (
  <p className="manuscript rounded-2xl bg-white/45 p-3 text-sm font-bold text-[#5e3b1c]">只作为下一章写作参考，不会自动写入正式设定。</p>
)}
```

When rendering `WorldOperationsDashboard`, add:

```tsx
materialReferences={nextPrep?.material_references ?? []}
```

- [ ] **Step 4: Run tests to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx -t "candidate material references as safe operations context"
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

Review diff for dashboard-only scope, unchanged Studio/context behavior, unchanged import/canon behavior, and preserved raw ID/enum hiding, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-operations-dashboard-candidate-reference-signal-design.md docs/superpowers/plans/2026-06-04-operations-dashboard-candidate-reference-signal.md frontend/src/world/WorldPage.tsx frontend/src/world/WorldPage.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: show candidate references in operations"
```

Do not push. Do not merge main.
