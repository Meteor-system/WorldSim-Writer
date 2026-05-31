# MVP13 Obsidian / Markdown Export 1.0 Design

## Goal

Let authors export the current formal world canon as an Obsidian-friendly Markdown bundle that can be downloaded locally, opened as a plain knowledge base, and used for demos or ownership handoff.

MVP13 upgrades the existing snapshot/export foundation into a user-facing archive export: it keeps export read-only, exports only formal canon and approved chapters, produces a predictable folder structure, and gives the frontend a real download path rather than only listing returned files.

## Current context

The repository already contains a `snapshot_export` backend module and `WorldArchivePanel` frontend section. Existing behavior includes:

- `POST /worlds/{world_id}/export/markdown` returns JSON with Markdown files.
- Snapshot/export routes require auth and enforce world ownership.
- Export already uses approved chapters only and does not create a snapshot or mutate world state.
- The frontend can trigger export and display returned file paths.

MVP13 should extend this path rather than create a parallel export subsystem.

## Recommended approach

Use a backend-generated Markdown bundle response with both:

1. structured file previews (`files`) for UI inspection and tests;
2. a base64-encoded ZIP archive (`archive_base64`) plus `archive_filename` so the browser can download the bundle without adding frontend dependencies.

This is the default best approach because Python has standard-library `zipfile`, the frontend currently has no ZIP dependency, and this keeps all path sanitization and bundle structure rules centralized on the backend.

## Alternatives considered

### A. Backend JSON files only

Keep returning only `{ files: [{ path, content }] }` and let the UI list paths. This is simplest and partially exists, but it does not satisfy the acceptance criterion that a user can obtain a local Markdown bundle from the UI.

### B. Frontend-created ZIP

Return JSON files and build a ZIP in the browser. This avoids base64 payloads but requires adding a dependency such as JSZip or relying on browser APIs not already present. That is unnecessary for MVP scale.

### C. Backend ZIP download endpoint only

Return `application/zip` directly. This is clean for download but worse for tests and preview UI because the frontend loses structured metadata unless a second preview endpoint is added. For MVP13, a JSON response with embedded archive keeps the existing API shape and adds download capability.

## Export contract

Endpoint:

```http
POST /worlds/{world_id}/export/markdown
```

Response:

```json
{
  "world_id": 7,
  "world_version": 3,
  "generated_at": "2026-05-31T00:00:00Z",
  "archive_filename": "WorldSim-Qinglan-City-v3-markdown.zip",
  "archive_base64": "...",
  "files": [
    { "path": "World.md", "content": "# 青岚城\n..." },
    { "path": "Characters/林砚.md", "content": "# 林砚\n..." },
    { "path": "Relations.md", "content": "# Character Relations\n..." },
    { "path": "Foreshadows/裂纹玉佩.md", "content": "# 裂纹玉佩\n..." },
    { "path": "Chapters/Chapter-001.md", "content": "# 第一章 雨巷密谈\n..." },
    { "path": "Timeline.md", "content": "# Timeline\n..." }
  ]
}
```

The existing `files` field remains compatible. `archive_filename` and `archive_base64` are additive.

## Markdown file structure

The bundle uses stable Obsidian-compatible relative paths:

```text
World.md
Relations.md
Characters/<character-name-or-id>.md
Foreshadows/<foreshadow-title-or-id>.md
Chapters/Chapter-001.md
Chapters/Chapter-002.md
Timeline.md
```

Rules:

- `World.md` contains world title, genre, world version, truth canon version, status, truth canon, story arc summary, links to characters, foreshadows, approved chapters, and timeline.
- Character files contain role, status, goals, public profile, hidden traits, destiny flag, and relations.
- `Relations.md` contains relation rows and, where possible, character names instead of only IDs.
- Foreshadow files contain type, status, urgency, related character names/links, expected resolution window, source chapter, and description.
- Chapter files contain only approved chapter content and approved metadata.
- `Timeline.md` contains recent/formal event history as a table and summary of world version transitions.

## Data inclusion rules

Export includes only formal canon:

- current world projection (`truth_canon`, world metadata, story arc);
- current characters and relations;
- current foreshadows;
- approved chapters where `status == 'approved'`, `approved_content` is present, and `approved_version` is present;
- formal event log history.

Export excludes:

- reviewing drafts;
- rejected drafts;
- draft-only proposed changes;
- transient approval preview/consistency state;
- any server-local file writes.

## Filename sanitization

All generated file path segments are sanitized on the backend:

- Preserve readable Unicode letters/numbers, `_`, `-`, and `.`.
- Replace path separators and unsafe punctuation with `-`.
- Strip leading/trailing separators.
- Use stable fallback names such as `Character-<id>` or `Foreshadow-<id>` when a title sanitizes to an empty value.
- De-duplicate collisions by appending `-2`, `-3`, etc.
- Use chapter sequence numbering (`Chapter-001.md`) based on approved chapter order rather than database ID, while keeping chapter ID in metadata.

## Frontend behavior

`WorldArchivePanel` keeps the existing archive section and adds a real download affordance:

1. User clicks `导出世界档案`.
2. Frontend calls `exportWorldArchiveMarkdown(world.id)`.
3. On success, it shows file count, filename, key paths, and generated version.
4. It automatically prepares a browser download from `archive_base64`, and also shows a `下载 Markdown ZIP` button so users can retry the download.
5. Errors remain localized to the Archive panel.

No new route or global state is needed.

## Testing strategy

Backend TDD:

- Add tests for exact Obsidian folder structure and `archive_base64` ZIP contents.
- Add tests for filename sanitization and collision handling.
- Add tests that reviewing/rejected drafts are excluded while approved chapters are included.
- Keep existing auth/ownership/read-only export tests passing.

Frontend TDD:

- Add API helper test proving the export endpoint is called.
- Add `WorldArchivePanel` test proving export success displays the archive filename and creates a downloadable ZIP link/button.
- Add error-state test coverage remains unchanged.
- Run targeted frontend tests and `npm run build`.

## Non-goals

MVP13 does not implement:

- two-way sync;
- Obsidian plugin integration;
- writing exported files to the server filesystem;
- cloud storage;
- incremental sync or conflict resolution;
- complex user-editable templates;
- push to remote git.

## Inline self-review

- Placeholder scan: no TBD/TODO placeholders remain.
- Scope check: this is a single implementation plan built around the existing snapshot/export module and Archive panel.
- Compatibility: the existing `files` response remains; new ZIP metadata is additive.
- Canon safety: export is read-only and only includes current formal projection plus approved chapters/events.
- Ambiguity resolved: the downloadable bundle is a backend-generated ZIP encoded in JSON, not a new binary-only endpoint.
