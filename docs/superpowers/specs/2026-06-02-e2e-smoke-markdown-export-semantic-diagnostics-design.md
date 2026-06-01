# E2E Smoke Markdown Export Semantic Diagnostics Design

## Context

`README.md` and `BETA_TESTING.md` define the markdown export response as part of the MVP smoke pass criteria: the backend should return a ZIP archive encoded as base64, inline preview files, and a `World.md` file. The smoke script already validates required export fields and file-list shape, but semantic archive failures are still only folded into the final `ok` boolean.

Examples of silent semantic failures today:

- `archive_format` is not `zip`.
- `archive_encoding` is not `base64`.
- `files_are_inline` is not `true`.
- `archive_base64` is empty.
- Inline `files` does not include `World.md`.

These all produce `ok: false` without a `failed_step` or actionable `error`.

## Goal

Make well-formed but invalid markdown export evidence fail at `failed_step: "markdown_export"` with a clear error and field-level evidence.

## Selected Approach

After constructing `summary['checks']['markdown_export']`, add one validation block that collects invalid export evidence fields:

- `archive_format` when it is not `zip`.
- `archive_encoding` when it is not `base64`.
- `files_are_inline` when it is not `True`.
- `archive_base64` when it is empty.
- `files.World.md` when no inline file has `path == "World.md"`.

If any field is invalid, set:

```python
summary['failed_step'] = 'markdown_export'
summary['error'] = 'MARKDOWN_EXPORT_INVALID_ARCHIVE'
summary['invalid_fields'] = invalid_export_fields
```

Then return the summary immediately.

## Alternatives Considered

1. Separate error codes per export predicate. This is more specific but adds unnecessary code/docs surface for beta smoke triage.
2. Keep relying on final `ok: false`. This preserves current behavior but leaves testers without the same diagnostic quality as earlier smoke steps.
3. Refactor all final `ok` predicates into helpers. This would be cleaner long-term but is too broad for this readiness round.

## Testing

Add focused regressions for representative invalid export evidence:

- Wrong `archive_format` and `archive_encoding`.
- Missing inline `World.md`.

Update docs regression and `BETA_TESTING.md` so beta testers know to inspect `invalid_fields` when `MARKDOWN_EXPORT_INVALID_ARCHIVE` appears.

## Scope Boundaries

- No frontend changes.
- No API response changes.
- No export generation changes.
- No changes to approval/event behavior.