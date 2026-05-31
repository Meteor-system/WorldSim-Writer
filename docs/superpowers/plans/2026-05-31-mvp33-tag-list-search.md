# MVP33 Tag List Search 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This repository run is explicitly inline-only: do not use dynamic workflows, subagents, or the code-review subagent.

**Goal:** Add local text search over the tag list so users can quickly find a tag before opening its detail.

**Architecture:** Frontend-only view enhancement in `WorldTagsPanel`. The component filters the loaded `TagListResponse.tags` array locally and clears selected detail if the active query hides the selected tag; no backend route, schema, database, canon, world-version, or EventLog behavior changes.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, Vite; existing FastAPI pytest tag/search suites for regression verification.

---

## File structure

- Modify `frontend/src/world/WorldTagsPanel.test.tsx` — add RED/GREEN coverage for local tag-list search.
- Modify `frontend/src/world/WorldTagsPanel.tsx` — add tag search state, derived visible tags, search UI, no-match state, and selected-detail clearing.
- Create `docs/superpowers/specs/2026-05-31-mvp33-tag-list-search-design.md` — MVP33 design spec.
- Create `docs/superpowers/plans/2026-05-31-mvp33-tag-list-search.md` — implementation plan.

---

### Task 1: Frontend tag-list search TDD

**Files:**
- Test: `frontend/src/world/WorldTagsPanel.test.tsx`
- Modify: `frontend/src/world/WorldTagsPanel.tsx`

- [ ] **Step 1: Write failing frontend tests**

In `frontend/src/world/WorldTagsPanel.test.tsx`, add these tests before the existing empty/error state test:

```tsx
it('searches visible tags by name', async () => {
  const user = userEvent.setup();
  renderPanel();

  await screen.findByText('灯塔线');
  expect(screen.getByText('主线归档')).toBeInTheDocument();

  await user.type(screen.getByLabelText('搜索标签'), '归档');

  expect(screen.queryByText('灯塔线')).not.toBeInTheDocument();
  expect(screen.getByText('主线归档')).toBeInTheDocument();
  expect(screen.getByText('显示 1 / 2 个标签')).toBeInTheDocument();
});

it('searches visible tags by object summary', async () => {
  const user = userEvent.setup();
  renderPanel();

  await screen.findByText('灯塔线');
  await user.type(screen.getByLabelText('搜索标签'), 'character 1');

  expect(screen.getByText('灯塔线')).toBeInTheDocument();
  expect(screen.queryByText('主线归档')).not.toBeInTheDocument();
});

it('shows an empty state when tag search has no matches', async () => {
  const user = userEvent.setup();
  renderPanel();

  await screen.findByText('灯塔线');
  await user.type(screen.getByLabelText('搜索标签'), '不存在的标签');

  expect(await screen.findByText('当前搜索没有匹配标签。')).toBeInTheDocument();
  expect(screen.getByText('显示 0 / 2 个标签')).toBeInTheDocument();
});

it('clears selected tag detail when tag search hides it', async () => {
  const user = userEvent.setup();
  renderPanel({ onLoadTag: vi.fn().mockResolvedValue(detailResponse) });

  await screen.findByText('灯塔线');
  await user.click(screen.getByRole('button', { name: '查看 灯塔线' }));
  expect(await screen.findByText('许砚')).toBeInTheDocument();

  await user.type(screen.getByLabelText('搜索标签'), '归档');

  expect(screen.queryByText('许砚')).not.toBeInTheDocument();
  expect(screen.queryByText('当前标签')).not.toBeInTheDocument();
});
```

- [ ] **Step 2: Run frontend RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx
```

Expected: new tests fail because the `搜索标签` input and visible-tag filtering do not exist.

- [ ] **Step 3: Add tag search state and derived visible tags**

In `frontend/src/world/WorldTagsPanel.tsx`, add state near the existing `tags` state:

```ts
const [tagSearchQuery, setTagSearchQuery] = useState('');
```

Before the existing detail-object filtering derivation, add:

```ts
const normalizedTagSearchQuery = tagSearchQuery.trim().toLowerCase();
const visibleTags = normalizedTagSearchQuery
  ? tags.filter((tag) => {
      const haystack = [tag.name, tag.slug, tag.color ?? '', String(tag.assignment_count), countText(tag)].join(' ').toLowerCase();
      return haystack.includes(normalizedTagSearchQuery);
    })
  : tags;
const visibleTagIdsKey = visibleTags.map((tag) => tag.id).join(',');
```

Add this effect after the existing `loadTags()` effect:

```ts
useEffect(() => {
  if (selectedTagId !== null && !visibleTags.some((tag) => tag.id === selectedTagId)) {
    setSelectedTagId(null);
    setDetail(null);
    setDeleteConfirming(false);
  }
}, [selectedTagId, visibleTagIdsKey]);
```

- [ ] **Step 4: Add tag-list search UI and visible rendering**

After the empty tag state and before the tag card list, add:

```tsx
{tags.length > 0 && (
  <label className="block rounded-2xl bg-white/45 p-3 text-sm font-bold text-[#3b2511]">
    搜索标签
    <input
      className="paper-input mt-1"
      aria-label="搜索标签"
      value={tagSearchQuery}
      onChange={(event) => setTagSearchQuery(event.target.value)}
      placeholder="按名称、颜色、类型或数量搜索"
    />
    <span className="ink-muted mt-2 block text-xs">显示 {visibleTags.length} / {tags.length} 个标签</span>
  </label>
)}
```

Change the tag-card list condition and map from `tags` to `visibleTags`:

```tsx
{visibleTags.length > 0 && (
  <div className="flex flex-wrap gap-2">
    {visibleTags.map((tag) => (
      ...existing tag button...
    ))}
  </div>
)}
```

After the tag-card list, add:

```tsx
{tags.length > 0 && visibleTags.length === 0 && !error && <p className="ink-muted">当前搜索没有匹配标签。</p>}
```

- [ ] **Step 5: Run frontend GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldTagsPanel.test.tsx
```

Expected: all panel tests pass.

---

### Task 2: Final verification, docs status, commit, and merge

**Files:**
- Modified frontend panel files and MVP33 docs.

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

Append implementation status sections to the MVP33 spec and plan after verification, recording RED/GREEN and command results.

- [ ] **Step 5: Commit**

Run:

```bash
git -C /opt/WorldSim-Writer status --short
git -C /opt/WorldSim-Writer add frontend/src/world/WorldTagsPanel.tsx frontend/src/world/WorldTagsPanel.test.tsx docs/superpowers/specs/2026-05-31-mvp33-tag-list-search-design.md docs/superpowers/plans/2026-05-31-mvp33-tag-list-search.md
git -C /opt/WorldSim-Writer commit -m "feat: search tag list"
```

- [ ] **Step 6: Fast-forward merge to main without push**

Run:

```bash
git -C /opt/WorldSim-Writer checkout main
git -C /opt/WorldSim-Writer merge --ff-only feat/mvp33-tag-list-search
```

Do not push.

- [ ] **Step 7: Post-merge verification**

Repeat backend targeted tests, frontend targeted tests, and frontend build from Steps 1-3 on `main`.

Expected: all pass after merge.

## Self-review

- This plan covers all MVP33 acceptance criteria.
- No placeholders remain.
- Types and labels are consistent with the existing component and tests.
- Tag-list search only filters already-loaded data; it does not call write APIs.
- No backend, database, canon, world-version, or EventLog behavior changes are introduced.

## Execution status

Implemented on `feat/mvp33-tag-list-search` using TDD. RED was observed in `WorldTagsPanel.test.tsx` for the missing tag-list search input; GREEN was observed after adding local search state, visible tags, matching by name/slug/color/count/type summary, no-match empty state, and selected-detail clearing. Pre-merge backend targeted tests, frontend targeted tests, and frontend build passed.
