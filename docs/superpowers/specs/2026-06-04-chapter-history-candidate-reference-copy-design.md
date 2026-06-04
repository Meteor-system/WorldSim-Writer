# Chapter History Candidate Reference Copy Design

## Goal

Make imported candidate materials in chapter history details read as safe candidate writing references after approval.

## Selected Small MVP Fix

Chapter history details show the approval audit trail and execution context from an approved chapter. This is a key canon guardrail surface because users can verify what was formally written and what remained writing reference. The material-reference heading still says `导入素材参考`, and the safety sentence says `这些导入素材只是本章创作参考，不代表已自动进入正式设定。`. The smallest useful fix is to rename the heading to `候选素材写作参考` and make the safety sentence explicitly say candidate material.

## Scope

- Frontend-only copy update in `frontend/src/world/ChapterHistoryPanel.tsx`.
- Update `frontend/src/world/ChapterHistoryPanel.test.tsx` to expect the safer heading and sentence.
- Keep material titles, summaries, source titles, approval audit fields, execution context details, and canon behavior unchanged.

## Non-Goals

- No backend API changes.
- No database changes.
- No chapter approval transaction changes.
- No import confirmation behavior changes.
- No automatic canon edits from imported candidate materials.
- No display of raw IDs, slugs, enums, or internal source fields.

## Safety Invariant

Imported materials remain candidate assets and writing references only. This task changes visible chapter-history copy only and does not change formal canon mutation, world versioning, event history, or projection updates.

## Testing

Use TDD in `frontend/src/world/ChapterHistoryPanel.test.tsx`:

1. Expect `候选素材写作参考` in the chapter detail material-reference section.
2. Expect `这些候选素材只是本章创作参考，不代表已自动进入正式设定。`.
3. Preserve existing assertions that raw `asset_id`, `batch_id`, `inspiration`, `markdown`, and `正式 canon` are not exposed.
4. Preserve existing approval audit assertions for world version, formal event, and formal settlement counts.
5. Verify RED with the targeted chapter history detail test before changing production copy.
6. Change the visible heading and safety sentence in `ChapterHistoryPanel.tsx`.
7. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, and commit.

## Self-Review

- Scope is small and presentation-only.
- The fix improves Import Node P1 safety at the post-approval audit point.
- The design does not create a new formal-canon mutation path.
