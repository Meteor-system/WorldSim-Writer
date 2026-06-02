# E2E Smoke Overview World Version Contract Design

## Goal

Fix real-LLM smoke false failures where approval succeeds and the world projection advances, but `ChapterResponse.approved_version` is not equal to the next `World.world_version`.

## Context

The smoke script currently treats `approve.approved_version` as the post-approval world version. In the backend API, `approved_version` is chapter/draft approval metadata, while the authoritative world version after approval is exposed by the post-approval world overview. Real-LLM smoke can therefore fail with `WORLD_VERSION_NOT_INCREMENTED` at `approve` even when `world.world_version` has advanced to `2` and the overview is correct.

## Decision

Keep validating the approval response shape and status at the `approve` step, but do not use `approved_version` as the world-version source of truth. After approval, fetch `/worlds/{world_id}/overview` and compare `overview.world_version` to `initial_world_version + 1`. Keep `checks.approve` useful by recording the approval response status, `approved_version`, expected next world version, and the validation source. Record actual world-version increment evidence in `checks.overview`.

## Scope

- Add a regression where approval returns `approved_version: 1` but overview returns `world_version: 2`; smoke should pass.
- Update stale-overview failure expectations so `WORLD_VERSION_NOT_INCREMENTED` is reported from the overview check.
- Update beta docs to clarify that world-version validation uses post-approval overview, not `approved_version`.

## Non-goals

- Change backend approval response schema.
- Add a new world detail endpoint call when overview already contains `world_version`.
- Weaken approval status or response-shape validation.
