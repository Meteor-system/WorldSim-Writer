# Import Node P1 Safe References Design

## Goal

实现一个小而可测的 Import Node P1：用户确认导入的候选素材可以作为“创作参考”进入下一章准备台和章节执行上下文，从而影响后续章节创建与正文生成；但这些素材不会自动写入正式 canon、不会改写世界投影、不会递增世界版本。

## Context

P0 已提供素材导入预览、确认、候选资产持久化和导入批次审计。当前候选资产只在素材导入面板中可见，还没有进入下一章准备台、章节执行上下文或 Writer prompt。P1 需要补上这个安全引用链路，让导入素材能参与创作，而不是成为孤立记录。

## Recommended approach

采用“只读引用快照”方案：

1. 从 `import_candidate_assets` 读取当前世界最新候选资产。
2. 在 `GET /worlds/{world_id}/next-chapter-prep` 返回 `material_references`。
3. 前端下一章准备台展示这些参考，并明确提示“只是创作参考，不自动改写正式 canon”。
4. 当用户使用下一章准备台进入创作台时，`material_references` 跟随 `ChapterExecutionContext` 冻结。
5. Writer prompt 格式化执行上下文时写入这些参考，并再次声明它们不是正式 canon。

## Alternatives considered

### A. Directly merge candidate canon into `truth_canon`

不采用。它违反 Import Node 风险边界，会污染正式 canon，并绕过用户逐条确认。

### B. 新增独立“素材选择器”流程

暂不采用。它会增加筛选、勾选、状态流转和 UI 复杂度，不符合 24h MVP 的小切片目标。

### C. Read-only references through Next Chapter Prep

采用。它复用已有下一章准备台和执行上下文，最小化迁移与 UI 面积，同时可通过后端 prompt 捕获测试验证参考确实影响章节生成。

## Data contract

新增轻量引用结构 `material_references`：

- `asset_id`: 候选资产 ID，仅用于审计和调试，不在 UI 中作为主标签暴露。
- `batch_id`: 来源导入批次 ID。
- `asset_pool`: `canon | character | inspiration`。
- `title`: 候选标题。
- `summary`: 候选摘要。
- `raw_text`: 来源片段。
- `source_title`: 导入来源标题。
- `source_type`: `pasted_text | markdown | txt`。
- `created_at`: 候选创建时间。
- `safety_note`: 固定安全说明，强调参考不是正式 canon。

P1 只读取 `status='candidate'` 的候选资产，按最新优先取少量条目，避免 prompt 过长。

## Backend changes

- `app.import_node.service` 增加只读 helper，用于加载世界候选素材参考。
- `app.narrative_control_center.schemas.NextChapterPrepResponse` 增加 `material_references`。
- `app.narrative_control_center.service.get_next_chapter_prep()` 将候选素材引用加入 response，并在存在引用时追加 `source_signals=['import_material_reference']`。
- `app.narrative.schemas.ChapterExecutionContext` 增加 `material_references`。
- `app.narrative.service.format_execution_context_for_prompt()` 输出“导入素材参考（非正式 canon）”，告诉 Writer 可以参考但不能当作已写入正史。

## Frontend changes

- `src/api/types.ts` 增加 `ImportMaterialReference` 并扩展 `NextChapterPrepResponse` / `ChapterExecutionContext`。
- `src/world/chapterExecutionContext.ts` 将下一章准备台的素材引用复制到冻结上下文；手动上下文默认为空列表。
- `src/world/NextChapterPrepPanel.tsx` 展示“导入素材参考”区块和安全说明，避免 raw enum、slug 或裸 ID 成为用户主信息。
- `src/studio/StudioPage.tsx` 的执行上下文摘要展示素材参考数量和非 canon 说明，让用户在章节流中看见引用边界。

## Safety invariants

- Import P1 不新增会修改 `truth_canon` 的代码路径。
- Import P1 不递增 `world.world_version`。
- Import P1 不把候选资产状态改成正式 canon。
- Next Chapter Prep 只读候选资产，不写事件，不写世界投影。
- Writer prompt 明确区分“正式世界设定”和“导入素材参考”。

## Test plan

Backend RED/GREEN：

1. `test_next_chapter_prep_surfaces_imported_candidates_as_safe_material_references`
   - 确认导入候选素材。
   - 调用下一章准备台。
   - 断言 response 有 `material_references` 和 `import_material_reference` signal。
   - 断言 world canon 与 world_version 未变化。
2. `test_import_material_references_are_frozen_and_prompted_as_non_canon`
   - 将下一章准备台 response 作为执行上下文创建草稿。
   - 捕获 Writer prompt。
   - 断言 prompt 包含导入素材标题和非正式 canon 安全说明。

Frontend RED/GREEN：

1. `NextChapterPrepPanel` 渲染导入素材参考区块与安全说明。
2. 点击“用作下一章目标”时，callback 的 execution context 包含 `material_references`。
3. `StudioPage` 展示冻结执行上下文中的素材参考数量和非 canon 说明。

## Out of scope

- 不做候选资产逐条选择器。
- 不做候选资产状态升级为 canon。
- 不做真实文件上传。
- 不做 LLM 重新分类或 embedding 检索。
- 不做大规模 prompt packing 或向量召回。
