# Review Studio 2.0 Phase 2：Critic Reports 设计规格

## 目标

在现有 Review Studio 草稿审核流程中加入基础“文学/结构 Critic 报告”，帮助用户在批准章节前发现节奏、张力、人物一致性、对白质量和世界观一致性问题。Critic 只提供诊断与修改建议，不自动提交世界状态变化；正式世界状态仍只在用户批准章节时提交。

## 评价维度

Critic 报告使用结构化评分与问题列表，首版覆盖以下维度：

1. **节奏 pacing**
   - 评估场景推进是否拖沓或跳跃。
   - 检查叙述、动作、对白、信息揭示之间的比例。

2. **张力 tension**
   - 评估章节是否有清晰冲突、悬念或情绪压力。
   - 检查关键段落是否推动危机升级。

3. **人物一致性 character_consistency**
   - 评估角色行为、目标、语气是否符合当前世界状态与角色设定。
   - 标记与角色身份、当前目标、已知关系冲突的段落。

4. **对白质量 dialogue_quality**
   - 评估对白是否自然、有角色区分度、是否承担推进剧情或揭示信息的功能。
   - 标记解释性过强、角色声音趋同或缺少潜台词的问题。

5. **结构清晰度 structure**
   - 评估章节开端、转折、高潮/钩子是否清晰。
   - 检查段落之间是否有因果连接。

6. **世界观/伏笔一致性 world_continuity**
   - 检查是否违背当前 canon、角色状态、关系、伏笔状态。
   - 标记可能需要调整 proposed_changes 的地方，但 Critic 本身不修改 proposed_changes。

7. **可读性 readability**
   - 评估语言是否顺畅、句式是否过密、信息负载是否过高。

每个维度返回：

- `score`: 0-100
- `summary`: 简短评价
- `issues`: 问题列表
- `suggestions`: 修改建议列表

问题项字段：

- `severity`: `low | medium | high`
- `dimension`: 维度名
- `message`: 问题说明
- `paragraph_index`: 可选，0-based 段落索引
- `suggested_action`: 可选，建议动作，例如“重写本段”“润色对白”“补强冲突”

## API 设计

### 1. 生成 Critic 报告

`POST /chapters/{chapter_id}/critic-report`

行为：

- 读取当前章节最新 draft version。
- 读取世界当前投影：角色、关系、伏笔、近期事件、story arc。
- 调用 LLM Critic，要求返回结构化 JSON。
- 将报告保存到 `Chapter.critique_report` 或新增 draft-scoped report 字段。
- 不修改 `ChapterDraft.proposed_changes`。
- 不递增 `world_version`。
- 不写正式 `EventLog`，除非未来增加非正式审稿事件类型。

请求体首版可为空：

```json
{}
```

响应：

```json
{
  "chapter_id": 12,
  "draft_version": 3,
  "overall_score": 78,
  "summary": "章节冲突清晰，但第二段信息揭示偏快，对白可更有潜台词。",
  "dimensions": {
    "pacing": {
      "score": 72,
      "summary": "中段推进略快。",
      "issues": [],
      "suggestions": ["放慢第二段的信息揭示。"]
    }
  },
  "issues": [
    {
      "severity": "medium",
      "dimension": "dialogue_quality",
      "message": "第二段对白解释性较强。",
      "paragraph_index": 1,
      "suggested_action": "润色本段对白，增加潜台词。"
    }
  ],
  "suggestions": ["优先重写第二段对白。"],
  "created_at": "2026-05-29T00:00:00Z"
}
```

### 2. 获取当前 Critic 报告

`GET /chapters/{chapter_id}/critic-report`

行为：

- 返回当前章节最新已保存 Critic 报告。
- 如果没有报告，返回 `404 NOT_FOUND` 或 `{ "critic_report": null }`；首选 `404`，保持 API 语义清晰。

### 3. 与现有 endpoint 的关系

现有 `POST /chapters/{chapter_id}/critique` 可以二选一处理：

- **推荐**：保留旧 endpoint 作为兼容别名，内部调用新的 Critic report service。
- 新前端使用 `/critic-report`，旧调用不立即删除。

## 前端 UI 设计

在 `StudioPage` 的 Review Studio 区域新增“文学/结构 Critic 报告”面板。

### 入口

- 在草稿操作区增加按钮：`生成 Critic 报告`。
- 按钮位置靠近：`暂存当前草稿`、`保存修改`、段落级重写/润色。
- 点击后显示 loading 状态：`Critic 正在审稿…`。

### 报告展示

面板内容：

1. **总评分与摘要**
   - 显示 `overall_score`。
   - 显示一句总评 `summary`。

2. **维度评分卡片**
   - pacing / tension / character_consistency / dialogue_quality / structure / world_continuity / readability。
   - 每张卡显示分数、摘要、1-3 条建议。

3. **问题列表**
   - 按 severity 排序：high → medium → low。
   - 显示维度、问题说明、段落编号。
   - 如果有 `paragraph_index`，提供快捷按钮：
     - `重写相关段落`
     - `润色相关段落`
   - 按钮复用 Phase 1 的 paragraph rewrite/polish endpoint。

4. **批准前提示**
   - 如果存在 high severity 问题，在批准按钮附近显示提示：
     - `Critic 发现高风险问题，建议修订后再批准。`
   - 首版只提示，不强制阻止批准。

## 与现有 Review Workflow 的集成

Phase 2 集成点：

1. 用户生成章节 draft。
2. Review Studio 显示草稿、proposed changes、diff、approval preview。
3. 用户点击 `生成 Critic 报告`。
4. Critic 读取当前 draft + 当前世界投影，生成结构化报告。
5. 用户根据报告选择：
   - 手动编辑整篇草稿。
   - 对具体段落执行 rewrite/polish。
   - 忽略建议并继续批准。
6. 每次手动编辑、stash、paragraph rewrite/polish 后：
   - 旧 Critic 报告仍可展示为“上一版报告”，但标记为 `可能已过期`。
   - 推荐首版简单处理：如果 `report.draft_version !== draft.draft_version`，UI 显示 `报告来自 vX，当前草稿为 vY，请重新生成。`
7. 用户批准章节时：
   - 只提交当前 draft 的 content 和 proposed_changes。
   - Critic report 不改变世界状态提交逻辑。

## 数据模型建议

首版优先复用现有 `Chapter.critique_report` JSON 字段，降低迁移成本。

报告 JSON 必须包含：

- `draft_version`
- `overall_score`
- `summary`
- `dimensions`
- `issues`
- `suggestions`
- `created_at`

如果后续需要多版本报告历史，再新增 `chapter_critic_reports` 表；Phase 2 不引入该表。

## 测试计划

### 后端

- `POST /chapters/{id}/critic-report` 为最新 draft 生成报告。
- 报告包含全部核心维度。
- 生成报告不修改 world projection、不递增 `world_version`。
- draft 版本变化后，旧报告的 `draft_version` 与当前 draft 不一致。
- 旧 `/critique` endpoint 仍兼容。

### 前端

- 生成 draft 后显示 `生成 Critic 报告` 按钮。
- 点击按钮后展示总评分、维度卡片、问题列表。
- 带 `paragraph_index` 的 issue 显示段落 rewrite/polish 快捷按钮。
- 当报告 draft version 过期时显示过期提示。
- high severity issue 显示批准前提醒。

## 非目标

Phase 2 不做：

- 自动重写整章。
- 自动修改 proposed_changes。
- 强制阻止批准。
- 多 Critic 角色投票。
- 独立 critic report 历史表。
- 复杂可视化评分仪表盘。
