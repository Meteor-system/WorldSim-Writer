# World Operations Terminology Polish Design

## Goal

Complete the P3 MVP from `docs/UX_UPDATE_PHASE.md` by reducing backend-feeling terminology in the most common WorldPage/Studio paths and adding story-operations waiting copy beyond the existing writing and canon-approval states.

## Scope

This round is frontend-only. Existing API fields and TypeScript type names stay unchanged; only visible copy, button labels, tests, and the UX phase document are updated. The goal is a low-risk polish pass rather than a global rewrite of every internal English panel title.

## Terminology polish

Prioritize visible Studio and WorldPage copy that users encounter during the main writing loop:

- `Pipeline` becomes `创作流程`.
- `世界版本` in Studio context becomes `世界进度`.
- `通过后将提交` becomes `写入正史前确认`.
- `一致性检查` becomes `设定冲突检查`.
- The approval button becomes `写入正史并更新世界` while preserving existing approval behavior.
- The story arc loading button changes from generic `规划中...` to story-operation copy.
- The WorldPage narrative console description explicitly says it reviews `世界历史记录` and prepares the next chapter.

Existing tests that validate API behavior may keep internal names in assertions where they reference structured data, but new user-facing tests should assert the polished labels.

## Waiting experience

Round 2 already covers:

- `导演正在拆场景…` during chapter drafting.
- `正在写入正史…` during approval.

This P3 MVP adds at least two more story-operation waiting prompts:

1. `编剧室正在排布章节骨架…` while `generateOutline()` is pending in Studio.
2. `评论席正在检查节奏与设定…` while `generateCriticReport()` is pending in Studio.
3. `故事弧线规划中…` while `generateStoryArc()` is pending in WorldPage.

Implementation should reuse the existing `operationHint` state in Studio and the existing `arcLoading` state in WorldPage. No new async state machine is needed.

## Documentation update

Update `docs/UX_UPDATE_PHASE.md` with a `阶段完成记录` section that records the MVP commits:

- P0: `f3ef8a2` — approval-after world settlement.
- P1: `d6d7ed9` — newcomer three-minute loop.
- P2: `ee8cc61` — world operations dashboard.
- P3: current round commit to be added after implementation.

The document should state that all four priority items now have a delivered MVP, while future work may continue broadening terminology coverage and waiting copy.

## Testing

Add focused frontend tests before implementation:

1. `StudioPage` shows at least three polished user-facing terms: `创作流程`, `世界进度：1`, `写入正史前确认`, `设定冲突检查`, and `写入正史并更新世界`.
2. `StudioPage` shows `编剧室正在排布章节骨架…` while outline generation is pending.
3. `StudioPage` shows `评论席正在检查节奏与设定…` while critic generation is pending.
4. `WorldPage` shows `故事弧线规划中…` while story arc generation is pending.
5. `docs/UX_UPDATE_PHASE.md` records P0/P1/P2/P3 MVP completion.

## Non-Goals

- No backend changes.
- No changes to API field names or persisted data.
- No full rewrite of every English component title.
- No visual redesign.
- No new LLM calls or generated copy.
