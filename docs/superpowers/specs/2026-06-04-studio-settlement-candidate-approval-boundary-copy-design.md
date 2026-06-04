# Studio Settlement Candidate Approval Boundary Copy Design

## Goal

Make the post-approval Studio settlement clearer that candidate materials remained writing references while chapter approval wrote only the approved chapter and formal world changes.

## Selected Small MVP Fix

The Studio settlement already reports candidate material usage after approval. The current safety note says:

- `候选素材仍是本章创作参考，没有自动写入正式设定。`

This is safe, but the approval moment is a high-risk review surface: the user just clicked `写入正史并更新世界`, so the UI should be explicit about what the approval did write and what it did not write. Replace the note with:

- `候选素材仍只是本章写作参考；本次批准只写入章节正文和世界变化。`

This keeps the wording low-cognitive and approval-boundary focused.

## Scope

- Frontend-only copy update in `frontend/src/studio/StudioPage.tsx`.
- Update `frontend/src/studio/StudioPage.test.tsx` settlement coverage.
- Keep approval payloads, backend transactions, import candidate records, formal world projection, `world_version`, and event history unchanged.

## Non-Goals

- No backend API changes.
- No database changes.
- No approval transaction changes.
- No import candidate persistence changes.
- No chapter generation or draft behavior changes.
- No broad Studio settlement redesign.

## Safety Invariant

Imported candidate materials remain writing references only. Only explicit chapter approval commits formal world-state changes and event history. This task changes visible settlement copy only and does not introduce any automatic canon mutation path.

## Testing

Use TDD in `frontend/src/studio/StudioPage.test.tsx`:

1. Update the settlement test with candidate references to expect `候选素材仍只是本章写作参考；本次批准只写入章节正文和世界变化。`.
2. Assert the older candidate-material settlement note is not visible.
3. Preserve existing assertions that raw IDs, slugs, enums, and `正式 canon` are hidden.
4. Verify RED before changing production copy.
5. Change only the visible settlement note in `StudioPage.tsx`.
6. Verify GREEN, then run backend import/approval safety tests, relevant frontend tests, build, diff checks, inline self-review, and commit.

## Self-Review

- Scope is small and presentation-only.
- The fix improves a later review/settlement surface where canon boundaries matter.
- The design does not create or alter any import-to-canon mutation path.
