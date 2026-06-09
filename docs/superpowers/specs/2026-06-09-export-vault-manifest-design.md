# Export Vault Manifest Design

## Goal

Add a small Obsidian/Markdown export improvement that helps beta testers verify what is inside a vault without changing the export API contract.

## Current State

The export already returns the existing JSON contract with inline `files` and a base64 ZIP. The vault includes `README.md`, `World.md`, `Story Bible.md`, `Relations.md`, `Timeline.md`, character/foreshadow/chapter/event notes, and indexes. Current tests cover path sanitization, ZIP parity, story/event wikilinks, and API compatibility.

The remaining small Beta-readiness gap is quick archive verification. Users can open `README.md`, but there is no single manifest note that lists world/version metadata, object counts, the preserved API shape, and every exported path for ZIP-vs-inline checks.

## Selected Slice

Add a top-level `Manifest.md` note:

1. Preserve all existing response fields and file paths.
2. Add `Manifest.md` to inline files and the ZIP.
3. Link it from `README.md` and `World.md` navigation.
4. Include YAML frontmatter with `worldsim_type: vault_manifest`, `world_id`, `world_version`, and `file_count`.
5. Include body sections for archive metadata, content counts, preserved API contract, and a file inventory with wikilinks for Markdown files.

## Out of Scope

- No frontend UI changes.
- No broad refactor of the export renderers.
- No API schema changes.
- No removal or renaming of existing files.
- No change to ZIP encoding behavior.

## Test Strategy

Use TDD in `backend/tests/test_snapshot_export.py`:

1. Add a failing test that exports a world after approving a chapter.
2. Assert `Manifest.md` exists, is linked from `README.md` and `World.md`, has manifest frontmatter, mentions preserved API fields, reports counts, and lists representative existing files such as `World.md`, `Story Bible.md`, `Chapters/Chapter-001.md`, and `Events/Event-001.md`.
3. Run the focused test and confirm RED because `Manifest.md` is absent.
4. Implement the smallest renderer changes.
5. Run focused, related export tests, full backend tests, and diff checks before committing.
