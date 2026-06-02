# E2E Smoke Markdown Archive Base64 Contract Design

## Goal

Prevent the MVP/Beta smoke script from accepting malformed markdown export archive payloads when `archive_base64` is truthy but not a non-empty string.

## Context

The smoke script already verifies markdown export fields are present, `files` is a list of objects, `archive_format` is `zip`, `archive_encoding` is `base64`, `files_are_inline` is `true`, and `files.World.md` appears in the inline preview. However, `archive_base64` is currently checked with truthiness. A list, object, number, or boolean value can therefore satisfy the final `ok` calculation even though beta testers cannot treat it as a base64 ZIP payload.

## Chosen approach

Add a small top-level string validation for `archive_base64` before archive validity checks:

- Missing `archive_base64` remains `MISSING_REQUIRED_FIELDS`.
- Non-string, boolean, object, list, number, or empty string values produce `INVALID_FIELD_TYPES` with `invalid_fields: ["archive_base64"]`.
- A non-empty string continues into the existing archive validity checks.

This uses the existing `_require_string_fields()` helper instead of adding a new validator.

## Scope

In scope:

- Add a focused regression test in `backend/tests/test_e2e_scripts.py`.
- Validate `archive_base64` in `backend/scripts/e2e_smoke.py`.
- Update `BETA_TESTING.md` and docs coverage terms so testers know malformed archive bodies are type diagnostics.

Out of scope:

- Decoding or inspecting ZIP bytes.
- Changing markdown export backend behavior.
- Frontend export/download changes.
- New smoke steps or real provider calls.

## Testing

Use TDD:

1. Add a test where markdown export returns `archive_base64` as a list while all other export fields are valid.
2. Verify the test fails because the current smoke reports success.
3. Add the minimal validation.
4. Verify focused test, full smoke-script tests, docs coverage, and full backend pytest.
