# Import Node Readable Input Copy Design

## Goal

Make the Import Node input and empty-error copy easier for newcomers by replacing technical file-type shorthand with low-cognitive Chinese guidance.

## Selected Small MVP Fix

Import Node P1 already keeps imported material as candidate references and shows them in later prep/writing surfaces. The next smallest onboarding blocker is the input helper/error copy: `请先粘贴 Markdown、txt 或文本素材。` and `当前只处理单份 Markdown/txt 或粘贴文本。` are technical and repeat raw file-format shorthand. For the 3-minute loop, this should read as a simple action: paste one material segment or upload/use one source at a time, and it remains a candidate reference.

## Scope

- Frontend-only copy update in `frontend/src/world/WorldImportPanel.tsx`.
- Update the empty-content error and input helper sentence.
- Update `WorldImportPanel` tests to expect readable Chinese copy and reject the old technical shorthand.
- Keep source-type select values, import payloads, preview/confirm behavior, batch listing, and canon behavior unchanged.

## Non-Goals

- No backend API changes.
- No database changes.
- No new upload flow.
- No new import-to-world-creation automation.
- No automatic canon edits from imported candidates.

## Safety Invariant

Imported materials remain candidate assets and writing references only. This task changes helper/error copy only and does not change canon mutation, world versioning, event history, or projection updates.

## Testing

Use TDD in `frontend/src/world/WorldImportPanel.test.tsx`:

1. Add assertions that the helper copy says `当前一次只处理一份素材来源，粘贴正文后会先生成候选预览。`.
2. Add an empty-content validation test that expects `请先粘贴一段素材正文。`.
3. Assert old technical shorthand is not visible.
4. Verify RED with targeted WorldImportPanel tests.
5. Implement minimal copy changes.
6. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, and commit.

## Self-Review

- The scope is small and presentation-only.
- The fix improves Import Node first-use comprehension.
- The design does not create a new formal-canon mutation path.
