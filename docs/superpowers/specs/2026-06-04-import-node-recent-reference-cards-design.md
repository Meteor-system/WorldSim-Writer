# Import Node Recent Reference Cards Design

## Goal

Make confirmed imported candidate materials visible as safe writing references in the newcomer three-minute loop without mutating formal canon.

## Selected Small MVP Fix

After import confirmation, `WorldImportPanel` already refreshes local audit history and parent next-chapter data, but the recent import batch cards still only show source title and counts. A newcomer can miss the actual candidate material titles they just made available. The smallest useful improvement is to show candidate asset titles and summaries inside each recent import batch card using Chinese, low-cognitive labels.

## Scope

- Frontend-only change in `frontend/src/world/WorldImportPanel.tsx`.
- In each recent import batch card, show a small section titled `可用创作参考`.
- List candidate asset titles and summaries grouped only by readable labels:
  - `正式设定候选`
  - `角色候选`
  - `灵感候选`
- Add safety copy: `这些素材只是写作参考，不会自动改写正式设定。`
- Preserve existing import confirm behavior and `onConfirmed` callback.
- Hide raw IDs and raw pool enum values from user-facing copy.

## Non-Goals

- No backend API changes.
- No database changes.
- No automatic canon edits from imported material.
- No new workflow stage or approval mechanism.
- No changes to chapter approval semantics.

## Safety Invariant

Confirmed import candidates remain candidate material only. They may appear as creative references in the UI and downstream next-chapter context, but they must not mutate `truth_canon`, increment `world_version`, or create formal chapter/canon projection events.

## Testing

Use TDD in `frontend/src/world/WorldImportPanel.test.tsx`:

1. Update the recent batch test to expect `可用创作参考`, readable pool labels, candidate titles/summaries, and safety copy.
2. Assert raw IDs and enum/slugs such as `batch #12`, `asset #1`, `inspiration`, `character`, and `canon` are not visible in the recent card copy.
3. Run the targeted test to verify RED.
4. Implement minimal rendering in `WorldImportPanel.tsx`.
5. Run targeted and relevant tests, frontend build, backend import safety tests, and `git diff --check` before commit.

## Self-Review

- The scope is small and isolated.
- The design improves the newcomer loop by surfacing candidate materials immediately after import and on reload.
- The design does not introduce any path for imported material to become formal canon automatically.
