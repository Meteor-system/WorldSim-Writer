# Studio Approval Preview Localization Design

## Goal

Remove remaining author-facing internal status enum leakage from the Studio approval preview while preserving approval selection behavior and API contracts.

## Current State

The Studio proposed-change summary now uses Chinese status labels and hides raw ID fallback strings. The adjacent "写入正史前确认" card still renders raw status transitions directly from `approvalPreview.character_changes` and `approvalPreview.foreshadow_changes`:

- Character preview can show `状态：active → 开始调查密信`.
- Foreshadow preview can show `状态：planted → advanced`.

These strings are visible exactly where beta users decide which formal world-state changes to approve. The checkbox labels and indexes drive selection behavior, so the slice must change only displayed text and keep `change_index` handling unchanged.

## Selected Slice

Update only Studio approval-preview display text:

1. Add a small helper in `frontend/src/studio/StudioPage.tsx` that formats status values with `labelStatus()` and keeps empty values as `未设置`.
2. Use that helper for character and foreshadow approval-preview status transitions.
3. Keep checkbox rendering, `previewIndex()`, `toggleCharacterSelection()`, `toggleForeshadowSelection()`, and `approveChapter()` payloads unchanged.

## Out of Scope

- No backend changes.
- No API response shape changes.
- No changes to selected change indexes or default selection behavior.
- No broad Studio copy rewrite.
- No localization of developer-only tests or API type definitions.

## Test Strategy

Use TDD in `frontend/src/studio/StudioPage.test.tsx`:

1. Add failing assertions to the existing approval preview test that the preview shows `状态：进行中 → 开始调查密信` and `状态：已埋下 → 推进中`.
2. Add negative assertions that the rendered page no longer contains `状态：active → 开始调查密信` or `状态：planted → advanced`.
3. Run the targeted Studio test and confirm RED.
4. Implement the minimal display helper/use-site changes.
5. Run the targeted Studio test, full frontend tests, frontend build, and diff checks before committing.
