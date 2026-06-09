# Export Foreshadow Source Links Design

## Goal

Make the Markdown/Obsidian export more author-ready by linking foreshadow ledger notes back to their source chapter notes when the source chapter is present in the approved chapter archive.

## Current State

Continuous chapter generation/context is already covered by backend pipeline tests and the optional two-chapter smoke diagnostics. The export path already creates an Obsidian-friendly vault with `World.md`, `Story Bible.md`, chapter notes, foreshadow notes, timeline/event notes, indexes, a README, and `Manifest.md`. Chapter/event links exist in timeline and event notes, and foreshadow notes link related characters.

The remaining small gap is foreshadow source evidence: each foreshadow note currently renders `Source Chapter` as a raw ID or blank. For beta authors reviewing exported vaults, that forces manual lookup instead of a direct Obsidian backlink to the originating chapter.

## Selected Slice

Add foreshadow-to-source-chapter wikilinks in exported Markdown notes:

- Keep all existing files, response fields, ZIP behavior, and inline preview behavior unchanged.
- When a foreshadow has `source_chapter_id` and that chapter is included in the approved chapter export, render `Source Chapter` as `[[Chapters/Chapter-NNN]]`.
- When no approved source chapter note is available, keep the existing raw ID/blank fallback behavior.
- Do not mutate world state, create snapshots, or change narrative approval/generation behavior.

## Out of Scope

- No frontend changes.
- No new API fields.
- No changes to chapter numbering or path generation.
- No inference of source chapters when `source_chapter_id` is absent.
- No changes to event payload scrubbing or timeline format.

## Test Strategy

Use TDD in `backend/tests/test_snapshot_export.py`:

1. Extend the existing story/event wikilink export test to assign a current foreshadow's `source_chapter_id` to the approved chapter ID before export.
2. Assert the relevant foreshadow note contains `- Source Chapter: [[Chapters/Chapter-001]]`.
3. Run the focused test and verify RED because `_foreshadow_markdown` currently renders the raw source chapter ID.
4. Pass `chapter_paths` into `_foreshadow_markdown` and add a small helper to render a source chapter wikilink when available.
5. Run focused, related snapshot export tests, and full backend pytest because this is a backend export serialization change.
6. Skip frontend tests/build because no frontend code changes.
