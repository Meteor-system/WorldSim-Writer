# MVP26 Search Result Tagging 0.5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use sequential inline execution because this repository request explicitly forbids subagents and dynamic workflows. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users apply an existing tag to all visible Global Search results without manually copying object IDs.

**Architecture:** Reuse the existing MVP25 `bulkAssignWorldTag` API helper and backend bulk endpoint. Extend `WorldSearchPanel` with an optional bulk assignment prop and UI that groups current search results by object type, then wire the helper through `WorldPage`. No backend production changes or schema migration are needed.

**Tech Stack:** React, TypeScript, Vite, Vitest, Testing Library, FastAPI, SQLAlchemy, pytest.

---

## File map

- Create: `docs/superpowers/specs/2026-05-31-mvp26-search-result-tagging-design.md` — design spec.
- Create: `docs/superpowers/plans/2026-05-31-mvp26-search-result-tagging.md` — implementation plan.
- Modify: `frontend/src/world/WorldSearchPanel.tsx` — optional search-result bulk tagging UI and behavior.
- Modify: `frontend/src/world/WorldSearchPanel.test.tsx` — RED/GREEN tests for grouping visible search results and success notices.
- Modify: `frontend/src/world/WorldPage.tsx` — pass `bulkAssignWorldTag` into `WorldSearchPanel`.
- Modify: `frontend/src/world/WorldPage.test.tsx` — integration coverage for the wired search-result tagging surface.

---

### Task 1: WorldSearchPanel RED tests

- [ ] Extend `frontend/src/world/WorldSearchPanel.test.tsx` with a failing test that renders `WorldSearchPanel` with `onListTags` and `onBulkAssignTag`, performs a search, selects target tag `灯塔线`, clicks `给搜索结果打标签`, and expects grouped calls:

```ts
expect(onBulkAssignTag).toHaveBeenNthCalledWith(1, 7, 3, { object_type: 'character', object_ids: [1] });
expect(onBulkAssignTag).toHaveBeenNthCalledWith(2, 7, 3, { object_type: 'foreshadow', object_ids: [2] });
expect(await screen.findByText('已为搜索结果打标：新增 2，已存在 1。')).toBeInTheDocument();
```

- [ ] Include an assertion that `onListTags` is called again after success so tag counts refresh.
- [ ] Extend the same test file with a failing validation test: render bulk tagging with a blank target select, click `给搜索结果打标签`, and expect alert text `请选择目标标签` without calling `onBulkAssignTag`.
- [ ] Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldSearchPanel.test.tsx
```

Expected: fail because `WorldSearchPanel` has no `onBulkAssignTag` prop and no `搜索结果批量打标` UI.

---

### Task 2: WorldSearchPanel GREEN implementation

- [ ] Import `ObjectTagBulkAssignResponse` in `frontend/src/world/WorldSearchPanel.tsx`.
- [ ] Extend props with:

```ts
onBulkAssignTag?: (worldId: number, tagId: number, data: { object_type: string; object_ids: number[] }) => Promise<ObjectTagBulkAssignResponse>;
```

- [ ] Add state for `targetTagId` and `bulkNotice`.
- [ ] Add helpers that collect visible results with non-null `object_id`, group by `object_type`, and deduplicate IDs within each group.
- [ ] Add `submitBulkTagging()` that validates target tag, calls `onBulkAssignTag` once per group, sums response counts, displays `已为搜索结果打标：新增 X，已存在 Y。`, and reloads tags with the existing tag loader.
- [ ] Render `搜索结果批量打标`, `目标标签`, and `给搜索结果打标签` only when bulk tagging is wired and there are taggable visible results.
- [ ] Rerun:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldSearchPanel.test.tsx
```

Expected: PASS.

---

### Task 3: WorldPage integration RED test

- [ ] Extend `frontend/src/world/WorldPage.test.tsx` so the Narrative Control Center test performs a search, waits for `搜索结果批量打标`, and verifies the bulk tagging surface exists when rendered through `WorldPage`.
- [ ] Mock `searchWorld` to return at least one object result with `object_id`.
- [ ] Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: fail until `WorldPage.tsx` passes `bulkAssignWorldTag` into `WorldSearchPanel`.

---

### Task 4: WorldPage GREEN implementation

- [ ] Update `frontend/src/world/WorldPage.tsx`:

```tsx
<WorldSearchPanel
  worldId={world.id}
  onSearch={searchWorld}
  onListTags={listWorldTags}
  onBulkAssignTag={bulkAssignWorldTag}
/>
```

- [ ] Rerun:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: PASS.

---

### Task 5: Targeted verification

- [ ] Run frontend targeted tests:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldSearchPanel.test.tsx src/world/WorldPage.test.tsx src/world/WorldTagsPanel.test.tsx src/api/client.test.ts
```

- [ ] Run backend targeted tests for reused search/tag contracts:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_tags.py tests/test_world_search.py -q
```

- [ ] Run frontend build:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: all commands pass.

---

### Task 6: Commit on feature branch only

- [ ] Confirm branch is `feat/mvp26-search-result-tagging`.
- [ ] Confirm working tree changes are limited to MVP26 spec, plan, and tested frontend code.
- [ ] Commit with Conventional Commit message:

```bash
git add docs/superpowers/specs/2026-05-31-mvp26-search-result-tagging-design.md docs/superpowers/plans/2026-05-31-mvp26-search-result-tagging.md frontend/src/world/WorldSearchPanel.tsx frontend/src/world/WorldSearchPanel.test.tsx frontend/src/world/WorldPage.tsx frontend/src/world/WorldPage.test.tsx
git commit -m "feat: add search result tagging"
```

Commit body must include:

```text
Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```

- [ ] Do not merge `main`.
- [ ] Do not push.
- [ ] Report branch, commit hash, RED/GREEN evidence, verification results, and that no merge/push was performed.

---

## Self-review

- No placeholders remain.
- The plan starts with failing frontend tests before production code.
- Backend production code is intentionally unchanged and covered by existing targeted backend tests.
- The plan respects inline execution, no dynamic workflows, no subagents, skip review, commit on feature branch only, no merge, and no push.
