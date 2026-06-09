# Obsidian/Markdown Export Upgrade Design

## Goal

Upgrade the existing Markdown ZIP export so it is more useful as an Obsidian vault for MVP/Beta users, without changing the public API response shape or removing/renaming currently asserted paths.

The endpoint remains `POST /worlds/{world_id}/export/markdown` and continues returning JSON with `archive_format: "zip"`, `archive_encoding: "base64"`, `archive_base64`, `files_are_inline: true`, and inline `files` entries.

## Backward compatibility

Preserve existing paths where practical:

- `World.md`
- `Relations.md`
- `Timeline.md`
- `Characters/<safe-name>.md`
- `Foreshadows/<safe-title>.md`
- `Chapters/Chapter-###.md`

Do not rename or remove these files. Improve them in place, and add new files only when useful.

## Export content improvements

1. Add YAML frontmatter to generated Markdown files. Include stable metadata such as `worldsim_type`, IDs, title/name, status, world version, chapter sequence, tags, and related IDs where available.
2. Keep existing visible sections and user-readable bullets so current tests and users still recognize the files.
3. Add richer navigation and summaries:
   - `World.md` becomes the vault index with links to main files, characters, foreshadows, approved chapters, and additive index files.
   - `Relations.md` keeps the relation table and gains metadata.
   - `Timeline.md` keeps event history and gains a summary section.
   - Character, foreshadow, and chapter files gain metadata, backlinks, and clearer headings.
4. Add additive Obsidian-friendly indexes:
   - `README.md` with vault usage guidance.
   - `Indexes/Characters.md`
   - `Indexes/Foreshadows.md`
   - `Indexes/Chapters.md`
   - `Indexes/Timeline.md`

## Error handling and safety

Continue to use existing ownership checks. Export remains read-only: it must not mutate worlds or create snapshots. Path sanitization and deduplication remain in place for user-controlled names.

Markdown formatting should tolerate missing or empty JSON fields by rendering empty strings or `暂无`, not raising errors.

## Testing strategy

Use TDD. First add targeted backend tests that fail against the current implementation:

1. Export includes YAML frontmatter and Obsidian metadata in existing files.
2. Export includes additive index/readme files without removing existing paths.
3. ZIP contents exactly match inline files after the additive files are included.
4. Read-only and path-sanitization behavior remains covered by existing tests.

Then implement the smallest service changes needed to pass these tests. Run targeted backend tests, full backend tests, frontend tests/build if touched or contract-adjacent, `git diff --check`, then commit. Do not push or merge.
