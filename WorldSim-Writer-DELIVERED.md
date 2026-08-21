# WorldSim-Writer 已交付功能清单 (Beta 0.2.0)

> **本文档描述当前代码库中已实现的功能。** 未交付的长期愿景请参阅 `WorldSim-Writer-ROADMAP.md`。
>
> 版本：`0.2.0-beta.1` | 状态：受限 Beta | 更新：2026-07-30

---

## 一、核心闭环

已交付"创建世界 → 章节草稿 → Studio 审稿 → 用户批准 → canon / 世界版本 / EventLog 更新"的完整闭环。

**核心不变式**：草稿、连续章节计划、候选素材和风格手册都不能自动写入 canon；只有用户明确批准的章节正文与世界变化才能推进世界版本并进入 EventLog。

---

## 二、用户功能

### 2.1 认证系统
- 注册 / 登录
- JWT 令牌认证
- 会话管理（localStorage 存储）

### 2.2 世界创建
- 内置示例世界（sample world）
- 题材模板创建（genre presets）
- 手动创建世界（自定义表单）
- 一句话生成世界创建草稿（brief → 自动填表 → 用户确认后创建）
- Seed/Preset 世界胚胎选择与创建
- 世界创建草稿可编辑，确认前不创建正式世界

### 2.3 章节工作室 (Studio)
- **草稿生成**：基于当前世界状态生成章节草稿
- **大纲生成**：可先生成章节大纲
- **正文写作**：基于大纲生成正文
- **文学评论**：对草稿进行文学性 critique
- **评论报告**：Critic report（逻辑问题、OOC 风险、俗套风险）
- **角色弧分析**：Character arc report
- **草稿编辑**：
  - 手动编辑草稿
  - 整章修订 (revise)
  - 段落级重写/润色 (revise paragraph)
  - 草稿暂存 (stash)
- **版本管理**：
  - 草稿版本树（每次重写/润色/编辑形成新版本）
  - 版本间差异对比 (draft diff)
  - 读取历史版本
- **审批流程**：
  - 审批预览 (approval preview)：展示拟议的世界变化
  - 一致性检查 (approval consistency)：设定冲突检测
  - 就绪检查 (approval readiness)：质量门检查
  - **首章质量门**：第一章必须通过 opening quality gate（背景、主角身份、动机、人格证据、冲突目标、锁定 POV）
  - 批准 (approve)：写入正史，推进世界版本，追加 EventLog
  - 驳回 (reject)：标记驳回，不更新世界状态
- 放弃草稿 (abandon)
- 恢复活跃会话 (resume active session)

### 2.4 角色管理
- 创建 / 查看 / 更新 / 删除角色
- 角色列表与筛选
- 角色关系管理（创建/查看/更新/删除关系）

### 2.5 伏笔管理
- 创建 / 查看 / 更新 / 删除伏笔
- 伏笔账本 (ledger)
- 伏笔时间线 (timeline)
- 过期伏笔标记 (stale)

### 2.6 导入节点 (Import Node)
- 参考文本预览与解析
- 风格手册预览 (style handbook preview)
- 确认导入批次
- 导入批次列表
- 候选素材进入预览区，确认前不进入 canon

### 2.7 标签系统
- 创建 / 查看 / 更新 / 合并 / 删除标签
- 对象标签映射

### 2.8 快照与导出
- 创建世界快照
- 快照列表与查看
- 快照对比
- Markdown ZIP 导出（base64 编码 ZIP + 内联文件预览）

### 2.9 叙事控制台 (Narrative Control Center)
- 已批准章节历史
- 下一章准备 (next chapter prep)
- 叙事健康 (narrative health)
- 开放线索 (open threads)
- 世界心跳 (world pulse)
- 故事弧计划 (arc plan)

### 2.10 世界运营
- 世界概览（聚合信息：世界进度、最近事件、角色、伏笔）
- 故事弧 (story arc) 管理
- 串行章节计划 (serial plan)
- 下一章目标建议 (suggest goal)
- 事件日志查询 (events)
- 全局搜索 (search)
- 世界状态更新 (archive/restore)

---

## 三、后端工程

### 3.1 技术栈
- **框架**：FastAPI（Python 3.12+）
- **ORM**：SQLAlchemy + Alembic 迁移
- **数据库**：PostgreSQL（生产）/ SQLite in-memory（测试）
- **LLM**：OpenAI 兼容接口（Chat Completions / Responses 模式），支持 Mock 模式

### 3.2 已交付工程能力
- 独立迁移 runner（`scripts/run_migrations.py`），不在 FastAPI startup 跑 migration
- 生产 API runner（`scripts/run_api.py`）
- `/live` 探针（进程存活）+ `/ready` 探针（流量就绪）
- 结构化请求日志（含 request ID，不含请求体/query string/authorization header）
- 并发/事务保护：`approve_chapter()` 使用行级锁 + `source_world_version` 校验
- 长 LLM 调用后的锁内复检与迟到写保护
- PostgreSQL 备份/恢复演练脚本
- Docker Compose 后端发布栈（PostgreSQL + 序列化迁移容器 + API 容器）
- 容器安全：read-only rootfs、drop capabilities、no-new-privileges、UID/GID 10001
- LLM 使用审计日志（`llm_usage` 表）

### 3.3 数据模型
已实现的数据表：
- `users` — 用户
- `worlds` — 世界
- `characters` — 角色
- `character_relations` — 角色关系
- `chapters` — 章节
- `chapter_drafts` — 章节草稿版本
- `foreshadows` — 伏笔
- `foreshadow_events` — 伏笔事件
- `event_logs` — 事件日志
- `import_batches` — 导入批次
- `import_candidate_assets` — 导入候选资产
- `tags` / `object_tags` — 标签系统
- `world_snapshots` — 世界快照
- `llm_usage_audit` — LLM 使用审计

### 3.4 测试
- pytest + FastAPI TestClient + in-memory SQLite
- JSONB 编译 shim（SQLite 兼容）
- 后端测试标记：`postgres`、`concurrency`
- Mock E2E 冒烟测试脚本（`scripts/e2e_smoke.py`）
- 真实 LLM canary 测试（需显式 opt-in）
- 前端 Vitest + Testing Library + jsdom

---

## 四、前端工程

### 4.1 技术栈
- React + TypeScript
- Vite 构建
- Tailwind CSS 样式
- Vitest + Testing Library 测试

### 4.2 已交付页面/面板
- **AuthPage**：登录/注册
- **WorldPage**：世界列表、创建世界、世界概览
- **WorldCreationForm**：一句话开书 + 自动填表 + 手动创建
- **StudioPage**：章节草稿、审批、评论、角色弧分析
- **CharacterManager**：角色 CRUD
- **RelationManager**：关系 CRUD
- **ForeshadowManager**：伏笔 CRUD
- **ApprovalReadinessPanel**：审批就绪检查
- **CriticReportPanel**：文学评论报告
- **CharacterArcPanel**：角色弧分析
- **WorldPulsePanel**：世界心跳
- **NarrativeHealthPanel**：叙事健康
- **OpenThreadsPanel**：开放线索
- **ChapterHistoryPanel**：章节历史
- **WorldTimelinePanel**：时间线
- **NextChapterPrepPanel**：下一章准备
- **ArcPlanPanel**：故事弧计划
- **SeedLibraryPanel**：世界胚胎库
- **WorldArchivePanel**：世界归档
- **WorldSearchPanel**：全局搜索
- **WorldTagsPanel**：标签管理
- **WorldImportPanel**：导入面板

### 4.3 UX 增强（P0-P3 已完成）
- P0：审批后世界推进结算页
- P1：新手 3 分钟闭环入口
- P2：世界运营仪表盘
- P3：术语用户化 + 等待体验优化

---

## 五、API 接口清单（已实现）

### 认证
- `POST /auth/register`
- `POST /auth/login`

### 世界
- `POST /worlds` — 创建世界
- `GET /worlds` — 列出世界
- `GET /worlds/{id}` — 获取世界
- `GET /worlds/{id}/overview` — 世界概览
- `PATCH /worlds/{id}/status` — 更新状态（archive/restore）
- `GET /worlds/seeds` — 世界胚胎列表
- `GET /worlds/seeds/{key}` — 胚胎详情
- `POST /worlds/from-seed` — 从胚胎创建
- `POST /worlds/from-template` — 从模板创建
- `POST /worlds/draft-from-brief` — 一句话生成创建草稿
- `GET /worlds/{id}/story-arc` — 故事弧
- `POST /worlds/{id}/serial-plan` — 串行计划
- `POST /worlds/{id}/suggest-goal` — 建议下一章目标
- `GET /worlds/{id}/events` — 事件日志
- `GET /worlds/{id}/search` — 全局搜索

### 角色
- `POST /worlds/{id}/characters`
- `GET /worlds/{id}/characters`
- `GET /characters/{id}`
- `PATCH /characters/{id}`
- `DELETE /characters/{id}`

### 角色关系
- `POST /worlds/{id}/relations`
- `GET /worlds/{id}/relations`
- `GET /relations/{id}`
- `PATCH /relations/{id}`
- `DELETE /relations/{id}`

### 章节（叙事）
- `POST /worlds/{id}/chapters` — 创建章节
- `POST /chapters/{id}/draft` — 生成草稿
- `POST /chapters/{id}/outline` — 生成大纲
- `POST /chapters/{id}/write` — 生成正文
- `POST /chapters/{id}/critique` — 文学评论
- `POST /chapters/{id}/critic-report` — 评论报告
- `GET /chapters/{id}/critic-report` — 查看评论报告
- `POST /chapters/{id}/character-arc-report` — 角色弧报告
- `GET /chapters/{id}/character-arc-report` — 查看角色弧报告
- `POST /chapters/{id}/abandon` — 放弃
- `POST /chapters/{id}/approve` — 批准（写入正史）
- `POST /chapters/{id}/reject` — 驳回
- `PUT /chapters/{id}/draft` — 编辑草稿
- `POST /chapters/{id}/revise` — 整章修订
- `POST /chapters/{id}/revise-paragraph` — 段落修订
- `GET /chapters/{id}/draft-diff` — 版本差异
- `GET /chapters/{id}/draft-version` — 读取历史版本
- `GET /chapters/{id}/approval-preview` — 审批预览
- `GET /chapters/{id}/approval-consistency` — 一致性检查
- `GET /chapters/{id}/approval-readiness` — 就绪检查
- `POST /chapters/{id}/stash` — 暂存草稿
- `GET /chapters/active-session` — 活跃会话

### 伏笔
- `POST /worlds/{id}/foreshadows`
- `GET /worlds/{id}/foreshadows`
- `GET /worlds/{id}/foreshadows/stale`
- `GET /worlds/{id}/foreshadows/ledger`
- `GET /worlds/{id}/foreshadows/timeline`
- `GET /foreshadows/{id}`
- `PATCH /foreshadows/{id}`
- `DELETE /foreshadows/{id}`

### 导入节点
- `POST /worlds/{id}/import/preview`
- `POST /worlds/{id}/import/style-handbook-preview`
- `POST /worlds/{id}/import/confirm`
- `GET /worlds/{id}/import/batches`

### 标签
- `GET /worlds/{id}/tags`
- `POST /worlds/{id}/tags`
- `PATCH /worlds/{id}/tags/{id}`
- `POST /worlds/{id}/tags/merge`
- `GET /worlds/{id}/tags/{id}`
- `DELETE /worlds/{id}/tags/{id}`

### 快照与导出
- `POST /worlds/{id}/snapshots`
- `GET /worlds/{id}/snapshots`
- `GET /snapshots/{id}`
- `GET /snapshots/compare`
- `POST /worlds/{id}/export/markdown`

### 叙事控制台
- `GET /worlds/{id}/approved-chapter-history`
- `GET /worlds/{id}/approved-chapter-history/{chapter_id}`
- `GET /worlds/{id}/next-chapter-prep`
- `GET /worlds/{id}/narrative-health`
- `GET /worlds/{id}/open-threads`
- `GET /worlds/{id}/world-pulse`
- `GET /worlds/{id}/arc-plan`

---

## 六、明确的非目标（MVP 不做项）

以下在 `WorldSim-Writer-ROADMAP.md` 中描述：

- 3D 星球地图（Three.js）
- 语音控制
- 多人协作审核
- 模板市场与插件生态
- 复杂分支世界管理
- Neo4j 图数据库
- ChromaDB / 独立向量数据库
- Redis 缓存
- Prometheus + Grafana 监控
- 微服务拆分
- 公开 SaaS 硬化（rate limiting、CSP、session 管理等）
