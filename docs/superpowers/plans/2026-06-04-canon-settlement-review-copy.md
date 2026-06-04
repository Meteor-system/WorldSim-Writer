# Canon Settlement Review Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This project run explicitly forbids subagents and requires inline TDD execution.

**Goal:** Make approval and review UI explain imported material usage, non-canon boundaries, and settled canon/events in natural Chinese without raw IDs, slugs, or English event labels.

**Architecture:** Frontend-only presentation layer over existing API data. Add small helper functions inside the current components to keep scope small: `StudioPage` explains settlement immediately after approval, and `ChapterHistoryPanel` explains durable approved-chapter review detail. Existing backend history/execution-context tests are verification-only.

**Tech Stack:** React, TypeScript, Vite, Vitest, Testing Library, FastAPI backend verification via pytest.

---

## File Structure

- Modify: `frontend/src/studio/StudioPage.test.tsx`
  - Add RED assertions for post-approval settlement copy with imported material references and Chinese event/canon wording.
- Modify: `frontend/src/studio/StudioPage.tsx`
  - Add helper functions for material reference titles and Chinese settlement copy.
  - Extend `WorldSettlement` with material reference titles.
  - Render the new copy in the existing settlement panel.
- Modify: `frontend/src/world/ChapterHistoryPanel.test.tsx`
  - Add RED assertions for approved chapter detail copy and absence of raw labels.
  - Extend fixture with one material reference.
- Modify: `frontend/src/world/ChapterHistoryPanel.tsx`
  - Add helper functions for event labels and readable change summaries.
  - Render “审批结算说明”.
  - Replace raw change/event display with Chinese-facing copy.
- Create: `docs/superpowers/specs/2026-06-04-canon-settlement-review-copy-design.md`
  - Already created during brainstorming.
- Create: `docs/superpowers/plans/2026-06-04-canon-settlement-review-copy.md`
  - This plan.

## Task 1: Studio post-approval settlement copy

**Files:**
- Modify: `frontend/src/studio/StudioPage.test.tsx`
- Modify: `frontend/src/studio/StudioPage.tsx`

- [ ] **Step 1: Write the failing Studio test**

Add assertions to the existing test `shows world progression settlement after approval before returning to overview` after the existing settlement assertions:

```ts
expect(screen.getByText('本章参考了 1 条导入素材：雨夜审讯。')).toBeInTheDocument();
expect(screen.getByText('导入素材仍是创作参考，没有自动写入正式 canon。')).toBeInTheDocument();
expect(screen.getByText('已写入正式章节。')).toBeInTheDocument();
expect(screen.getByText('正式事件：章节已批准并写入世界历史。')).toBeInTheDocument();
expect(screen.getByText('世界版本：第 1 版 → 第 2 版。')).toBeInTheDocument();
expect(screen.queryByText('chapter_approved · 世界 1 → 2')).not.toBeInTheDocument();
```

- [ ] **Step 2: Run Studio test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx -t "shows world progression settlement after approval before returning to overview"
```

Expected: FAIL because the new Chinese material-reference and event settlement copy is not rendered yet.

- [ ] **Step 3: Implement minimal Studio settlement helpers and state**

In `frontend/src/studio/StudioPage.tsx`, extend `WorldSettlement`:

```ts
type WorldSettlement = {
  worldBefore: number;
  worldAfter: number;
  approvedChapterCount: number;
  characterChangeCount: number;
  foreshadowChangeCount: number;
  hasChapterApprovedEvent: boolean;
  materialReferenceTitles: string[];
  overview: WorldOverview;
  exportMessage?: string;
  exportError?: string;
};
```

Add helpers near `names()`:

```ts
function materialReferenceTitles(context?: ChapterExecutionContext | null): string[] {
  return (context?.material_references ?? []).map((reference) => reference.title).filter(Boolean);
}

function materialReferenceSentence(titles: string[]): string {
  if (titles.length === 0) return '本章未使用导入素材参考。';
  return `本章参考了 ${titles.length} 条导入素材：${titles.join('、')}。`;
}
```

In `approveDraft()`, compute material references before calling the API:

```ts
const settledMaterialReferenceTitles = materialReferenceTitles(draft.execution_context ?? chapter?.execution_context ?? executionContext);
```

Add this field to `setSettlement({ ... })`:

```ts
materialReferenceTitles: settledMaterialReferenceTitles,
```

In the settlement panel, add these lines below the intro paragraph:

```tsx
<div className="rounded-2xl bg-white/65 p-4 text-emerald-950">
  <p className="font-bold">{materialReferenceSentence(settlement.materialReferenceTitles)}</p>
  {settlement.materialReferenceTitles.length > 0 && (
    <p className="manuscript mt-2 text-sm">导入素材仍是创作参考，没有自动写入正式 canon。</p>
  )}
  <p className="manuscript mt-2 text-sm">已写入正式章节。</p>
  <p className="manuscript mt-1 text-sm">
    {settlement.hasChapterApprovedEvent ? '正式事件：章节已批准并写入世界历史。' : '正式事件：正在等待世界历史刷新。'}
  </p>
  <p className="manuscript mt-1 text-sm">世界版本：第 {settlement.worldBefore} 版 → 第 {settlement.worldAfter} 版。</p>
</div>
```

- [ ] **Step 4: Run Studio test to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx -t "shows world progression settlement after approval before returning to overview"
```

Expected: PASS.

## Task 2: Chapter history detail settlement copy

**Files:**
- Modify: `frontend/src/world/ChapterHistoryPanel.test.tsx`
- Modify: `frontend/src/world/ChapterHistoryPanel.tsx`

- [ ] **Step 1: Write the failing ChapterHistoryPanel test**

In the `detail.execution_context` fixture, replace `material_references: []` with:

```ts
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
```

Add assertions to `renders approved chapter list and loads detail view with changes` after opening the detail:

```ts
expect(screen.getByText('审批结算说明')).toBeInTheDocument();
expect(screen.getByText('导入素材参考：雨夜审讯（来源：旧设定.md）。')).toBeInTheDocument();
expect(screen.getByText('这些导入素材只是本章创作参考，不代表已自动进入正式 canon。')).toBeInTheDocument();
expect(screen.getByText('正式事件：章节已批准并写入世界历史。')).toBeInTheDocument();
expect(screen.getByText('正式结算：角色变化 1 条，伏笔变化 1 条。')).toBeInTheDocument();
expect(screen.getByText('角色：林砚')).toBeInTheDocument();
expect(screen.getByText('状态：active → 开始调查密信')).toBeInTheDocument();
expect(screen.getByText('目标：追查湿信来源')).toBeInTheDocument();
expect(screen.getByText('伏笔：裂纹玉佩')).toBeInTheDocument();
expect(screen.getByText('状态：planted → advanced')).toBeInTheDocument();
expect(screen.queryByText('chapter_approved · 世界 1 → 2')).not.toBeInTheDocument();
expect(screen.queryByText(/character_change · character #1/)).not.toBeInTheDocument();
expect(screen.queryByText(/foreshadow_change · foreshadow #1/)).not.toBeInTheDocument();
```

- [ ] **Step 2: Run ChapterHistoryPanel test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/ChapterHistoryPanel.test.tsx
```

Expected: FAIL because “审批结算说明” and the Chinese change/event rendering do not exist yet.

- [ ] **Step 3: Implement readable history helpers**

In `frontend/src/world/ChapterHistoryPanel.tsx`, replace the existing helper area with these helpers while preserving `contextNames()`:

```ts
function valueText(value: unknown): string {
  if (Array.isArray(value)) return value.map(String).join('、') || '无';
  if (value === null || value === undefined || value === '') return '未设置';
  return String(value);
}

function contextNames(values: Array<{ name?: string; title?: string }>): string {
  return values.map((value) => value.name ?? value.title).filter(Boolean).join('、') || '无';
}

function eventLabel(eventType: string): string {
  const labels: Record<string, string> = {
    chapter_approved: '章节已批准并写入世界历史',
    character_change: '角色状态已更新',
    foreshadow_change: '伏笔状态已更新',
    world_version_increment: '世界版本已推进',
    WORLD_CREATED: '世界已创建',
  };
  return labels[eventType] ?? '世界历史已更新';
}

function changeTarget(change: ChapterHistoryChange): string {
  const payloadName = typeof change.payload?.name === 'string' ? change.payload.name : undefined;
  const afterName = typeof change.after?.name === 'string' ? change.after.name : undefined;
  const beforeName = typeof change.before?.name === 'string' ? change.before.name : undefined;
  const fallback = change.object_type === 'foreshadow' ? '伏笔' : '角色';
  return payloadName ?? afterName ?? beforeName ?? fallback;
}

function changeLines(change: ChapterHistoryChange): string[] {
  const lines: string[] = [];
  if (change.before?.status !== undefined || change.after?.status !== undefined) {
    lines.push(`状态：${valueText(change.before?.status)} → ${valueText(change.after?.status)}`);
  }
  if (change.after?.current_goals !== undefined) {
    lines.push(`目标：${valueText(change.after.current_goals)}`);
  }
  if (change.after?.description !== undefined) {
    lines.push(`说明：${valueText(change.after.description)}`);
  }
  if (change.after?.description_note !== undefined) {
    lines.push(`说明：${valueText(change.after.description_note)}`);
  }
  return lines.length > 0 ? lines : ['已写入正式变化。'];
}
```

Replace `ChangeList` with:

```tsx
function ChangeList({ title, changes, targetLabel }: { title: string; changes: ChapterHistoryChange[]; targetLabel: string }) {
  return (
    <div className="rounded-2xl bg-white/35 p-4">
      <h4 className="font-black text-[#3b2511]">{title}</h4>
      {changes.length === 0 && <p className="ink-muted mt-2 text-sm">无正式变化。</p>}
      <div className="mt-3 space-y-3">
        {changes.map((change, index) => (
          <article key={`${targetLabel}-${index}`} className="rounded-xl border border-amber-900/10 bg-amber-50/40 p-3">
            <p className="text-sm font-bold text-[#5e3b1c]">{targetLabel}：{changeTarget(change)}</p>
            {changeLines(change).map((line) => (
              <p key={line} className="manuscript mt-2 text-sm">{line}</p>
            ))}
          </article>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Render approval settlement explanation in history detail**

In `ChapterHistoryPanel.tsx`, add this block after the approved content block and before execution context:

```tsx
<div className="rounded-2xl bg-white/35 p-4">
  <h4 className="font-black text-[#3b2511]">审批结算说明</h4>
  <p className="manuscript mt-2 text-sm">
    世界版本：第 {selectedDetail.world_version_before} 版 → 第 {selectedDetail.world_version_after} 版。
  </p>
  <p className="manuscript mt-1 text-sm">
    正式结算：角色变化 {selectedDetail.character_changes.length} 条，伏笔变化 {selectedDetail.foreshadow_changes.length} 条。
  </p>
  {selectedDetail.events.some((event) => event.event_type === 'chapter_approved') && (
    <p className="manuscript mt-1 text-sm">正式事件：章节已批准并写入世界历史。</p>
  )}
  {(selectedDetail.execution_context?.material_references ?? []).length > 0 ? (
    <div className="mt-2 space-y-1">
      {selectedDetail.execution_context?.material_references.map((reference) => (
        <p key={`${reference.source_title}-${reference.title}`} className="manuscript text-sm">
          导入素材参考：{reference.title}（来源：{reference.source_title}）。
        </p>
      ))}
      <p className="manuscript text-sm font-bold text-[#5e3b1c]">这些导入素材只是本章创作参考，不代表已自动进入正式 canon。</p>
    </div>
  ) : (
    <p className="manuscript mt-1 text-sm">本章未使用导入素材参考。</p>
  )}
</div>
```

Replace event rendering with:

```tsx
{selectedDetail.events.map((event) => (
  <p key={event.id} className="manuscript text-sm">
    {eventLabel(event.event_type)} · 世界第 {event.world_version_before} 版 → 第 {event.world_version_after} 版
  </p>
))}
```

Replace change list calls with:

```tsx
<ChangeList title="角色变化" changes={selectedDetail.character_changes} targetLabel="角色" />
<ChangeList title="伏笔变化" changes={selectedDetail.foreshadow_changes} targetLabel="伏笔" />
```

- [ ] **Step 5: Run ChapterHistoryPanel test to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/ChapterHistoryPanel.test.tsx
```

Expected: PASS.

## Task 3: Final verification and commit

**Files:**
- Modified files from Tasks 1 and 2
- Docs created in brainstorming and planning

- [ ] **Step 1: Run relevant backend verification**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 ./.venv/bin/pytest tests/test_chapter_execution_context.py tests/test_narrative_approval.py -v
```

Expected: PASS. This confirms history context and approval invariants still hold.

- [ ] **Step 2: Run relevant frontend tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx src/world/ChapterHistoryPanel.test.tsx
```

Expected: PASS.

- [ ] **Step 3: Run frontend build**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: PASS.

- [ ] **Step 4: Run diff whitespace check**

Run:

```bash
git -C /opt/WorldSim-Writer diff --check
```

Expected: no output.

- [ ] **Step 5: Inline self-review**

Check these points manually before committing:

- `StudioPage.tsx` does not add backend mutations.
- Imported materials are described as references, not formal canon.
- `ChapterHistoryPanel.tsx` no longer shows raw `chapter_approved`, `character_change`, `foreshadow_change`, or object ID copy in the targeted detail surfaces.
- No dynamic workflows, subagents, or code-review subagent were used.

- [ ] **Step 6: Commit once after verification**

Run:

```bash
git -C /opt/WorldSim-Writer status --short
git -C /opt/WorldSim-Writer add docs/superpowers/specs/2026-06-04-canon-settlement-review-copy-design.md docs/superpowers/plans/2026-06-04-canon-settlement-review-copy.md frontend/src/studio/StudioPage.tsx frontend/src/studio/StudioPage.test.tsx frontend/src/world/ChapterHistoryPanel.tsx frontend/src/world/ChapterHistoryPanel.test.tsx
git -C /opt/WorldSim-Writer commit -m "feat: clarify canon settlement review copy"
```

Expected: one local commit on `feat/import-node-p0`. Do not push. Do not merge main.

## Plan Self-Review

- Spec coverage: Task 1 covers Studio settlement; Task 2 covers history review detail; Task 3 covers backend/frontend/build/diff verification and commit.
- Placeholder scan: no `TBD`, `TODO`, or open implementation holes remain.
- Type consistency: helper names and fields match `ChapterExecutionContext`, `ChapterHistoryChange`, and current component props.
