# Review Studio 2.0 Phase 3：Character Arc Tracking & Chapter Progression Hints 设计规格

**日期：** 2026-05-29  
**阶段：** Review Studio 2.0 Phase 3  
**目标：** 在现有章节草稿审核流程中加入“角色弧线追踪”和“下一章推进提示”，帮助用户判断当前章节是否推动了人物成长、关系变化和主线节奏，同时保持“只有用户批准才提交正式世界状态”的核心不变量。

---

## 1. 背景与问题

当前 Review Studio 2.0 已具备：

- Phase 1：草稿版本、暂存、手动编辑版本、段落重写/润色、diff、批准前世界状态变更预览。
- Phase 2：结构化 Critic 报告，包括节奏、张力、人物一致性、对白质量、结构、世界连续性、可读性等维度。

这些能力已经能帮助用户审稿和局部修订，但还缺少一个更偏“长篇写作控制台”的视角：

1. 某个角色在本章经历了什么变化？
2. 这些变化是否符合既定人物目标、状态和关系？
3. 本章是否真正推进了角色弧线，而不是只发生了情节事件？
4. 下一章应该优先推进哪条人物线、关系线或伏笔线？
5. 当前章节批准后，哪些角色状态变化会进入正式世界投影？

Phase 3 的目标是补上这层“连续章节写作导航”。它不替代 Critic 报告，而是在 Critic 之外提供更具体的角色弧线追踪和下一章写作提示。

---

## 2. 目标

### 2.1 用户目标

用户在 Review Studio 中查看章节草稿时，应能快速看到：

- 本章涉及哪些角色。
- 每个角色的当前状态、目标和可能变化。
- 本章对角色弧线的推进程度。
- 本章是否存在角色动机跳跃、成长断裂或关系变化缺少铺垫的问题。
- 系统建议下一章推进哪些角色、关系或伏笔。
- 这些提示与批准前的 proposed world-state changes 如何对应。

### 2.2 产品目标

- 提高长篇连载写作中的人物连续性。
- 帮助用户在批准章节前理解“剧情事件”与“人物成长”的关系。
- 为后续更完整的 Showrunner / Director / Critics pipeline 打基础。
- 避免引入复杂分支世界、多用户协作或外部知识库。

### 2.3 工程目标

- 复用现有 `Chapter`、`ChapterDraft`、`Character`、`CharacterRelation`、`Foreshadow`、`EventLog` 数据。
- 以只读分析为主，不在生成报告时修改正式世界状态。
- 报告可以存储在章节上，或以轻量 JSON 结构存储，便于前端重复读取。
- 与现有 Critic report API 和 Review Studio UI 风格保持一致。
- TDD 实现：先后端 API 测试，再前端组件测试，再集成到 StudioPage。

---

## 3. 非目标

Phase 3 不做以下内容：

- 不实现复杂角色弧线图数据库。
- 不实现多章节自动重写。
- 不自动批准或提交角色状态变化。
- 不让 LLM 直接修改 `Character`、`CharacterRelation` 或 `Foreshadow` 正式投影。
- 不实现多分支剧情树。
- 不做 Obsidian 导出。
- 不做完整 Showrunner 多代理流水线。
- 不引入 Redis、向量数据库或独立检索服务。
- 不做复杂可视化图表库；前端以卡片、列表和简单时间线为主。

---

## 4. 核心原则

### 4.1 审核优先，不自动提交

角色弧线报告和章节推进提示都属于 review metadata。它们可以帮助用户理解草稿，但不能改变正式世界状态。

只有用户执行 approve chapter 时，现有审批逻辑才可以提交：

- `ChapterDraft.proposed_changes.characters`
- `ChapterDraft.proposed_changes.foreshadows`
- 世界版本递增
- `EventLog` 写入

### 4.2 角色弧线基于当前投影 + 草稿提案

报告输入应包括：

- 当前世界版本。
- 当前角色列表。
- 当前角色关系。
- 当前伏笔列表。
- 当前章节草稿正文。
- 当前草稿 proposed changes。
- 近期事件日志。
- 可选：已批准章节数量与 story arc 摘要。

系统应明确区分：

- **当前正式状态**：已经批准并进入 projection 的角色状态。
- **本章拟提交变化**：草稿中 proposed changes 建议的角色/伏笔变化。
- **分析建议**：Arc report 认为下一章可以推进什么，但尚未成为 formal state。

### 4.3 与 Critic report 互补

Critic report 回答：“这章写得是否好？”

Character Arc report 回答：“这章是否推动了人物线？下一章应该怎么推进？”

两者可以互相引用，但 Phase 3 不要求 Critic report 作为前置条件。

---

## 5. 功能范围

### 5.1 Character Arc Report

新增角色弧线报告，按角色输出结构化分析。

每个角色条目包括：

- `character_id`
- `name`
- `role_type`
- `current_status`
- `current_goals`
- `presence_level`
  - `absent`
  - `mentioned`
  - `supporting`
  - `major`
- `arc_stage`
  - `setup`
  - `pressure`
  - `choice`
  - `consequence`
  - `growth`
  - `regression`
  - `resolution`
  - `unknown`
- `chapter_function`
  - 该角色在本章承担的叙事功能，例如“制造冲突”“揭示线索”“推动主角选择”。
- `observed_shift`
  - 从正文中观察到的变化，例如“从回避调查转向主动询问”。
- `proposed_state_change`
  - 与 draft proposed changes 对应的拟提交变化。
- `continuity_risk`
  - `none`
  - `low`
  - `medium`
  - `high`
- `risk_reason`
  - 风险说明，例如“本章结尾突然信任沈微霜，但前文缺少建立信任的桥段”。
- `suggested_revision`
  - 对当前草稿的修订建议。
- `next_chapter_setup`
  - 下一章可以如何继续推进该角色。

### 5.2 Relationship Progression Notes

在角色弧线报告中加入关系推进摘要。

每条关系提示包括：

- `source_character_id`
- `target_character_id`
- `source_name`
- `target_name`
- `relation_type`
- `current_intensity`
- `visibility`
- `chapter_shift`
  - 本章关系变化描述。
- `progression_hint`
  - 下一章建议推进方式。
- `risk_level`
  - `none` / `low` / `medium` / `high`
- `risk_reason`

Phase 3 不要求自动修改 `CharacterRelation`。如果未来要让关系变化进入 formal state，应作为后续 Phase 处理，并继续走 approval governance。

### 5.3 Chapter Progression Hints

新增章节推进提示，用于指导下一章或下一轮修订。

提示分为四类：

1. **角色线推进**
   - 哪个角色需要做出选择、承受后果、暴露秘密或改变目标。
2. **关系线推进**
   - 哪组关系需要升温、破裂、误解或和解。
3. **伏笔线推进**
   - 哪条伏笔应该 planted / advanced / resolved / delayed。
4. **主线节奏推进**
   - 下一章应该偏向调查、冲突、揭示、反转、喘息或高潮前铺垫。

每条提示包括：

- `hint_type`
  - `character`
  - `relationship`
  - `foreshadow`
  - `plot`
- `priority`
  - `low`
  - `medium`
  - `high`
- `title`
- `rationale`
- `suggested_next_beat`
- `related_character_ids`
- `related_foreshadow_ids`
- `can_seed_next_chapter_goal`
  - boolean，表示是否适合作为“下一章目标建议”。

### 5.4 Review Studio UI

在 `StudioPage` 的草稿审核区域新增一个 `CharacterArcPanel`。

Panel 显示：

- 顶部操作区：
  - `生成角色弧线报告`
  - `刷新角色弧线报告`
- 报告状态：
  - 关联 draft version。
  - 如果报告版本落后于当前 draft，显示 stale warning。
- 角色卡片：
  - 角色名、角色类型、出现程度、弧线阶段。
  - 当前状态和目标。
  - 本章观察到的变化。
  - 拟提交状态变化。
  - 连续性风险提示。
  - 修订建议。
  - 下一章铺垫建议。
- 关系推进区：
  - 关系变化、风险、下一章推进方式。
- 下一章提示区：
  - 按优先级排序。
  - 高优先级提示突出显示。
  - 可复制为下一章目标。

Phase 3 前端不需要复杂图表。用现有 card/list 风格即可。

---

## 6. 后端 API 设计

### 6.1 新增 endpoint

#### 生成角色弧线报告

```http
POST /chapters/{chapter_id}/character-arc-report
```

行为：

- 校验当前用户拥有该 chapter 所属 world。
- 获取当前最新 draft。
- 构建 LLM 输入消息。
- 调用 LLM 生成结构化报告。
- 校验报告结构。
- 保存到 `Chapter` 的 JSON 字段，或新建轻量 report 表。
- 不修改 world projection。
- 不写 `EventLog`。
- 返回 report。

建议响应模型：

```json
{
  "chapter_id": 11,
  "draft_version": 3,
  "current_draft_version": 3,
  "is_stale": false,
  "summary": "本章主要推进林砚从被动调查转向主动追问。沈微霜仍保持信息优势，但信任建立略显跳跃。",
  "character_arcs": [],
  "relationship_notes": [],
  "progression_hints": [],
  "created_at": "2026-05-29T00:00:00Z"
}
```

#### 读取角色弧线报告

```http
GET /chapters/{chapter_id}/character-arc-report
```

行为：

- 如果没有报告，返回 `404 NOT_FOUND`。
- 如果当前 draft version 高于报告 draft version，返回 `is_stale: true`。
- 不重新生成。

### 6.2 错误行为

- `401`：未登录。
- `403`：用户不拥有章节所属世界。
- `404`：章节不存在，或 GET 时报告不存在。
- `409 DRAFT_REQUIRED`：章节还没有草稿。
- `502 MODEL_RESPONSE_INVALID`：LLM 返回结构不符合 schema。

### 6.3 与现有 endpoint 的关系

Phase 3 不改变：

- `POST /chapters/{id}/critic-report`
- `GET /chapters/{id}/critic-report`
- `GET /chapters/{id}/approval-preview`
- `POST /chapters/{id}/approve`
- `POST /chapters/{id}/draft/paragraph`

Character arc report 可以在 UI 中和 Critic report 并列显示。

---

## 7. 数据模型设计

### 7.1 推荐方案：复用 Chapter JSON 字段

在 `Chapter` 上新增 JSON 字段：

```python
character_arc_report: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
```

优点：

- 与现有 `critique_report` 模式一致。
- 实现成本低。
- 报告与章节强绑定。
- 适合 MVP 阶段。

缺点：

- 不适合长期保存多版本 report 历史。
- 不方便跨章节查询角色弧线趋势。

### 7.2 暂不推荐：单独 CharacterArcReport 表

单独表适合未来做多版本报告历史和跨章节角色趋势查询，但 Phase 3 的主要目标是 Review Studio 内的单章审核辅助。为了控制风险，暂不引入新表。

### 7.3 Migration

新增 Alembic migration：

- `chapters.character_arc_report JSONB nullable`

SQLite 测试环境继续使用现有 JSONB shim 模式。

---

## 8. LLM Schema 设计

### 8.1 CharacterArcEntry

字段：

- `character_id: int`
- `name: str`
- `role_type: str | None`
- `current_status: str | None`
- `current_goals: list[str]`
- `presence_level: Literal['absent', 'mentioned', 'supporting', 'major']`
- `arc_stage: Literal['setup', 'pressure', 'choice', 'consequence', 'growth', 'regression', 'resolution', 'unknown']`
- `chapter_function: str`
- `observed_shift: str`
- `proposed_state_change: dict | None`
- `continuity_risk: Literal['none', 'low', 'medium', 'high']`
- `risk_reason: str | None`
- `suggested_revision: str | None`
- `next_chapter_setup: str | None`

### 8.2 RelationshipProgressionNote

字段：

- `source_character_id: int`
- `target_character_id: int`
- `source_name: str`
- `target_name: str`
- `relation_type: str`
- `current_intensity: int | None`
- `visibility: str | None`
- `chapter_shift: str`
- `progression_hint: str`
- `risk_level: Literal['none', 'low', 'medium', 'high']`
- `risk_reason: str | None`

### 8.3 ChapterProgressionHint

字段：

- `hint_type: Literal['character', 'relationship', 'foreshadow', 'plot']`
- `priority: Literal['low', 'medium', 'high']`
- `title: str`
- `rationale: str`
- `suggested_next_beat: str`
- `related_character_ids: list[int]`
- `related_foreshadow_ids: list[int]`
- `can_seed_next_chapter_goal: bool`

### 8.4 CharacterArcReport

字段：

- `summary: str`
- `character_arcs: list[CharacterArcEntry]`
- `relationship_notes: list[RelationshipProgressionNote]`
- `progression_hints: list[ChapterProgressionHint]`

后端 service 在持久化时补充：

- `chapter_id`
- `draft_version`
- `current_draft_version`
- `is_stale`
- `created_at`

---

## 9. LLM Prompt 输入

生成报告时，后端应构建 Chat Completions messages。

System message 要求：

- 你是长篇小说角色弧线编辑。
- 只输出 JSON。
- 不要编造不存在的 character_id、foreshadow_id 或 relation。
- 区分“正式当前状态”和“草稿拟提交变化”。
- 不要建议自动提交世界状态。

User message 包含：

- World title / genre / tone。
- Truth canon 摘要。
- Current world_version。
- Characters：id、name、role_type、status、current_goals、public_profile、hidden_traits。
- Relations：source、target、relation_type、intensity、visibility。
- Foreshadows：id、title、status、urgency_level、related_character_ids。
- Recent event logs。
- Chapter metadata。
- Draft version。
- Draft content。
- Proposed changes。

---

## 10. 前端组件设计

### 10.1 新增组件

```text
frontend/src/studio/CharacterArcPanel.tsx
```

职责：

- 接收 `CharacterArcReportResponse`。
- 展示角色弧线卡片。
- 展示关系推进提示。
- 展示下一章 progression hints。
- 暴露回调：
  - `onUseHintAsGoal(hintTitleOrBeat: string)` 可选。
  - `onReviseParagraph?(paragraphIndex, mode)` 不作为 Phase 3 必需能力，因为 arc report 不一定绑定段落。

### 10.2 StudioPage 集成

在已有 Review Studio 区域加入：

- `characterArcReport` state。
- `arcLoading` 或复用 `working`。
- `generateCharacterArcReport()` handler。
- 可选：draft 变化后尝试 `GET /character-arc-report`，如果 404 则静默不显示。

UI 位置建议：

1. 草稿正文和段落修订。
2. Diff / approval preview。
3. Critic Report。
4. Character Arc Report。

理由：用户先看正文和 formal-state preview，再看质量评价和角色推进建议。

### 10.3 API client

新增：

```typescript
export function generateCharacterArcReport(chapterId: number) {
  return apiRequest<CharacterArcReportResponse>(`/chapters/${chapterId}/character-arc-report`, {
    method: 'POST',
    body: '{}',
  });
}

export function getCharacterArcReport(chapterId: number) {
  return apiRequest<CharacterArcReportResponse>(`/chapters/${chapterId}/character-arc-report`);
}
```

### 10.4 TypeScript types

新增：

- `CharacterPresenceLevel`
- `CharacterArcStage`
- `ContinuityRisk`
- `CharacterArcEntry`
- `RelationshipProgressionNote`
- `ChapterProgressionHint`
- `CharacterArcReportResponse`

---

## 11. 用户流程

### 11.1 典型流程

1. 用户生成章节草稿。
2. 用户打开 Review Studio。
3. 用户查看 approval preview，确认草稿拟提交的世界状态变化。
4. 用户生成 Critic report，检查文学质量和结构问题。
5. 用户生成 Character Arc report。
6. 用户查看：
   - 角色弧线是否推进。
   - 是否有高风险连续性问题。
   - 下一章应该推进什么。
7. 用户根据建议进行段落重写、手动编辑或暂存。
8. 草稿版本变化后，旧 arc report 显示 stale warning。
9. 用户重新生成报告或批准章节。
10. 批准章节时仍只提交 proposed changes，不提交 report hints。

### 11.2 下一章目标提示

如果某条 progression hint 的 `can_seed_next_chapter_goal` 为 true，前端可以显示“可作为下一章目标”。

Phase 3 可以先只提供复制文本，不强制自动填入下一章创建表单。

---

## 12. 测试计划

### 12.1 后端测试

新增：

```text
backend/tests/test_character_arc_reports.py
```

测试用例：

1. `POST /chapters/{id}/character-arc-report` 生成结构化报告。
   - 返回 chapter_id、draft_version、summary。
   - 至少包含一个 character arc。
   - 不修改 world_version。
   - 不写 EventLog。

2. `GET /chapters/{id}/character-arc-report` 返回已保存报告。

3. 草稿版本变化后，GET 返回 `is_stale: true`。

4. 没有 report 时 GET 返回 404。

5. 没有 draft 时 POST 返回 409 `DRAFT_REQUIRED`。

6. LLM 返回不存在的 character_id 时，后端拒绝或过滤。
   - 推荐拒绝并返回 `MODEL_RESPONSE_INVALID`，避免误导用户。

### 12.2 LLM schema 测试

在 `backend/tests/test_llm_schemas.py` 或新文件中测试：

- 合法 character arc JSON 可以 parse。
- 缺少 summary 会失败。
- 非法 enum 会失败。
- score 不适用；本报告不需要总评分。

### 12.3 前端 API 测试

扩展：

```text
frontend/src/api/client.test.ts
```

测试：

- generate 调用 `POST /chapters/{id}/character-arc-report`。
- get 调用 `GET /chapters/{id}/character-arc-report`。

### 12.4 前端组件测试

新增：

```text
frontend/src/studio/CharacterArcPanel.test.tsx
```

测试：

- 渲染 summary。
- 渲染角色卡片。
- 渲染 stale warning。
- 高风险 continuity risk 显示警告样式。
- 渲染 relationship notes。
- 渲染 high priority progression hints。
- 点击复制/使用提示按钮调用 callback。

### 12.5 StudioPage 集成测试

扩展：

```text
frontend/src/studio/StudioPage.test.tsx
```

测试：

- 生成草稿后显示“生成角色弧线报告”按钮。
- 点击按钮后显示角色弧线报告。
- 如果报告 stale，显示版本落后提示。

---

## 13. 实现顺序建议

1. 后端 schema 测试：写 CharacterArcReport parser 的 RED 测试。
2. 后端 LLM schema：实现 parser 和 Pydantic models。
3. 后端 endpoint 测试：写 POST/GET report API RED 测试。
4. 后端 model/migration：给 Chapter 增加 `character_arc_report`。
5. 后端 service：实现 report 生成、保存、读取、stale 标记。
6. 后端 router：注册 POST/GET endpoints。
7. 前端 API 类型与 client 测试。
8. 前端 `CharacterArcPanel` 测试。
9. 前端 `CharacterArcPanel` 实现。
10. `StudioPage` 集成测试。
11. `StudioPage` 接入按钮、状态和 panel。
12. 全量回归：backend pytest + frontend test/build。

---

## 14. 风险与缓解

### 14.1 LLM 幻觉 character_id

风险：模型可能引用不存在的角色或伏笔。

缓解：后端校验所有 returned IDs 必须属于当前 world。非法则拒绝报告，返回 `MODEL_RESPONSE_INVALID`。

### 14.2 报告被误解为正式世界状态

风险：用户以为 progression hints 已经进入世界状态。

缓解：UI 明确标注：

- “这是审核建议，不会自动提交世界状态。”
- “只有批准章节才会提交 approval preview 中列出的 proposed changes。”

### 14.3 功能与 Critic report 重叠

风险：用户困惑两个报告的区别。

缓解：文案区分：

- Critic Report：文学质量与结构问题。
- Character Arc Report：人物弧线、关系推进、下一章方向。

### 14.4 UI 过载

风险：Review Studio 面板过多。

缓解：Phase 3 使用折叠区块或独立卡片，不默认展开所有细节。优先显示 summary、高风险项、高优先级 hints。

---

## 15. 验收标准

Phase 3 完成后，应满足：

- 用户可以在 Review Studio 为当前 chapter 生成角色弧线报告。
- 报告包含 character arcs、relationship notes、progression hints。
- 报告保存后可通过 GET 读取。
- 草稿版本变化后，旧报告显示 stale。
- 生成报告不会修改 world_version。
- 生成报告不会写 EventLog。
- 生成报告不会提交 character/relation/foreshadow projection changes。
- 前端能展示角色卡、关系推进和下一章提示。
- 高风险角色连续性问题有明显提示。
- 全部新增后端和前端测试通过。

---

## 16. 自检结果

- **范围检查：** 本设计聚焦 Review Studio Phase 3，不包含自动改写、多分支剧情、图数据库或 Showrunner 多代理流水线。
- **一致性检查：** 所有 report/hints 均为 review metadata，不改变正式 world projection，符合项目核心不变量。
- **可测试性检查：** 后端 API、LLM schema、前端 API client、Panel 组件和 StudioPage 集成都有明确测试路径。
- **风险检查：** 已覆盖 LLM ID 幻觉、报告误解为正式状态、与 Critic report 重叠、UI 过载四类主要风险。
