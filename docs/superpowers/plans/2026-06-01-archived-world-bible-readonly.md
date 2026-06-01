# Archived World Bible Read-Only Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This run explicitly forbids subagents and dynamic workflows, so execute inline with strict TDD.

**Goal:** Make World Bible manager tabs read-only for archived worlds.

**Architecture:** Frontend-only prop threading from `WorldPage` into manager components. Each manager hides mutating controls when `readOnly` is true while keeping inspection UI visible.

**Tech Stack:** React, TypeScript, Vite, Vitest, React Testing Library.

---

## File Structure

- Modify: `frontend/src/world/WorldPage.test.tsx`
  - Add archived manager read-only regression test.
- Modify: `frontend/src/world/WorldPage.tsx`
  - Pass `readOnly={isArchivedWorld}` to manager tabs.
- Modify: `frontend/src/components/CharacterManager.tsx`
  - Add optional read-only prop and hide character edit actions.
- Modify: `frontend/src/components/RelationManager.tsx`
  - Add optional read-only prop and hide relation create/edit actions.
- Modify: `frontend/src/components/ForeshadowManager.tsx`
  - Add optional read-only prop and hide mutating foreshadow actions.
- Create: `docs/superpowers/specs/2026-06-01-archived-world-bible-readonly-design.md`
  - Design spec for this MVP.
- Create: `docs/superpowers/plans/2026-06-01-archived-world-bible-readonly.md`
  - This implementation plan.

---

### Task 1: Add RED test

**Files:**
- Modify: `frontend/src/world/WorldPage.test.tsx`

- [ ] **Step 1: Add archived manager read-only test**

Add under `describe('WorldPage Narrative Control Center', ...)` near the existing manager-tab test:

```ts
it('keeps World Bible manager tabs read-only for archived worlds', async () => {
  const user = userEvent.setup();
  vi.mocked(apiRequest).mockReset();
  vi.mocked(apiRequest)
    .mockResolvedValueOnce([
      { id: 7, title: '青岚城', genre_template: 'xianxia', truth_canon: '灵脉正在衰退。', truth_canon_version: 1, world_version: 2, status: 'archived', tone_profile: {}, current_characters: [], current_foreshadows: [], current_relations: [] },
    ])
    .mockResolvedValueOnce(archivedWorld);

  render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

  await user.click(await screen.findByRole('button', { name: '打开 青岚城' }));
  await user.click(screen.getByRole('button', { name: '角色管理' }));

  expect(await screen.findByText('已归档小说为只读模式；恢复写作后才能编辑世界资料。')).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '编辑' })).not.toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: '关系管理' }));
  expect(await screen.findByText('已归档小说为只读模式；恢复写作后才能编辑世界资料。')).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '+ 新增关系' })).not.toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: '伏笔账本' }));
  expect(await screen.findByText('已归档小说为只读模式；恢复写作后才能编辑世界资料。')).toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '+ 新增伏笔' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '放弃伏笔' })).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: '删除' })).not.toBeInTheDocument();
  expect(await screen.findByRole('button', { name: '展开时间线' })).toBeInTheDocument();
});
```

- [ ] **Step 2: Run focused test and verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: the new test fails because archived manager tabs still show edit actions and no read-only manager notice exists.

---

### Task 2: Implement minimal GREEN

**Files:**
- Modify: `frontend/src/components/CharacterManager.tsx`
- Modify: `frontend/src/components/RelationManager.tsx`
- Modify: `frontend/src/components/ForeshadowManager.tsx`
- Modify: `frontend/src/world/WorldPage.tsx`

- [ ] **Step 1: Add read-only prop and notice to CharacterManager**

Change props:

```ts
type Props = { worldId: number; onChanged?: () => Promise<void> | void; readOnly?: boolean };
```

Change component signature:

```tsx
export function CharacterManager({ worldId, onChanged, readOnly = false }: Props) {
```

Replace the formal edit warning with:

```tsx
<p className="mt-3 rounded-2xl border border-amber-700/25 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-900">
  {readOnly ? '已归档小说为只读模式；恢复写作后才能编辑世界资料。' : '这些编辑会正式写入世界状态，并使 world_version 增长。'}
</p>
```

Wrap the edit action:

```tsx
{!readOnly && (
  <div className="mt-auto flex gap-2 pt-2">
    <button className="secondary-button text-sm" onClick={() => openEdit(c)}>
      编辑
    </button>
  </div>
)}
```

- [ ] **Step 2: Add read-only prop and notice to RelationManager**

Change props:

```ts
type Props = { worldId: number; characters: Character[]; onChanged?: () => Promise<void> | void; readOnly?: boolean };
```

Change signature:

```tsx
export function RelationManager({ worldId, characters, onChanged, readOnly = false }: Props) {
```

Render create button only when not read-only:

```tsx
{!readOnly && (
  <button className="primary-button" onClick={openCreate} disabled={characters.length < 2}>
    + 新增关系
  </button>
)}
```

Use the same read-only notice copy and wrap relation edit actions in `!readOnly`.

- [ ] **Step 3: Add read-only prop and notice to ForeshadowManager**

Change props:

```ts
type Props = { worldId: number; characters: Character[]; onChanged?: () => Promise<void> | void; readOnly?: boolean };
```

Change signature:

```tsx
export function ForeshadowManager({ worldId, characters, onChanged, readOnly = false }: Props) {
```

In `dropOnStatus`, add:

```ts
if (readOnly) return;
```

In `renderForeshadowCard`, set:

```tsx
draggable={!readOnly}
onDragStart={() => { if (!readOnly) setDraggingId(f.id); }}
```

Hide mutating controls with `!readOnly`:

- status advance button should become a non-button status pill in read-only mode;
- `编辑`, `放弃伏笔`, delete confirmation controls should not render;
- `+ 新增伏笔` should not render.

Use the same read-only notice copy in the warning area.

- [ ] **Step 4: Pass readOnly from WorldPage**

Change manager renders:

```tsx
{tab === 'characters' && <CharacterManager worldId={world.id} onChanged={loadWorld} readOnly={isArchivedWorld} />}

{tab === 'relations' && (
  <RelationManager worldId={world.id} characters={world.characters} onChanged={loadWorld} readOnly={isArchivedWorld} />
)}

{tab === 'foreshadows' && (
  <ForeshadowManager worldId={world.id} characters={world.characters} onChanged={loadWorld} readOnly={isArchivedWorld} />
)}
```

- [ ] **Step 5: Run focused test and verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: all `WorldPage` tests pass.

---

### Task 3: Verification and commit

**Files:**
- Verify changed docs, tests, and implementation.

- [ ] **Step 1: Run frontend build**

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 2: Run full frontend tests**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test
```

Expected: all frontend tests pass.

- [ ] **Step 3: Run diff check and status review**

```bash
cd /opt/WorldSim-Writer && git diff --check && git status --short && git diff --stat
```

Expected: no whitespace errors; do not stage `backend/worldsim-dev.db` or unrelated `.hermes/plans/*`.

- [ ] **Step 4: Commit relevant files only**

```bash
cd /opt/WorldSim-Writer && git add docs/superpowers/specs/2026-06-01-archived-world-bible-readonly-design.md docs/superpowers/plans/2026-06-01-archived-world-bible-readonly.md frontend/src/world/WorldPage.test.tsx frontend/src/world/WorldPage.tsx frontend/src/components/CharacterManager.tsx frontend/src/components/RelationManager.tsx frontend/src/components/ForeshadowManager.tsx && git commit -m "fix: keep archived world bible read-only"
```

Expected: commit succeeds. Do not push and do not merge.
