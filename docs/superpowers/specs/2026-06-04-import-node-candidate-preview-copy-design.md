# Import Node Candidate Preview Copy Design

## Goal

Make the Import Node preview step use beginner-friendly candidate-material wording instead of technical `结构化预览` copy.

## Selected Small MVP Fix

The Import Node currently uses `结构化预览` for the main preview action and preview result heading. This is accurate internally, but it asks newcomers to understand a technical transformation step. The product value is simpler: the system will turn pasted material into candidate material for review.

Replace visible preview copy with candidate-material wording:

- `生成结构化预览` → `生成候选素材预览`
- `结构化预览` → `候选素材预览`
- `结构化预览生成失败` → `候选素材预览生成失败`

This keeps the preview action aligned with the rest of Import Node P1 wording: candidate materials are visible, reviewable, and safe, but do not automatically change formal settings.

## Scope

- Frontend-only copy update in `frontend/src/world/WorldImportPanel.tsx`.
- Update `frontend/src/world/WorldImportPanel.test.tsx` expectations for the button, heading, and fallback error copy.
- Update the `frontend/src/world/WorldPage.test.tsx` import-refresh regression to click the renamed preview button.
- Keep preview/confirm callbacks, request payloads, API fields, TypeScript type names, backend behavior, and persistence unchanged.

## Non-Goals

- No backend API changes.
- No database changes.
- No import candidate persistence changes.
- No automatic canon edits from imported candidate materials.
- No changes to conflict detection or asset grouping.
- No broad Import Node layout redesign.

## Safety Invariant

Imported materials remain candidate-only writing references. This task changes visible frontend copy only and does not change formal canon mutation, world versioning, event history, or projection updates.

## Testing

Use TDD in `frontend/src/world/WorldImportPanel.test.tsx`:

1. Update the empty-content validation test to click `生成候选素材预览` and assert the old button copy is not visible.
2. Update the preview test to click `生成候选素材预览`, expect `候选素材预览`, and assert `结构化预览` is not visible.
3. Add a fallback error test where `onPreview` rejects with a non-Error value, expecting `候选素材预览生成失败` and rejecting `结构化预览生成失败`.
4. Verify RED before changing production copy.
5. Change only visible preview button, heading, and fallback error copy in `WorldImportPanel.tsx`.
6. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, inline self-review, and commit.

## Self-Review

- Scope is small and user-facing.
- The fix improves the beginner import loop before confirmation.
- The design does not create or alter any canon mutation path.
