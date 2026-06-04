# Import Node Candidate Record Intro Copy Design

## Goal

Make the Import Node intro explain confirmation with low-cognitive candidate-material record wording instead of visible internal batch terminology.

## Selected Small MVP Fix

`WorldImportPanel` already explains that imported material enters the candidate material pool and does not automatically rewrite formal settings. One remaining intro sentence still says:

- `确认后只写入候选素材和导入批次审计记录。`

`导入批次` is an implementation/audit concept. For newcomers, the safer and clearer mental model is that confirmation creates candidate material records, not formal canon. The thin fix is to change the visible sentence to:

- `系统会先解析、分类、清洗并提示冲突，确认后只写入候选素材记录，不会改动正式设定。`

This reinforces the candidate-only safety invariant at the top of the Import Node before users preview or confirm material.

## Scope

- Frontend-only copy update in `frontend/src/world/WorldImportPanel.tsx`.
- Update `frontend/src/world/WorldImportPanel.test.tsx` to expect the clearer intro sentence.
- Keep API fields, TypeScript types, import confirmation payloads, recent record rendering, backend persistence, and audit data unchanged.

## Non-Goals

- No backend API changes.
- No database changes.
- No import batch model rename in code or payloads.
- No automatic canon edits from imported candidate materials.
- No world embryo generation changes.
- No broad Import Node layout redesign.

## Safety Invariant

Imported materials remain candidate-only writing references. This task changes visible frontend copy only and does not change formal canon mutation, world versioning, event history, or projection updates.

## Testing

Use TDD in `frontend/src/world/WorldImportPanel.test.tsx`:

1. Add an expectation for `确认后只写入候选素材记录，不会改动正式设定。` in the preview test that already checks the Import Node intro.
2. Assert the old internal wording `导入批次审计记录` is not visible.
3. Verify RED before changing production copy.
4. Change only the visible intro sentence in `WorldImportPanel.tsx`.
5. Verify GREEN, then run backend import safety tests, relevant frontend tests, build, diff checks, inline self-review, and commit.

## Self-Review

- Scope is intentionally small and presentation-only.
- The copy improves newcomer understanding before the first import confirmation.
- The design does not create or alter any canon mutation path.
