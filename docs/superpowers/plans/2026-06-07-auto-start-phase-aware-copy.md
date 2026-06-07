# Auto-Start Phase-Aware Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Inline execution only for this run. Do not use subagents, agents, code-review subagents, or dynamic workflows. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the brief-created-world Studio notice accurately describe auto-start progress, failure/retry, and draft review states.

**Architecture:** Keep this frontend-only inside `StudioPage`. Replace the fixed auto-start notice copy with phase-aware rendering based on existing state: `working`/no draft means generating, `error`/no draft means retry needed, and `draft` means review. Do not change API calls, chapter approval, world versions, or EventLog behavior.

**Tech Stack:** React, TypeScript, Vitest, Testing Library.

---

## File Structure

- Modify `frontend/src/studio/StudioPage.test.tsx` — add RED assertions for generating and failed auto-start states.
- Modify `frontend/src/studio/StudioPage.tsx` — compute notice title/detail/version copy from current Studio state.

---

### Task 1: Add RED tests for phase-aware notice states

- [ ] **Step 1: Add pending/generating-state test**

In `frontend/src/studio/StudioPage.test.tsx`, add a test near the existing auto-start tests:

```ts
it('shows generating copy while auto-start first draft is still running', async () => {
  vi.mocked(createChapter).mockImplementationOnce(async () => new Promise<Awaited<ReturnType<typeof createChapter>>>(() => {}));

  render(<StudioPage world={world} launchContext={{ initialChapterGoal: executionContext.goal, executionContext, autoStartFirstDraft: true }} onBack={vi.fn()} onApproved={vi.fn()} />);

  expect(await screen.findByText('世界已创建，正在生成第一章草稿')).toBeInTheDocument();
  expect(screen.getByText('系统正在创建章节、大纲和正文草稿；这一步不会写入正史，也不会推进世界进度。')).toBeInTheDocument();
  expect(screen.queryByText('世界已创建，第一章正在草稿审阅中')).not.toBeInTheDocument();
  expect(approveChapter).not.toHaveBeenCalled();
});
```

- [ ] **Step 2: Strengthen failure-state test**

In `shows a friendly retry path when auto-start first draft fails`, add:

```ts
expect(screen.getByText('世界已创建，第一章草稿尚未生成')).toBeInTheDocument();
expect(screen.getByText('世界已经保留；请检查章节目标后点击下方创建章节按钮手动重试。')).toBeInTheDocument();
expect(screen.queryByText('世界已创建，第一章正在草稿审阅中')).not.toBeInTheDocument();
```

- [ ] **Step 3: Verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx --run
```

Expected: fails because the notice still uses fixed review copy.

---

### Task 2: Implement phase-aware notice copy

- [ ] **Step 1: Add notice copy variables**

In `frontend/src/studio/StudioPage.tsx`, after existing derived values near `reviewMaterialReferenceTitles`, add:

```ts
  const autoStartNoticeTitle = error && !draft
    ? '世界已创建，第一章草稿尚未生成'
    : !draft
      ? '世界已创建，正在生成第一章草稿'
      : '世界已创建，第一章正在草稿审阅中';
  const autoStartNoticeDetail = error && !draft
    ? '世界已经保留；请检查章节目标后点击下方创建章节按钮手动重试。'
    : !draft
      ? '系统正在创建章节、大纲和正文草稿；这一步不会写入正史，也不会推进世界进度。'
      : '这章尚未写入正史；只有点击「写入正史并更新世界」后，世界进度、事件历史和正式设定才会更新。';
```

- [ ] **Step 2: Use variables in the notice**

Replace fixed title/detail inside the auto-start notice with:

```tsx
<h2 className="text-xl font-black text-[#203045]">{autoStartNoticeTitle}</h2>
<p className="manuscript mt-2 text-sm text-[#26364d]">{autoStartNoticeDetail}</p>
{draft && <p className="manuscript mt-1 text-sm text-[#26364d]">当前世界进度仍为 v{localWorld.world_version}，草稿基准为 v{chapter?.base_world_version ?? localWorld.world_version}。</p>}
```

- [ ] **Step 3: Verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx --run
```

Expected: all StudioPage tests pass.

---

### Task 3: Final verification and commit

- [ ] **Step 1: Run targeted Next-3 tests**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldCreationForm.test.tsx src/world/WorldPage.test.tsx src/studio/StudioPage.test.tsx --run
```

Expected: all targeted tests pass.

- [ ] **Step 2: Run frontend build**

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: TypeScript and Vite build pass.

- [ ] **Step 3: Run diff checks and commit**

```bash
git -C /opt/WorldSim-Writer diff --check
git -C /opt/WorldSim-Writer add docs/superpowers/plans/2026-06-07-auto-start-phase-aware-copy.md frontend/src/studio/StudioPage.test.tsx frontend/src/studio/StudioPage.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "fix: make auto-start draft notice phase-aware"
```

Expected: commit succeeds on current branch. Do not push. Do not merge.

---

## Inline Self-Review

- Spec coverage: closes the remaining Next-3 copy gap for generating and failed auto-start states.
- Scope check: frontend-only copy logic, no API/canon behavior change.
- Placeholder scan: no TBD/TODO placeholders.
