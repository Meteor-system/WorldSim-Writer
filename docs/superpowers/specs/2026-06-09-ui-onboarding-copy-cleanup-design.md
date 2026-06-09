# UI Onboarding and Chinese-Friendly Copy Cleanup Design

## Goal

Improve the MVP frontend experience for authors by making visible copy warmer, clearer, and less technical across Story Bible, continuous chapter flow, export/archive, world overview, and studio pages. Keep all backend APIs and response shapes unchanged.

## Scope

This is a targeted frontend copy and display-formatting pass, not a visual redesign or data-model change.

In scope:

- Story Bible tab copy and help text.
- World overview / Narrative Control Center labels that currently expose English product or internal terms.
- Studio context and settlement copy for continuous chapters.
- World Archive snapshot/export/compare copy and displayed metadata.
- Small shared display-label helpers for statuses, object types, change types, file paths, and snapshot labels.
- Targeted tests that verify author-friendly copy and absence of raw technical fields in visible UI.

Out of scope:

- Backend schema changes.
- Broad component refactors.
- New UI libraries or large layout redesign.
- Changing core workflow behavior.

## Approach

Use a conservative, compatibility-first frontend layer:

1. Preserve API calls and TypeScript types.
2. Convert raw enum/token/id/file metadata only at render time.
3. Add copy that explains what authors should do next, especially when panels are empty.
4. Keep existing button names stable where tests and user flow depend on them, unless a test is updated first for a clearer user-facing label.

## Targeted UX changes

### Story Bible

Rename user-facing copy from mixed English/internal language toward author terms:

- `Story Bible` kicker becomes `故事圣经`.
- `正史资料` remains the tab title.
- Explain that edits become future-chapter writing canon and should be used for durable setting corrections.
- Replace `正史文本版本 1` with `设定修订：第 1 次`.
- Add edit-form help text: editing affects future drafts and records a world history note.

### World Archive / Export

Make archive/export copy more author-friendly:

- `World Archive` becomes `世界档案库`.
- `Snapshot #12` becomes `保存点 · 第 3 版` or a label-based equivalent; avoid showing raw snapshot IDs in normal success copy.
- Hide low-level export metadata such as `zip`, `base64`, and `files_are_inline` from visible success copy.
- Show useful language instead: `Obsidian ZIP 已准备好`, `包含 N 个 Markdown 文件`, `世界进度：第 N 版`, `生成时间：...`.
- Keep file paths visible in the preview selector/list because they are meaningful in the downloaded vault.
- In snapshot compare, localize object types/change types/field names instead of showing `character`, `changed`, `status`.

### World overview / Narrative Control

Keep the dashboard structure but soften internal product terms:

- `Narrative Control Center` becomes `下一章准备中心`.
- `Story Arc Planner` becomes `故事弧线规划`.
- Keep English-only strings out of author-facing headings where practical.
- Empty states should explain next action, not only say data is absent.

### Studio / Continuous Chapters

Reduce internal execution-context language:

- `本章执行上下文` becomes `本章写作依据`.
- `NCC 执行上下文` becomes `系统会在创建章节时保存本章写作依据`.
- `源世界版本：v2` becomes `依据的世界进度：第 2 版`.
- `世界进度 v1 → v2` becomes `世界进度：第 1 版 → 第 2 版`.
- Keep technical data in API payloads and tests where needed, but not as visible author copy.

## Testing strategy

Use TDD. Add/update focused frontend tests first, then implement:

1. `WorldArchivePanel.test.tsx`: export success hides raw archive fields and snapshot success hides `Snapshot #id`; compare uses Chinese labels for object/change/field names.
2. `WorldPage.test.tsx`: Story Bible heading/help text uses author-friendly copy and does not show English `Story Bible`; Narrative Control heading becomes author-facing.
3. `StudioPage.test.tsx`: context and settlement copy use `写作依据` / `第 N 版` formatting and avoid raw `vN` copy in those target areas.
4. Run the relevant test files, then broader frontend tests/build. Backend should not need tests because no backend code changes are planned.

## Safety

No backend behavior changes. No persistence changes. Raw IDs may remain in React keys, select values, API requests, and test setup; the cleanup targets visible copy only.
