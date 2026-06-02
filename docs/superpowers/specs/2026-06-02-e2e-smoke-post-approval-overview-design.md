# E2E Smoke Post-Approval Overview Design

## Goal

Make the smoke script prove that the beta-visible world overview read path reflects an approved chapter after the approval transaction completes.

## Problem

The smoke script currently verifies draft generation, approval preview/readiness/consistency, approval response version, event logging, and markdown export. It does not fetch the world overview after approval. That leaves a main-flow beta gap: the approval API can report success while the user-facing overview read path is stale, malformed, or missing projected character/foreshadow state.

The beta playbook asks testers to return to the world overview and confirm `world_version` changed, the approved chapter is visible in world state, and projection data remains visible. Automated smoke should catch the same class of regression before manual testers see it.

## Brainstormed Options

1. Only document the manual world overview check. This is low cost, but keeps the regression manual-only.
2. Add a full semantic diff of proposed projection changes against overview characters and foreshadows. This is precise, but brittle for real LLM output because different providers may propose different valid fields.
3. Add a lightweight post-approval overview check. Fetch `/worlds/{world_id}/overview`, require core projection collections to be list-of-objects, require `world_version` to match the approval response, require `approved_chapter_count` to show the newly approved chapter, and require non-empty character/foreshadow projection collections.

## Selected Design

Use option 3. After approval succeeds and `approved_version` matches the expected world version, the smoke script should call `GET /worlds/{world_id}/overview` before event/export checks.

It should record `checks.overview` with:

- `world_version`
- `approved_chapter_count`
- `expected_world_version`
- `expected_approved_chapter_count`
- `world_version_matches_approval`
- `approved_chapter_count_incremented`
- `character_count`
- `foreshadow_count`

Failure diagnostics:

- Missing or wrong-shaped overview fields continue to use existing `MISSING_REQUIRED_FIELDS` / `INVALID_FIELD_TYPES` diagnostics.
- Stale overview version uses `OVERVIEW_WORLD_VERSION_NOT_UPDATED`.
- Missing approved chapter evidence uses `OVERVIEW_APPROVED_CHAPTER_MISSING`.
- Empty visible projection collections use `OVERVIEW_PROJECTION_EMPTY` with `invalid_fields` naming `characters` and/or `foreshadows`.

## Scope Boundaries

- Do not compare every model-proposed change semantically in this slice.
- Do not alter approval transaction semantics.
- Do not alter frontend UI.
- Do not repeat completed smoke timeout/auth/redaction diagnostics work.

## Test Strategy

- Update the smoke happy-path test to expect the new overview request and overview summary fields.
- Add a failing regression where approval returns version 2 but overview still reports world version 1; the smoke should stop with `OVERVIEW_WORLD_VERSION_NOT_UPDATED`.
- Update `BETA_TESTING.md` and the documentation coverage test so the new diagnostic is documented.
