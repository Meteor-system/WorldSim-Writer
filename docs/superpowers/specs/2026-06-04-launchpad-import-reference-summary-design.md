# First Chapter Launchpad Import Reference Summary Design

## Goal

Make imported candidate materials more useful in the newcomer three-minute loop by showing their summaries in the First Chapter Launchpad, while keeping them as safe writing references only.

## Selected Small MVP Fix

The First Chapter Launchpad is one of the earliest places where a new user moves from world setup into chapter writing. It already lists imported material reference titles, but it does not show the reference summary and still uses `正式 canon` wording. The smallest high-value fix is to render each imported reference as a readable card with title, source, and summary, using Chinese safety copy that says the material will not automatically write formal settings.

## Scope

- Frontend-only change in `frontend/src/world/WorldPage.tsx` inside `FirstChapterLaunchpad`.
- Render imported references with:
  - title
  - source title
  - summary
  - low-cognitive Chinese safety copy
- Replace `正式 canon` with `正式设定` on this launchpad surface.
- Keep raw IDs, backend pool enums, source type slugs, and raw text out of visible copy.
- Preserve the existing Studio handoff: material references still flow into `executionContext` when the user clicks `用此目标进入创作台`.

## Non-Goals

- No backend API changes.
- No database changes.
- No automatic canon edits from imported material.
- No changes to draft approval or world projection logic.
- No broad cleanup of unrelated event labels or other world panels in this task.

## Safety Invariant

Imported candidates remain candidate/reference material. They can help the writer understand what to use in the next chapter, but they must not edit formal settings, increment world versions, or create formal history events by themselves.

## Testing

Use TDD in `frontend/src/world/WorldPage.test.tsx`:

1. Update the First Chapter Launchpad import-reference test to expect the summary and `正式设定` safety copy.
2. Assert the old `正式 canon` copy is not visible.
3. Keep assertions that raw IDs and pool enum text are not visible.
4. Verify RED with the targeted WorldPage test.
5. Implement the minimal launchpad rendering change.
6. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, and commit.

## Self-Review

- The scope is small and presentation-only.
- The change improves Import Node P1 where imported candidates meet first-chapter onboarding.
- The design does not introduce any formal-canon mutation path.
