# Studio Import Reference Cards Design

## Goal

Make imported candidate materials more visible and safer in the chapter writing path by showing them as readable reference cards in Studio, without mutating formal canon.

## Selected Small MVP Fix

After Import Node P1, imported candidates can reach `ChapterExecutionContext.material_references`, but Studio still shows them as a count or one-line title and uses raw/internal copy such as `canon` in safety text. The next highest-value small beta fix is to render imported references in Studio as Chinese, low-cognitive writing reference cards before and after chapter creation.

## Scope

- Frontend-only change in `frontend/src/studio/StudioPage.tsx`.
- In the launch execution context summary, show each imported material reference with:
  - title
  - source title
  - summary
  - safety note that it is only a writing reference
- In the frozen execution context snapshot after drafting, show the same readable cards.
- Replace `正式 canon` wording on these Studio reference surfaces with `正式设定`.
- Hide raw IDs, raw pool enums, and source slugs from user-facing Studio copy.

## Non-Goals

- No backend API changes.
- No database changes.
- No automatic canon editing from imported material.
- No chapter approval behavior changes.
- No new import confirmation step.

## Safety Invariant

Imported candidates stay candidate/reference material. They can guide chapter drafting through the frozen execution context, but only user approval of a draft can write formal chapter/canon events and world projection changes.

## Testing

Use TDD in `frontend/src/studio/StudioPage.test.tsx`:

1. Update the launch execution context test to expect readable reference card copy and no raw `canon` safety copy.
2. Update the frozen execution context snapshot test to expect title, source, summary, and safe Chinese copy.
3. Verify RED with targeted Studio tests.
4. Implement minimal helper/rendering in `StudioPage.tsx`.
5. Verify GREEN, then run relevant backend/frontend tests, frontend build, and `git diff --check` before commit.

## Self-Review

- The fix is small and isolated to the Studio presentation layer.
- It improves the newcomer chapter writing path by showing what imported material is being used.
- It preserves the invariant that imported material does not auto-edit formal canon.
