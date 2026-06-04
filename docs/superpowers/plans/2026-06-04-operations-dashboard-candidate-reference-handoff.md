# Operations Dashboard Candidate Reference Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use inline TDD execution only for this task. Steps use checkbox (`- [ ]`) syntax for tracking. This run explicitly forbids subagents and workflows.

**Goal:** Make the operations dashboard `继续下一章` action carry candidate material references into Studio as safe drafting context when references are available.

**Architecture:** Frontend-only change in `WorldPage`. Use existing `buildExecutionContextFromPrep(nextPrep)` as a fallback operations-dashboard launch context only when candidate material references exist and no explicit selected context is already set.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI pytest for import safety regression.

---

## File Structure

- Modify: `frontend/src/world/WorldPage.test.tsx`
  - Add a dashboard click regression with one candidate material reference.
  - Assert the Studio launch payload includes `material_references` and hides raw ID/enum/slug terms.
- Modify: `frontend/src/world/WorldPage.tsx`
  - Import `buildExecutionContextFromPrep`.
  - Compute an operations-dashboard launch context from `nextPrep` only when candidate references exist and no selected context exists.
  - Pass that context through the existing `onEnterStudio` call.
- Verify: `backend/tests/test_import_node.py`
  - Existing import safety tests prove imports remain candidate/audit only and do not mutate canon/world version.

---

### Task 1: Operations dashboard carries candidate references into Studio context

**Files:**
- Modify: `frontend/src/world/WorldPage.test.tsx`
- Modify: `frontend/src/world/WorldPage.tsx`

- [ ] **Step 1: Write the failing test**

In `WorldPage.test.tsx`, inside `describe('WorldPage operations dashboard', () => {`, add this test after `shows candidate material references as safe operations context`:

```ts
  it('carries candidate references into Studio from the operations continue action', async () => {
    const user = userEvent.setup();
    const onEnterStudio = vi.fn();
    vi.mocked(getNextChapterPrep).mockResolvedValueOnce({
      world_id: 7,
      world_version: 2,
      next_chapter_number: 2,
      suggested_goal: '林砚带着湿信赴城主府外墙，并设置一次试探。',
      recommended_pov_character_id: 1,
      recommended_pov_character_name: '林砚',
      source_signals: ['import_material_reference'],
      priority_characters: [],
      priority_foreshadows: [],
      progression_hints: [],
      continuity_warnings: [],
      recent_events: [],
      material_references: [{ asset_id: 9, batch_id: 12, asset_pool: 'inspiration', title: '雨夜审讯', summary: '雨夜审讯从一盏坏灯开始。', raw_text: '灵感：雨夜审讯从一盏坏灯开始。', source_title: '旧设定.md', source_type: 'pasted_text', created_at: '2026-06-04T00:00:01Z', safety_note: '导入素材参考只用于创作提示，不会自动改写正式 canon。' }],
    });

    render(<WorldPage onEnterStudio={onEnterStudio} autoFocusTitle={false} />);

    const dashboard = within(await screen.findByLabelText('世界运营仪表盘'));
    expect(await dashboard.findByText('候选素材参考：1 条')).toBeInTheDocument();
    await user.click(dashboard.getByRole('button', { name: '继续下一章' }));

    expect(onEnterStudio).toHaveBeenCalledWith(world, {
      initialChapterGoal: '林砚带着湿信赴城主府外墙，并设置一次试探。',
      executionContext: expect.objectContaining({
        source: 'next_chapter_prep',
        material_references: expect.arrayContaining([expect.objectContaining({ title: '雨夜审讯', source_title: '旧设定.md' })]),
      }),
    });
    expect(document.body).not.toHaveTextContent('asset_id');
    expect(document.body).not.toHaveTextContent('batch_id');
    expect(document.body).not.toHaveTextContent('inspiration');
  });
```

- [ ] **Step 2: Run tests to verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx -t "carries candidate references into Studio from the operations continue action"
```

Expected: FAIL because the operations dashboard currently enters Studio with `executionContext: undefined` unless the user selected a context manually.

- [ ] **Step 3: Write minimal implementation**

In `WorldPage.tsx`, add:

```ts
import { buildExecutionContextFromPrep } from './chapterExecutionContext';
```

Before the JSX return after world/archive state is known, compute:

```ts
const operationsExecutionContext = selectedExecutionContext
  ?? ((nextPrep?.material_references ?? []).length > 0 ? buildExecutionContextFromPrep(nextPrep) : undefined);
```

Then change the operations-dashboard `onContinue` payload from:

```ts
initialChapterGoal: selectedExecutionContext?.goal,
executionContext: selectedExecutionContext ?? undefined,
```

To:

```ts
initialChapterGoal: operationsExecutionContext?.goal,
executionContext: operationsExecutionContext,
```

- [ ] **Step 4: Run tests to verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx -t "carries candidate references into Studio from the operations continue action"
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

Review diff for operations-dashboard handoff scope, unchanged import/canon behavior, unchanged approval behavior, and preserved raw ID/enum hiding, then:

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-operations-dashboard-candidate-reference-handoff-design.md docs/superpowers/plans/2026-06-04-operations-dashboard-candidate-reference-handoff.md frontend/src/world/WorldPage.tsx frontend/src/world/WorldPage.test.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: pass candidate references from operations"
```

Do not push. Do not merge main.
