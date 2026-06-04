# Studio Candidate Reference Create CTA Design

## Goal

Make imported candidate material influence visible at the Studio chapter-creation point without changing canon or world state automatically.

## Selected Small MVP Fix

Studio already displays candidate material references in the execution context and sends them in the chapter creation payload when present. However, the primary creation CTA remains generic: `创建章节`. For newcomers, the exact moment where candidate material becomes writing context is easy to miss.

Change the create CTA only when the active execution context has candidate material references:

- With references: `用候选素材参考创建章节`
- Without references: keep `创建章节`
- After chapter creation: keep `章节已创建`

This makes candidate material influence visible at the action point while preserving the rule that candidate material is writing/reference context only.

## Scope

- Frontend-only conditional CTA copy in `frontend/src/studio/StudioPage.tsx`.
- Update `frontend/src/studio/StudioPage.test.tsx` to cover the conditional label and no-reference fallback.
- Preserve chapter creation payload shape, backend behavior, import persistence, canon mutation, world versioning, and event history rules.
- Preserve raw ID/enum/slug hiding assertions.

## Non-Goals

- No backend API changes.
- No database changes.
- No import candidate persistence changes.
- No automatic canon edits from imported candidate materials.
- No changes to LLM prompts or chapter generation logic.
- No broad Studio layout redesign.

## Safety Invariant

Candidate imported materials remain writing references only. Renaming the create action does not commit formal canon, world projections, or event history. Formal world-state changes still require explicit approval after draft review.

## Testing

Use TDD in `frontend/src/studio/StudioPage.test.tsx`:

1. In the existing execution-context creation test, expect `用候选素材参考创建章节` and assert the generic `创建章节` button is absent before creation.
2. In the manual/no-context creation test, preserve `创建章节` and assert `用候选素材参考创建章节` is absent.
3. Verify RED before changing production.
4. Change only the Studio create button label logic.
5. Verify GREEN, then run relevant backend/frontend tests, build, diff checks, inline self-review, and commit.

## Self-Review

- Scope is small and user-facing.
- The fix improves later chapter drafting visibility.
- The design does not create or alter any canon mutation path.
