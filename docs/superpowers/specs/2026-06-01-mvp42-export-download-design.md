# MVP42 Export Download Experience Design

## Product-route analysis

WorldSim-Writer already has a backend archive endpoint: `POST /worlds/{world_id}/export/markdown` returns JSON containing a ZIP archive as base64 plus inline Markdown files. Hardening clarified that contract, but the product experience still needs to make the export feel usable from the frontend: a user should understand what was generated, download the ZIP confidently, and inspect the Markdown output before leaving the app.

This MVP42 slice intentionally stays on the stable MVP loop and does not alter chapter approval, world-state projection, events, or archive generation. It turns the existing export contract into a clearer user-facing workflow.

## Candidates and recommendation

### 1. Improve the existing World Archive panel — recommended

Keep the current backend API and enhance `WorldArchivePanel` with explicit archive metadata, download readiness copy, and inline Markdown preview. The export remains a client-side Blob download generated from `archive_base64`, while `files` power a quick in-app preview.

Why this is best:

- It is the smallest high-value change because the backend endpoint and initial download link already exist.
- It directly addresses the usability gap: users can verify and download the archive without needing to infer response semantics.
- It avoids backend churn and preserves existing frontend navigation.
- It is easy to test with Vitest and React Testing Library.

### 2. Add a raw Markdown or raw ZIP backend endpoint

Trade-off: a raw file response could simplify browser download behavior later, but it adds API surface and backend tests. Hardening explicitly preferred preserving the JSON response and avoiding breakage, so this is not the right first MVP42 slice.

### 3. Build a full export center route

Trade-off: a dedicated route could eventually support export history, formats, and settings, but the current app has a small stateful flow instead of routing. This is too large for a small MVP and not required for current acceptance.

## Recommendation

Implement **MVP42 Export Download Experience** as a frontend-only enhancement to the existing `WorldArchivePanel`.

## Goals

1. Show export contract metadata after export:
   - archive filename,
   - archive format (`zip`),
   - archive encoding (`base64`),
   - world version,
   - generated timestamp,
   - inline file count.
2. Keep a clear browser download action using the ZIP filename from the API.
3. Add an inline Markdown preview:
   - default to the first returned file,
   - let users switch files by path,
   - render the selected file content in a readable preformatted panel.
4. Make the empty state explain that export generates a downloadable ZIP and inline preview without writing server-side files.
5. Keep the backend API unchanged and do not mutate world state.
6. Update frontend TypeScript types to match the hardened backend export metadata.

## Non-goals

- No new backend endpoint.
- No raw file streaming response.
- No export history persistence.
- No server-side file writes.
- No markdown rendering library; preview is plain preformatted text for safety and scope control.
- No changes to chapter approval, event logging, world versioning, snapshot creation, or archive file contents.
- No dynamic workflows, no subagents, and no code-review subagent.

## Frontend design

### API type alignment

Update `frontend/src/api/types.ts` so `WorldMarkdownExportResponse` includes the hardened fields already returned by the backend:

- `archive_format: string`
- `archive_encoding: string`
- `files_are_inline: boolean`

The client helper `exportWorldArchiveMarkdown(worldId)` keeps calling the same `POST /worlds/{world_id}/export/markdown` path.

### WorldArchivePanel export UX

Enhance `frontend/src/world/WorldArchivePanel.tsx`:

- Track `selectedExportPath` alongside `markdownExport` and `downloadUrl`.
- After a successful export, set `selectedExportPath` to the first file path.
- When export fails, clear the selected path as well as the export/download state.
- Derive the selected preview file from `markdownExport.files` and `selectedExportPath`.
- Display a download-ready summary with:
  - `下载包已就绪`,
  - filename,
  - format/encoding,
  - generated world version,
  - file count.
- Keep the existing download link but make it clearly labeled as the ZIP download.
- Add a file selector and preview panel when inline files are available.

### Object URL lifecycle

Continue using `URL.createObjectURL(new Blob(..., { type: 'application/zip' }))` for the download link and keep the existing object URL cleanup behavior. The implementation should not introduce persistent browser storage or server-side writes.

## Testing strategy

Use strict TDD:

1. Add a failing frontend component test that expects the export success state to show archive metadata, a ZIP download link, and an inline file preview.
2. Run that targeted test and verify it fails because the metadata/preview UI is missing.
3. Add the minimal type and component implementation.
4. Re-run the targeted test and verify it passes.
5. Add a failing test that switches preview files and verifies the displayed content changes.
6. Run that targeted test and verify it fails because file selection behavior is missing.
7. Implement the minimal selection behavior.
8. Re-run the targeted component tests.
9. Run the relevant API/client and archive panel targeted frontend tests.
10. Run frontend build.

Backend targeted tests are not expected to change for this frontend-only slice, but a backend export test may be run as a safety check if time allows.

## Acceptance criteria

- The world archive panel explains that Markdown export produces a downloadable ZIP plus inline Markdown files.
- After export, users see the archive filename, ZIP/base64 metadata, world version, generated time, and file count.
- Users can download the archive via a link whose `download` attribute uses `archive_filename`.
- Users can preview at least one inline Markdown file and switch between returned file paths.
- `WorldMarkdownExportResponse` frontend type matches the backend export metadata fields.
- Targeted frontend tests for `WorldArchivePanel` pass.
- Frontend build passes.
- Work is committed on `feat/mvp42-export-download`, fast-forward merged to `main`, and not pushed.

## Risks and mitigations

- **Invalid base64 could break export UI.** Keep existing error boundary behavior around `onExportMarkdown`; failed export clears export state and shows an error.
- **Large Markdown files could make preview heavy.** This MVP renders plain text only and uses the existing response payload; no extra parsing or rendering is introduced.
- **Object URLs could leak.** Keep cleanup via `URL.revokeObjectURL` when the download URL changes or the component unmounts.
- **Frontend type drift could recur.** Add new metadata fields to the TypeScript response type and tests' mock payload.

## Self-review

- No placeholders remain.
- Scope is focused on the existing export/download UX.
- The design preserves backend semantics and the approval/world-state invariant.
- Each goal maps to a frontend change and a testable acceptance criterion.

## Implementation status — 2026-06-01

Implemented on `feat/mvp42-export-download`:

- `WorldMarkdownExportResponse` now includes `archive_format`, `archive_encoding`, and `files_are_inline`, matching the hardened backend export contract.
- `WorldArchivePanel` now presents a download-ready state with archive filename, ZIP/base64 metadata, world version, generated timestamp, file count, and the existing ZIP download link.
- `WorldArchivePanel` now defaults to the first inline Markdown file and provides a selector plus preformatted preview for returned `files`.
- The empty export state now explains that export creates a downloadable ZIP and inline Markdown preview without writing server-side files.
- Frontend test fixtures were updated to include the hardened export metadata.

Verification evidence captured before commit:

- RED observed for missing archive metadata copy in `WorldArchivePanel.test.tsx`.
- RED observed for missing Markdown preview selector/content in `WorldArchivePanel.test.tsx`.
- RED observed for missing empty-state copy in `WorldArchivePanel.test.tsx`.
- Frontend build succeeded with `tsc && vite build`.
- Targeted frontend tests passed: `3 passed`, `33 passed` for `WorldArchivePanel`, `WorldPage`, and API client tests.
