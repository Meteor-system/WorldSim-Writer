# WorldSim-Writer Beta 准入报告

**报告日期**：2026-08-04
**候选分支**：`integration/import-node-p0-ui7`
**候选提交**：`92e674886516f8d74823aacc9cd7222a0f7dc235`（`guard-opening-evidence-repair`）
**候选状态**：分支相对远端 ahead 3；已跟踪产品代码无改动，工作树仅有本报告未跟踪；未创建 tag，未 push
**验证环境**：Windows 本地环境；一次性隔离 Docker PostgreSQL、mock LLM、真实 LLM provider 与独立前端验证栈

---

## 1. 执行结论

**综合判定：HOLD——当前不创建 Beta tag，继续 RC 收口。**

冻结候选已经证明以下核心能力成立：

- 默认后端测试套件通过；
- 前端质量建议接入、目标测试和构建通过；
- Docker Compose 配置、迁移、健康检查和数据库隔离通过；
- 既有隔离 PostgreSQL + mock LLM 环境中的主写作流程、显式审批写入 canon、导出、快照、归档只读和恢复写作均有动态 UI 通过证据；本候选新增的时间线修复与开篇证据修复另经目标测试、后端全量测试、真实 provider canary 和前端生产构建验证；
- LLM 失败诊断已限制为不可逆标记，不保留原始响应或凭据，并通过大规模模糊测试；
- 事件时间线角色/伏笔变化标签已修复，不再渲染为 `[object Object]`；
- 真实 PostgreSQL 并发/marker 与恢复目标空库保护门禁通过；
- 真实 `pg_dump → pg_restore` 演练通过。

当前不放行 Beta tag，原因是剩余一项真实 LLM 质量门禁未通过：

1. 真实 provider canary 已在当前 SHA 上通过，为 `8 passed`；
2. 真实 LLM 首章隔离 E2E 已确认真实模式并完成健康、迁移、注册、建世界、首章草稿和审批预览，但仍在 `approval_readiness` 被业务质量门禁阻断，未到达审批、版本推进、事件和导出。

因此当前结论仍为 **HOLD**。真实 provider canary 已为 **PASS**，真实首章 E2E 必须保持为 **NOT PASS**，不能解释为完整流程通过；除非修复或重新审查该质量门禁并在新 SHA 上重跑真实首章 E2E，或由发布负责人明确接受风险，不得创建 Beta tag。

---

## 2. 门禁结果汇总

| 门禁项 | 状态 | 当前候选证据 | Beta tag 影响 |
|---|---|---|---|
| 候选冻结与可追溯性 | PASS | `92e674886516f8d74823aacc9cd7222a0f7dc235`；已跟踪产品代码无改动；仅本报告未跟踪 | 不阻塞 |
| 后端默认全量测试 | PASS | `781 passed, 16 skipped`；skipped 不计为已验证 | 不阻塞 |
| LLM 诊断脱敏与边界 | PASS | 仅保留标记；不保留原始响应/密钥；截断后小于 400 字符；20,000 次 fuzz 通过 | 不阻塞 |
| 前端质量建议接入 | PASS | `quality_report.advisories` 对齐；目标测试通过；前端构建通过 | 不阻塞 |
| Docker Compose 运行门禁 | PASS | 配置、迁移、健康检查通过；PostgreSQL 未发布宿主端口 | 不阻塞 |
| mock 主写作流程 UI | PASS（既有栈证据） | `worldsim_ui_055ace48` 已验证创建世界、生成草稿、质量门禁、审批、版本推进、事件、导出；当前 SHA 的时间线改动另有目标回归测试、前端全量测试和构建证据 | 不阻塞；仅证明 mock 路径 |
| 归档只读与恢复写作 | PASS（既有栈证据） | `worldsim_ui_055ace48` 验证归档后写控件消失、读工具保留；恢复后 API 状态为 `active` 且写控件回归 | 不阻塞 |
| 真实 PostgreSQL 并发/marker 测试 | PASS | 一次性 loopback PostgreSQL 隔离栈；`5 passed, 2 deselected` | 不阻塞 |
| 真实 PostgreSQL 恢复目标空库保护 | PASS | 一次性隔离恢复库；`1 passed`；目标空库保护生效 | 不阻塞 |
| 真实 `pg_dump → pg_restore` 演练 | PASS | `migration_exit=0`、`backup_exit=0`、`restore_exit=0`；dump 54,992 bytes；源/目标关键计数均为 `1,1` | 不阻塞 |
| 真实 provider canary | PASS | `8 passed`；Responses 与 Chat Completions 两种 API mode 均通过 | 不阻塞 |
| 真实 LLM 首章隔离 E2E | NOT PASS | `LLM_MOCK=false`；健康/迁移/注册/建世界/草稿/审批预览通过；`approval_readiness` 被业务质量门禁阻断 | 阻塞 Beta tag |
| 事件描述渲染 | PASS | `character_change` 与 `foreshadow_change` 目标测试 3 passed；不再显示 `[object Object]` | 不阻塞 |

---

## 3. 自动化与代码级证据

### 3.1 后端默认套件

- 结果：`781 passed, 16 skipped`。
- 结论：默认测试路径通过，无已知失败。
- 限制：16 个 skipped 不能并入通过数量；真实 PostgreSQL 专用门禁已通过独立一次性栈另行执行，不并入默认套件计数。

### 3.2 冻结候选的质量与日志修复

独立复核确认：

- LLM 失败诊断只保留不可逆分类标记；
- 不保留原始 provider 响应、请求正文、授权头、API key、provider URL 或模型名；
- 标记感知截断后诊断长度小于 400 字符；
- 20,000 个模糊输入全部满足脱敏与长度约束；
- 开篇证据校正、重复术语建议和前端 advisory 显示路径保持一致。

### 3.3 前端质量报告接入

已验证：

- `quality_report.advisories` 与后端结构对齐；
- advisory 为非阻断信息，不会绕过或替代 hard gate；
- 后端 0-based `corrected_index` 在 UI 中按 1-based 段号显示；
- 相关目标测试通过；
- 前端生产构建通过。

---

## 4. Docker / PostgreSQL 运行证据

### 4.1 工具与编排

- Docker Engine：`29.3.1`；
- Docker Compose：`v5.1.1`；
- Compose 配置校验通过；
- PostgreSQL 容器健康；
- 数据库未发布宿主端口；
- migration 一次性任务退出码为 0，并输出 `{"ok":true,"status":"up_to_date"}`；
- API 容器健康；
- `/live` 与 `/ready` 均返回 HTTP 200。

### 4.2 隔离验证栈

动态 UI 验证使用独立栈，未复用共享数据库：

- mock Compose project：`worldsim_ui_055ace48`；
- mock API：`127.0.0.1:18002`；
- mock Frontend：`127.0.0.1:5175`；
- mock LLM：启用；
- PostgreSQL：独立且健康；
- 数据：唯一测试账户和测试世界。

真实 LLM 首章 E2E 另使用一次性 Compose project `worldsim_real_e2e_92e6748`、API `127.0.0.1:18004`、独立 PostgreSQL 卷和 `LLM_MOCK=false`。该项目、卷、端口和测试数据已在测试后清理。

现有 `8000`、`18000`、`18001` 服务及既有 `worldsim_ui_055ace48` 栈未被停止、覆盖或写入；真实 E2E 使用独立端口和数据库。

### 4.3 备份恢复边界

已确认：

- 备份/恢复脚本实现存在；
- 不依赖真实 PostgreSQL 的脚本单元测试通过；
- 目标数据库非空保护逻辑有单元测试覆盖；
- 真实 PostgreSQL 恢复目标空库保护测试通过：`1 passed`；
- 真实 `pg_dump → pg_restore` 演练通过：migration、backup、restore 退出码均为 0。

演练证据：

- dump 大小：54,992 bytes；
- dump SHA-256：`7bfdd6513dc7c6e43a74a0b3c487afb90955bfb775d95de1150f72576bf898c1`；
- 源库/目标库关键计数均为 `1,1`；
- 恢复后 migration head：`0014_add_chapter_draft_quality_report`；
- 临时容器、端口、dump 和卷均已清理。

因此真实 PostgreSQL 恢复目标保护与完整备份恢复演练均为 **PASS**。

---

## 5. 动态 UI 主流程证据（mock LLM）

此前在独立 mock 隔离栈 `worldsim_ui_055ace48` 中按 `BETA_TESTING.md` 主流程执行；该栈证据用于验证既有主流程，不宣称本轮在候选 SHA 上完整重跑：

1. 注册唯一测试用户；
2. 创建内置示例世界；
3. 生成第一章草稿并进入 Studio；
4. 六项 hard quality gates 全部通过；
5. UI 显示三项开篇缺失 advisory 和一项术语密度 advisory，均保持非阻断；
6. POV 确认框未勾选时审批按钮禁用，勾选后才允许审批；
7. 显式审批章节；
8. 世界由 `v1` 推进到 `v2`，生成一章 canon 章节；
9. `chapter_approved` 事件记录版本 `1 → 2`；
10. 角色和伏笔投影按审批结果结算；
11. Markdown ZIP 导出成功，包含七个文件并显示内联预览。

该流程验证了核心不变量：**生成草稿和 advisory 不会写入 canonical world state；只有用户显式审批才推进世界版本和正式事件历史。**

限制：上述生成质量证据来自 mock LLM，不得表述为真实模型质量验证。

---

## 6. 归档只读与恢复写作证据

此前在独立 mock 隔离栈 `worldsim_ui_055ace48` 中完成 `BETA_TESTING.md` 的归档抽查；该证据用于验证既有归档/恢复行为，不宣称本轮在候选 SHA 上完整重跑：

1. 在 active 状态创建快照 `#1` 和 `#2`；
2. 加载快照列表并比较同版本快照，结果为 `v2 → v2`、零变化；
3. 归档世界；
4. 归档 UI 明确进入只读模式；
5. 章节生成、故事弧线生成、素材导入、标签创建和快照创建等写控件隐藏或禁用；
6. 世界概览、章节历史、事件、搜索/标签浏览、快照列表/对比和 Markdown 导出继续可用；
7. 角色、关系、伏笔页面保持可读并显示只读提示；
8. 执行“取消归档当前小说”；
9. API 交叉核对返回世界状态 `active`；
10. 最新 `world_status_changed` 事件记录 `archived → active`，世界版本保持 `2 → 2`；
11. 标签创建、快照创建、章节生成、故事弧线、后续章节队列和素材导入控件全部恢复。

归档与恢复后事件总数为 7；状态变更没有错误推进世界版本。

---

## 7. 未通过门禁及明确阻塞原因

### 7.1 真实 PostgreSQL 测试

本轮使用一次性、唯一、可销毁的 loopback PostgreSQL 资源，并显式启用真实数据库测试许可：

- 并发/marker 测试：`5 passed, 2 deselected`；
- 恢复目标空库保护：`1 passed`；
- 测试后容器、卷、端口和临时连接均已清理；
- 未复用共享服务或生产式数据库。

两类真实 PostgreSQL 门禁均为 **PASS**。测试结果不并入默认套件的 `781 passed, 16 skipped` 计数。

### 7.2 真实 provider canary

本轮已满足真实调用的双重成本许可与显式 pytest 选择条件：

- `RUN_REAL_LLM_CANARY=1`；
- `LLM_CANARY_ACK_COST=1`；
- pytest 参数 `--run-real-llm`。

结果为 **8 passed**，因此门禁状态为 **PASS**。本次覆盖 Responses API 与 Chat Completions API 两种 mode；开篇证据 repair、重复/重叠/跨 check 复用和相邻段落错误索引等边界均通过，未发现 provider 包装器或成本门禁异常。

### 7.3 真实 LLM 首章隔离 E2E

使用一次性 Compose project `worldsim_real_e2e_92e6748`、API `127.0.0.1:18004`、独立数据库和 `LLM_MOCK=false` 执行。健康响应确认：`status=ok`、`migration.up_to_date=true`、`llm.mock=false`。

已完成：

- 注册唯一账户；
- 创建模板世界；
- 生成首章草稿；
- 获取审批预览；
- 观察到真实模型产生角色变化提案。

在 `approval_readiness` 阶段被业务质量门禁阻断：状态为 `blocked`，阻塞原因为开篇结构/模型提供的可定位证据未通过验证；Critic 报告和角色弧线报告尚未生成。因此未进入审批、版本推进、事件核验和 Markdown 导出，整条真实首章 E2E 状态为 **NOT PASS**，不是基础设施故障。隔离项目、卷、端口和测试数据已清理。

---

## 8. 已修复缺陷

### 开篇证据 repair 与事件描述 `[object Object]` 渲染

已在候选提交 `92e674886516f8d74823aacc9cd7222a0f7dc235` 修复或加固：

- 首章生成后最多执行一次 evidence-only repair；repair 只能替换 `opening_evidence`，不能改写正文或其它 generation 字段；
- repair 响应严格拒绝额外字段，并拒绝重复、重叠、跨 check 复用或同句证据；
- 首章服务端移除旧的 `±1` 段落索引自动纠正，统一使用严格 0-based 非空自然段校验；

### 事件描述 `[object Object]` 渲染

已在候选提交 `92e674886516f8d74823aacc9cd7222a0f7dc235` 保留修复：

- 正确读取真实后端事件结构 `payload.change.status`；
- 兼容历史字符串形态；
- 覆盖 `character_change` 与 `foreshadow_change`；
- 前端目标测试结果：`3 passed`；
- 前端全量测试和生产构建通过。

该缺陷不再作为 Beta 阻塞项。

---

## 9. Beta tag 前的最小收口清单

1. 修复或重新审查真实首章 E2E 中开篇结构/可定位证据质量门禁的剩余阻断问题；在新 SHA 上重跑真实 LLM 首章 E2E，至少完成审批、版本推进、事件和 Markdown 导出。
2. 若上述代码或质量契约改动影响写作链路，重新冻结 SHA，并至少重跑受影响测试、前端构建、mock 主流程、归档恢复抽查及真实首章 E2E；provider canary 已在当前 SHA 上通过，若改动影响 provider 链路则必须重跑。
3. 只有真实首章 E2E 通过、报告复核一致后，才单独决定是否创建 Beta tag；tag 与 push 必须另行执行并记录。

---

## 10. 发布建议

**建议：保留提交 `92e674886516f8d74823aacc9cd7222a0f7dc235` 作为当前 RC 收口候选，不创建 Beta tag，不 push。**

当前允许继续的工作：

- 修复或重新审查真实首章 E2E 的开篇结构/可定位证据质量门禁；
- 在新 SHA 上重跑真实首章 E2E，并在质量契约或 provider 链路发生变化时重跑真实 provider canary。

当前已确认：

- 真实 PostgreSQL 并发/marker 门禁通过；
- 真实 PostgreSQL 恢复目标空库保护通过；
- 真实 `pg_dump → pg_restore` 演练通过；
- `[object Object]` 时间线缺陷已修复；
- 共享服务未触碰，临时真实 E2E 资源已清理。

不允许的表述：

- 不得把真实首章 E2E 的 `approval_readiness` 阻断表述为完整流程通过；
- 不得把真实 provider canary 的 `8 passed` 外推为真实首章 E2E 已通过；
- 不得把 mock UI 章节质量称为真实模型质量；
- 不得把当前结果归属于旧提交 `055ace48...`。

---

## 11. 当前运行与证据保留状态

- mock UI 隔离栈 `worldsim_ui_055ace48` 仍在运行，以便复核；
- 真实 LLM E2E 隔离栈 `worldsim_real_e2e_92e6748` 已停止并删除其临时卷；
- 真实 E2E 的 API 端口 `18004`、临时数据库和测试数据已清理；
- 共享服务未触碰；
- 未创建 tag，未 push；
- 本报告为唯一未跟踪文件，未进入候选提交；
- 临时原始日志、容器、卷和 dump 已清理，报告仅保留结果摘要、退出码、关键计数、迁移 head 与 dump SHA-256；独立复验需按本报告记录的门禁重跑。

---

## 12. Beta 稳定化补充验证（2026-08-04）

本轮针对批准的 Beta 稳定化方案完成了以下收口，工作树仍未提交：

- LLM usage audit 使用独立短事务；草稿端点显式传入 audit session factory；提交、回滚、关闭均由审计事务自行管理。
- 审计关联对象遇到独立事务不可见的外键完整性错误时，降级为不带 `world_id/chapter_id/draft_id` 的审计记录，避免业务请求因 telemetry 失败而中断。
- `POST /worlds/draft-from-brief` 已覆盖 request-id 透传/生成、错误码矩阵、422 输入脱敏、provider 错误脱敏、真实 mock LLM 审计落库，以及 World/Chapter/Character/Relation/Foreshadow/EventLog 零领域写入。
- `WorldCreationForm` 自定义题材 focus 测试改为等待下一帧；失败恢复、保留编辑内容和重试成功回归均通过。
- 真实 LLM canary 默认仍不出网：`6 passed, 2 skipped`；本轮未启用成本确认，因此不把它解释为真实 provider 质量门禁通过。

验证结果：

- 后端：`819 passed, 10 skipped`；仅有既有 pytest/Alembic 弃用警告。
- 前端：`23` 个测试文件、`308 passed`；生产构建通过。
- Python `compileall` 通过；`git diff --check` 通过，仅报告既有 LF/CRLF 转换提示。
- 未创建 commit、tag 或 push；原报告中真实首章 E2E 的 `approval_readiness` 阻断仍有效，发布状态保持 **HOLD**。

---

**报告生成者**：OpenCoWork
**最终状态**：HOLD；真实 PostgreSQL/备份门禁已补齐，真实 provider canary 已通过，但真实首章 E2E 仍在 `approval_readiness` 被质量门禁阻断，完成修复或契约审查并重跑前不得创建 Beta tag。
