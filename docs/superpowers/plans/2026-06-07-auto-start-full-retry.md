# Auto-Start Full Retry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Inline execution only for this run. Do not use subagents, agents, code-review subagents, or dynamic workflows. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the `重新创建第一章草稿` recovery CTA actually retry the full first-chapter draft pipeline after auto-start failure.

**Architecture:** Keep this frontend-only in `StudioPage`. Extract the existing auto-start create → outline → write sequence into a reusable in-component helper, use it from both the initial auto-start effect and the retry CTA, and keep the existing lower `创建章节` button as a manual fallback. Do not change backend APIs, approval behavior, world version, EventLog, or canon writes.

**Tech Stack:** React, TypeScript, Vitest, Testing Library.

---

## File Structure

- Modify `frontend/src/studio/StudioPage.test.tsx` — strengthen the auto-start failure retry test so clicking `重新创建第一章草稿` ends with a Writer Draft and calls `generateOutline` and `writeChapter`.
- Modify `frontend/src/studio/StudioPage.tsx` — reuse the full auto-start draft pipeline for the retry CTA.

---

### Task 1: Add RED coverage for full retry behavior

- [ ] **Step 1: Update the retry test to expect a full draft**

In `frontend/src/studio/StudioPage.test.tsx`, inside `shows a friendly retry path when auto-start first draft fails`, after `vi.mocked(createChapter).mockClear();`, also clear outline/write mocks:

```ts
vi.mocked(generateOutline).mockClear();
vi.mocked(writeChapter).mockClear();
```

Change the retried chapter mock title to the real first chapter review path:

```ts
title: '重试第一章目标',
```

After clicking `重新创建第一章草稿`, replace the old chapter-session-only assertion:

```ts
expect(await screen.findByText('重试第一章')).toBeInTheDocument();
expect(screen.queryByText('世界已创建，第一章草稿尚未生成')).not.toBeInTheDocument();
```

with:

```ts
expect(generateOutline).toHaveBeenCalledWith(12, {});
expect(writeChapter).toHaveBeenCalledWith(12, { outline_beats: expect.arrayContaining([expect.objectContaining({ beat_id: 'beat-1' })]) });
expect(await screen.findByText('Writer Draft')).toBeInTheDocument();
expect(screen.getByText('世界已创建，第一章正在草稿审阅中')).toBeInTheDocument();
expect(screen.getByText('这章尚未写入正史；只有点击「写入正史并更新世界」后，世界进度、事件历史和正式设定才会更新。')).toBeInTheDocument();
expect(screen.queryByText('世界已创建，第一章草稿尚未生成')).not.toBeInTheDocument();
expect(approveChapter).not.toHaveBeenCalled();
```

- [ ] **Step 2: Verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx --run
```

Expected: fails because the retry button currently only creates a chapter session and does not run outline/write.

---

### Task 2: Reuse the full auto-start pipeline for retry

- [ ] **Step 1: Extract the full first-draft pipeline**

In `frontend/src/studio/StudioPage.tsx`, add a helper function before the auto-start `useEffect`:

```tsx
async function runAutoStartFirstDraftPipeline(initialGoal: string, isCancelled: () => boolean = () => false) {
  setWorking(true);
  setOperationHint('正在生成第一章草稿…');
  setError('');
  try {
    const frozenContext = withEditedGoal(executionContext, localWorld, initialGoal);
    const created = await createChapterRequest(localWorld.id, {
      chapter_goal: initialGoal,
      title: initialGoal.slice(0, 40),
      execution_context: frozenContext,
    });
    if (isCancelled()) return;
    setChapter(created);
    setOutlineBeats(created.outline_beats);
    setOutlineContext(created.outline_context);
    setDraft(null);
    setApprovalPreview(null);
    clearApprovalSelection();
    clearApprovalConsistency();
    setApprovalReadiness(null);
    setCritique(null);
    setCharacterArcReport(null);
    setSettlement(null);

    const outline = await generateOutline(created.id, {});
    if (isCancelled()) return;
    setOutlineBeats(outline.outline_beats);
    setOutlineContext(outline.outline_context);
    setChapter({ ...created, status: outline.status, outline_beats: outline.outline_beats, outline_context: outline.outline_context });

    const nextDraft = normalizeDraft(await writeChapter(created.id, { outline_beats: outline.outline_beats }));
    if (isCancelled()) return;
    setDraft(nextDraft);
    setDraftVersions([nextDraft.draft_version]);
    setLatestDraftVersion(nextDraft.draft_version);
    await refreshReviewStudioPanels(nextDraft);
    if (isCancelled()) return;
    setCritique(null);
    setCharacterArcReport(null);
    setEditMode(false);
    setEditContent('');
    setChapter({
      ...created,
      title: nextDraft.title,
      status: nextDraft.status ?? 'reviewing',
      outline_beats: nextDraft.outline_beats ?? outline.outline_beats,
      outline_context: nextDraft.outline_context ?? outline.outline_context,
      critique_report: nextDraft.critique_report ?? {},
    });
    setAutoStartRetryCreatedChapter(false);
  } catch {
    if (!isCancelled()) setError('自动生成第一章草稿失败，请检查章节目标后手动重试。');
  } finally {
    if (!isCancelled()) {
      setWorking(false);
      setOperationHint('');
    }
  }
}
```

- [ ] **Step 2: Replace duplicated auto-start effect logic**

Inside the existing auto-start `useEffect`, replace the nested `runAutoStartFirstDraft` body with:

```tsx
void runAutoStartFirstDraftPipeline(initialGoal, () => cancelled);
```

Keep the `cancelled` flag and cleanup function.

- [ ] **Step 3: Add a retry handler for the explicit CTA**

Add:

```tsx
async function retryAutoStartFirstDraft() {
  const retryGoal = goal.trim();
  if (!retryGoal) {
    setError('请先填写章节目标，再重新创建第一章草稿。');
    return;
  }
  setAutoStartRetryCreatedChapter(false);
  await runAutoStartFirstDraftPipeline(retryGoal);
}
```

- [ ] **Step 4: Wire the CTA to the full retry handler**

Change the retry CTA from:

```tsx
<button className="primary-button mt-4" disabled={working || Boolean(chapter)} onClick={createChapterSession}>重新创建第一章草稿</button>
```

to:

```tsx
<button className="primary-button mt-4" disabled={working} onClick={() => void retryAutoStartFirstDraft()}>重新创建第一章草稿</button>
```

The lower `用候选素材参考创建章节` button still uses `createChapterSession` as a manual fallback.

- [ ] **Step 5: Verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/studio/StudioPage.test.tsx --run
```

Expected: all StudioPage tests pass.

---

### Task 3: Final verification and commit

- [ ] **Step 1: Run related one-sentence → first-chapter regression tests**

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldCreationForm.test.tsx src/world/WorldPage.test.tsx src/studio/StudioPage.test.tsx --run
```

Expected: all targeted tests pass.

- [ ] **Step 2: Run frontend build**

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: TypeScript and Vite build pass.

- [ ] **Step 3: Run diff checks, inspect status/log, and commit**

```bash
git -C /opt/WorldSim-Writer diff --check
git -C /opt/WorldSim-Writer add docs/superpowers/plans/2026-06-07-auto-start-full-retry.md frontend/src/studio/StudioPage.test.tsx frontend/src/studio/StudioPage.tsx
git -C /opt/WorldSim-Writer diff --cached --check
git -C /opt/WorldSim-Writer status --short
git -C /opt/WorldSim-Writer commit -m "fix: retry full first draft pipeline"
git -C /opt/WorldSim-Writer status --short --branch
git -C /opt/WorldSim-Writer log --oneline -5
```

Expected: commit succeeds on current branch. Do not push. Do not merge.

---

## Inline Self-Review

- Spec coverage: makes the explicit retry CTA fulfill its promise by returning users to first-chapter draft review after an auto-start failure.
- Scope check: frontend-only refactor and test change; no backend API, approval, canon, EventLog, or world-version changes.
- TDD check: strengthened test fails first because retry currently stops after chapter creation, then implementation reuses the full pipeline.
- Placeholder scan: no TBD/TODO placeholders.
