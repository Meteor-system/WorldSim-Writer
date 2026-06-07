# Auto-Start Canon Boundary Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Inline execution only for this run. Do not use subagents, agents, code-review subagents, or dynamic workflows. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Next-3 auto-created first draft clearly communicate that the world exists but the chapter remains an unapproved draft until the user writes it into 正史.

**Architecture:** Keep this frontend-only. Add a small contextual notice in `StudioPage` only when `launchContext.autoStartFirstDraft` is true, place it near the chapter goal/review controls, and reuse existing approval/settlement UI for the actual canon write boundary. The notice must disappear for normal manual Studio launches and must not affect API calls.

**Tech Stack:** React, TypeScript, Vitest, Testing Library.

---

## File Structure

- Modify `frontend/src/studio/StudioPage.test.tsx` — add RED coverage for the auto-start canon-boundary notice and normal-launch absence.
- Modify `frontend/src/studio/StudioPage.tsx` — render the notice when Studio is launched with `autoStartFirstDraft`.

---

### Task 1: Add RED tests for auto-start boundary copy

- [ ] **Step 1: Add failing assertions to the auto-start test**

In `frontend/src/studio/StudioPage.test.tsx`, update `auto-generates the first draft for review when launched with auto-start intent` with these expectations after `Writer Draft` appears:

```ts
expect(screen.getByText('世界已创建，第一章正在草稿审阅中')).toBeInTheDocument();
expect(screen.getByText('这章尚未写入正史；只有点击「写入正史并更新世界」后，世界进度、事件历史和正式设定才会更新。')).toBeInTheDocument();
expect(screen.getByText('当前世界进度仍为 v1，草稿基准为 v1。')).toBeInTheDocument();
expect(screen.queryByText('世界推进结算')).not.toBeInTheDocument();
```

- [ ] **Step 2: Add normal-launch absence check**

In the existing manual drafting test `renders version selector, stash, paragraph controls, diff, and approval preview after drafting`, add:

```ts
expect(screen.queryByText('世界已创建，第一章正在草稿审阅中')).not.toBeInTheDocument();
```

- [ ] **Step 3: Verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx --run
```

Expected: fails because the new auto-start boundary notice is not rendered yet.

---

### Task 2: Render auto-start canon-boundary notice

- [ ] **Step 1: Add minimal UI**

In `frontend/src/studio/StudioPage.tsx`, after the chapter-goal card and before the error block, render this conditional notice:

```tsx
{launchContext?.autoStartFirstDraft && !settlement && (
  <section className="book-card border-2 border-sky-500/25 bg-sky-50/70 p-5" role="status" aria-live="polite">
    <p className="chapter-kicker">开书草稿</p>
    <h2 className="text-xl font-black text-[#203045]">世界已创建，第一章正在草稿审阅中</h2>
    <p className="manuscript mt-2 text-sm text-[#26364d]">这章尚未写入正史；只有点击「写入正史并更新世界」后，世界进度、事件历史和正式设定才会更新。</p>
    <p className="manuscript mt-1 text-sm text-[#26364d]">当前世界进度仍为 v{localWorld.world_version}，草稿基准为 v{chapter?.base_world_version ?? localWorld.world_version}。</p>
  </section>
)}
```

- [ ] **Step 2: Verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx --run
```

Expected: passes.

---

### Task 3: Final verification and commit

- [ ] **Step 1: Run targeted tests**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx --run
```

Expected: all `StudioPage` tests pass.

- [ ] **Step 2: Run related Next-3 regression tests**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldCreationForm.test.tsx src/world/WorldPage.test.tsx src/studio/StudioPage.test.tsx --run
```

Expected: all targeted Next-3-related tests pass.

- [ ] **Step 3: Run frontend build**

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: TypeScript and Vite build pass.

- [ ] **Step 4: Run diff checks**

```bash
git -C /opt/WorldSim-Writer diff --check
git -C /opt/WorldSim-Writer diff --cached --check
```

Expected: no output.

- [ ] **Step 5: Commit**

```bash
git -C /opt/WorldSim-Writer add docs/superpowers/plans/2026-06-07-auto-start-canon-boundary-copy.md frontend/src/studio/StudioPage.test.tsx frontend/src/studio/StudioPage.tsx
git -C /opt/WorldSim-Writer commit -m "fix: clarify auto-start draft canon boundary"
```

Expected: commit succeeds on current branch. Do not push. Do not merge.

---

## Inline Self-Review

- Spec coverage: closes the documented Next-3 risk that users must distinguish created world, draft review, and 正史 write.
- Placeholder scan: no TBD/TODO placeholders.
- Scope check: frontend-only copy/UI change, no backend contracts, no canon behavior changes.
