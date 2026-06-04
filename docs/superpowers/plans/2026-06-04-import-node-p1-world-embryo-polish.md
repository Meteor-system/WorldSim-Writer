# Import Node P1 World Embryo Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This run explicitly forbids subagents, so execute inline with strict TDD.

**Goal:** Make imported candidate materials visible and safely usable in the three-minute/newcomer/world-embryo loop without auto-writing formal canon.

**Architecture:** Use the existing Import Node and Next Chapter Prep reference bridge. Frontend changes add a parent callback after import confirmation, refresh Narrative Control Center data, display `material_references` in the First Chapter Launchpad, and include references in story-arc launch execution contexts. Backend production code should not change; backend tests extend safety coverage around import candidates.

**Tech Stack:** FastAPI/Pytest backend, React/TypeScript/Vite frontend, Vitest + Testing Library.

---

## File Structure

- Modify: `backend/tests/test_import_node.py`
  - Extend import safety test to assert no `chapter_approved` or projection events are written when confirming imports.
- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
  - Add RED test for callback/copy after confirm and no batch ID exposure in success copy.
- Modify: `frontend/src/world/WorldImportPanel.tsx`
  - Add optional `onConfirmed` callback and low-cognitive confirm success copy.
- Modify: `frontend/src/world/WorldPage.test.tsx`
  - Add RED tests for First Chapter Launchpad material reference visibility and refresh after import confirm.
- Modify: `frontend/src/world/WorldPage.tsx`
  - Add `materialReferences` prop to `FirstChapterLaunchpad`.
  - Pass references from `nextPrep.material_references`.
  - Copy references into `buildStoryArcExecutionContext()`.
  - Refresh Narrative Control Center after import confirm.
- Create: `docs/superpowers/specs/2026-06-04-import-node-p1-world-embryo-polish-design.md`
- Create: `docs/superpowers/plans/2026-06-04-import-node-p1-world-embryo-polish.md`

## Task 1: Backend import safety test

**Files:**
- Modify: `backend/tests/test_import_node.py`

- [ ] **Step 1: Write/extend the backend safety test**

In `test_import_confirm_writes_candidates_and_audit_without_mutating_canon_or_world_version`, after the existing import audit assertions, add:

```python
    event_types = list(db_session.scalars(select(EventLog.event_type).where(EventLog.world_id == world.id).order_by(EventLog.id)))
    assert 'material_import_confirmed' in event_types
    assert 'chapter_approved' not in event_types
    assert 'character_change' not in event_types
    assert 'foreshadow_change' not in event_types
```

- [ ] **Step 2: Run backend test to verify status**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 ./.venv/bin/pytest tests/test_import_node.py::test_import_confirm_writes_candidates_and_audit_without_mutating_canon_or_world_version -v
```

Expected: PASS if current backend already preserves this invariant. If it fails, fix backend minimally without adding new canon writes.

## Task 2: WorldImportPanel confirm callback and safer copy

**Files:**
- Modify: `frontend/src/world/WorldImportPanel.test.tsx`
- Modify: `frontend/src/world/WorldImportPanel.tsx`

- [ ] **Step 1: Write failing frontend test**

In `WorldImportPanel.test.tsx`, update the confirm test to pass `const onConfirmed = vi.fn();` and render:

```tsx
render(
  <WorldImportPanel
    worldId={7}
    onPreview={onPreview}
    onConfirm={onConfirm}
    onListBatches={vi.fn().mockResolvedValue(emptyBatches)}
    onConfirmed={onConfirmed}
  />,
);
```

Replace the current success assertions with:

```ts
expect(onConfirmed).toHaveBeenCalledWith(confirmResponse);
expect(await screen.findByRole('status')).toHaveTextContent('已写入候选素材。');
expect(screen.getByText('这些素材会作为创作参考出现在下一章准备区，不会自动改写正式 canon。')).toBeInTheDocument();
expect(screen.queryByText(/批次 #12/)).not.toBeInTheDocument();
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx -t "confirms preview assets"
```

Expected: FAIL because `onConfirmed` is not a prop and old success copy exposes `批次 #12`.

- [ ] **Step 3: Implement minimal panel change**

In `WorldImportPanel.tsx`, extend props:

```ts
  onConfirmed?: (response: ImportConfirmResponse) => void;
```

Update function signature:

```ts
export function WorldImportPanel({ worldId, readOnly = false, onPreview, onConfirm, onListBatches, onConfirmed }: Props) {
```

Inside `confirmPreview()`, after `setBatches(...)`, call:

```ts
      onConfirmed?.(response);
```

Replace success block with:

```tsx
{confirmed && (
  <div role="status" className="paper-success p-4" data-testid="import-confirmed-batch">
    <p className="font-bold">已写入候选素材。</p>
    <p className="mt-1 font-normal">这些素材会作为创作参考出现在下一章准备区，不会自动改写正式 canon。</p>
    <span className="mt-2 block font-normal">{countText(confirmed.batch.asset_counts)}</span>
  </div>
)}
```

- [ ] **Step 4: Run test to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx -t "confirms preview assets"
```

Expected: PASS.

## Task 3: WorldPage launchpad material reference usage

**Files:**
- Modify: `frontend/src/world/WorldPage.test.tsx`
- Modify: `frontend/src/world/WorldPage.tsx`

- [ ] **Step 1: Write failing launchpad visibility/context test**

In `WorldPage.test.tsx`, add this test under `describe('WorldPage Story Arc Planner', ...)`:

```ts
  it('shows imported references in the first chapter launchpad and carries them into Studio context', async () => {
    const user = userEvent.setup();
    const onEnterStudio = vi.fn();
    vi.mocked(apiRequest).mockReset();
    vi.mocked(apiRequest)
      .mockResolvedValueOnce([{ id: 7 }])
      .mockResolvedValueOnce(storyArcWorld);
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
      material_references: [
        {
          asset_id: 9,
          batch_id: 3,
          asset_pool: 'inspiration',
          title: '雨夜审讯',
          summary: '雨夜审讯从一盏坏灯开始。',
          raw_text: '灵感：雨夜审讯从一盏坏灯开始。',
          source_title: '旧设定.md',
          source_type: 'markdown',
          created_at: '2026-06-04T00:00:00Z',
          safety_note: '导入素材参考只用于创作提示，不会自动改写正式 canon。',
        },
      ],
    });

    render(<WorldPage onEnterStudio={onEnterStudio} autoFocusTitle={false} />);

    expect(await screen.findByText('导入素材参考')).toBeInTheDocument();
    expect(screen.getByText('已准备 1 条导入素材参考。')).toBeInTheDocument();
    expect(screen.getByText('雨夜审讯（来源：旧设定.md）')).toBeInTheDocument();
    expect(screen.getByText('这些素材只会随下一章目标进入创作台，不会自动写入正式 canon。')).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent('asset_id');
    expect(document.body).not.toHaveTextContent('batch_id');
    expect(document.body).not.toHaveTextContent('inspiration');

    await user.click(screen.getByRole('button', { name: '用此目标进入创作台' }));

    expect(onEnterStudio).toHaveBeenCalledWith(storyArcWorld, {
      initialChapterGoal: '第 2 章标题：第 2 章摘要：林砚推进裂纹玉佩线索。',
      executionContext: expect.objectContaining({
        material_references: expect.arrayContaining([expect.objectContaining({ title: '雨夜审讯', source_title: '旧设定.md' })]),
      }),
    });
  });
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx -t "shows imported references in the first chapter launchpad"
```

Expected: FAIL because launchpad does not render material references and story-arc execution context uses an empty array.

- [ ] **Step 3: Implement launchpad reference display and context copy**

In `WorldPage.tsx`, add `ImportMaterialReference` to imports from `../api/types`.

Change `buildStoryArcExecutionContext` signature:

```ts
function buildStoryArcExecutionContext(world: WorldOverview, chapter: StoryArcChapter, materialReferences: ImportMaterialReference[] = []): ChapterExecutionContext {
```

Set:

```ts
    material_references: materialReferences,
```

Change props:

```ts
type FirstChapterLaunchpadProps = {
  world: WorldOverview;
  nextChapter: StoryArcChapter | null;
  arcLoading: boolean;
  materialReferences: ImportMaterialReference[];
  onGenerateArc: () => void;
  onLaunchChapter: (chapter: StoryArcChapter) => void;
};
```

Render inside the `nextChapter` branch before the launch button:

```tsx
{materialReferences.length > 0 && (
  <section className="rounded-2xl bg-white/45 p-3">
    <h3 className="font-black text-[#3b2511]">导入素材参考</h3>
    <p className="manuscript mt-1 text-sm">已准备 {materialReferences.length} 条导入素材参考。</p>
    <div className="mt-2 space-y-1">
      {materialReferences.map((reference) => (
        <p key={`${reference.source_title}-${reference.title}`} className="manuscript text-sm">
          {reference.title}（来源：{reference.source_title}）
        </p>
      ))}
    </div>
    <p className="manuscript mt-2 text-sm font-bold text-[#5e3b1c]">这些素材只会随下一章目标进入创作台，不会自动写入正式 canon。</p>
  </section>
)}
```

In `launchStoryArcChapter`:

```ts
const executionContext = buildStoryArcExecutionContext(world, chapter, nextPrep?.material_references ?? []);
```

When rendering `FirstChapterLaunchpad`, pass:

```tsx
materialReferences={nextPrep?.material_references ?? []}
```

- [ ] **Step 4: Run test to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx -t "shows imported references in the first chapter launchpad"
```

Expected: PASS.

## Task 4: WorldPage refreshes references after import confirm

**Files:**
- Modify: `frontend/src/world/WorldPage.test.tsx`
- Modify: `frontend/src/world/WorldPage.tsx`

- [ ] **Step 1: Write failing refresh test**

Add this test under `describe('WorldPage Narrative Control Center', ...)`:

```ts
  it('refreshes next chapter references after confirming imported material', async () => {
    const user = userEvent.setup();
    vi.mocked(previewWorldImport).mockResolvedValueOnce({
      world_id: 7,
      source_type: 'pasted_text',
      source_title: '旧设定.md',
      cleaned_excerpt: '灵感：雨夜审讯从一盏坏灯开始。',
      asset_counts: { canon: 0, character: 0, inspiration: 1 },
      conflicts: [],
      assets: [{ asset_pool: 'inspiration', title: '雨夜审讯', summary: '雨夜审讯从一盏坏灯开始。', raw_text: '灵感：雨夜审讯从一盏坏灯开始。', metadata: {} }],
    });
    vi.mocked(confirmWorldImport).mockResolvedValueOnce({
      batch: {
        id: 12,
        world_id: 7,
        source_type: 'pasted_text',
        source_title: '旧设定.md',
        original_excerpt: '灵感：雨夜审讯从一盏坏灯开始。',
        cleaned_excerpt: '灵感：雨夜审讯从一盏坏灯开始。',
        status: 'confirmed',
        asset_counts: { canon: 0, character: 0, inspiration: 1 },
        conflicts: [],
        created_at: '2026-06-04T00:00:00Z',
        confirmed_at: '2026-06-04T00:00:01Z',
      },
      assets: [{ id: 9, world_id: 7, batch_id: 12, status: 'candidate', asset_pool: 'inspiration', title: '雨夜审讯', summary: '雨夜审讯从一盏坏灯开始。', raw_text: '灵感：雨夜审讯从一盏坏灯开始。', metadata: {}, created_at: '2026-06-04T00:00:01Z' }],
    });
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

    render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

    await screen.findByText('素材导入节点');
    await user.type(screen.getByLabelText('素材正文'), '灵感：雨夜审讯从一盏坏灯开始。');
    await user.click(screen.getByRole('button', { name: '生成结构化预览' }));
    await user.click(await screen.findByRole('button', { name: '确认写入候选资产' }));

    expect(await screen.findByText('已写入候选素材。')).toBeInTheDocument();
    expect(await screen.findByText('导入素材参考')).toBeInTheDocument();
    expect(getNextChapterPrep).toHaveBeenCalledTimes(2);
  });
```

- [ ] **Step 2: Run refresh test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx -t "refreshes next chapter references"
```

Expected: FAIL because `WorldPage` does not pass an import-confirm callback to refresh NCC data.

- [ ] **Step 3: Implement refresh callback**

In `WorldPage.tsx`, update `WorldImportPanel` usage:

```tsx
<WorldImportPanel
  worldId={world.id}
  readOnly={isArchivedWorld}
  onPreview={previewWorldImport}
  onConfirm={confirmWorldImport}
  onListBatches={listWorldImports}
  onConfirmed={() => void loadNarrativeControlCenter(world.id)}
/>
```

- [ ] **Step 4: Run refresh test to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx -t "refreshes next chapter references"
```

Expected: PASS.

## Task 5: Final verification and commit

**Files:**
- All modified files from Tasks 1-4
- Design/plan docs

- [ ] **Step 1: Run backend tests**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 ./.venv/bin/pytest tests/test_import_node.py tests/test_narrative_control_center.py tests/test_chapter_execution_context.py -v
```

Expected: PASS.

- [ ] **Step 2: Run frontend tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldImportPanel.test.tsx src/world/WorldPage.test.tsx src/world/NextChapterPrepPanel.test.tsx src/studio/StudioPage.test.tsx
```

Expected: PASS.

- [ ] **Step 3: Run frontend build**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: PASS.

- [ ] **Step 4: Run diff check**

Run:

```bash
git -C /opt/WorldSim-Writer diff --check
```

Expected: no output.

- [ ] **Step 5: Inline self-review**

Verify:

- no dynamic workflows were used;
- no subagents/agents/code-review subagent were used;
- import confirmation still does not mutate formal canon;
- UI copy says candidate materials are references only;
- targeted UI does not expose raw IDs/slugs/enums as primary copy.

- [ ] **Step 6: Commit**

Run:

```bash
git -C /opt/WorldSim-Writer status --short
git -C /opt/WorldSim-Writer add backend/tests/test_import_node.py frontend/src/world/WorldImportPanel.tsx frontend/src/world/WorldImportPanel.test.tsx frontend/src/world/WorldPage.tsx frontend/src/world/WorldPage.test.tsx docs/superpowers/specs/2026-06-04-import-node-p1-world-embryo-polish-design.md docs/superpowers/plans/2026-06-04-import-node-p1-world-embryo-polish.md
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "feat: surface import references in world launchpad" -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

Expected: one local commit on `feat/import-node-p0`. Do not push. Do not merge.

## Plan Self-Review

- Spec coverage: Tasks cover backend safety, import confirmation callback/copy, launchpad visibility/context, refresh after import, final verification/commit.
- Placeholder scan: no placeholders remain.
- Type consistency: `ImportMaterialReference`, `material_references`, `onConfirmed`, and existing component names match current API/types.
