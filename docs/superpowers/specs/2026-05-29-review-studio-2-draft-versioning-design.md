# Review Studio 2.0 Phase 1：草稿版本化与局部编辑设计

日期：2026-05-29

## 目标

本阶段把现有创作台从“生成一版草稿后整章编辑/通过”的基础审稿页，升级为可持续改稿的 Review Studio 2.0 Phase 1。重点是草稿版本化、手动编辑留痕、段落级重写/润色、版本差异查看，以及通过前明确展示即将写入世界状态的变更。

必须保持 WorldSim-Writer 的核心不变量：草稿生成、保存、手动编辑、局部改写和局部润色都只改变草稿缓存，不改变正式世界状态、不递增 `world_version`、不写正式 `EventLog`。只有用户点击“通过并更新世界”时，才在事务中提交章节正文、世界状态变化和事件历史。

## 当前上下文

当前代码已经具备：

- `Chapter` 与 `ChapterDraft` 模型，其中 `chapter_drafts` 已有 `(chapter_id, draft_version)` 唯一约束。
- `Chapter.draft_version` 指向当前草稿版本。
- `PUT /chapters/{chapter_id}/draft` 已支持整章手动编辑，但目前是在原 `ChapterDraft` 行上直接覆盖内容，没有形成新版本。
- `POST /chapters/{chapter_id}/approve` 会读取当前 `draft_version` 对应的最新草稿，并把其中 `content` 与 `proposed_changes` 正式提交。
- 前端 `StudioPage.tsx` 已有编辑正文、保存修改、展示 proposed changes、Critic 报告和审批按钮。

因此，本阶段优先复用现有 `ChapterDraft` 表和审批事务，不引入全新的草稿事件流或复杂版本树。

## 范围

### 本阶段包含

1. 草稿保存/暂存：用户可以显式保存当前草稿状态，形成一个新的草稿版本快照。
2. 手动编辑版本化：用户整章编辑后保存时，不覆盖旧版本，而是创建新的 `ChapterDraft` 版本。
3. 段落级重写/润色：用户选择某个段落，只重新生成该段落，并保存为新的草稿版本。
4. 当前版本 vs 上一版本 diff：前端展示当前草稿与前一草稿之间的差异。
5. 通过前世界状态变更预览：审批按钮附近展示本次通过会提交的角色、伏笔和世界版本变化摘要。

### 本阶段不包含

- 多分支草稿树。
- 版本合并。
- 段落级结构化存储表。
- CodeMirror 或复杂富文本编辑器。
- 批注系统。
- 自动保存。
- 对 proposed changes 的手动编辑。
- 审批事务模型重写。
- 地图、Obsidian、快照/分支世界。

## 设计决策

### 推荐方案：线性草稿版本链

采用线性版本链：每次保存、整章手动编辑、段落重写或段落润色，都会创建 `draft_version + 1` 的 `ChapterDraft` 行，并更新 `Chapter.draft_version` 指向新版本。

优点：

- 与现有 `chapter_drafts` 表和唯一约束天然匹配。
- 不需要新增复杂版本树模型。
- 审批逻辑基本不变：仍然审批当前 `Chapter.draft_version`。
- 测试和 UI 都更容易验证。

取舍：

- 不能表达“从旧版本分叉出另一个候选稿”。这是 Phase 2 或更后续能力。
- 段落编辑仍以整篇 `content` 字符串保存新版本，而不是把正文拆成段落对象。

## 后端设计

### 数据模型

复用现有 `ChapterDraft`，增加少量元数据字段以支持版本解释和 diff 展示。

建议新增字段：

- `change_type: String(40)`：版本来源。
  - `generated`：Writer 生成。
  - `stash`：用户显式暂存。
  - `manual_edit`：用户整章手动编辑。
  - `paragraph_rewrite`：段落级重写。
  - `paragraph_polish`：段落级润色。
- `change_summary: Text | None`：面向用户的简短说明，例如“手动保存草稿”“重写第 3 段”。
- `parent_draft_version: Integer | None`：上一版本号。线性版本中通常等于 `draft_version - 1`，显式保存便于未来扩展和测试。

不新增独立 `draft_events` 表。当前阶段的审稿版本属于草稿缓存，不作为正式世界事件。

### 迁移

新增 Alembic migration：

- 给 `chapter_drafts` 添加 `change_type`，非空，默认 `'generated'`。
- 添加 `change_summary`，可空。
- 添加 `parent_draft_version`，可空。
- 回填已有草稿：`change_type='generated'`，`parent_draft_version=NULL`。
- 如项目现有 JSONB migration 风格会移除 server default，则保持一致。

### Schema

新增/调整 Pydantic schemas：

- `DraftVersionSummary`
  - `draft_id`
  - `draft_version`
  - `change_type`
  - `change_summary`
  - `parent_draft_version`
  - `source_world_version`
- `DraftResponse` 增加：
  - `draft_version`
  - `change_type`
  - `change_summary`
  - `parent_draft_version`
  - `previous_draft_version`
- `StashDraftRequest`
  - `note: str | None`
- `EditDraftRequest`
  - `content: str`
  - `change_summary: str | None`
- `ParagraphReviseRequest`
  - `paragraph_index: int`
  - `instruction: str | None`
  - `mode: 'rewrite' | 'polish'`

### API

保留现有接口并扩展行为：

#### 整章手动编辑

```http
PUT /chapters/{chapter_id}/draft
```

行为变化：

- 以前：覆盖当前 `ChapterDraft.content`。
- 现在：创建一个新的 `ChapterDraft` 行，版本号 `current + 1`。
- 新版本继承上一版本的：
  - `context_summary`
  - `review_hints`
  - `proposed_changes`
  - `source_world_version`
  - `rejection_feedback=NULL`
- `change_type='manual_edit'`。
- `change_summary` 使用请求中的说明；为空时默认“手动编辑正文”。
- 更新 `Chapter.draft_version`。
- 不改变 `world_version`，不写 `EventLog`。

#### 显式暂存当前草稿

```http
POST /chapters/{chapter_id}/draft/stash
```

用途：在用户开始编辑前，显式保存当前草稿状态。

行为：

- 读取当前最新草稿。
- 创建内容完全相同的新版本。
- `change_type='stash'`。
- `change_summary` 默认为“暂存当前草稿”。
- 更新 `Chapter.draft_version`。
- 返回新的 `DraftResponse`。

说明：即使内容未变化，也允许暂存形成快照。这样用户可以在后续 diff 中看到“从暂存版本开始改动”。

#### 段落级重写/润色

```http
POST /chapters/{chapter_id}/draft/paragraph
```

请求：

```json
{
  "paragraph_index": 2,
  "mode": "rewrite",
  "instruction": "让这一段更紧张，减少解释"
}
```

段落切分规则：

- 后端以空行分段：使用连续空白行作为段落边界。
- `paragraph_index` 使用 0-based index。
- 如果索引越界，返回 `400 INVALID_PARAGRAPH_INDEX`。
- 生成后保持原段落顺序，只替换目标段落。

LLM 行为：

- 新增 `LLMClient.revise_paragraph(messages)`。
- mock 模式返回可预测文本，便于测试。
- 非 mock 模式调用 OpenAI-compatible Chat Completions。
- 模型只返回 JSON：

```json
{
  "paragraph": "改写后的单段文本",
  "revision_note": "修改说明"
}
```

版本行为：

- 创建新的 `ChapterDraft`。
- `change_type='paragraph_rewrite'` 或 `paragraph_polish`。
- `change_summary` 默认为“重写第 N 段”或“润色第 N 段”，如模型返回 `revision_note` 可追加。
- 继承上一版 `proposed_changes`。
- 不改变世界状态。

#### 获取草稿版本列表

```http
GET /chapters/{chapter_id}/drafts
```

返回按 `draft_version` 降序排列的版本摘要，用于前端版本选择和展示。

#### 获取当前 vs 上一版 diff

```http
GET /chapters/{chapter_id}/draft/diff
```

返回：

```json
{
  "chapter_id": 1,
  "current_version": 4,
  "previous_version": 3,
  "current_content": "...",
  "previous_content": "...",
  "diff_lines": [
    { "type": "unchanged", "text": "..." },
    { "type": "removed", "text": "..." },
    { "type": "added", "text": "..." }
  ]
}
```

实现使用 Python 标准库 `difflib`，按行 diff。前端不负责计算核心 diff，只负责渲染。

如果当前版本没有上一版，返回 `previous_version=null`、`diff_lines=[]`。

#### 审批预览

```http
GET /chapters/{chapter_id}/approval-preview
```

返回通过当前草稿会提交的正式变更摘要：

```json
{
  "chapter_id": 1,
  "draft_version": 4,
  "source_world_version": 1,
  "current_world_version": 1,
  "will_increment_world_version": true,
  "world_version_before": 1,
  "world_version_after": 2,
  "version_conflict": false,
  "character_changes": [
    {
      "character_id": 1,
      "name": "林砚",
      "before": { "status": "active", "current_goals": [] },
      "after": { "status": "获得预言古书", "current_goals": ["追查密道"] }
    }
  ],
  "foreshadow_changes": [
    {
      "foreshadow_id": 1,
      "title": "裂纹玉佩",
      "before": { "status": "planted", "description": "..." },
      "after": { "status": "advanced", "description": "...审核备注..." }
    }
  ],
  "warnings": []
}
```

预览必须复用审批路径中的校验逻辑或共享 helper，避免出现“预览说能通过，审批实际失败”的分叉规则。

如果世界版本已变化：

- `version_conflict=true`
- `will_increment_world_version=false`
- `warnings` 包含 `WORLD_VERSION_MISMATCH`
- 前端禁用审批按钮或提示用户重新生成/调整草稿。

### 服务层边界

在 `backend/app/narrative/service.py` 中增加小型 helper：

- `_create_draft_version(...)`：负责创建新 `ChapterDraft`、递增 `chapter.draft_version`、继承元数据。
- `_split_paragraphs(content)`：按空行分段，并保留重组格式。
- `_build_approval_preview(...)`：复用审批前的变更解析和 before/after 计算。

建议把审批中解析 `character_changes` 与 `foreshadow_changes` 的逻辑抽出，供 `approve_chapter()` 与 `approval_preview()` 共用。

## LLM 设计

新增 schema：

- `ParagraphRevision`
  - `paragraph: str`
  - `revision_note: str | None`

新增 parser：

- `parse_paragraph_revision(raw_text)`

新增 prompt builder：

- `build_paragraph_revision_messages(world, chapter, draft, paragraph, mode, instruction)`

Prompt 要求：

- 只改写用户选中的段落。
- 不新增多个段落。
- 不改变未选中段落事实。
- 不提交或暗示正式世界状态变化。
- `rewrite` 偏结构、动作、信息重组。
- `polish` 偏语言、节奏、气质优化。
- 输出严格 JSON，不使用 Markdown/code fence。

## 前端设计

### API 类型与 client

在 `frontend/src/api/types.ts` 增加：

- `DraftVersionSummary`
- `DraftDiffLine`
- `DraftDiffResponse`
- `ApprovalPreviewResponse`
- `ParagraphReviseRequest`

在 `frontend/src/api/client.ts` 增加：

- `stashDraft(chapterId, data)`
- `editDraft(chapterId, data)`
- `reviseParagraph(chapterId, data)`
- `getDrafts(chapterId)`
- `getDraftDiff(chapterId)`
- `getApprovalPreview(chapterId)`

### StudioPage 交互

现有 `StudioPage.tsx` 已经偏大。本阶段允许先在同一文件内实现，但建议抽出轻量组件，避免继续膨胀：

- `DraftVersionPanel`
- `DraftDiffView`
- `ApprovalPreviewPanel`
- `ParagraphEditorPanel`

如时间有限，至少把 diff 和 approval preview 拆成独立组件。

### 草稿暂存

在正文区域按钮组增加：

- `暂存当前草稿`

点击后：

- 调用 `POST /chapters/{id}/draft/stash`。
- 更新当前 `draft`。
- 刷新版本列表和 diff。
- 显示新版本号，例如“当前草稿：v3”。

### 手动编辑版本化

现有“编辑正文 / 保存修改”保留，但保存逻辑改为调用版本化接口。

保存成功后：

- 当前 `draft` 指向新版本。
- 退出编辑模式。
- Critic 报告清空，因为正文已变化。
- 刷新 diff。
- 显示“已保存为 vN”。

### 段落级重写/润色

前端以空行切分当前 `draft.content` 并显示段落卡片。每段提供：

- `重写本段`
- `润色本段`
- 可选指令输入框，默认空。

点击后：

- 调用 `POST /chapters/{id}/draft/paragraph`。
- 后端返回新草稿版本。
- 前端更新正文、版本号和 diff。
- 清空 Critic 报告。

错误处理：

- LLM 超时显示 `MODEL_TIMEOUT` 或格式化错误。
- 索引越界显示“段落不存在，请刷新后重试”。
- 已审批章节不允许再改，显示 `ALREADY_APPROVED`。

### Diff 视图

在草稿正文下方增加“查看与上一版差异”区块。

展示规则：

- `added`：绿色浅底。
- `removed`：红色浅底并删除线。
- `unchanged`：普通 manuscript 样式或折叠显示。

Phase 1 默认只做当前 vs 上一版，不做任意版本对比。

### 审批前状态变化预览

将现有“世界状态变化”展示升级为“通过后将提交”。位置应靠近“通过并更新世界”按钮。

内容包括：

- 当前草稿版本。
- 世界版本从 `before` 到 `after`。
- 角色变化：角色名、字段、before/after。
- 伏笔变化：伏笔名、状态变化、备注追加。
- 如无 proposed changes，显示“通过后只会提交章节正文和世界版本递增，不会改变角色/伏笔投影”。
- 如果 `version_conflict=true`，显示红色警告并禁用审批按钮。

## 状态一致性规则

- 新草稿版本的 `source_world_version` 继承上一版。
- 手动编辑和段落改写不会重新计算 proposed changes。
- 审批预览和审批都基于当前 `Chapter.draft_version`。
- 如果手动编辑改变了正文但 proposed changes 仍来自旧生成结果，前端必须明确提示：
  - “状态变更仍来自当前草稿携带的结构化提案；如正文已大幅改变，请重新生成 Critic 或重新生成正文。”
- 本阶段不允许编辑 proposed changes，避免在 UI 中绕过后端校验。

## 错误处理

新增错误码：

- `DRAFT_REQUIRED`：章节没有可编辑草稿。
- `ALREADY_APPROVED`：已审批章节不能再编辑。
- `INVALID_PARAGRAPH_INDEX`：段落索引无效。
- `MODEL_TIMEOUT`：段落重写/润色超时。
- `MODEL_RESPONSE_INVALID`：模型没有返回合法段落 JSON。
- `WORLD_VERSION_MISMATCH`：审批预览或审批发现世界版本冲突。

所有草稿写操作失败时不得创建半版本。如果 LLM 成功但保存失败，应整体回滚。

## 测试策略

必须按 TDD 实施：先写失败测试，再实现最小代码。

### 后端测试

新增或扩展 `backend/tests/test_narrative_draft_versioning.py`。

覆盖：

1. 手动编辑创建新版本
   - 初始草稿 v1。
   - `PUT /chapters/{id}/draft` 后返回 v2。
   - v1 内容仍保留。
   - `Chapter.draft_version == 2`。
   - `world_version` 不变。
   - 不新增 `EventLog`。

2. 暂存创建相同内容的新版本
   - `POST /draft/stash` 后版本 +1。
   - 新旧内容相同。
   - `change_type='stash'`。

3. 段落级重写只替换目标段落
   - 给定三段正文。
   - fake LLM 返回新段落。
   - 只有目标段落变化。
   - 创建新版本。

4. 段落索引越界
   - 返回 `400 INVALID_PARAGRAPH_INDEX`。
   - 不创建新版本。

5. diff 返回当前 vs 上一版
   - v1/v2 内容不同。
   - diff 中包含 added/removed。

6. 审批使用当前版本
   - v1 生成后手动编辑为 v2。
   - 审批后 `approved_version == 2`，`approved_content == v2.content`。

7. 审批预览
   - 返回 world version before/after。
   - 返回 character/foreshadow before/after。
   - 版本冲突时 `version_conflict=true`。

8. 已审批章节不可编辑
   - 对 approved chapter 调用 stash/edit/paragraph revise 均返回 `409 ALREADY_APPROVED`。

### LLM/schema 测试

覆盖：

- `parse_paragraph_revision` 接受合法 JSON。
- 拒绝缺少 `paragraph`、空 `paragraph` 或非 JSON。
- mock `revise_paragraph` 返回稳定结果。

### 前端测试/验证

当前前端测试较少，本阶段最低要求：

- `npm run build` 通过。
- 若轻量可行，新增 Vitest 覆盖 API client helper 的 path/body。

手动验收：

1. 创建章节并生成正文。
2. 点击“暂存当前草稿”，看到版本号增加。
3. 进入编辑正文，修改后保存，看到版本号再次增加。
4. 查看 diff，看到当前版相对上一版的增删内容。
5. 选择某段点击“润色本段”，只替换该段并生成新版本。
6. 查看“通过后将提交”，确认角色/伏笔变化与世界版本变化清楚展示。
7. 点击通过，确认正式世界状态只在此时更新。

## 验证命令

后端：

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest -v'
```

前端：

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

## 实施顺序建议

1. 后端测试：草稿版本化、暂存、diff、审批当前版本。
2. 后端实现：迁移、schema、service helper、router。
3. 后端测试：段落级重写/润色与 LLM parser。
4. 后端实现：paragraph revision LLM client 与 endpoint。
5. 后端测试：approval preview。
6. 后端实现：preview helper 与 endpoint。
7. 前端类型和 API client。
8. 前端 StudioPage/组件更新。
9. 全量验证。

## 后续 Phase 2 预留

- 任意两个版本 diff。
- 版本回退。
- 草稿版本树。
- 批注和修改原因。
- proposed changes 可视化编辑。
- 段落级持久化对象。
- 自动保存和冲突恢复。
