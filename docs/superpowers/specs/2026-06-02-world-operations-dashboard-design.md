# World Operations Dashboard Design

## Goal

Upgrade the world overview page from static world-bible display into a story-world operations dashboard that answers: `今天这个世界需要处理什么？`

## Scope

This is the P2 MVP from `docs/UX_UPDATE_PHASE.md`. It is frontend-only because `WorldOverview` already contains enough data for a useful first dashboard: world progress, approved chapter count, characters, foreshadows, recent events, story arc, and status. No backend endpoints are required for this round.

## User Experience

### Dashboard placement

Add a prominent `世界运营仪表盘` card near the top of the world overview tab, immediately after the world title/truth canon and before the existing first-chapter launchpad. This keeps the entry visible without restructuring the existing tab system.

### Current state metrics

Show a compact set of user-facing metrics using product language:

- `世界进度 v{world.world_version}`
- `已写入正史章节：{world.approved_chapter_count}`
- `近期世界历史记录：{world.recent_events.length}`
- `待处理悬念/伏笔：{openForeshadowCount}`

The dashboard should not expose raw backend terminology as the primary user-facing label.

### Recommended actions

Show `今天建议处理什么` with simple, explainable recommendations derived from existing world data:

1. `继续下一章` when the world is active, linking the user's next move to the existing Studio flow.
2. `回收或推进悬念/伏笔` when there are open foreshadows, using urgency/status to explain why.
3. `检查世界历史记录` when recent events exist, or `写入第一条世界历史记录` when none exist yet.

These are guidance cards, not generated story content. They must not invent LLM chapter text or hidden world facts.

### Summary slices

Show small operational summaries for at least three categories:

- `活跃角色` — first few characters with current goals or status.
- `紧迫悬念/伏笔` — highest urgency open foreshadows, with urgency and status.
- `近期世界历史记录` — recent events rendered through existing `describeEvent()` language; use an empty-state sentence when there are no events.

Keep the lists short for MVP readability.

### CTA alignment

Use existing actions only:

- `继续下一章` calls the same `onEnterStudio(world, context)` path as the existing `进入创作台` button, including selected execution context when present.
- `查看悬念/伏笔账本` switches to the existing `伏笔账本` tab.
- `查看章节历史` anchors to the existing `#chapter-history` section.

Archived worlds should show read-only copy and should not present the `继续下一章` button as an active writing action.

## Testing

Add frontend tests before implementation:

1. `WorldPage` renders `世界运营仪表盘` and key metrics (`世界进度 v2`, `已写入正史章节：1`, history count, open foreshadow count).
2. `WorldPage` renders at least two recommended actions derived from fixture data, including `继续下一章` and `回收或推进悬念/伏笔`.
3. `WorldPage` renders at least two summary categories from existing data, including `活跃角色` and `紧迫悬念/伏笔`.
4. `WorldPage` does not render fixture-only/mock generated chapter text as dashboard content.

## Non-Goals

- No backend API changes.
- No persisted checklist or daily task model.
- No new LLM calls.
- No hardcoded generated chapter prose in production UI.
- No large visual redesign or routing change.
