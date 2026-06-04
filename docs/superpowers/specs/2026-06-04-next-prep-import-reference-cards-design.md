# Next Chapter Prep Import Reference Cards Design

## Goal

Make imported candidate materials safer and more readable in the newcomer three-minute loop by showing them as reviewable writing references in Next Chapter Prep, without mutating formal canon.

## Selected Small MVP Fix

`NextChapterPrepPanel` is the bridge between world embryo/onboarding and Studio. It already carries `material_references`, but the current UI shows a basic imported-material block and still uses `正式 canon` wording. The highest-value small beta fix is to make this panel match the newer Import Node and Studio reference-card pattern.

## Scope

- Frontend-only change in `frontend/src/world/NextChapterPrepPanel.tsx`.
- Render imported material references as Chinese reference cards with:
  - material title
  - source title
  - summary
  - safe reference-only copy
- Replace `正式 canon` wording with `正式设定`.
- Keep raw IDs, raw pool enum values, and backend slugs out of user-facing copy.
- Keep `buildExecutionContextFromPrep(prep)` unchanged so material references still flow to Studio as frozen writing context.

## Non-Goals

- No backend API changes.
- No database changes.
- No automatic canon edits from imported material.
- No changes to draft approval or formal world-state projection.
- No broad cleanup of unrelated raw event labels in this task.

## Safety Invariant

Imported candidates remain candidate/reference material. They can be shown and passed to the chapter writing context, but only draft approval can write formal chapter/canon events and world projection changes.

## Testing

Use TDD in `frontend/src/world/NextChapterPrepPanel.test.tsx`:

1. Update tests to expect reference-card copy with title, source, summary, and `正式设定` safety wording.
2. Assert raw ID names and raw pool enum text are not visible in the panel body.
3. Verify RED with targeted Next Chapter Prep tests.
4. Implement minimal rendering changes in `NextChapterPrepPanel.tsx`.
5. Verify GREEN, then run relevant backend/frontend tests, frontend build, `git diff --check`, and commit.

## Self-Review

- The scope is small and presentation-only.
- The fix strengthens Import Node P1 in the newcomer loop.
- The design does not create any automatic formal-canon write path.
