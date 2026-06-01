# E2E Smoke ID and Version Type Diagnostics Design

## Goal

Make smoke failures more precise when successful API responses return malformed scalar IDs or version fields.

## Problem

`backend/scripts/e2e_smoke.py` validates required fields and list shapes, but some critical scalar fields are trusted before use:

- `create_world.id` is interpolated into later URLs.
- `create_world.world_version` is used as the approval baseline.
- `draft.chapter_id` is interpolated into later URLs.
- `draft.draft_version` is sent to consistency/approval endpoints.
- `approve.approved_version` is compared with the expected world version.

If an API regression returns a string, boolean, or object for one of these values, smoke can proceed to later steps with misleading URLs or silently produce less useful world-version evidence. Beta testers need the smoke summary to stop at the API step that returned the malformed field.

## Design

Keep validation local to the smoke script:

- Add a helper that validates top-level fields are integers and not booleans.
- Reuse the existing `INVALID_FIELD_TYPES` diagnostic and `invalid_fields` list.
- Validate `id` and `world_version` immediately after `create_world` required-field checks.
- Validate `chapter_id` and `draft_version` immediately after `draft` required-field checks.
- Validate `approved_version` immediately after `approve` required-field checks.
- Do not change the approval/state mutation invariant.
- Do not add broad new product behavior or frontend changes.

## Test Strategy

- Add a failing smoke regression for malformed create-world scalar fields.
- Add a failing smoke regression for malformed draft scalar fields.
- Add a failing smoke regression for malformed approve scalar fields.
- Implement the minimal helper and call sites.
- Run focused smoke tests, all smoke script tests, full backend pytest, and diff checks before committing.
