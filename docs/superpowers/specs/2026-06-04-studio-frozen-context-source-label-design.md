# Studio Frozen Context Source Label Design

## Goal

Make the Studio frozen execution-context banner readable for newcomers by replacing raw source slugs with Chinese labels while preserving imported material reference safety.

## Selected Small MVP Fix

The Studio writing path already shows imported candidate materials as safe reference cards, but after a chapter is created the frozen execution-context banner still displays `next_chapter_prep`. This is a raw internal source slug in the same panel that carries imported references into chapter writing. The smallest useful fix is to reuse the existing `sourceLabel()` helper for the frozen banner so the panel reads like user-facing onboarding copy.

## Scope

- Frontend-only change in `frontend/src/studio/StudioPage.tsx`.
- Update the frozen execution-context banner from raw `context.source` to `sourceLabel(context.source)`.
- Keep imported material reference cards and safety copy unchanged.
- Keep Studio chapter creation, draft generation, approval, and settlement behavior unchanged.
- Keep raw IDs, backend enums, source slugs, and internal identifiers out of visible copy for this surface.

## Non-Goals

- No backend API changes.
- No database changes.
- No automatic canon edits from imported material.
- No broad Studio UI redesign.
- No changes to execution context data shape or API payloads.

## Safety Invariant

Imported candidates remain writing references only. This task changes display copy only and does not change canon mutation, world versioning, approval events, or projection updates.

## Testing

Use TDD in `frontend/src/studio/StudioPage.test.tsx`:

1. Update the launch execution-context test to expect the post-create frozen banner `已冻结执行上下文：下一章准备台 · v2`.
2. Assert `已冻结执行上下文：next_chapter_prep · v2` is not visible after chapter creation.
3. Keep existing imported material reference card and safety assertions.
4. Verify RED with the targeted Studio launch execution-context test.
5. Implement minimal label substitution in `StudioPage.tsx`.
6. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, and commit.

## Self-Review

- The scope is small and presentation-only.
- The fix improves the chapter writing path that carries imported references.
- The design does not create a new formal-canon mutation path.
