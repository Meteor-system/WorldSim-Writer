# First Chapter Launchpad Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This project run explicitly forbids subagents and dynamic workflows, so execute inline with strict TDD.

**Goal:** Add a compact world-overview launchpad that tells users the next writing action and can send the correct next story-arc chapter into Studio.

**Architecture:** Keep this as a frontend-only thin slice in `WorldPage`. Reuse existing `generateStoryArc`, `runStoryArcPlanner`, and `onEnterStudio` pathways; derive a manual `ChapterExecutionContext` from existing `world.story_arc` and `world.approved_chapter_count` without backend changes.

**Tech Stack:** React, TypeScript, Vite, Vitest, React Testing Library.

---

## File Structure

- Modify: `frontend/src/world/WorldPage.test.tsx`
  - Add TDD regression/feature tests for launchpad empty-arc and arc-ready states.
- Modify: `frontend/src/world/WorldPage.tsx`
  - Add a small `FirstChapterLaunchpad` component/helper and render it on the overview.
  - Add a helper to launch Studio with a manual execution context from the selected story arc chapter.
- Create: `docs/superpowers/specs/2026-06-01-first-chapter-launchpad-design.md`
  - Design spec for this MVP slice.
- Create: `docs/superpowers/plans/2026-06-01-first-chapter-launchpad.md`
  - This implementation plan.

---

### Task 1: Add launchpad RED tests

**Files:**
- Modify: `frontend/src/world/WorldPage.test.tsx`

- [ ] **Step 1: Import the existing story arc API mock**

Update the import from `../api/client` to include `generateStoryArc` because the empty-arc launchpad test must prove it uses the existing planner API.

- [ ] **Step 2: Reset the mock in `beforeEach`**

Add `vi.mocked(generateStoryArc).mockReset();` and default only per-test where needed.

- [ ] **Step 3: Add failing test for empty-arc guidance**

Add this test near the Story Arc Planner tests:

```ts
it('shows a first chapter launchpad that can generate an arc when no story arc exists', async () => {
  const user = userEvent.setup();
  vi.mocked(generateStoryArc).mockResolvedValueOnce({
    world_id: 7,
    story_arc: storyArcWorld.story_arc,
  });

  render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

  expect(await screen.findByText('First Chapter Launchpad')).toBeInTheDocument();
  expect(screen.getByText('先生成前 10 章故事弧线，再把下一章目标带入创作台。')).toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: '生成第一轮故事弧线' }));

  expect(generateStoryArc).toHaveBeenCalledWith(7);
  expect(await screen.findByText('第 2 章标题')).toBeInTheDocument();
});
```

- [ ] **Step 4: Add failing test for next story-arc chapter selection**

```ts
it('shows the next unapproved story arc chapter in the launchpad', async () => {
  vi.mocked(apiRequest).mockReset();
  vi.mocked(apiRequest)
    .mockResolvedValueOnce([{ id: 7 }])
    .mockResolvedValueOnce(storyArcWorld);

  render(<WorldPage onEnterStudio={vi.fn()} autoFocusTitle={false} />);

  expect(await screen.findByText('First Chapter Launchpad')).toBeInTheDocument();
  expect(screen.getByText('下一章 · 第 2 章')).toBeInTheDocument();
  expect(screen.getByText('第 2 章标题')).toBeInTheDocument();
  expect(screen.queryByText('下一章 · 第 1 章')).not.toBeInTheDocument();
});
```

- [ ] **Step 5: Add failing test for Studio launch context**

```ts
it('launches Studio with the selected story arc chapter goal', async () => {
  const user = userEvent.setup();
  const onEnterStudio = vi.fn();
  vi.mocked(apiRequest).mockReset();
  vi.mocked(apiRequest)
    .mockResolvedValueOnce([{ id: 7 }])
    .mockResolvedValueOnce(storyArcWorld);

  render(<WorldPage onEnterStudio={onEnterStudio} autoFocusTitle={false} />);

  await user.click(await screen.findByRole('button', { name: '用此目标进入创作台' }));

  expect(onEnterStudio).toHaveBeenCalledWith(storyArcWorld, {
    initialChapterGoal: '第 2 章标题：第 2 章摘要：林砚推进裂纹玉佩线索。',
    executionContext: expect.objectContaining({
      source: 'manual',
      source_world_version: 2,
      next_chapter_number: 2,
      goal: '第 2 章标题：第 2 章摘要：林砚推进裂纹玉佩线索。',
      recommended_pov: { character_id: null, name: '第 2 章 POV 建议' },
    }),
  });
});
```

- [ ] **Step 6: Run focused test and verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: the new launchpad tests fail because `First Chapter Launchpad` is not rendered yet.

---

### Task 2: Implement minimal launchpad GREEN

**Files:**
- Modify: `frontend/src/world/WorldPage.tsx`

- [ ] **Step 1: Add helper functions above `WorldPage`**

Add:

```tsx
function buildStoryArcGoal(chapter: StoryArcChapter) {
  return `${chapter.title}：${chapter.summary}`;
}

function buildStoryArcExecutionContext(world: WorldOverview, chapter: StoryArcChapter): ChapterExecutionContext {
  return {
    source: 'manual',
    source_world_version: world.world_version,
    next_chapter_number: chapter.chapter_number,
    goal: buildStoryArcGoal(chapter),
    recommended_pov: { character_id: null, name: chapter.pov_suggestion || null },
    source_signals: ['story_arc_planner'],
    priority_characters: [],
    priority_foreshadows: [],
    progression_hints: [],
    continuity_warnings: [],
    recent_events: [],
  };
}
```

- [ ] **Step 2: Add `FirstChapterLaunchpad` component above `WorldPage`**

Add a component that accepts `world`, `nextChapter`, `arcLoading`, `onGenerateArc`, and `onLaunchChapter`. It renders the empty-arc and arc-ready states from the spec.

- [ ] **Step 3: Derive the next story arc chapter inside `WorldPage`**

After `activeWorlds` / `archivedWorlds`, add:

```tsx
const nextStoryArcChapter = world
  ? (world.story_arc.find((chapter) => chapter.chapter_number === world.approved_chapter_count + 1) ?? world.story_arc[0] ?? null)
  : null;
```

- [ ] **Step 4: Add launch handler inside `WorldPage`**

Add:

```tsx
function launchStoryArcChapter(chapter: StoryArcChapter) {
  if (!world) return;
  const executionContext = buildStoryArcExecutionContext(world, chapter);
  onEnterStudio(world, {
    initialChapterGoal: executionContext.goal,
    executionContext,
  });
}
```

- [ ] **Step 5: Render the launchpad in overview left column**

Render it after the canon paragraph and before the archive card:

```tsx
<FirstChapterLaunchpad
  world={world}
  nextChapter={nextStoryArcChapter}
  arcLoading={arcLoading}
  onGenerateArc={runStoryArcPlanner}
  onLaunchChapter={launchStoryArcChapter}
/>
```

- [ ] **Step 6: Run focused test and verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: all tests in `WorldPage.test.tsx` pass.

---

### Task 3: Verification and commit

**Files:**
- Verify all changed files.

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

- [ ] **Step 3: Check diff and whitespace**

```bash
cd /opt/WorldSim-Writer && git diff --check && git status --short && git diff --stat
```

Expected: no whitespace errors; changed files are only the launchpad docs/tests/implementation plus pre-existing untracked files.

- [ ] **Step 4: Commit only relevant files**

```bash
cd /opt/WorldSim-Writer && git add docs/superpowers/specs/2026-06-01-first-chapter-launchpad-design.md docs/superpowers/plans/2026-06-01-first-chapter-launchpad.md frontend/src/world/WorldPage.test.tsx frontend/src/world/WorldPage.tsx && git commit -m "feat: add first chapter launchpad"
```

Expected: commit succeeds on `feat/first-chapter-launchpad`. Do not merge and do not push.
