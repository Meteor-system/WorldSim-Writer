# World Pulse Localization Design

## Goal

Make the WorldPage world-pulse panel more beta-reader friendly by replacing remaining English headings, raw mode/status enum values, and raw thread IDs with Chinese labels.

## Current State

Discovery after recent commits found that `ArcPlanPanel` and `ChapterHistoryPanel` are now localized, but `frontend/src/world/WorldPulsePanel.tsx` still shows internal or English copy:

- Kicker/title: `Operational Overview` and `World Pulse`.
- Status and mode pills: `状态：urgent` and `模式：converge`.
- Focus item priority: raw values such as `urgent`.
- Related thread IDs: `关联线索：foreshadow:9`.
- Some backend-generated strings used in tests include English product names like `World Pulse`, `Narrative Health`, or `Open Threads Board`, plus status fragments such as `watch`.

This panel is visible in the WorldPage control center and summarizes whether the next author action should draft, repair, converge, or archive. Hiding internal tokens here improves onboarding without touching backend APIs.

## Selected Slice

Localize `WorldPulsePanel` only:

- Rename the visible title/kicker to Chinese copy.
- Render pulse status and primary mode with Chinese labels.
- Render focus priority with Chinese labels instead of raw enum tokens.
- Hide raw related thread IDs; show thread-source labels such as `线索来源：伏笔线索`.
- Normalize known English product names and simple status fragments in displayed headline/indicator/action copy to Chinese (`World Pulse` → `世界心跳`, `Narrative Health` → `叙事健康度`, `Open Threads Board` → `开放线索看板`, `watch` → `需要观察`).
- Preserve all component props, API contracts, callbacks, styling structure, and behavior.

## Out of Scope

- No backend changes.
- No API shape changes.
- No full i18n framework.
- No unrelated localization outside `WorldPulsePanel` and tests that assert its rendered output through WorldPage.
- No attempt to resolve related thread IDs to object names; type-based labels avoid exposing IDs without adding data dependencies.

## Test Strategy

Use TDD in `frontend/src/world/WorldPulsePanel.test.tsx`:

1. Update the existing render test to expect Chinese title/status/mode/priority/source labels and normalized English product names.
2. Assert old English headings, raw enum values, and raw thread IDs are absent from `document.body`.
3. Run the focused Vitest test and verify RED.
4. Implement label maps and copy normalization in `WorldPulsePanel.tsx`.
5. Run focused test, related WorldPage test, frontend build, and git diff checks before committing.
