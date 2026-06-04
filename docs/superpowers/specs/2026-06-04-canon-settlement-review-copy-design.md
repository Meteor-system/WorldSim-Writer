# Canon Settlement Review Copy Design

## Goal

Improve beginner beta-readiness in the approval/review loop by making the UI explain, in natural Chinese, what happened when a chapter was approved:

- whether imported material references were used;
- imported references are not formal canon by themselves;
- which approved chapter/canon/event settlement became formal history;
- no raw IDs, slugs, enum names, or English event labels in the user-facing review copy.

## Scope

Small MVP slice only. This design changes the frontend review/approval presentation and uses existing backend data already returned by chapter draft/history APIs.

In scope:

1. `StudioPage` post-approval settlement panel.
2. `ChapterHistoryPanel` approved chapter detail view.
3. Small formatting helpers for Chinese labels and readable change summaries.
4. Frontend tests proving the copy appears and raw event/change labels are hidden for the targeted review surfaces.

Out of scope:

- New backend tables or endpoints.
- Canon upgrade flow for imported candidates.
- Material selection UI.
- Broad redesign of Studio or World pages.
- Full i18n system.

## Selected approach

Use existing data and add a compact “审批结算说明” layer in the frontend.

### Why this approach

The current backend already preserves the necessary facts:

- `ChapterExecutionContext.material_references` says whether imported references informed the chapter context.
- `approvalPreview` and selected change indexes indicate what the user chose to settle.
- `WorldOverview.recent_events` confirms the approval event after approval.
- Chapter history detail exposes `execution_context`, `events`, `character_changes`, and `foreshadow_changes`.

A frontend-only presentation layer is the smallest high-value fix. It avoids changing canon semantics and keeps the sprint focused on beginner clarity.

## UI behavior

### Studio post-approval settlement panel

After approval, the “世界推进结算” panel should include a clear Chinese explanation:

- If material references were present in the frozen execution context:
  - “本章参考了 1 条导入素材：雨夜审讯。”
  - “导入素材仍是创作参考，没有自动写入正式 canon。”
- If no references were present:
  - “本章未使用导入素材参考。”
- Canon/event settlement:
  - “已写入正式章节。”
  - “正式事件：章节已批准并写入世界历史。”
  - “角色变化：1 条。”
  - “伏笔变化：1 条。”
  - “世界版本：第 1 版 → 第 2 版。”

The panel should keep the current action buttons: continue next chapter, view overview, export archive.

### Chapter history detail

The approved chapter detail should show a durable review explanation:

- an “审批结算说明” section;
- imported reference usage and non-canon boundary using titles/source names only;
- formal settlement summary in Chinese;
- readable character/foreshadow change cards without raw IDs or enum labels.

Examples:

- “导入素材参考：雨夜审讯（来源：旧设定.md）。”
- “这些导入素材只是本章创作参考，不代表已自动进入正式 canon。”
- “角色变化：林砚：状态由 active 调整为 开始调查密信；目标更新为 追查湿信来源。”
- “伏笔变化：裂纹玉佩：状态由 planted 调整为 advanced。”

For this MVP, status values inside nested `before/after` payloads can remain as persisted state words when there is no stable display dictionary yet, but the surrounding labels must be Chinese and object IDs/event enum strings must not be primary UI copy.

## Data flow

No new API contract is required.

- Studio gets material reference usage from `draft.execution_context ?? chapter.execution_context ?? launchContext.executionContext`.
- Studio gets settled counts from selected approval indexes and post-approval overview.
- Chapter history gets material reference usage from `selectedDetail.execution_context.material_references`.
- Chapter history gets formal event/change facts from existing `selectedDetail.events`, `character_changes`, and `foreshadow_changes`.

## Safety invariants

- Imported material references remain read-only context.
- The UI must not imply imported materials became formal canon.
- Formal canon/history changes remain tied only to chapter approval and selected projection changes.
- No backend mutation is added.

## Test plan

Frontend TDD tests:

1. `StudioPage.test.tsx`
   - After approving a draft with material references, the settlement panel states the draft used imported material references, lists the material title, says references did not automatically enter canon, and shows Chinese formal settlement/event copy.
2. `ChapterHistoryPanel.test.tsx`
   - Detail view shows “审批结算说明”, material reference usage, non-canon boundary, Chinese event copy, and readable change summaries.
   - Targeted assertions ensure raw `chapter_approved`, `character_change`, `foreshadow_change`, and `object #id` strings are absent from the new detail surface.

Backend verification:

- Run the existing chapter execution context/history tests to confirm backend still returns execution context and reference data.

Final verification:

- Relevant frontend tests.
- Relevant backend tests.
- `npm run build`.
- `git diff --check`.
