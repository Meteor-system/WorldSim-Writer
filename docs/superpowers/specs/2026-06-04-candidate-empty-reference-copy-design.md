# Candidate Empty Reference Copy Design

## Goal

Make the later creation and audit surfaces use candidate-material wording even when a chapter did not use imported references.

## Selected Small MVP Fix

Studio settlement and chapter history already explain non-empty imported references as `候选素材` writing references. The remaining small gap is the empty state copy:

- Studio approval settlement: `本章未使用导入素材参考。`
- Chapter history detail: `本章未使用导入素材参考。`

This wording is safe but less consistent than the Import Node P1 candidate-material vocabulary. The smallest useful fix is to change these empty states to `本章未使用候选素材参考。` while keeping all import, chapter, approval, world-version, and event-history behavior unchanged.

## Scope

- Frontend-only copy update in `frontend/src/studio/StudioPage.tsx`.
- Frontend-only copy update in `frontend/src/world/ChapterHistoryPanel.tsx`.
- Add focused Vitest coverage for the no-reference Studio settlement path.
- Add focused Vitest coverage for the no-reference chapter-history detail path.
- Preserve existing non-empty reference cards, material titles, source titles, summaries, formal settlement counts, event summaries, and raw ID/slug/enum hiding.

## Non-Goals

- No backend API changes.
- No database changes.
- No import parsing, confirmation, or persistence changes.
- No chapter generation or approval transaction changes.
- No automatic canon edits from imported candidate materials.
- No new reference selection or promotion workflow.

## Safety Invariant

Imported materials remain candidate-only writing references. This task changes visible empty-state copy only and does not change formal canon mutation, world versioning, event history, or projection updates.

## Testing

Use TDD:

1. In `StudioPage.test.tsx`, mock a draft whose execution context has no `material_references`, approve it, and expect `本章未使用候选素材参考。` in the settlement panel.
2. Assert the older `本章未使用导入素材参考。` is not exposed in that Studio settlement.
3. In `ChapterHistoryPanel.test.tsx`, load a chapter detail whose execution context has no `material_references`, and expect `本章未使用候选素材参考。`.
4. Assert the older `本章未使用导入素材参考。` is not exposed in that chapter-history detail.
5. Preserve existing assertions that raw `asset_id`, `batch_id`, `inspiration`, `markdown`, and `正式 canon` are not exposed in reference/audit surfaces.
6. Verify RED before changing production copy.
7. Change only the two visible frontend strings.
8. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, inline self-review, and commit.

## Self-Review

- Scope is small and presentation-only.
- The fix improves later creation and audit clarity for the common no-reference case.
- The design keeps imported candidates out of formal canon until explicit chapter approval commits approved draft changes through the existing path.
