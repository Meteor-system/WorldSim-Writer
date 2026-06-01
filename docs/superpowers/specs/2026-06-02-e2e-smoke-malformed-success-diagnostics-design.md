# E2E Smoke Malformed Success Diagnostics Design

## Context

The smoke script already records `failed_step`, `status_code`, and `response_body` for HTTP failures, and request errors are tied to the step that failed. Real-LLM smoke can also fail because the backend returns a 200 JSON object that is structurally incomplete for the smoke's next assertion, for example a draft response without `chapter_id` or an approval response without `approved_version`.

Today those malformed success responses can raise raw `KeyError` or `TypeError` exceptions outside `_step_json`, which makes the smoke summary less actionable. The output may identify only a Python exception instead of a step-scoped API contract failure.

## Goal

Make smoke diagnostics identify malformed 2xx response payloads at the step where required fields are missing.

## Approach

Add a small helper that validates required response fields after each successful `_step_json` call. When required fields are missing, it writes:

- `failed_step`: the API step name.
- `error`: a stable `MISSING_REQUIRED_FIELDS` marker.
- `missing_fields`: the missing field names.

Then return the normal summary without raising. Apply this helper only to fields the smoke must dereference for subsequent steps:

- register/login: `access_token`
- create_world: `id`
- draft: `chapter_id`, `draft_version`

Continue treating optional diagnostic fields like `draft_id`, `world_version`, and `user.id` as optional.

This is a smoke-script robustness change only:

- No backend API response shape changes.
- No frontend changes.
- No request headers, bearer tokens, API keys, provider URLs, or model names are added to diagnostics.
- No approval/world-state behavior changes.

## Acceptance Criteria

- A successful draft response missing `chapter_id` produces `ok: false`, `failed_step: "draft"`, `error: "MISSING_REQUIRED_FIELDS"`, and `missing_fields: ["chapter_id"]`.
- The smoke script no longer raises a raw `KeyError` for that malformed response.
- Existing happy-path smoke test still passes.
- `BETA_TESTING.md` documents `MISSING_REQUIRED_FIELDS` and `missing_fields` as smoke diagnostic fields.
