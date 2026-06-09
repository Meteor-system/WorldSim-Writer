# E2E Smoke Runbook Payload Design

## Goal

Make mock and real-LLM smoke failures easier to triage from the JSON output testers already paste into beta bug reports.

## Problem

`backend/scripts/e2e_smoke.py` validates the full MVP writing loop and already records structured fields such as `failed_step`, `error`, `status_code`, and redacted `response_body`. The README and beta playbook explain many failures, but a failed smoke run does not include a concise next action. The summary also hard-codes a cleanup command that assumes `/opt/WorldSim-Writer/backend` and `.venv/bin/python`, which is less reliable when the script is run with `python`, `conda run`, or from a different checkout path.

## Design

Keep the smoke flow unchanged and add runbook metadata to the existing summary object:

- `runbook.required_backend_env`: mode-specific backend environment hints.
  - Mock mode: `LLM_MOCK=true`.
  - Real-LLM mode: `LLM_MOCK=false`, `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL`.
- `runbook.client_env`: smoke-client environment hints such as `BASE_URL`, `E2E_REAL_LLM`, and `E2E_TIMEOUT_SECONDS`.
- `cleanup_command`: build from the detected backend directory and `sys.executable` instead of a hard-coded `.venv` path.
- `next_action`: when the smoke fails with a common error, add one short safe triage instruction. Examples include restarting with the correct LLM mock mode, running migrations, increasing timeout, checking provider credentials/quota, or running the cleanup command after the run.

The payload must not include secrets, provider request messages, or raw authorization headers.

## Scope

In scope:

- Small helper functions in `backend/scripts/e2e_smoke.py`.
- Focused tests in `backend/tests/test_e2e_scripts.py` for mode runbook metadata, dynamic cleanup command, and common failure `next_action` values.
- README and `BETA_TESTING.md` wording that points testers to `runbook`, `next_action`, and cleanup dry-run/confirm flow.

Out of scope:

- Changing API endpoints.
- Changing draft generation, approval, export, or cleanup behavior.
- Real external LLM calls in tests.
- Frontend changes.

## Test Strategy

Use existing `SequencedTransport` tests around `run_smoke()`:

1. Add a failing success-path test asserting the summary includes mode-specific runbook metadata and a cleanup command using `sys.executable`.
2. Add failing preflight mismatch tests asserting `BACKEND_LLM_MOCK_DISABLED` and `BACKEND_LLM_MOCK_ENABLED` include actionable `next_action` strings.
3. Add a failing real-provider HTTP failure test asserting a `MODEL_AUTH_FAILED` or `MODEL_RATE_LIMITED` response body produces provider-specific `next_action` while preserving existing redaction behavior.
4. Implement the smallest helper functions needed to pass.
5. Run focused backend tests, related cleanup tests, and diff checks before committing.
