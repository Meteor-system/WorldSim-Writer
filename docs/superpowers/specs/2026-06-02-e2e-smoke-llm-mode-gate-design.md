# E2E Smoke LLM Mode Gate Design

## Context

The Beta playbook separates mock smoke from real-LLM smoke, but the smoke script currently only records the mode selected by `E2E_REAL_LLM`. It does not verify that the running backend is configured with the matching `LLM_MOCK` value. A tester can accidentally run mock smoke against a real-LLM backend, creating slow or costly model calls, or run real-LLM smoke against a mock backend and get a misleading pass.

## Decision

Expose a safe LLM readiness flag from `/health` and make the smoke script fail fast when the requested smoke mode does not match the backend LLM mode.

`/health` will include:

```json
{
  "status": "ok",
  "migration": {"up_to_date": true},
  "llm": {"mock": true}
}
```

The field intentionally exposes only the boolean mock mode. It must not expose `LLM_API_KEY`, bearer tokens, request headers, or other secrets.

## Smoke behavior

After the existing health and migration checks, the smoke script records:

```json
"checks": {
  "health": {
    "status": "ok",
    "migration_up_to_date": true,
    "llm_mock": true
  }
}
```

Fail-fast cases:

- Mock smoke (`E2E_REAL_LLM` unset/false) with backend `llm.mock: false` returns `failed_step: "health"` and `error: "BACKEND_LLM_MOCK_DISABLED"`.
- Real-LLM smoke (`E2E_REAL_LLM=1`) with backend `llm.mock: true` returns `failed_step: "health"` and `error: "BACKEND_LLM_MOCK_ENABLED"`.

If the backend is correctly configured, the existing main-flow smoke continues unchanged.

## Testing

Use TDD:

1. Add a health test that expects `/health` to report `llm.mock`.
2. Add smoke-script tests for mock-mode mismatch and real-mode mismatch.
3. Update the Beta docs regression so the playbook documents `llm_mock` and the mismatch errors.
4. Implement the minimal code and docs changes.

## Scope boundaries

- Do not add provider names, model names, base URLs, API keys, or request headers to `/health` or smoke diagnostics.
- Do not change the chapter generation flow.
- Do not add new external dependencies.
