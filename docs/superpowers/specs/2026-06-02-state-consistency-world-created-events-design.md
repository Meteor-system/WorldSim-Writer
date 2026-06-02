# State Consistency WORLD_CREATED Event Test Design

## Brainstorming outcome

Backend full pytest is blocked by stale `tests/test_state_consistency.py` expectations. The current product behavior writes an append-only `WORLD_CREATED` event during world creation. That behavior is valuable and should not be weakened. The failing tests should distinguish initial lifecycle events from chapter approval events.

## Scope

- Keep `WORLD_CREATED` event behavior unchanged.
- Update state consistency tests so they explicitly account for `WORLD_CREATED`.
- Approval-specific assertions should filter to chapter approval/change events instead of assuming all world events were created by approval.
- Rollback tests should assert that failed approval creates no additional approval events while preserving the initial `WORLD_CREATED` event.
- Event endpoint pagination expectations should include `WORLD_CREATED` in totals and offsets.

## Non-goals

- Do not remove or rename `WORLD_CREATED`.
- Do not change event endpoint filtering/pagination behavior.
- Do not alter frontend/API contracts.

## Testing

- Reproduce failing `tests/test_state_consistency.py`.
- Update stale assertions.
- Run the targeted state consistency test file.
- Run backend full pytest to green.
