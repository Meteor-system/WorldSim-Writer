# Auto-Start First Draft Retry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Inline execution only for this run. Do not use subagents, agents, code-review subagents, or dynamic workflows. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give users an explicit retry button when the post-creation auto-start first chapter draft fails, while preserving the created world and the write-to-正史 boundary.

**Architecture:** Keep this frontend-only in `StudioPage`. Use the existing auto-start failure state (`launchContext.autoStartFirstDraft`, `error`, and no `draft`) to render a retry CTA in the auto-start notice. The retry should call the existing manual `createChapterSession` path, which freezes the edited chapter goal and creates a chapter without writing 正史.

**Tech Stack:** React, TypeScript, Vitest, Testing Library.

---

## File Structure

- Modify `frontend/src/studio/StudioPage.test.tsx` — strengthen the auto-start failure regression to expect and exercise an explicit retry CTA.
- Modify `frontend/src/studio/StudioPage.tsx` — render a retry button in the auto-start failure notice and wire it to `createChapterSession`.

---

### Task 1: Add RED test coverage for explicit retry

- [ ] **Step 1: Update the auto-start failure test**

In `frontend/src/studio/StudioPage.test.tsx`, update `shows a friendly retry path when auto-start first draft fails` to click an explicit retry button in the auto-start notice:

```ts
expect(screen.getByRole('button', { name: '重新创建第一章草稿' })).toBeEnabled();
expect(screen.getByRole('button', { name: '用候选素材参考创建章节' })).toBeEnabled();
vi.mocked(createChapter).mockClear();
vi.mocked(createChapter).mockResolvedValueOnce({
  id: 12,
  world_id: 7,
  title: '重试第一章',
  status: 'drafting',
  draft_version: 1,
  approved_version: null,
  base_world_version: 1,
  approved_content: null,
  chapter_goal: executionContext.goal,
  outline_beats: [],
  outline_context: {},
  critique_report: {},
  execution_context: executionContext,
});

await user.click(screen.getByRole('button', { name: '重新创建第一章草稿' }));

expect(createChapter).toHaveBeenCalledWith(7, expect.objectContaining({
  chapter_goal: executionContext.goal,
  execution_context: expect.objectContaining({ goal: executionContext.goal }),
}));
expect(await screen.findByText('重试第一章')).toBeInTheDocument();
expect(screen.queryByText('世界已创建，第一章草稿尚未生成')).not.toBeInTheDocument();
```

- [ ] **Step 2: Verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx --run
```

Expected: fails because `重新创建第一章草稿` does not exist yet.

---

### Task 2: Implement the retry CTA

- [ ] **Step 1: Add auto-start retry state and failure boolean**

In `frontend/src/studio/StudioPage.tsx`, add retry-created state near the existing error state:

```tsx
const [autoStartRetryCreatedChapter, setAutoStartRetryCreatedChapter] = useState(false);
```

Near the auto-start notice constants, add:

```tsx
const autoStartFailedWithoutDraft = Boolean(launchContext?.autoStartFirstDraft && error && !draft);
```

- [ ] **Step 2: Mark successful post-failure manual chapter creation**

At the start of `createChapterSession`, record whether this call is retrying a failed auto-start:

```tsx
const wasAutoStartFailureRetry = Boolean(launchContext?.autoStartFirstDraft && error && !draft);
```

After successfully setting the created chapter state, add:

```tsx
if (wasAutoStartFailureRetry) setAutoStartRetryCreatedChapter(true);
```

This lets both the explicit retry CTA and the existing lower manual creation button clear the stale failure banner after success.

- [ ] **Step 3: Render the retry button inside the auto-start notice**

Inside the auto-start notice section after `autoStartNoticeDetail`, render:

```tsx
{autoStartFailedWithoutDraft && (
  <button className="primary-button mt-4" disabled={working || Boolean(chapter)} onClick={createChapterSession}>重新创建第一章草稿</button>
)}
```

The button reuses the existing manual creation path so it does not auto-run outline/write and does not write 正史.

- [ ] **Step 4: Hide only the stale post-retry failure notice**

Change the auto-start notice render condition from:

```tsx
{launchContext?.autoStartFirstDraft && !settlement && (
```

to:

```tsx
{launchContext?.autoStartFirstDraft && !settlement && !autoStartRetryCreatedChapter && (
```

This keeps the normal auto-start generation notice visible even after the chapter record exists but before the draft exists, while removing the stale failure banner once a manual retry successfully creates a chapter session.

- [ ] **Step 5: Verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx --run
```

Expected: all StudioPage tests pass.

---

### Task 3: Final verification and commit

- [ ] **Step 1: Run related Next-3 regression tests**

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
git -C /opt/WorldSim-Writer add docs/superpowers/plans/2026-06-07-auto-start-first-draft-retry.md frontend/src/studio/StudioPage.test.tsx frontend/src/studio/StudioPage.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer commit -m "fix: add first draft retry after auto-start failure"
```

Expected: commit succeeds on current branch. Do not push. Do not merge.

---

## Inline Self-Review

- Spec coverage: closes a documented Next-3 reliability gap by giving a clear retry entrance after auto-start fails without rolling back the created world.
- Scope check: frontend-only CTA and test change; no API, canon, EventLog, world version, or auto-approval behavior changes.
- TDD check: test expects a missing button first, then implementation adds minimal behavior.
- Placeholder scan: no TBD/TODO placeholders.
