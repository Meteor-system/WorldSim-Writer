# Operations Dashboard Candidate Reference Handoff Design

## Goal

Let imported candidate materials safely influence later chapter drafting by carrying next-chapter prep context from the operations dashboard when candidate references are available.

## Selected Small MVP Fix

The operations dashboard now shows that candidate material references are available, but its primary `继续下一章` action still enters Studio without the next-chapter prep context unless the user first clicks `用作下一章目标` in the Narrative Control Center.

When next-chapter prep contains candidate material references, make the operations dashboard `继续下一章` action pass the next-chapter prep execution context by default. This carries candidate references into Studio as writing context, not as canon.

## Scope

- Frontend-only handoff update in `frontend/src/world/WorldPage.tsx`.
- Build the existing `ChapterExecutionContext` from `nextPrep` only when `nextPrep.material_references` is non-empty and no explicit selected context overrides it.
- Update `frontend/src/world/WorldPage.test.tsx` to cover the operations-dashboard click path.
- Preserve backend behavior, import persistence, and formal canon mutation rules.
- Preserve existing raw ID/enum/slug hiding assertions.

## Non-Goals

- No backend API changes.
- No database changes.
- No import candidate persistence changes.
- No automatic canon edits from imported candidate materials.
- No changes to next-chapter prep generation or material-reference selection.
- No broad dashboard redesign.

## Safety Invariant

Candidate materials remain writing references only. Passing them into Studio execution context can influence drafting prompts/review context, but does not mutate formal canon, world projections, event history, or world version. Formal world-state changes still require explicit chapter approval.

## Testing

Use TDD in `frontend/src/world/WorldPage.test.tsx`:

1. Add a regression where `getNextChapterPrep` returns one `material_references` item.
2. Click the operations dashboard `继续下一章` action.
3. Expect `onEnterStudio` to receive `executionContext.material_references` containing that reference and an `initialChapterGoal` from next-chapter prep.
4. Assert raw terms such as `asset_id`, `batch_id`, and `inspiration` are not visible.
5. Verify RED before changing production.
6. Implement the minimal handoff using existing `buildExecutionContextFromPrep`.
7. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, inline self-review, and commit.

## Self-Review

- Scope is small and user-facing through existing operations dashboard action.
- The fix improves candidate material influence on drafting without adding any canon mutation path.
- The design preserves explicit approval as the only formal world-state mutation step.
