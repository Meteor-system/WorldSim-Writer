# MVP #7 Foreshadow Ledger 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This project explicitly forbids subagents and dynamic workflows for this MVP.

**Goal:** Upgrade the existing foreshadow editor into a ledger/governance view with summary counts, unresolved/stale/overdue filters, risk metadata, and lifecycle advance/drop actions.

**Architecture:** Keep backend production code unchanged unless tests expose a missing contract. Implement the ledger in `ForeshadowManager` by deriving summary/filter state from existing `getForeshadows` and `getStaleForeshadows` responses, then reusing `updateForeshadow` for lifecycle actions. Keep WorldPage integration unchanged except for test coverage that the foreshadow tab exposes the ledger.

**Tech Stack:** FastAPI + SQLAlchemy + Pytest backend; React + TypeScript + Vite + Vitest + Testing Library frontend.

---

## File Map

- Modify: `frontend/src/components/ForeshadowManager.test.tsx` — RED tests for ledger summary, filters, risk metadata, advance/drop behavior.
- Modify: `frontend/src/components/ForeshadowManager.tsx` — ledger summary/filter UI, risk badges, source/window metadata, drop action.
- Modify: `frontend/src/world/WorldPage.test.tsx` — assert WorldPage foreshadow tab exposes ledger summary while preserving governance warning.
- Verify only: `backend/tests/test_foreshadow_crud.py` — existing backend contract for filtering, stale, transitions, world_version increments.
- Create: `docs/superpowers/specs/2026-05-30-mvp7-foreshadow-ledger-design.md` — already written during brainstorming.

## Domain Decisions

- Persisted statuses remain `planted | advanced | resolved | expired`.
- UI lifecycle labels map to existing statuses:
  - `planted` → `已埋设`
  - `advanced` → `活跃推进`
  - `resolved` → `已收束`
  - `expired` → `已放弃`
- `unresolved` filter means `planted` or `advanced`.
- `stale` filter means IDs returned by `getStaleForeshadows(worldId)`.
- `overdue` filter means stale items with `alert_level === 'critical'`.
- High urgency means `urgency_level >= 4`.
- Drop action means `updateForeshadow(id, { status: 'expired' })` for `planted` or `advanced`.

---

### Task 1: Frontend ledger summary and filters

**Files:**
- Modify: `frontend/src/components/ForeshadowManager.test.tsx`
- Modify: `frontend/src/components/ForeshadowManager.tsx`

- [ ] **Step 1: Write failing tests for summary and filters**

Add test data in `ForeshadowManager.test.tsx` with four foreshadows:

```typescript
const foreshadows: Foreshadow[] = [
  {
    id: 1,
    source_chapter_id: 3,
    title: '裂纹玉佩',
    description: '玉佩出现裂纹。',
    foreshadow_type: 'plot',
    status: 'advanced',
    urgency_level: 4,
    related_character_ids: [1],
    expected_resolution_window: '第2-4章',
  },
  {
    id: 2,
    source_chapter_id: 1,
    title: '井中红光',
    description: '井底有红光。',
    foreshadow_type: 'world',
    status: 'planted',
    urgency_level: 5,
    related_character_ids: [2],
    expected_resolution_window: null,
  },
  {
    id: 3,
    source_chapter_id: 2,
    title: '旧盟约',
    description: '旧盟约已经兑现。',
    foreshadow_type: 'character',
    status: 'resolved',
    urgency_level: 2,
    related_character_ids: [],
    expected_resolution_window: '第5章',
  },
  {
    id: 4,
    source_chapter_id: null,
    title: '废弃暗门',
    description: '暗门线已放弃。',
    foreshadow_type: 'plot',
    status: 'expired',
    urgency_level: 1,
    related_character_ids: [],
    expected_resolution_window: null,
  },
];

const staleForeshadows: StaleForeshadow[] = [
  { foreshadow: foreshadows[1], chapters_since_planted: 6, alert_level: 'critical' },
];
```

Add tests:

```typescript
it('renders ledger summary counts and governance metadata', async () => {
  render(<ForeshadowManager worldId={7} characters={characters} />);

  expect(await screen.findByText('Foreshadow Ledger')).toBeInTheDocument();
  expect(screen.getByText('总数：4')).toBeInTheDocument();
  expect(screen.getByText('未收束：2')).toBeInTheDocument();
  expect(screen.getByText('Stale：1')).toBeInTheDocument();
  expect(screen.getByText('Overdue：1')).toBeInTheDocument();
  expect(screen.getByText('高紧迫：2')).toBeInTheDocument();
  expect(screen.getByText('来源章节：#3')).toBeInTheDocument();
  expect(screen.getByText('收束窗口：第2-4章')).toBeInTheDocument();
  expect(screen.getByText('关联角色：林砚')).toBeInTheDocument();
  expect(screen.getByText('生命周期：活跃推进')).toBeInTheDocument();
  expect(screen.getByText('状态：advanced')).toBeInTheDocument();
});

it('filters unresolved stale overdue resolved and dropped foreshadows', async () => {
  const user = userEvent.setup();
  render(<ForeshadowManager worldId={7} characters={characters} />);

  expect(await screen.findByText('裂纹玉佩')).toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: '未收束 2' }));
  expect(screen.getByText('裂纹玉佩')).toBeInTheDocument();
  expect(screen.getByText('井中红光')).toBeInTheDocument();
  expect(screen.queryByText('旧盟约')).not.toBeInTheDocument();
  expect(screen.queryByText('废弃暗门')).not.toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: 'Stale 1' }));
  expect(screen.getByText('井中红光')).toBeInTheDocument();
  expect(screen.getByText('Overdue')).toBeInTheDocument();
  expect(screen.queryByText('裂纹玉佩')).not.toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: 'Overdue 1' }));
  expect(screen.getByText('井中红光')).toBeInTheDocument();
  expect(screen.queryByText('裂纹玉佩')).not.toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: '已收束 1' }));
  expect(screen.getByText('旧盟约')).toBeInTheDocument();
  expect(screen.queryByText('井中红光')).not.toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: '已放弃 1' }));
  expect(screen.getByText('废弃暗门')).toBeInTheDocument();
  expect(screen.queryByText('旧盟约')).not.toBeInTheDocument();
});
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/components/ForeshadowManager.test.tsx
```

Expected: FAIL because `Foreshadow Ledger`, summary counts, filter buttons, and governance metadata are not implemented yet.

- [ ] **Step 3: Implement summary/filter derivation in `ForeshadowManager.tsx`**

Add filter state and helpers near existing constants:

```typescript
type LedgerFilter = 'all' | 'unresolved' | 'stale' | 'overdue' | 'resolved' | 'dropped';

const FILTER_LABELS: Record<LedgerFilter, string> = {
  all: '全部',
  unresolved: '未收束',
  stale: 'Stale',
  overdue: 'Overdue',
  resolved: '已收束',
  dropped: '已放弃',
};

const LIFECYCLE_LABELS: Record<ForeshadowStatus, string> = {
  planted: '已埋设',
  advanced: '活跃推进',
  resolved: '已收束',
  expired: '已放弃',
};

function isUnresolved(statusValue: ForeshadowStatus) {
  return statusValue === 'planted' || statusValue === 'advanced';
}
```

Inside component state:

```typescript
const [ledgerFilter, setLedgerFilter] = useState<LedgerFilter>('all');
```

After stale count calculation, derive sets/counts/items:

```typescript
const staleById = new Map(staleForeshadows.map((item) => [item.foreshadow.id, item]));
const overdueIds = new Set(staleForeshadows.filter((item) => item.alert_level === 'critical').map((item) => item.foreshadow.id));
const summary = {
  total: foreshadows.length,
  unresolved: foreshadows.filter((item) => isUnresolved(item.status)).length,
  stale: staleForeshadows.length,
  overdue: overdueIds.size,
  highUrgency: foreshadows.filter((item) => item.urgency_level >= 4).length,
  resolved: foreshadows.filter((item) => item.status === 'resolved').length,
  dropped: foreshadows.filter((item) => item.status === 'expired').length,
};
const visibleForeshadows = foreshadows.filter((item) => {
  if (ledgerFilter === 'unresolved') return isUnresolved(item.status);
  if (ledgerFilter === 'stale') return staleById.has(item.id);
  if (ledgerFilter === 'overdue') return overdueIds.has(item.id);
  if (ledgerFilter === 'resolved') return item.status === 'resolved';
  if (ledgerFilter === 'dropped') return item.status === 'expired';
  return true;
});
const filterCounts: Record<LedgerFilter, number> = {
  all: summary.total,
  unresolved: summary.unresolved,
  stale: summary.stale,
  overdue: summary.overdue,
  resolved: summary.resolved,
  dropped: summary.dropped,
};
```

Render summary/filter controls above error/cards:

```tsx
<section className="mt-4 rounded-3xl border border-amber-900/15 bg-amber-50/50 p-4">
  <div className="flex flex-wrap items-center justify-between gap-3">
    <div>
      <p className="chapter-kicker">Foreshadow Ledger</p>
      <h2 className="text-2xl font-black text-[#34210f]">伏笔治理台</h2>
    </div>
    <div className="flex flex-wrap gap-2 text-xs font-black text-[#5e3b1c]">
      <span className="rounded-full bg-white/70 px-3 py-1">总数：{summary.total}</span>
      <span className="rounded-full bg-white/70 px-3 py-1">未收束：{summary.unresolved}</span>
      <span className="rounded-full bg-white/70 px-3 py-1">Stale：{summary.stale}</span>
      <span className="rounded-full bg-white/70 px-3 py-1">Overdue：{summary.overdue}</span>
      <span className="rounded-full bg-white/70 px-3 py-1">高紧迫：{summary.highUrgency}</span>
    </div>
  </div>
  <div className="mt-4 flex flex-wrap gap-2">
    {(Object.keys(FILTER_LABELS) as LedgerFilter[]).map((filter) => (
      <button
        key={filter}
        type="button"
        className={ledgerFilter === filter ? 'primary-button text-sm' : 'secondary-button text-sm'}
        onClick={() => setLedgerFilter(filter)}
      >
        {FILTER_LABELS[filter]} {filterCounts[filter]}
      </button>
    ))}
  </div>
</section>
```

Change list/kanban rendering to use `visibleForeshadows` instead of `foreshadows`.

- [ ] **Step 4: Add metadata and risk badges to cards**

Inside `renderForeshadowCard`, derive risk info:

```typescript
const staleItem = staleById.get(f.id);
const isOverdue = overdueIds.has(f.id);
```

Add metadata block after type/urgency chips:

```tsx
<div className="grid gap-2 rounded-2xl bg-amber-50/60 p-3 text-xs ink-muted">
  <p><span className="font-semibold text-[#4a321e]">生命周期：</span>{LIFECYCLE_LABELS[f.status]}</p>
  <p><span className="font-semibold text-[#4a321e]">状态：</span>{f.status}</p>
  <p><span className="font-semibold text-[#4a321e]">来源章节：</span>{f.source_chapter_id ? `#${f.source_chapter_id}` : '未绑定来源章节'}</p>
  <p><span className="font-semibold text-[#4a321e]">收束窗口：</span>{f.expected_resolution_window ?? '未设定收束窗口'}</p>
</div>
{(staleItem || f.urgency_level >= 4) && (
  <div className="flex flex-wrap gap-2 text-xs font-black">
    {f.urgency_level >= 4 && <span className="rounded-full border border-red-700/25 bg-red-100 px-2 py-0.5 text-red-800">高紧迫</span>}
    {staleItem && <span className="rounded-full border border-amber-700/25 bg-amber-100 px-2 py-0.5 text-amber-900">Stale · {staleItem.chapters_since_planted} 章未推进</span>}
    {isOverdue && <span className="rounded-full border border-red-700/25 bg-red-100 px-2 py-0.5 text-red-800">Overdue</span>}
  </div>
)}
```

- [ ] **Step 5: Run tests to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/components/ForeshadowManager.test.tsx
```

Expected: PASS for ForeshadowManager tests.

---

### Task 2: Lifecycle drop action and refresh behavior

**Files:**
- Modify: `frontend/src/components/ForeshadowManager.test.tsx`
- Modify: `frontend/src/components/ForeshadowManager.tsx`

- [ ] **Step 1: Write failing drop-action test**

Add:

```typescript
it('drops an unresolved foreshadow and refreshes the world overview', async () => {
  const user = userEvent.setup();
  const onChanged = vi.fn();
  render(<ForeshadowManager worldId={7} characters={characters} onChanged={onChanged} />);

  expect(await screen.findByText('裂纹玉佩')).toBeInTheDocument();
  await user.click(screen.getAllByRole('button', { name: '放弃伏笔' })[0]);

  await waitFor(() => expect(updateForeshadow).toHaveBeenCalledWith(1, { status: 'expired' }));
  expect(getForeshadows).toHaveBeenCalledTimes(2);
  expect(getStaleForeshadows).toHaveBeenCalledTimes(2);
  expect(onChanged).toHaveBeenCalledTimes(1);
});
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/components/ForeshadowManager.test.tsx
```

Expected: FAIL because `放弃伏笔` button is absent.

- [ ] **Step 3: Implement drop action**

Add helper:

```typescript
function canDropStatus(statusValue: ForeshadowStatus) {
  return statusValue === 'planted' || statusValue === 'advanced';
}

async function dropForeshadow(f: Foreshadow) {
  if (!canDropStatus(f.status)) return;
  try {
    await updateForeshadow(f.id, { status: 'expired' });
    await load();
    await onChanged?.();
  } catch (err) {
    setError(err instanceof Error ? err.message : '放弃伏笔失败');
  }
}
```

Render the button in the card action row near advance/edit:

```tsx
{canDropStatus(f.status) && (
  <button className="ghost-button text-sm text-red-700/80" onClick={() => void dropForeshadow(f)}>
    放弃伏笔
  </button>
)}
```

- [ ] **Step 4: Run test to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/components/ForeshadowManager.test.tsx
```

Expected: PASS.

---

### Task 3: WorldPage ledger integration test

**Files:**
- Modify: `frontend/src/world/WorldPage.test.tsx`

- [ ] **Step 1: Write failing WorldPage assertion**

In the existing `renders World Bible Editor manager tabs with governance warning` test, after clicking `伏笔账本`, add:

```typescript
expect(await screen.findByText('Foreshadow Ledger')).toBeInTheDocument();
expect(screen.getByText('伏笔治理台')).toBeInTheDocument();
expect(screen.getByText('总数：1')).toBeInTheDocument();
```

- [ ] **Step 2: Run WorldPage test**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected after Task 1 implementation: PASS. If run before Task 1, expected RED because ledger header is absent.

---

### Task 4: Verification and git completion

**Files:**
- Verify: backend and frontend test/build commands.
- Commit/merge: git branch `feat/mvp7-foreshadow-ledger` into `main`.

- [ ] **Step 1: Run backend foreshadow targeted tests**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_foreshadow_crud.py -v
```

Expected: all tests pass. These verify existing backend filter/stale/lifecycle/world-version contracts remain intact.

- [ ] **Step 2: Run frontend targeted tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/components/ForeshadowManager.test.tsx src/world/WorldPage.test.tsx
```

Expected: all targeted frontend tests pass.

- [ ] **Step 3: Run frontend build**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: TypeScript and Vite build succeed.

- [ ] **Step 4: Check git diff and status**

Run:

```bash
git status --short --branch
git diff -- docs/superpowers/specs/2026-05-30-mvp7-foreshadow-ledger-design.md docs/superpowers/plans/2026-05-30-mvp7-foreshadow-ledger.md frontend/src/components/ForeshadowManager.tsx frontend/src/components/ForeshadowManager.test.tsx frontend/src/world/WorldPage.test.tsx
```

Expected: only MVP7 spec/plan/frontend ledger changes are present.

- [ ] **Step 5: Commit on feature branch**

Run:

```bash
git add docs/superpowers/specs/2026-05-30-mvp7-foreshadow-ledger-design.md docs/superpowers/plans/2026-05-30-mvp7-foreshadow-ledger.md frontend/src/components/ForeshadowManager.tsx frontend/src/components/ForeshadowManager.test.tsx frontend/src/world/WorldPage.test.tsx
git commit -m "feat: add foreshadow ledger"
```

Commit message body must include:

```text
Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```

- [ ] **Step 6: Merge back to main without pushing**

Run:

```bash
git checkout main
git merge feat/mvp7-foreshadow-ledger
```

Do not push.

- [ ] **Step 7: Post-merge verification**

Run at least targeted commands again after merge:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_foreshadow_crud.py -v
cd /opt/WorldSim-Writer/frontend && npm run test -- src/components/ForeshadowManager.test.tsx src/world/WorldPage.test.tsx && npm run build
```

Expected: all pass after merge.

## Self-Review

- Spec coverage: summary counts, filters, stale/overdue badges, lifecycle advance/drop, refresh callbacks, backend non-change, non-goals, and verification are covered.
- Placeholder scan: no TBD/TODO/fill-in instructions remain; code snippets and commands are explicit.
- Type consistency: plan uses current `Foreshadow`, `ForeshadowStatus`, `StaleForeshadow`, `updateForeshadow`, `getForeshadows`, and `getStaleForeshadows` names from the frontend API.
