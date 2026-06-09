# Obsidian Vault Story Bible and Events Design

## Goal

Make the existing Markdown export feel more like an Obsidian-ready vault while preserving the current API response contract.

## Current State

The backend already returns `archive_format: "zip"`, `archive_encoding: "base64"`, `archive_base64`, `files_are_inline: true`, and inline `files`. Existing export coverage already verifies `World.md`, `README.md`, `Relations.md`, `Timeline.md`, index files, character files, foreshadow files, chapter files, path sanitization, and ZIP parity.

The remaining small Beta-readiness gap is navigation depth: the canon/Story Bible lives only inside `World.md`, and events appear only as rows in `Timeline.md`. That makes the ZIP less useful as an Obsidian vault because users cannot link directly to the Story Bible or individual event notes.

## Selected Slice

Add one compatibility-preserving vault-structure upgrade:

1. Add `Story Bible.md` as a first-class note for canon and story arc.
2. Add one Markdown note per event under `Events/`.
3. Add `Indexes/Events.md` as an event directory.
4. Link `README.md`, `World.md`, `Timeline.md`, and `Indexes/Timeline.md` to the new notes.
5. Keep existing `World.md`, `Relations.md`, `Timeline.md`, indexes, chapter paths, character paths, foreshadow paths, ZIP fields, and inline `files` shape intact.
6. Keep stable internal IDs in YAML frontmatter for machine traceability, but avoid introducing new visible ID-heavy body text; event and chapter bodies should emphasize labels, world versions, related chapter links, and narrative context.

## Out of Scope

- No API schema changes.
- No frontend UI changes unless the existing preview/download flow breaks.
- No large rewrite of all visible enum labels in this slice.
- No removal of existing files or existing frontmatter fields that tests or downstream users may depend on.

## Test Strategy

Use TDD in `backend/tests/test_snapshot_export.py`:

1. Add a failing test that exports after approving a chapter and asserts the vault includes `Story Bible.md`, `Events/Event-001.md`, and `Indexes/Events.md`.
2. Assert the new files are wikilinked from `README.md`, `World.md`, `Timeline.md`, and `Indexes/Timeline.md`.
3. Assert event notes link back to `[[World]]`, link to the approved chapter when available, include frontmatter `event_id`, and do not display a body line like `Event ID:`.
4. Run the focused test and observe RED.
5. Implement the smallest renderer changes.
6. Run focused and related backend tests, plus frontend tests/build only if frontend code changes.
