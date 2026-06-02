# Single-World Bookshelf Gateway Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This run explicitly forbids subagents and dynamic workflows, so execute inline with strict TDD.

**Goal:** Let users with exactly one auto-opened world return to the bookshelf and create another novel without breaking single-world auto-open.

**Architecture:** Frontend-only change in `WorldPage`. Keep existing `loadWorld()` auto-open behavior; adjust only the visibility condition for the existing `返回作品书架` control and add tests proving the single-world gateway works.

**Tech Stack:** React, TypeScript, Vite, Vitest, React Testing Library.

---

## File Structure

- Modify: `frontend/src/world/WorldPage.test.tsx`
  - Add two single-world bookshelf gateway tests in the existing `WorldPage bookshelf` describe block.
- Modify: `frontend/src/world/WorldPage.tsx`
  - Change the archive-card return-to-bookshelf button condition from `worlds.length > 1` to `worlds.length > 0`.
- Create: `docs/superpowers/specs/2026-06-01-single-world-bookshelf-gateway-design.md`
  - Design spec for this MVP.
- Create: `docs/superpowers/plans/2026-06-01-single-world-bookshelf-gateway.md`
  - This TDD plan.

---

### Task 1: Add RED tests

**Files:**
- Modify: `frontend/src/world/WorldPage.test.tsx`

- [ ] **Step 1: Add single-world return test**

Add under `describe('WorldPage bookshelf', ...)`, before the existing single-world auto-open regression:

```ts
it('returns from a single auto-opened world to the bookshelf', async () => {
  const user = userEvent.setup();

  render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

  expect(await screen.findByText('World Canon')).toBeInTheDocument();
  expect(screen.queryByText('作品书架')).not.toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: '返回作品书架' }));

  expect(screen.getByText('作品书架')).toBeInTheDocument();
  expect(screen.getByText('青岚城')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '创建新小说' })).toBeInTheDocument();
});
```

- [ ] **Step 2: Add single-world create-new test**

```ts
it('opens the creation form from a single-world bookshelf', async () => {
  const user = userEvent.setup();

  render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

  await user.click(await screen.findByRole('button', { name: '返回作品书架' }));
  await user.click(screen.getByRole('button', { name: '创建新小说' }));

  expect(await screen.findByText('创建世界工坊')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: '返回作品书架' })).toBeInTheDocument();
  expect(listWorldSeeds).toHaveBeenCalled();
});
```

- [ ] **Step 3: Run focused test and verify RED**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: the new tests fail because `返回作品书架` is not present for a single auto-opened world.

---

### Task 2: Minimal GREEN implementation

**Files:**
- Modify: `frontend/src/world/WorldPage.tsx`

- [ ] **Step 1: Change the button condition**

Replace:

```tsx
{worlds.length > 1 && <button className="secondary-button" type="button" onClick={returnToBookshelf}>返回作品书架</button>}
```

with:

```tsx
{worlds.length > 0 && <button className="secondary-button" type="button" onClick={returnToBookshelf}>返回作品书架</button>}
```

- [ ] **Step 2: Run focused test and verify GREEN**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: `WorldPage.test.tsx` passes.

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

Expected: no whitespace errors; do not stage `.hermes/plans/*` or `backend/worldsim-dev.db`.

- [ ] **Step 4: Commit only relevant files**

```bash
cd /opt/WorldSim-Writer && git add docs/superpowers/specs/2026-06-01-single-world-bookshelf-gateway-design.md docs/superpowers/plans/2026-06-01-single-world-bookshelf-gateway.md frontend/src/world/WorldPage.test.tsx frontend/src/world/WorldPage.tsx && git commit -m "fix: expose bookshelf from single world"
```

Expected: commit succeeds. Do not merge and do not push.
