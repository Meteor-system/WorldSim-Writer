# E2E Smoke Migration Gate Design

## Goal

Make `backend/scripts/e2e_smoke.py` stop early with a clear diagnostic when `/health` reports that database migrations are not up to date.

## Problem

The smoke script records `checks.health.migration_up_to_date`, but it does not require that value to be true before continuing. If a beta tester starts the backend before running `alembic upgrade head`, later steps can fail with noisy auth/world/draft errors. The first actionable fix is to tell the tester to run migrations.

## Scope

- Keep the `/health` API unchanged.
- Keep successful smoke behavior unchanged when `migration.up_to_date` is true.
- If `migration.up_to_date` is false, return a JSON summary with:
  - `ok: false`
  - `failed_step: "health"`
  - `error: "MIGRATION_NOT_UP_TO_DATE"`
  - existing `checks.health` migration details
- Do not continue to register/login or create smoke data when migrations are stale.
- Document the gate in `BETA_TESTING.md`.

## Non-goals

- Do not run Alembic automatically.
- Do not modify migration discovery code.
- Do not change backend startup behavior.
- Do not add frontend changes.

## Testing

Add a regression test in `backend/tests/test_e2e_scripts.py` where the `/health` response has `migration.up_to_date: false`. The smoke summary should fail at `health`, preserve migration details, and make no request beyond `/health`.
