# First Chapter Launchpad Design

## Goal

Help a user who has just opened a world understand the next concrete action: plan the first 10 chapters if no arc exists, then launch the correct next chapter goal into Studio from the world overview.

This is the next MVP slice because README and `WorldSim-Writer.md` both emphasize a 10-minute first-day loop: view a world, generate a draft, review/approve it, and keep canon protected. The current app already has Story Arc Planner, Next Chapter Prep, Studio launch context, snapshot/export, and bookshelf switching, but the top of the world overview still leaves the user to discover which module to use next.

## Scope

### In scope

- Add a compact `First Chapter Launchpad` panel to the world overview.
- Use existing world data only; no backend or API changes.
- If `world.story_arc` is empty:
  - explain that the next step is generating the first 10-chapter arc;
  - provide a button that calls the existing story arc planner action.
- If `world.story_arc` exists:
  - derive the next chapter from `world.approved_chapter_count + 1`;
  - show chapter number, title, summary, POV suggestion, and core conflict;
  - provide a button that opens Studio with that arc chapter as the initial chapter goal.
- Preserve the existing regular `进入创作台` button and Next Chapter Prep launch flow.
- Preserve Story Arc, NCC, Studio, bookshelf/archive, and snapshot/export behavior.

### Out of scope

- Persisting a separate chapter intent contract.
- Backend prompt changes.
- New model calls.
- Replacing Next Chapter Prep.
- Changing chapter approval or formal world-state mutation behavior.

## UX

The panel appears in the left side of the world overview, near the canon title and before archive/creation actions, so it is visible before the user scrolls to Narrative Control Center.

Empty arc state copy:

- Heading: `First Chapter Launchpad`
- Message: `先生成前 10 章故事弧线，再把下一章目标带入创作台。`
- Button: same underlying action as Story Arc Planner, disabled while `arcLoading` is true.

Arc-ready state copy:

- Heading: `First Chapter Launchpad`
- Kicker: `下一章 · 第 N 章`
- Title: story arc chapter title.
- Body: story arc summary.
- Metadata: POV suggestion and core conflict.
- Button: `用此目标进入创作台`.

If all story arc chapters are already approved or the next chapter is not found, show a safe fallback that suggests regenerating the story arc or using Narrative Control Center.

## Data flow

- `WorldPage` already owns `world`, `arcLoading`, `runStoryArcPlanner()`, and `onEnterStudio()`.
- Add a small helper inside `WorldPage`:
  - `nextStoryArcChapter = world.story_arc.find(chapter => chapter.chapter_number === world.approved_chapter_count + 1) ?? world.story_arc[0] ?? null`.
- Launching from the panel calls `onEnterStudio(world, { initialChapterGoal, executionContext })` where:
  - `initialChapterGoal` is a concise goal built from the arc chapter title and summary;
  - `executionContext.source` is `manual` because this is frontend-derived from existing story arc data, not a backend Next Chapter Prep response;
  - `source_world_version` is `world.world_version`;
  - `next_chapter_number` is the chapter number;
  - `goal` matches `initialChapterGoal`;
  - `recommended_pov.name` is the arc chapter POV suggestion and `character_id` is null;
  - arrays for priority characters, foreshadows, hints, warnings, and events are empty.

## Testing

Add focused React tests in `frontend/src/world/WorldPage.test.tsx`:

1. Empty story arc state shows launchpad guidance and can trigger existing story arc generation.
2. Story arc state shows the next unapproved chapter from `approved_chapter_count + 1` and does not show chapter 1 as the next chapter when chapter 1 is already approved.
3. Clicking `用此目标进入创作台` calls `onEnterStudio` with an initial chapter goal and a manual execution context containing the next chapter number.

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
cd /opt/WorldSim-Writer/frontend && npm run build
```

Run full frontend tests before commit if targeted tests and build pass:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test
```

## Acceptance criteria

- Users opening a world can see the recommended next action without scrolling.
- Users with no story arc can generate the arc from the launchpad.
- Users with a story arc can send the correct next arc chapter into Studio.
- Existing Story Arc Planner, quick nav anchors, Narrative Control Center, bookshelf/archive, and snapshot/export tests remain green.
