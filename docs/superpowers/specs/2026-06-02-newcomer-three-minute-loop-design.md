# Newcomer Three-Minute Loop Design

## Goal

Make the first-minute experience clear and compelling for a new or empty-state user: choose a world embryo, generate a first chapter, write it into canon, and view the world changes.

## Scope

This is the P1 MVP from `docs/UX_UPDATE_PHASE.md`. It is frontend-only because the current app already supports seed worlds, sample/custom world creation, Studio chapter generation, approval, and post-approval settlement.

## User Experience

### Empty-state creation page

When there is no open world and the creation form is visible, show a prominent `3 分钟开始运营你的故事世界` guide above the creation controls. It explains the loop in user language:

1. `选世界胚胎`
2. `生成第一章`
3. `写入正史`
4. `查看世界变化`

The copy should frame the product as a story-world operation experience, not a backend setup form. It should also point users to high-tension embryos.

### World embryo entry

Enhance the seed library with a stronger `高张力世界胚胎` label and a short reassurance that embryo cards are only starting prompts. Direct seed creation continues to call `createWorldFromSeed(seedKey)`; applying a seed only fills the form. No seed hook or tension copy is treated as generated chapter content.

### First chapter launchpad alignment

The existing `FirstChapterLaunchpad` should use the same loop language. It should explicitly tell users that the next action is generating/writing chapter one and then writing it into canon to see the settlement/world changes.

### Waiting copy

Improve at least one key waiting path with story-operations language. For this MVP, update Studio’s writing button text while `working` is true during chapter generation to say `导演正在拆场景…`, and update approval button waiting text to say `正在写入正史…`. The existing generic disabled behavior remains.

## Testing

Add frontend tests before implementation:

1. `WorldPage` empty-state creation shows the 3-minute guide, all four steps, and seed cards as high-tension embryos.
2. Direct seed creation still calls `createWorldFromSeed(seedKey)` and does not display the seed hook as generated chapter/draft content.
3. `FirstChapterLaunchpad` shows the 3-minute loop/canon-world-change copy for a world with no story arc.
4. `StudioPage` shows improved waiting copy when starting writing and approval.

## Non-Goals

- No new backend endpoints.
- No full onboarding router or persisted checklist.
- No changes to mock LLM output.
- No automatic chapter generation immediately after world creation.
- No visual redesign beyond the minimal cards/copy needed for this P1 MVP.
