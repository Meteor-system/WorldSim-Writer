# Chapter History Localization Design

## Goal

Make the WorldPage chapter history/review surface friendlier for beta readers by replacing remaining English headings, raw version shorthand, and raw status enum values with Chinese copy.

## Current State

Discovery focused on the WorldPage and StudioPage review/canon/events/export areas. Several panels already use `displayLabels.ts` helpers, and the previous slice localized `ArcPlanPanel`. The smallest visible remaining gap is `frontend/src/world/ChapterHistoryPanel.tsx`:

- The panel kicker still says `Approved Chapter History`.
- The detail kicker still says `Chapter Detail`.
- Chapter rows show raw draft shorthand like `v2` and raw world numbers like `世界 1 → 2`.
- Detail rows show `世界版本：1 → 2` instead of the existing friendly `第 N 版` copy.
- Change details render raw status tokens in before/after values, such as `active → 开始调查密信` and `planted → advanced`.
- Critic feedback is labeled `Critic：...` instead of a Chinese author-facing label.
- The execution context section uses technical copy (`执行上下文快照`) instead of writer-facing copy.

This panel is directly linked from WorldPage and is part of the review/canon/history flow, so it is a good small MVP/Beta-readiness slice.

## Selected Slice

Localize `ChapterHistoryPanel` only:

- Replace English kickers with Chinese labels.
- Render approved draft version as `批准稿第 N 版` instead of `vN`.
- Render world versions through `labelWorldVersion` instead of raw numbers.
- Translate known status enum values in change lines through `labelStatus`.
- Rename `Critic` feedback to Chinese copy.
- Rename `执行上下文快照` to `写作依据快照`.
- Preserve all API contracts, component props, callbacks, styling structure, and data behavior.

## Out of Scope

- No backend changes.
- No API shape changes.
- No full i18n framework.
- No unrelated localization outside `ChapterHistoryPanel`.
- No attempt to resolve unknown IDs beyond the existing name lookup behavior.

## Test Strategy

Use TDD in `frontend/src/world/ChapterHistoryPanel.test.tsx`:

1. Update the existing chapter history render test to expect Chinese labels and `labelWorldVersion` style output.
2. Assert old English/technical/raw strings are absent from `document.body`.
3. Run the focused Vitest test and verify RED.
4. Implement minimal label helper updates in `ChapterHistoryPanel.tsx`.
5. Run focused test, related WorldPage test if needed, frontend build, and git diff checks before committing.
