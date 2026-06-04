# Studio Settlement Import Safety Copy Design

## Goal

Make imported candidate materials safer and clearer in the Studio approval settlement, after a chapter is approved, without implying imported material automatically became formal canon.

## Selected Small MVP Fix

The Studio `世界推进结算` panel is a later creation-path surface shown immediately after approval. It already tells users which imported material titles were referenced, but it still uses `正史 / canon` and `正式 canon` wording. The smallest high-value fix is to keep the settlement concise while replacing raw canon wording with low-cognitive Chinese copy and explicitly saying imported materials remain writing references.

## Scope

- Frontend-only change in `frontend/src/studio/StudioPage.tsx`.
- Update the settlement panel copy to:
  - say the chapter has entered formal history/settings in Chinese
  - say imported materials remain writing references
  - avoid `canon` wording in visible UI
- Keep existing settlement counts, export controls, and overview handoff unchanged.
- Keep raw IDs, backend pool enums, source type slugs, and internal event slugs out of visible copy.

## Non-Goals

- No backend API changes.
- No database changes.
- No automatic canon edits from imported material.
- No changes to approval logic, world versioning, formal events, or projection updates.
- No redesign of the whole settlement panel.

## Safety Invariant

Imported candidates remain candidate/reference material. The approved chapter can commit formal world changes only through the existing approval path. Imported reference material shown in the settlement explains what the writer referenced; it does not automatically enter formal settings.

## Testing

Use TDD in `frontend/src/studio/StudioPage.test.tsx`:

1. Update the settlement test to expect Chinese `正式设定` / reference-only copy and no `正式 canon` text.
2. Keep existing assertions for settlement counts, formal event summary, export controls, and no raw event slug.
3. Verify RED with the targeted Studio settlement test.
4. Implement minimal copy changes in `StudioPage.tsx`.
5. Verify GREEN, then run backend import safety tests, relevant frontend tests, frontend build, diff checks, and commit.

## Self-Review

- The scope is small and presentation-only.
- The fix improves a later creation path immediately after approval.
- The design does not introduce any formal-canon mutation path for imported candidates.
