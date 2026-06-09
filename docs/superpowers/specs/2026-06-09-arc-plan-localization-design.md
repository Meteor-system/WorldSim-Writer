# Arc Plan Localization Design

## Goal

Make the Story Arc Planner panel more beta-reader friendly by replacing internal English enum tokens and raw relation IDs with Chinese labels/explanations.

## Current State

Quick UI discovery found several existing localization helpers in `frontend/src/world/displayLabels.ts`, and many major flows already hide raw API field names. The smallest high-value remaining gap is `ArcPlanPanel`: it still shows English headings (`Story Convergence`, `Arc Mode / Closure Plan`), raw arc/budget/treatment enums (`converge`, `locked`, `close`, `must_close`), and raw related character/foreshadow IDs (`关联角色：1`, `关联伏笔：9`). This panel is directly relevant to next-chapter planning and beta onboarding, so internal tokens there are disproportionately visible.

## Selected Slice

Localize the Story Arc Planner surface:

- Rename the visible title/kicker to Chinese copy.
- Render arc mode and expansion budget with Chinese labels plus short author-facing explanations.
- Render closure treatment and priority with Chinese labels instead of raw enums.
- Hide raw related character/foreshadow IDs; show count-based Chinese copy instead, such as `关联角色：2 位` and `关联伏笔：1 条`.
- Preserve all data flow, styling structure, API contracts, and behavior.

## Out of Scope

- No backend changes.
- No API shape changes.
- No full i18n framework.
- No attempt to resolve related IDs to names in this slice; count labels avoid exposing IDs without adding data dependencies.
- No unrelated localization outside `ArcPlanPanel`.

## Test Strategy

Use TDD in `frontend/src/world/ArcPlanPanel.test.tsx`:

1. Update the existing render test to expect Chinese title/labels/explanations and count-based related item copy.
2. Assert internal tokens/IDs are not visible in `document.body`.
3. Run the focused Vitest test and verify RED.
4. Implement label maps and copy changes in `ArcPlanPanel.tsx`.
5. Run focused test, related frontend tests for this file, full frontend test suite, and `npm run build`.
