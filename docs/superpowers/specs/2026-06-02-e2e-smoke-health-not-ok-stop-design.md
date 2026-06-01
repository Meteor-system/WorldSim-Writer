# E2E Smoke Health Not-OK Stop Design

## Problem

The smoke script requires the health response to contain a `status` field and includes `health.get('status') == 'ok'` in the final `ok` gate, but it can continue into auth/world/draft writes when `/health` returns a non-`ok` status. For beta and real-LLM smoke, a degraded health response should stop the flow before any state-changing calls.

## Goal

Treat `/health` status values other than `ok` as a hard preflight failure before registration/login, world creation, drafting, or approval.

## Scope

In scope:

- Add an early stop in `backend/scripts/e2e_smoke.py` when `health.status != "ok"`.
- Preserve safe diagnostics under `checks.health`.
- Use `failed_step: "health"` and `error: "HEALTH_STATUS_NOT_OK"`.
- Add smoke-script regression coverage that verifies only `/health` is called.
- Document the beta tester remediation path in `BETA_TESTING.md`.

Out of scope:

- Changing backend `/health` implementation.
- Changing migration or LLM-mode checks.
- Frontend changes.

## Design

After health required-path validation and `checks.health` population, the smoke script checks the safe status value. If it is anything other than `ok`, the script returns immediately with:

```json
{
  "failed_step": "health",
  "error": "HEALTH_STATUS_NOT_OK",
  "checks": {
    "health": {
      "status": "degraded",
      "migration_up_to_date": true,
      "llm_mock": true
    }
  }
}
```

This check runs before migration and LLM-mode checks because status is the broadest health preflight gate.

## Test strategy

Add a `SequencedTransport` unit test in `backend/tests/test_e2e_scripts.py` with a health payload containing `status: "degraded"`, valid migration state, and valid mock LLM mode. Assert `ok` is false, the error code is `HEALTH_STATUS_NOT_OK`, health diagnostics are present, and the only requested path is `/health`.
