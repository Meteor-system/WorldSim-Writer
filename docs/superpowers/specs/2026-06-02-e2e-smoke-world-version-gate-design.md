# E2E Smoke World Version Gate Design

## Goal

Make `backend/scripts/e2e_smoke.py` validate that approving a chapter advances the world version, matching the MVP main-flow invariant and beta manual checklist.

## Problem

The smoke script already checks that chapter approval returns `status: approved`, that a `chapter_approved` event appears, and that export works. However, it does not require the approval response version to advance from the world version used to create the draft. A broken approval path could return `approved` without advancing `world_version`, and smoke would still report `ok: true`.

## Scope

- Keep the existing smoke flow unchanged.
- Record the initial world version from world creation.
- Record approval version diagnostics in `checks.approve`:
  - `approved_version`
  - `expected_world_version_after`
  - `world_version_incremented`
- Require `world_version_incremented` for `summary.ok`.
- Document the automated pass criterion in `BETA_TESTING.md`.

## Non-goals

- Do not change backend approval behavior.
- Do not add new API endpoints.
- Do not fetch world overview after approval in this iteration.
- Do not change frontend behavior.

## Testing

Add a regression test in `backend/tests/test_e2e_scripts.py` where approval returns `status: approved` but `approved_version` does not advance beyond the initial world version. The smoke summary should be `ok: false` and include `world_version_incremented: false`.
