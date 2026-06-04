# Chapter History Import Reference Cards Design

## Goal

Make imported candidate materials clearer in approved chapter history by showing them as safe writing references with summaries, without implying they automatically became formal canon.

## Selected Small MVP Fix

`ChapterHistoryPanel` shows the approval settlement for a chapter after it is written into world history. It already lists imported material titles from the frozen execution context, but the copy still says `正式 canon` and the references are one-line items without summaries. The highest-value small fix is to make this history/settlement surface match the safer Import Node, Launchpad, Next Prep, and Studio reference-card pattern.

## Scope

- Frontend-only change in `frontend/src/world/ChapterHistoryPanel.tsx`.
- Render `execution_context.material_references` in the approval settlement as readable cards with:
  - material title
  - source title
  - summary
  - Chinese reference-only safety copy
- Replace `正式 canon` with `正式设定` on this surface.
- Keep raw IDs, backend pool enums, source type slugs, and raw text out of visible copy.
- Preserve existing chapter history detail loading and formal event/change rendering.

## Non-Goals

- No backend API changes.
- No database changes.
- No automatic canon edits from imported material.
- No changes to draft approval, world versioning, formal events, or projection updates.
- No broad cleanup of unrelated status labels in the chapter history panel.

## Safety Invariant

Imported candidates remain candidate/reference material. The approved chapter may write formal world-state changes only through the existing draft approval path. Imported materials displayed in chapter history explain what the writer referenced; they do not automatically become formal settings.

## Testing

Use TDD in `frontend/src/world/ChapterHistoryPanel.test.tsx`:

1. Update the approved-detail test to expect title/source/summary cards and `正式设定` safety wording.
2. Assert the old `正式 canon` wording and raw ID/pool/source slugs are not visible.
3. Verify RED with the targeted ChapterHistoryPanel test.
4. Implement the minimal rendering change in `ChapterHistoryPanel.tsx`.
5. Verify GREEN, then run backend import safety tests, relevant frontend tests, frontend build, diff checks, and commit.

## Self-Review

- The scope is small and presentation-only.
- The fix improves Import Node P1 safety after the newcomer flow reaches an approved chapter.
- The design does not introduce a formal-canon mutation path.
