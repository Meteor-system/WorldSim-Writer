# Import Node Readable Source Options Design

## Goal

Make Import Node source-type options read like newcomer-facing Chinese choices instead of terse file-format shorthand.

## Selected Small MVP Fix

The Import Node input guidance now explains that one pasted material source becomes a candidate preview first. The source selector still shows `Markdown` and `txt`, which are understandable to technical users but terse for a 3-minute newcomer loop. The smallest useful fix is to localize the visible labels while keeping API enum values unchanged: `Markdown 文档` and `纯文本文件`.

## Scope

- Frontend-only copy update in `frontend/src/world/WorldImportPanel.tsx`.
- Update visible labels for `markdown` and `txt` source options only.
- Keep select values, request payloads, preview/confirm behavior, batch listing, and canon behavior unchanged.
- Update `WorldImportPanel` tests to assert readable labels and payload stability.

## Non-Goals

- No backend API changes.
- No database changes.
- No new upload flow.
- No changes to import source enum values.
- No automatic canon edits from imported candidates.

## Safety Invariant

Imported materials remain candidate assets and writing references only. This task changes source-option labels only and does not change canon mutation, world versioning, event history, or projection updates.

## Testing

Use TDD in `frontend/src/world/WorldImportPanel.test.tsx`:

1. Expect readable source options `Markdown 文档` and `纯文本文件`.
2. Continue selecting the `markdown` enum value and assert the API payload still sends `source_type: 'markdown'`.
3. Verify RED with the targeted WorldImportPanel test.
4. Implement minimal label changes in `SOURCE_LABELS`.
5. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, and commit.

## Self-Review

- The scope is small and presentation-only.
- The fix improves Import Node first-use readability.
- The design does not create a new formal-canon mutation path.
