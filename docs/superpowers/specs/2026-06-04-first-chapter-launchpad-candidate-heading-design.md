# First Chapter Launchpad Candidate Heading Design

## Goal

Make first-chapter launchpad imported references consistently read as candidate writing references.

## Selected Small MVP Fix

The first-chapter launchpad already says `已准备 1 条候选素材写作参考。`, but its section heading still says `导入素材参考` and its guardrail says `这些素材只会随下一章目标进入创作台，不会自动写入正式设定。`. Both are safe, but they are less explicit than the candidate-material copy now used across Import Node P1. The smallest useful fix is to change the heading to `候选素材写作参考` and the guardrail to `这些候选素材只会随下一章目标进入创作台，不会自动写入正式设定。`.

## Scope

- Frontend-only copy update in `frontend/src/world/WorldPage.tsx`.
- Update `frontend/src/world/WorldPage.test.tsx` to expect the clearer first-chapter launchpad heading and guardrail.
- Keep Studio handoff behavior, execution context payloads, imported reference rendering, and canon behavior unchanged.

## Non-Goals

- No backend API changes.
- No database changes.
- No import parsing or classification changes.
- No chapter generation changes.
- No automatic canon edits from imported candidate materials.
- No display of raw IDs, slugs, enums, or internal source fields.

## Safety Invariant

Imported materials remain candidate-only writing references. This task changes visible first-chapter launchpad copy only and does not change formal canon mutation, world versioning, event history, or projection updates.

## Testing

Use TDD in `frontend/src/world/WorldPage.test.tsx`:

1. Expect the first-chapter launchpad section heading `候选素材写作参考`.
2. Expect the guardrail `这些候选素材只会随下一章目标进入创作台，不会自动写入正式设定。`.
3. Assert the older `这些素材只会随下一章目标进入创作台，不会自动写入正式设定。` is not exposed.
4. Preserve existing assertions that raw IDs, slugs, enums, and `正式 canon` are not exposed.
5. Verify RED before changing production copy.
6. Change only visible frontend strings in `WorldPage.tsx`.
7. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, inline self-review, and commit.

## Self-Review

- Scope is small and presentation-only.
- The fix improves novice first-chapter clarity without changing data flow.
- The design keeps imported candidates out of formal canon until explicit approval.
