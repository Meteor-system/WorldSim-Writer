# MVP30 Tag Detail Filtering 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This repository run is explicitly inline-only: do not use dynamic workflows, subagents, or the code-review subagent.

**Goal:** Add local object-type filtering to selected tag details so users can navigate busy tag collections by character, foreshadow, chapter, or event.

**Architecture:** Frontend-only view enhancement in `WorldTagsPanel`. The component uses existing `TagDetailResponse` objects and `object_type_counts`; no backend route, schema, database, canon, world-version, or EventLog behavior changes.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, Vite; existing FastAPI pytest tag/search suites for regression verification.

---

## File structure

- Modify `frontend/src/world/WorldTagsPanel.test.tsx` — add RED/GREEN coverage for local tag detail filtering.
- Modify `frontend/src/world/WorldTagsPanel.tsx` — add filter state, buttons, derived filtered objects, and empty state.
- Create `docs/superpowers/specs/2026-05-31-mvp30-tag-detail-filter-design.md` — MVP30 design spec.
- Create `docs/superpowers/plans/2026-05-31-mvp30-tag-detail-filter.md` — implementation plan.

---

### Task 1: Frontend tag detail filter TDD

**Files:**
- Test: `frontend/src/world/WorldTagsPanel.test.tsx`
- Modify: `frontend/src/world/WorldTagsPanel.tsx`

- [ ] **Step 1: Write failing frontend tests**

In `frontend/src/world/WorldTagsPanel.test.tsx`, add richer tagged-object fixtures near `detailResponse`:

```ts
const mixedDetailResponse: TagDetailResponse = {
  tag: { ...tag, assignment_count: 3, object_type_counts: { character: 1, foreshadow: 1, chapter: 1 } },
  objects: [
    detailResponse.objects[0],
    {
      object_type: 'foreshadow',
      object_id: 2,
      title: '黑匣子脉冲',
      subtitle: 'Foreshadow · planted · urgency 4',
      snippet: '废弃黑匣子收到来自未来的求救信号。',
      metadata: { status: 'planted' },
    },
    {
      object_type: 'chapter',
      object_id: 11,
      title: '第一章 灯塔低鸣',
      subtitle: 'Chapter · approved · world v1',
      snippet: '许砚调查灯塔异常。',
      metadata: { status: 'approved' },
    },
  ],
};
```

Add tests before the existing empty/error state test:

```tsx
it('filters selected tag objects by object type', async () => {
  const user = userEvent.setup();
  renderPanel({ onLoadTag: vi.fn().mockResolvedValue(mixedDetailResponse) });

  await screen.findByText('灯塔线');
  await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
  expect(await screen.findByText('许砚')).toBeInTheDocument();
  expect(screen.getByText('黑匣子脉冲')).toBeInTheDocument();
  expect(screen.getByText('第一章 灯塔低鸣')).toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: '只看伏笔 1' }));

  expect(screen.queryByText('许砚')).not.toBeInTheDocument();
  expect(screen.getByText('黑匣子脉冲')).toBeInTheDocument();
  expect(screen.queryByText('第一章 灯塔低鸣')).not.toBeInTheDocument();
});

it('shows a targeted empty state for filters with no objects', async () => {
  const user = userEvent.setup();
  renderPanel({ onLoadTag: vi.fn().mockResolvedValue(mixedDetailResponse) });

  await screen.findByText('灯塔线');
  await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
  await screen.findByText('许砚');
  await user.click(screen.getByRole('button', { name: '只看事件 0' }));

  expect(await screen.findByText('当前筛选下没有对象。')).toBeInTheDocument();
});

it('resets the object type filter when loading another tag', async () => {
  const user = userEvent.setup();
  const targetDetail: TagDetailResponse = {
    tag: { ...targetTag, assignment_count: 1, object_type_counts: { character: 1 } },
    objects: [detailResponse.objects[0]],
  };
  const onLoadTag = vi.fn()
    .mockResolvedValueOnce(mixedDetailResponse)
    .mockResolvedValueOnce(targetDetail);
  renderPanel({ onLoadTag });

  await screen.findByText('灯塔线');
  await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
  await screen.findByText('黑匣子脉冲');
  await user.click(screen.getByRole('button', { name: '只看伏笔 1' }));
  expect(screen.queryByText('许砚')).not.toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: '查看 主线归档' }));

  expect(await screen.findByText('许砚')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '查看全部对象 1' })).toHaveClass('ring-2');
});
```

- [ ] **Step 2: Run frontend RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx
```

Expected: new tests fail because object-type filter buttons and filtered rendering do not exist.

- [ ] **Step 3: Add filter state and derived data**

In `frontend/src/world/WorldTagsPanel.tsx`, add state near existing detail state:

```ts
const [detailObjectTypeFilter, setDetailObjectTypeFilter] = useState('all');
```

In `loadTag()`, after edit and merge reset state, add:

```ts
setDetailObjectTypeFilter('all');
```

Before the return statement, add:

```ts
const filteredObjects = detail
  ? detailObjectTypeFilter === 'all'
    ? detail.objects
    : detail.objects.filter((item) => item.object_type === detailObjectTypeFilter)
  : [];
```

- [ ] **Step 4: Add filter UI and filtered rendering**

In the selected tag detail panel, after the merge form and before assignment form, add:

```tsx
<div className="space-y-2 rounded-2xl bg-amber-50/40 p-3">
  <p className="text-sm font-black text-[#3b2511]">对象筛选</p>
  <div className="flex flex-wrap gap-2">
    <button
      className={`rounded-full border border-amber-900/15 px-3 py-1 text-xs font-bold text-[#5e3b1c] ${detailObjectTypeFilter === 'all' ? 'ring-2 ring-amber-800' : ''}`}
      type="button"
      onClick={() => setDetailObjectTypeFilter('all')}
      aria-label={`查看全部对象 ${detail.tag.assignment_count}`}
    >
      全部 {detail.tag.assignment_count}
    </button>
    {OBJECT_TYPES.map((item) => {
      const count = detail.tag.object_type_counts[item.value] ?? 0;
      return (
        <button
          key={item.value}
          className={`rounded-full border border-amber-900/15 px-3 py-1 text-xs font-bold text-[#5e3b1c] ${detailObjectTypeFilter === item.value ? 'ring-2 ring-amber-800' : ''}`}
          type="button"
          onClick={() => setDetailObjectTypeFilter(item.value)}
          aria-label={`只看${item.label} ${count}`}
        >
          {item.label} {count}
        </button>
      );
    })}
  </div>
</div>
```

Change object rendering from `detail.objects` to `filteredObjects`:

```tsx
{detail.objects.length === 0 ? (
  <p className="ink-muted">这个标签还没有关联对象。</p>
) : filteredObjects.length === 0 ? (
  <p className="ink-muted">当前筛选下没有对象。</p>
) : (
  <div className="space-y-3">
    {filteredObjects.map((item) => (
      ...existing article rendering...
    ))}
  </div>
)}
```

- [ ] **Step 5: Run frontend GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx
```

Expected: all panel tests pass.

---

### Task 2: Final verification, commit, and merge

**Files:**
- Modified frontend panel files and MVP30 docs.

- [ ] **Step 1: Run targeted backend verification**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_tags.py tests/test_world_search.py -q
```

Expected: all selected backend tests pass.

- [ ] **Step 2: Run targeted frontend verification**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx src/world/WorldSearchPanel.test.tsx src/world/WorldPage.test.tsx src/api/client.test.ts
```

Expected: all selected frontend tests pass.

- [ ] **Step 3: Run frontend build**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 4: Update docs status**

Append implementation status sections to the MVP30 spec and plan after verification, recording RED/GREEN and command results.

- [ ] **Step 5: Commit**

Run:

```bash
git -C /opt/WorldSim-Writer/frontend status --short
git -C /opt/WorldSim-Writer/frontend add frontend/src/world/WorldTagsPanel.tsx frontend/src/world/WorldTagsPanel.test.tsx docs/superpowers/specs/2026-05-31-mvp30-tag-detail-filter-design.md docs/superpowers/plans/2026-05-31-mvp30-tag-detail-filter.md
git -C /opt/WorldSim-Writer/frontend commit -m "feat: filter tag detail objects"
```

- [ ] **Step 6: Fast-forward merge to main without push**

Run:

```bash
git -C /opt/WorldSim-Writer/frontend checkout main
git -C /opt/WorldSim-Writer/frontend merge --ff-only feat/mvp30-tag-detail-filter
```

Do not push.

- [ ] **Step 7: Post-merge verification**

Repeat backend targeted tests, frontend targeted tests, and frontend build from Steps 1-3 on `main`.

Expected: all pass after merge.

## Self-review

- This plan covers all MVP30 acceptance criteria.
- No placeholders remain.
- Types and labels are consistent with the existing component and tests.
- No backend, database, canon, world-version, or EventLog behavior changes are introduced.

## Execution status

Implemented on `feat/mvp30-tag-detail-filter` using TDD. RED was observed in `WorldTagsPanel.test.tsx` for missing filter buttons; GREEN was observed after adding local filter state, counts, filtered rendering, and targeted empty state. Pre-merge backend targeted tests, frontend targeted tests, and frontend build passed.
