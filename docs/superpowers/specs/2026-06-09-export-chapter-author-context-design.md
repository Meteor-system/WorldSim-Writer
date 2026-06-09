# Export Chapter Author Context Design

## Goal

Make exported chapter notes more useful to authors by preserving the chapter goal, model context summary, and review hints alongside the approved prose.

## Current State

The Markdown/Obsidian export already builds a vault with world, Story Bible, relations, timeline/events, character notes, foreshadow notes, chapter notes, indexes, README, and manifest. Chapter notes currently include metadata such as chapter number, approval version, base world version, and the approved content. Tests cover ZIP integrity, metadata, indexes, story/event wikilinks, foreshadow source chapter links, path sanitization, auth, and rejected-draft exclusion.

The remaining author-facing gap is chapter-level writing context. `ChapterDraft` stores `context_summary` and `review_hints`, and `Chapter` stores `chapter_goal`, but `build_world_archive_payload()` drops those fields. As a result, exported chapter notes lose the reason the chapter was written, the summary that should seed continuity, and the review notes authors may want when revising in Obsidian.

## Selected Slice

Add author context to approved chapter exports:

- Include `chapter_goal`, approved draft `context_summary`, and approved draft `review_hints` in each `approved_chapters` archive payload item.
- Render chapter notes with:
  - `- Chapter Goal: ...` in the metadata list.
  - `## Context Summary` before `## Content`.
  - `## Review Hints` before `## Content`, with one bullet per hint or `- 暂无` when empty.
- Keep existing response shape fields, ZIP behavior, filenames, chapter paths, and approval/generation behavior unchanged.
- Continue exporting only approved chapters; rejected drafts stay excluded.

## Out of Scope

- No frontend changes.
- No new API route fields outside the existing flexible archive payload/files content.
- No export of full execution context JSON in this slice.
- No change to chapter numbering/path generation.
- No inference or generation of missing summaries/hints.

## Test Strategy

Use TDD in `backend/tests/test_snapshot_export.py`:

1. Extend an existing chapter export test to assert the chapter note includes the known `chapter_goal`, `context_summary`, and `review_hints` from `SnapshotExportLLMClient`.
2. Run the focused test and verify RED because chapter notes currently omit those fields.
3. Add approved draft context fields to `build_world_archive_payload()`.
4. Render those fields in `_chapter_markdown()`.
5. Run focused, related snapshot export tests, and full backend pytest because this changes backend export serialization.
6. Skip frontend tests/build because no frontend code or typed API contract changed.
