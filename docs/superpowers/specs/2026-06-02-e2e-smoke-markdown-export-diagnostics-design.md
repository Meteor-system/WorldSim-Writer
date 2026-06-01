# E2E Smoke Markdown Export Diagnostics Design

## Context

README and `BETA_TESTING.md` both define the markdown export response shape as part of the main MVP smoke pass criteria. The smoke script currently checks export fields at the final `ok` gate, but a malformed 200 OK export response only yields `ok: false` with partial `checks.markdown_export` details.

For beta triage, this is less actionable than the existing malformed-success diagnostics used for register, create-world, draft, and approval responses.

## Goal

Fail smoke at the `markdown_export` step with `MISSING_REQUIRED_FIELDS` when a successful export response omits fields required by the documented archive contract.

## Approach

Reuse `_require_fields` after the markdown export API call succeeds and before computing export checks. Require these documented fields:

- `archive_format`
- `archive_encoding`
- `archive_base64`
- `files_are_inline`
- `files`

This is deliberately a presence check, not a semantic check. The existing final `ok` gate still validates the expected values (`zip`, `base64`, inline files, non-empty base64, and `World.md`).

This is a smoke diagnostics change only:

- No backend API response shape changes.
- No frontend changes.
- No archive/export behavior changes.
- No secrets, headers, tokens, provider URLs, or model names are added to diagnostics.

## Acceptance Criteria

- A successful markdown export response missing `archive_base64` produces `ok: false`, `failed_step: "markdown_export"`, `error: "MISSING_REQUIRED_FIELDS"`, and `missing_fields: ["archive_base64"]`.
- Existing markdown export semantic checks still control final `ok` when all required fields are present but have wrong values.
- Existing docs for `MISSING_REQUIRED_FIELDS` and `missing_fields` remain accurate.
