# WorldSim-Writer MVP 最小闭环设计

日期：2026-05-27

## 背景

当前仓库仍处于需求与架构设计阶段。现有源文档是 [WorldSim-Writer.md](../../../WorldSim-Writer.md)，其中明确项目目标是构建长篇叙事创作系统，而不是单次文本生成工具。

本设计把第一版开发范围收敛为一个可运行的最小闭环：用户能在浏览器中登录、创建示例世界、调用真实大模型生成章节草稿、审核通过，并看到世界状态被正式更新。

## 已确认决策

- 第一版形态：后端 API + 简单网页 UI。
- 模型调用：接真实 OpenAI-compatible Chat Completions API。
- 数据库：本机 PostgreSQL。
- 运行环境：本地 conda 环境 `worldsim`，Python 3.12。
- 账号体系：单用户注册/登录。
- 前端页面：登录页、世界页、创作台页。
- 世界创建：先做 1 个内置示例模板和少量可编辑字段。
- 审核通过后的状态更新：章节、事件日志、世界版本、角色状态、伏笔状态。

## 总体架构

第一版采用单体全栈架构，并保留清晰的领域模块边界。

- 后端：FastAPI 单体应用。
- 数据库：PostgreSQL。
- ORM 与迁移：SQLAlchemy + Alembic。
- 前端：React + Vite + Tailwind。
- 模型：后端封装 LLM Client，兼容 OpenAI Chat Completions 格式。
- 配置：通过环境变量注入数据库连接和模型配置。

后端模块边界：

- `auth`：注册、登录、会话、当前用户。
- `world`：世界、真理库、世界版本。
- `character`：角色、关系、状态。
- `narrative`：章节草稿、生成、审核、通过。
- `foreshadow`：伏笔账本与状态。
- `event`：正式事件日志。
- `llm`：大模型请求、响应解析、结构校验。

第一版不实现地图 UI、Obsidian 导出、分支世界、角色 Skill 集群对话、复杂权限角色。相关能力只保留模块位置或字段余量。

## 最小用户闭环

目标流程：

1. 用户注册或登录。
2. 用户创建内置示例世界。
3. 系统初始化真理库、默认角色、角色关系和初始伏笔。
4. 用户进入创作台，输入章节目标。
5. 后端读取世界状态、角色状态和紧迫伏笔，组装上下文。
6. 后端调用真实 OpenAI-compatible API 生成草稿。
7. 前端展示章节草稿、上下文摘要、审核提示和建议状态变更。
8. 用户点击通过。
9. 后端在一个数据库事务中写入正式章节、事件日志、角色变更、伏笔变更，并把 `world_version` 加一。
10. 前端刷新世界页和创作台状态，显示版本、事件、角色和伏笔变化。

## 数据模型

第一版只建闭环必需表。

### `users`

保存账号、密码哈希和创建时间。MVP 只做单用户登录，但表结构允许后续多用户。

### `worlds`

关键字段：

- `id`
- `owner_id`
- `title`
- `genre_template`
- `truth_canon`
- `truth_canon_version`
- `world_version`
- `status`
- `tone_profile`
- `created_at`
- `updated_at`

创建世界时使用一个内置示例模板初始化。

### `characters`

关键字段：

- `id`
- `world_id`
- `name`
- `role_type`
- `status`
- `public_profile`
- `hidden_traits`
- `destiny_flag`
- `current_goals`

`public_profile`、`hidden_traits`、`destiny_flag` 和 `current_goals` 可使用 JSON 字段，以便先保留叙事数据弹性。

### `character_relations`

关键字段：

- `world_id`
- `source_character_id`
- `target_character_id`
- `relation_type`
- `intensity`
- `visibility`

第一版只展示基础关系，不做复杂关系推演。

### `foreshadows`

关键字段：

- `id`
- `world_id`
- `source_chapter_id`
- `title`
- `description`
- `foreshadow_type`
- `status`
- `urgency_level`
- `related_character_ids`
- `expected_resolution_window`

第一版支持 `planted`、`triggered`、`resolved`、`expired` 等状态。

### `chapters`

关键字段：

- `id`
- `world_id`
- `title`
- `pov_character_id`
- `status`
- `draft_version`
- `approved_version`
- `base_world_version`
- `approved_content`

### `chapter_drafts`

关键字段：

- `chapter_id`
- `draft_version`
- `content`
- `context_summary`
- `review_hints`
- `proposed_changes`
- `source_world_version`

`proposed_changes` 保存模型建议的角色和伏笔变更。审批时后端校验这些变更，再正式落库。

### `event_logs`

关键字段：

- `id`
- `world_id`
- `event_type`
- `source_type`
- `commit_id`
- `payload`
- `world_version_before`
- `world_version_after`
- `created_at`

章节通过时写入 `CHAPTER_APPROVED` 事件，并记录变更对象摘要。

### 第一版暂不建表

- `tiles`：地图功能后续再做。
- `snapshots` 与分支世界相关表：第一版不做真实分支。
- `sync_logs`：Obsidian 导出开发时再建。
- 投影表：第一版直接查询核心表聚合，不引入复杂状态投影。

## 章节审批事务

`POST /chapters/{chapter_id}/approve` 必须在一个数据库事务中完成：

1. 检查 `chapter_drafts.source_world_version == worlds.world_version`。
2. 更新 `chapters.status`、`chapters.approved_content` 和 `chapters.approved_version`。
3. 应用 `proposed_changes` 到 `characters` 和 `foreshadows`。
4. 写入 `event_logs`。
5. 将 `worlds.world_version` 加一。

任一步失败则回滚。系统不得出现“正文已通过但状态未更新”或“状态已更新但事件未记录”的半成功状态。

## API 设计

### Auth

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`

### World

- `POST /worlds/from-template`
- `GET /worlds`
- `GET /worlds/{world_id}`
- `GET /worlds/{world_id}/overview`

### Characters

- `GET /worlds/{world_id}/characters`
- `GET /worlds/{world_id}/characters/{character_id}`

### Foreshadows

- `GET /worlds/{world_id}/foreshadows`

### Narrative

- `POST /worlds/{world_id}/chapters/draft`
- `GET /worlds/{world_id}/chapters`
- `GET /chapters/{chapter_id}`
- `POST /chapters/{chapter_id}/approve`
- `POST /chapters/{chapter_id}/reject`

### Events

- `GET /worlds/{world_id}/events`

## 章节生成流程

`POST /worlds/{world_id}/chapters/draft` 执行流程：

1. 验证用户登录、世界归属和世界可写状态。
2. 读取世界、真理库、默认角色和紧迫伏笔。
3. 组装精简上下文包。
4. 调用真实 OpenAI-compatible API。
5. 要求模型返回结构化 JSON。
6. 校验 JSON 字段和关联对象 ID。
7. 创建 `chapters` 和 `chapter_drafts`，章节进入 `reviewing` 状态。
8. 返回草稿、上下文摘要、审核提示和建议变更。

模型返回结构：

- `title`
- `draft_content`
- `context_summary`
- `review_hints`
- `proposed_character_changes`
- `proposed_foreshadow_changes`

## LLM 配置

后端通过环境变量读取模型配置：

- `LLM_BASE_URL`
- `LLM_API_KEY`
- `LLM_MODEL`
- `LLM_TIMEOUT_SECONDS`

前端不得接触 API Key。所有模型调用都经过后端代理。

## 错误处理

第一版必须处理这些错误：

- `UNAUTHORIZED`：未登录。
- `FORBIDDEN`：无权访问目标世界。
- `NOT_FOUND`：目标不存在。
- `MODEL_RESPONSE_INVALID`：模型返回非 JSON、缺字段或字段非法。
- `MODEL_TIMEOUT`：模型调用超时。
- `WORLD_VERSION_MISMATCH`：草稿基于的世界版本过期。
- `INTERNAL_ERROR`：审批事务或未知服务错误。

版本冲突必须提示用户重新生成草稿，不允许静默覆盖当前世界状态。

## 前端页面

第一版前端包含 3 个页面。

### 登录页

能力：

- 注册。
- 登录。
- 登录后跳转世界页。

目标是满足“不允许匿名正式写入”。

### 世界页

能力：

- 无世界时创建内置示例世界。
- 展示世界标题、题材、真理库摘要、`world_version` 和状态。
- 展示默认角色、角色关系、伏笔列表和最近事件。
- 提供进入创作台入口。

### 创作台页

能力：

- 输入章节目标。
- 查看当前上下文摘要、POV 角色和紧迫伏笔。
- 调用后端生成草稿。
- 展示章节草稿、审核提示和建议变更。
- 通过或驳回章节。
- 通过后展示世界版本、事件日志、角色状态和伏笔状态变化。

## 测试策略

### 后端测试

- 模型返回合法 JSON 时能创建草稿。
- 模型返回非 JSON、缺字段、无效角色 ID 或无效伏笔 ID 时返回 `MODEL_RESPONSE_INVALID`。
- 审批成功时同时完成章节状态更新、事件日志新增、角色/伏笔更新和世界版本加一。
- 审批失败时事务回滚。
- 草稿世界版本过期时返回 `WORLD_VERSION_MISMATCH`。
- 未登录用户不能创建世界、生成草稿或通过章节。
- 用户不能访问不属于自己的世界。

### 前端测试

- 登录后能进入世界页。
- 无世界时能创建示例世界。
- 世界页能显示角色、伏笔、世界版本和事件摘要。
- 创作台能输入章节目标并生成草稿。
- 创作台能展示审核提示和建议变更。
- 通过章节后，页面能看到世界版本、角色状态、伏笔状态和事件日志变化。

## 手动验收标准

MVP 完成时必须能演示：

1. 执行 `conda activate worldsim`。
2. 启动 FastAPI 后端。
3. 启动 React 前端。
4. 在浏览器注册或登录。
5. 创建内置示例世界。
6. 输入章节目标。
7. 调用真实 OpenAI-compatible API 生成草稿。
8. 点击通过。
9. 页面显示 `world_version` 从 1 变为 2。
10. 页面显示新增 `CHAPTER_APPROVED` 事件。
11. 页面显示至少一个角色状态或目标发生变化。
12. 页面显示至少一个伏笔状态发生变化，或显示模型建议未改变伏笔的审核说明。

## 后续扩展预留

后续功能继续按 [WorldSim-Writer.md](../../../WorldSim-Writer.md) 扩展，但必须保持 MVP 闭环稳定。

建议扩展顺序：

1. 角色库详情页和关系编辑。
2. 伏笔账本筛选与手动状态调整。
3. 地图与地块状态。
4. 记忆摘要和检索优化。
5. Obsidian 单向导出。
6. 分支世界和快照。
7. 多角色 Skill 挂载和高级文学性二审。

每次扩展都应沿用现有模块边界和审批事务规则，不绕过正式事件日志。
