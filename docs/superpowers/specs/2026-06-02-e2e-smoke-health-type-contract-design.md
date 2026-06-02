# E2E Smoke Health Type Contract Design

## Goal

Make the smoke script reject malformed `/health` preflight type data before it can run the main writing loop against an ambiguous backend state.

## Problem

The smoke script currently requires `/health` to include `status`, `migration.up_to_date`, and `llm.mock`, but it does not validate that the two mode/version flags are booleans. If a backend regression or proxy returned values like `"false"`, the smoke script could misclassify the backend mode or migration state because Python string truthiness and identity checks do not behave like JSON booleans.

This is a beta-readiness risk because `/health` is the guardrail that prevents mock smoke from hitting a real LLM backend, real-LLM smoke from hitting a mock backend, and smoke runs from proceeding before migrations are applied.

## Brainstormed Options

1. Coerce string values such as `"true"` and `"false"` into booleans. This is permissive, but hides backend response contract drift.
2. Add special diagnostics for each malformed health flag. This is precise, but adds new error vocabulary for cases the existing type diagnostic already covers.
3. Reuse `INVALID_FIELD_TYPES` for health preflight paths. Require `migration.up_to_date` and `llm.mock` to be JSON booleans before any mode checks run.

## Selected Design

Use option 3. Add a small nested boolean validator to the smoke script and apply it immediately after `_require_paths(...)` succeeds for `/health`.

If either health flag is present but not a JSON boolean, stop with:

```json
{
  "failed_step": "health",
  "error": "INVALID_FIELD_TYPES",
  "invalid_fields": ["migration.up_to_date", "llm.mock"]
}
```

The helper must treat Python `bool` values as valid and all other types, including strings, integers, `null`, objects, and arrays, as invalid.

## Scope Boundaries

- Do not change backend `/health` response shape.
- Do not add new error codes when `INVALID_FIELD_TYPES` is sufficient.
- Do not repeat completed timeout/auth/redaction/post-approval overview checks.
- Do not alter model-call or approval behavior.

## Test Strategy

- Add a failing unit test for `/health` returning string values for `migration.up_to_date` and `llm.mock`.
- Assert the smoke stops before auth with `failed_step: "health"`, `error: "INVALID_FIELD_TYPES"`, and both nested paths listed in `invalid_fields`.
- Implement the minimal nested boolean helper.
- Update `BETA_TESTING.md` and docs coverage so beta testers know health preflight type failures may name health paths.
