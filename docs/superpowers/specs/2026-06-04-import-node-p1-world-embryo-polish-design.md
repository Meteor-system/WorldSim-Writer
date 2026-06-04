# Import Node P1 World Embryo Polish Design

## Goal

Make imported candidate materials visible and safely usable in the beginner three-minute/world-embryo loop without automatically writing formal canon.

The small MVP outcome:

- after a user confirms imported candidate materials, the newcomer loop refreshes and surfaces those materials as “创作参考”;
- the first-chapter/world-embryo launch area explains that references can guide the next draft but are not formal canon;
- using the launch button carries the references into the existing frozen chapter execution context;
- UI copy is low-cognitive Chinese and avoids raw IDs, slugs, and enum labels.

## Scope

In scope:

1. Refresh next-chapter/reference data after an import is confirmed.
2. Show imported material references in the world overview beginner launch area.
3. Let the first-chapter/story-arc launch context carry material references safely into Studio.
4. Keep the backend safety invariant covered by tests: confirmed import candidates remain candidates and do not mutate `truth_canon` or `world_version`.
5. Add frontend tests for the newcomer/world-embryo loop and import confirmation refresh.

Out of scope:

- Canon upgrade/promotion workflow.
- User selection/deselection of individual references.
- Editing world seed payloads with imported material.
- New database schema.
- Embedding/vector retrieval.
- Broad UI redesign.

## Selected approach

Use the existing `NextChapterPrepResponse.material_references` data as the safe reference bridge.

### Why

The previous Import Node P1 slice already established the safe backend path: imported candidate assets appear as read-only material references in Next Chapter Prep and can be frozen into a chapter execution context. The missing MVP polish is visibility and freshness in the beginner path.

This design keeps the import and canon boundaries intact:

- import confirmation writes only candidate assets and import audit records;
- next-chapter prep reads those candidates as references;
- the first-chapter/world-embryo launch UI shows them as references;
- Studio receives them only inside `ChapterExecutionContext.material_references`.

## UI behavior

### Import confirmation

After confirming an import, `WorldImportPanel` still shows its local success state, but it also notifies the parent page.

WorldPage responds by reloading the Narrative Control Center data for the current world. This makes the imported references appear in the next-chapter/world-embryo loop without the user refreshing the page.

Copy remains simple:

- “已写入候选素材。”
- “这些素材会作为创作参考出现在下一章准备区，不会自动改写正式 canon。”

No batch IDs are shown in the success message.

### First Chapter Launchpad

When `nextPrep.material_references` has references, the launchpad shows a compact “导入素材参考” block:

- “已准备 1 条导入素材参考。”
- material titles and source titles, e.g. “雨夜审讯（来源：旧设定.md）”;
- “这些素材只会随下一章目标进入创作台，不会自动写入正式 canon。”

If references are empty, no extra block is shown.

### Launching Studio from a story arc/world embryo chapter

`buildStoryArcExecutionContext()` accepts safe material references and copies them into `ChapterExecutionContext.material_references`.

This lets imported references influence drafting prompts through the existing execution context path while preserving the invariant that only chapter approval writes formal canon/history.

## Backend behavior

No new backend production code is required for this small slice.

Add/extend backend tests to cover the safety guarantee in the world-embryo/import path:

- importing into a newly created seed/template world leaves `truth_canon` unchanged;
- `world_version` does not increment;
- candidate assets remain `candidate`;
- event history records import audit but no canon settlement event.

## Data flow

1. User creates or opens a world embryo/world.
2. User imports pasted material in `WorldImportPanel`.
3. Import confirm persists candidate assets only.
4. `WorldImportPanel` calls `onConfirmed`.
5. `WorldPage` reloads Narrative Control Center data.
6. `nextPrep.material_references` appears in the launchpad and Next Chapter Prep.
7. Launching Studio from the story-arc/embryo goal freezes references into `ChapterExecutionContext`.

## Safety invariants

- Imported materials are candidate references, not formal canon.
- Import confirmation does not mutate `truth_canon`.
- Import confirmation does not increment `world_version`.
- Launching Studio with references does not write events.
- Only chapter approval writes formal canon/history.

## Test plan

Backend:

- Extend `tests/test_import_node.py` with a seed/template-world import safety assertion covering canon/version/status/event boundary.

Frontend:

- `WorldImportPanel.test.tsx`: after confirmation, success copy avoids batch IDs and says the material will appear as reference, then invokes `onConfirmed`.
- `WorldPage.test.tsx`: when Next Chapter Prep returns material references, the First Chapter Launchpad shows low-cognitive Chinese reference copy and launching Studio from the story-arc/embryo goal passes `material_references` in the execution context.
- `WorldPage.test.tsx`: confirming import refreshes Narrative Control Center data so newly imported references can appear without page reload.

Final verification:

- Relevant backend tests.
- Relevant frontend tests.
- `npm run build`.
- `git diff --check`.
