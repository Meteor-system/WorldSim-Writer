# Narrative Control Center 1.0 设计规格

**阶段名称：** Narrative Control Center 1.0  
**范围：** Approved Chapter History + Next Chapter Prep Panel  
**目标：** 将已经完成的章节生成、Review Studio、world-state approval、Critic report、Character Arc report 与 EventLog 串成一个长篇写作控制台，让用户在“批准这一章之后”能清楚理解历史、后果、风险，并准备下一章。

---

## 1. 背景

WorldSim-Writer 当前已经具备稳定的本地 MVP 写作闭环：

1. 用户创建世界。
2. 系统生成章节草稿。
3. 用户在 Review Studio 中审核、暂存、编辑、重写段落、查看 diff。
4. Critic report 检查文学与结构问题。
5. Character Arc report 检查角色弧线、关系推进与下一章提示。
6. 用户批准章节。
7. 后端在同一事务中提交正式 world-state projection 和 EventLog。

这些能力已经解决了“单章怎么生成和审核”的问题。

下一阶段的核心问题是：

> 章节批准后，用户如何快速理解“已经发生了什么、正式改变了什么、下一章应该写什么”？

Narrative Control Center 1.0 要补上这层长篇叙事控制能力。

---

## 2. 设计目标

### 2.1 用户目标

用户应能在 World Overview 或 Studio 附近看到：

- 已批准章节历史。
- 每章批准的正文摘要和版本信息。
- 每章造成的角色、伏笔、世界版本变化。
- 最近发生的正式事件。
- 下一章建议目标。
- 下一章优先关注的角色与伏笔。
- 来自上一章 Character Arc Report 的 progression hints。
- 可能影响下一章的 continuity warnings。

### 2.2 产品目标

- 把 WorldSim-Writer 从“单章审稿台”推进到“长篇叙事操作系统”。
- 强化“可回溯优先于黑盒”的产品原则。
- 降低用户写下一章前的上下文整理成本。
- 为后续 Obsidian export、world snapshot、memory compression 打基础。

### 2.3 工程目标

- 尽量复用现有数据：`Chapter`、`ChapterDraft`、`EventLog`、`Character`、`Foreshadow`、`World.story_arc`、`Chapter.character_arc_report`。
- 不改变 approval 事务逻辑。
- 不在 Next Chapter Prep 阶段自动修改 formal world-state。
- 第一版优先 deterministic aggregation，不强制新增 LLM 调用。
- TDD 实现：先后端 API 测试，再前端组件测试，再页面集成测试。

---

## 3. 非目标

Narrative Control Center 1.0 不做以下内容：

- 不实现 3D 地图或沙盘可视化。
- 不实现复杂分支世界。
- 不自动生成完整下一章草稿。
- 不自动批准任何 world-state changes。
- 不修改 Critic report 或 Character Arc report 的生成逻辑。
- 不实现 Obsidian export。
- 不引入 Redis、向量数据库或独立记忆服务。
- 不实现完整 multi-agent Showrunner pipeline。
- 不做复杂图表库；前端使用现有卡片、列表和简单 timeline。

---

## 4. 核心原则

### 4.1 历史只展示已批准内容

Approved Chapter History 只展示已经正式批准的章节。草稿、驳回稿、暂存版本不进入 approved history。

判断条件：

- `Chapter.status == 'approved'`
- `Chapter.approved_version is not None`
- `Chapter.approved_content is not None`

### 4.2 Next Chapter Prep 只是建议，不提交状态

Next Chapter Prep Panel 的输出属于 writing guidance。它不能：

- 修改角色状态。
- 修改伏笔状态。
- 写 EventLog。
- 递增 world_version。
- 自动创建 chapter。

用户可以把 suggested goal 复制或一键带入 Studio 的章节目标，但正式状态变化仍必须经过章节生成、Review Studio、approval。

### 4.3 所有正式变化都必须能追溯到 EventLog

章节历史中的 world-state changes 应优先来自 `EventLog`，而不是重新推断。

每条变化应尽可能显示：

- event type
- source type
- world_version_before
- world_version_after
- payload.before
- payload.after
- related chapter_id

### 4.4 先 deterministic，后 LLM polish

第一版 Next Chapter Prep 推荐使用 deterministic aggregation。

来源优先级：

1. 下一章 story arc。
2. 最近批准章节的 Character Arc Report progression hints。
3. 当前 stale / urgent foreshadows。
4. 最近 EventLog。
5. 当前角色状态。

后续版本可以新增 `POST /next-chapter-prep/generate` 调用 LLM 润色 suggested goal，但不是 1.0 必需项。

---

## 5. 功能范围概览

Narrative Control Center 1.0 包含两个主模块：

1. **Approved Chapter History**
   - 已批准章节列表。
   - 单章历史详情。
   - 章节正式世界变化摘要。

2. **Next Chapter Prep Panel**
   - 下一章目标建议。
   - 推荐 POV。
   - 优先角色。
   - 优先伏笔。
   - progression hints。
   - continuity warnings。

---

## 6. Approved Chapter History 设计

### 6.1 列表视图

在 WorldPage 或 Narrative Control Center 区域展示已批准章节列表。

每个章节卡片包含：

- chapter id
- title
- status
- approved_version
- base_world_version
- world_version_after
- approved content excerpt
- event count
- character change count
- foreshadow change count

示例：

```json
{
  "id": 11,
  "title": "第一章 雨巷密谈",
  "status": "approved",
  "approved_version": 2,
  "base_world_version": 1,
  "world_version_after": 2,
  "approved_excerpt": "林砚停在雨巷口，掌心玉佩微微发烫……",
  "event_count": 3,
  "character_change_count": 1,
  "foreshadow_change_count": 1
}
```

### 6.2 详情视图

点击章节后展示详情：

- 标题。
- approved content。
- approved_version。
- base_world_version。
- world version before / after。
- 角色变化列表。
- 伏笔变化列表。
- chapter approved event。
- 可选：Critic report summary。
- 可选：Character Arc report summary。

### 6.3 EventLog 聚合规则

章节详情中的变化来自：

```python
EventLog.chapter_id == chapter.id
```

按类型聚合：

- `character_change`
- `foreshadow_change`
- `world_version_increment`
- `chapter_approved`

对于 character change：

```json
{
  "event_type": "character_change",
  "object_type": "character",
  "object_id": 1,
  "before": {"status": "active"},
  "after": {"status": "开始调查密信"}
}
```

对于 foreshadow change：

```json
{
  "event_type": "foreshadow_change",
  "object_type": "foreshadow",
  "object_id": 1,
  "before": {"status": "planted"},
  "after": {"status": "advanced"}
}
```

---

## 7. Next Chapter Prep Panel 设计

### 7.1 目标

Next Chapter Prep Panel 回答：

> 当前世界下一章应该优先写什么？为什么？要注意哪些角色、伏笔和连续性风险？

### 7.2 输入来源

后端聚合以下数据：

- `World`
  - `world_version`
  - `story_arc`
  - `approved_chapter_count`
- 最近批准章节
  - `Chapter.status == 'approved'`
  - `approved_content`
  - `character_arc_report`
  - `critique_report`
- 当前角色
  - `Character.status`
  - `Character.current_goals`
- 当前关系
  - `CharacterRelation`
- 当前伏笔
  - `Foreshadow.status`
  - `Foreshadow.urgency_level`
- stale foreshadows service 输出
- 最近 EventLog

### 7.3 输出结构

建议响应：

```json
{
  "world_id": 7,
  "world_version": 3,
  "next_chapter_number": 3,
  "suggested_goal": "林砚带着湿信前往城主府外墙，试探沈微霜是否可信，并发现密道入口的新线索。",
  "recommended_pov_character_id": 1,
  "recommended_pov_character_name": "林砚",
  "source_signals": [
    "story_arc",
    "character_arc_progression_hint",
    "urgent_foreshadow",
    "recent_event_log"
  ],
  "priority_characters": [],
  "priority_foreshadows": [],
  "progression_hints": [],
  "continuity_warnings": [],
  "recent_events": []
}
```

### 7.4 Suggested Goal 生成规则

第一版不需要 LLM。

优先级：

1. 如果最近批准章节的 `character_arc_report.progression_hints` 中存在：
   - `priority == 'high'`
   - `can_seed_next_chapter_goal == true`

   则使用第一个高优先级 hint 的 `suggested_next_beat` 作为 `suggested_goal`。

2. 否则，如果 `World.story_arc` 中存在下一章：

   ```python
   next_chapter_number = approved_chapter_count + 1
   story_arc[next_chapter_number].summary
   ```

   使用该 summary。

3. 否则，使用当前最高紧迫伏笔生成模板：

   ```text
   推进伏笔《{title}》，让相关角色围绕该线索做出新的选择。
   ```

4. 如果以上都没有，使用 fallback：

   ```text
   基于最近世界事件继续推进主线冲突，并让核心角色做出新的选择。
   ```

### 7.5 Recommended POV 规则

优先级：

1. 如果 selected progression hint 只有一个 related character，使用该角色。
2. 如果 story arc 的 `pov_suggestion` 能匹配角色名，使用匹配角色。
3. 否则使用世界中第一个 protagonist。
4. 否则使用第一个角色。
5. 否则为 null。

### 7.6 Priority Characters

来源：

- selected progression hints 的 `related_character_ids`
- 最近 Character Arc Report 中 `continuity_risk == 'high' | 'medium'` 的角色
- 当前有 active goals 的 protagonist / major characters

字段：

```json
{
  "character_id": 1,
  "name": "林砚",
  "role_type": "protagonist",
  "status": "开始调查密信",
  "reason": "上一章 progression hint 建议让该角色做出选择。"
}
```

### 7.7 Priority Foreshadows

来源：

- selected progression hints 的 `related_foreshadow_ids`
- stale foreshadows
- urgency_level 高的 planted / advanced foreshadows

字段：

```json
{
  "foreshadow_id": 1,
  "title": "裂纹玉佩",
  "status": "advanced",
  "urgency_level": 4,
  "reason": "该伏笔与上一章角色弧线提示相关，且紧迫度较高。"
}
```

### 7.8 Continuity Warnings

第一版 warnings 来源：

- 最近 Character Arc Report 中 high continuity risk。
- 最近 Critic Report 中 high severity issue。
- stale foreshadows。
- story arc 缺失下一章。
- 没有可用角色。

示例：

```json
{
  "severity": "high",
  "category": "character_arc",
  "message": "林砚在上一章的信任转变缺少铺垫，下一章应补足试探过程。",
  "related_character_ids": [1],
  "related_foreshadow_ids": []
}
```

---

## 8. 后端 API 设计

### 8.1 Approved Chapter History List

```http
GET /worlds/{world_id}/chapters/history
```

返回：

```json
{
  "world_id": 7,
  "chapters": [
    {
      "id": 11,
      "title": "第一章 雨巷密谈",
      "status": "approved",
      "approved_version": 2,
      "base_world_version": 1,
      "world_version_after": 2,
      "approved_excerpt": "林砚停在雨巷口……",
      "event_count": 4,
      "character_change_count": 1,
      "foreshadow_change_count": 1
    }
  ]
}
```

### 8.2 Approved Chapter Detail

```http
GET /chapters/{chapter_id}/history
```

返回：

```json
{
  "id": 11,
  "world_id": 7,
  "title": "第一章 雨巷密谈",
  "status": "approved",
  "approved_version": 2,
  "base_world_version": 1,
  "approved_content": "完整正文...",
  "world_version_before": 1,
  "world_version_after": 2,
  "events": [],
  "character_changes": [],
  "foreshadow_changes": [],
  "critic_summary": "章节冲突清晰，但第二段信息揭示偏快。",
  "character_arc_summary": "本章推动林砚从被动等待转向主动追查。"
}
```

错误：

- `404 NOT_FOUND`：章节不存在。
- `403 FORBIDDEN`：用户不拥有章节所属 world。
- `409 CHAPTER_NOT_APPROVED`：章节尚未批准。

### 8.3 Next Chapter Prep

```http
GET /worlds/{world_id}/next-chapter-prep
```

返回：

```json
{
  "world_id": 7,
  "world_version": 2,
  "next_chapter_number": 2,
  "suggested_goal": "林砚带着湿信前往城主府外墙，并设置一次试探。",
  "recommended_pov_character_id": 1,
  "recommended_pov_character_name": "林砚",
  "source_signals": ["character_arc_progression_hint", "story_arc"],
  "priority_characters": [],
  "priority_foreshadows": [],
  "progression_hints": [],
  "continuity_warnings": [],
  "recent_events": []
}
```

错误：

- `404 NOT_FOUND`：world 不存在。
- `403 FORBIDDEN`：用户不拥有 world。

---

## 9. 后端实现设计

### 9.1 新增 schemas

建议在：

```text
backend/app/narrative/schemas.py
```

新增：

- `ApprovedChapterHistoryItem`
- `ApprovedChapterHistoryResponse`
- `ApprovedChapterHistoryDetailResponse`
- `NextChapterPrepCharacter`
- `NextChapterPrepForeshadow`
- `NextChapterPrepWarning`
- `NextChapterPrepEvent`
- `NextChapterPrepResponse`

### 9.2 新增 service functions

建议在：

```text
backend/app/narrative/service.py
```

新增：

```python
def get_approved_chapter_history(db: Session, user: User, world_id: int) -> dict:
    ...


def get_approved_chapter_history_detail(db: Session, user: User, chapter_id: int) -> dict:
    ...


def get_next_chapter_prep(db: Session, user: User, world_id: int) -> dict:
    ...
```

### 9.3 聚合 helper

建议增加私有 helper：

- `_approved_chapters_query(world_id)`
- `_chapter_events(db, chapter_id)`
- `_event_counts(events)`
- `_approved_excerpt(content, limit=180)`
- `_latest_approved_chapter(db, world_id)`
- `_select_progression_hint(chapter)`
- `_next_story_arc_chapter(world, next_chapter_number)`
- `_recommended_pov(...)`
- `_priority_characters(...)`
- `_priority_foreshadows(...)`
- `_continuity_warnings(...)`

保持 deterministic、可测试。

### 9.4 router endpoints

建议加到现有 narrative router：

```python
@router.get('/worlds/{world_id}/chapters/history', response_model=ApprovedChapterHistoryResponse)
def approved_history(...):
    ...

@router.get('/chapters/{chapter_id}/history', response_model=ApprovedChapterHistoryDetailResponse)
def approved_history_detail(...):
    ...

@router.get('/worlds/{world_id}/next-chapter-prep', response_model=NextChapterPrepResponse)
def next_chapter_prep(...):
    ...
```

---

## 10. 前端设计

### 10.1 API client

在：

```text
frontend/src/api/types.ts
frontend/src/api/client.ts
```

新增类型：

- `ApprovedChapterHistoryItem`
- `ApprovedChapterHistoryResponse`
- `ApprovedChapterHistoryDetailResponse`
- `NextChapterPrepCharacter`
- `NextChapterPrepForeshadow`
- `NextChapterPrepWarning`
- `NextChapterPrepResponse`

新增 client：

```typescript
export function getApprovedChapterHistory(worldId: number) {
  return apiRequest<ApprovedChapterHistoryResponse>(`/worlds/${worldId}/chapters/history`);
}

export function getApprovedChapterHistoryDetail(chapterId: number) {
  return apiRequest<ApprovedChapterHistoryDetailResponse>(`/chapters/${chapterId}/history`);
}

export function getNextChapterPrep(worldId: number) {
  return apiRequest<NextChapterPrepResponse>(`/worlds/${worldId}/next-chapter-prep`);
}
```

### 10.2 新增组件：ChapterHistoryPanel

路径：

```text
frontend/src/world/ChapterHistoryPanel.tsx
```

职责：

- 展示 approved chapter list。
- 支持点击章节查看详情。
- 展示角色变化、伏笔变化和事件。
- 处理 loading / empty / error 状态。

UI：

```text
章节历史
├── 第一章 雨巷密谈 · v2 · 世界 1 → 2
│   ├── 角色变化 1
│   ├── 伏笔变化 1
│   └── 查看详情
└── 第二章 城主府外墙 · v1 · 世界 2 → 3
```

详情：

```text
章节详情
├── approved content
├── character changes
├── foreshadow changes
├── EventLog
├── Critic summary
└── Character arc summary
```

### 10.3 新增组件：NextChapterPrepPanel

路径：

```text
frontend/src/world/NextChapterPrepPanel.tsx
```

职责：

- 展示 suggested goal。
- 展示 recommended POV。
- 展示 priority characters。
- 展示 priority foreshadows。
- 展示 progression hints。
- 展示 continuity warnings。
- 提供“用作下一章目标”按钮。

组件 props：

```typescript
type Props = {
  prep: NextChapterPrepResponse;
  onUseGoal?: (goal: string) => void;
};
```

第一版如果 WorldPage 与 StudioPage 还没有共享 goal state，可以先只提供 copy-style 行为：

- 点击后调用 `onUseGoal`。
- 如果没有 callback，则将文本写入 clipboard 或不显示按钮。

为了避免浏览器权限复杂度，推荐第一版只使用 callback。

### 10.4 WorldPage 集成

在 WorldPage 中新增：

```text
Narrative Control Center
├── NextChapterPrepPanel
└── ChapterHistoryPanel
```

加载策略：

- 进入 world overview 后加载。
- 创建 sample world 后加载。
- 审批章节返回 world overview 后重新加载。

错误处理：

- history 加载失败：显示“章节历史暂不可用”。
- prep 加载失败：显示“下一章准备台暂不可用”。

---

## 11. 用户流程

### 11.1 已批准章节历史流程

1. 用户批准章节。
2. 后端提交 world-state changes 和 EventLog。
3. 用户回到 WorldPage。
4. Narrative Control Center 显示新增章节卡。
5. 用户点击卡片，查看：
   - 正文。
   - 角色变化。
   - 伏笔变化。
   - world version change。
   - report summaries。

### 11.2 下一章准备流程

1. 用户批准章节后回到 WorldPage。
2. Next Chapter Prep Panel 自动显示下一章建议。
3. 用户看到：
   - suggested goal。
   - recommended POV。
   - priority characters。
   - priority foreshadows。
   - continuity warnings。
4. 用户点击“用作下一章目标”。
5. 第一版可以将该 goal 传给 WorldPage state，并在进入 Studio 时作为初始 goal。
6. 如果暂不做跨页面 state，也可以只展示文本，让用户复制。

---

## 12. 测试计划

### 12.1 后端 TDD

新增：

```text
backend/tests/test_narrative_control_center.py
```

测试用例：

1. `GET /worlds/{id}/chapters/history` 只返回 approved chapters。
2. history item 包含 approved excerpt、event counts、change counts。
3. `GET /chapters/{id}/history` 返回 approved content 和 EventLog changes。
4. 未批准 chapter detail 返回 `409 CHAPTER_NOT_APPROVED`。
5. `GET /worlds/{id}/next-chapter-prep` 优先使用 high priority character arc progression hint。
6. 没有 progression hint 时 fallback 到 next story arc summary。
7. 没有 story arc 时 fallback 到 highest urgency foreshadow。
8. Next Chapter Prep 不修改 world_version，不写 EventLog。
9. 非 owner 访问返回 403。

### 12.2 前端 API TDD

扩展：

```text
frontend/src/api/client.test.ts
```

测试：

- `getApprovedChapterHistory` endpoint。
- `getApprovedChapterHistoryDetail` endpoint。
- `getNextChapterPrep` endpoint。

### 12.3 前端组件 TDD

新增：

```text
frontend/src/world/ChapterHistoryPanel.test.tsx
frontend/src/world/NextChapterPrepPanel.test.tsx
```

测试：

- ChapterHistoryPanel 渲染章节列表。
- 点击章节调用加载详情。
- 渲染 character changes / foreshadow changes。
- 空历史显示 empty state。
- NextChapterPrepPanel 渲染 suggested goal。
- 渲染 recommended POV。
- 渲染 priority characters / foreshadows。
- 渲染 continuity warnings。
- 点击“用作下一章目标”调用 callback。

### 12.4 WorldPage 集成测试

如果现有 WorldPage 测试不足，新增或扩展：

- world overview 成功加载后显示 Narrative Control Center。
- history / prep API 失败时显示降级信息。
- next chapter goal callback 可更新后续进入 Studio 的初始 goal，或至少触发 callback。

---

## 13. 实现顺序建议

1. 后端 RED：写 `test_narrative_control_center.py`。
2. 后端 GREEN：实现 history list。
3. 后端 GREEN：实现 history detail。
4. 后端 GREEN：实现 next chapter prep deterministic aggregation。
5. 后端回归：跑 narrative / world / critic / character arc 相关测试。
6. 前端 RED：写 API client tests。
7. 前端 GREEN：加 types 和 client methods。
8. 前端 RED：写 `ChapterHistoryPanel.test.tsx`。
9. 前端 GREEN：实现 `ChapterHistoryPanel`。
10. 前端 RED：写 `NextChapterPrepPanel.test.tsx`。
11. 前端 GREEN：实现 `NextChapterPrepPanel`。
12. 前端 RED/GREEN：WorldPage 集成。
13. 全量回归：backend pytest + frontend test + frontend build。

---

## 14. 风险与缓解

### 14.1 EventLog payload 结构不一致

风险：不同 event type 的 payload 字段不同，前端展示容易出错。

缓解：后端 response 中先规范化：

- `character_changes`
- `foreshadow_changes`
- `events`

前端不要直接解析原始 EventLog payload 来决定核心展示。

### 14.2 Next Chapter Prep 看起来像自动生成章节

风险：用户误解 suggested goal 会自动创建章节或提交状态。

缓解：UI 标注：

> 下一章准备台只提供写作建议，不会自动修改世界状态。

### 14.3 UI 过载

风险：WorldPage 已有角色、关系、伏笔、事件等内容，新增控制台可能太长。

缓解：

- Narrative Control Center 使用独立区域。
- History 默认只显示最近 3-5 章。
- Detail 按需展开。
- Prep Panel 优先展示 suggested goal 和 warnings，其余可折叠。

### 14.4 Deterministic suggested goal 太机械

风险：不调用 LLM 的 suggested goal 文案可能不够自然。

缓解：第一版先强调可靠性；后续可加 `POST /next-chapter-prep/generate` 做 LLM polish，但仍不提交状态。

---

## 15. 验收标准

完成后应满足：

- WorldPage 能显示 Narrative Control Center。
- 用户能看到 approved chapter history。
- 用户能查看单章 approved content 和正式 world-state changes。
- Next Chapter Prep 能给出 suggested goal。
- Next Chapter Prep 能显示 recommended POV。
- Next Chapter Prep 能显示 priority characters / foreshadows。
- Next Chapter Prep 能显示 continuity warnings。
- Prep 优先使用上一章 Character Arc progression hints。
- 没有 hints 时能 fallback 到 story arc。
- 没有 story arc 时能 fallback 到 urgency foreshadow。
- 所有 prep 操作都不修改 world_version，不写 EventLog。
- 后端和前端测试覆盖主要流程。
- 全量 backend pytest、frontend test、frontend build 通过。

---

## 16. 未来扩展

Narrative Control Center 1.0 完成后，可继续扩展：

1. **LLM-polished Next Chapter Prep**
   - 在 deterministic prep 基础上调用 LLM 润色章节目标和 beats。

2. **Continuity Risk Dashboard 2.0**
   - 聚合 Critic high issues、Character Arc risks、stale foreshadows、长期缺席角色。

3. **Obsidian Export**
   - 导出 approved chapter history、character cards、foreshadow ledger、event timeline。

4. **Memory Compression**
   - 每章批准后生成 fact cards、emotion cards、causal chain summary。

5. **World Snapshot**
   - 按 world_version 查看历史 projection，支持复盘和未来分支。

---

## 17. 自检结果

- **范围检查：** 本设计聚焦 Approved Chapter History 和 Next Chapter Prep，没有扩张到 3D 地图、Obsidian、复杂多代理或分支世界。
- **一致性检查：** 所有建议性内容都不修改 formal world-state，符合“审核优先于落库”的核心原则。
- **可测试性检查：** 后端 API、aggregation helper、前端 API、组件和 WorldPage 集成均有明确测试路径。
- **风险检查：** 已覆盖 EventLog payload、UI 过载、用户误解 suggested goal、deterministic goal 文案机械四类主要风险。
