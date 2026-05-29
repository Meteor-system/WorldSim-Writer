# Phase 4: 伏笔账本增强 (Foreshadow Ledger Enhancement)

## 背景

当前伏笔系统已有基础 CRUD（创建/读取/更新/删除），状态支持 planted/advanced/resolved，但缺少：
1. 伏笔生命周期追踪（哪些章节触发/推进了哪些伏笔）
2. `expired` 状态（伏笔过期）
3. 状态迁移验证（防止非法状态跳转）
4. 陈旧伏笔检测（planted 太久未 resolved）
5. 前端看板视图

## 当前代码结构

- **Model**: `backend/app/foreshadow/models.py` — Foreshadow ORM 模型
- **Schema**: `backend/app/foreshadow/schemas.py` — Pydantic 请求/响应 schema
- **Service**: `backend/app/foreshadow/service.py` — 业务逻辑
- **Router**: `backend/app/foreshadow/router.py` — API 路由
- **Frontend**: `frontend/src/components/ForeshadowManager.tsx` — 伏笔管理组件
- **API Client**: `frontend/src/api/client.ts` — API 调用函数
- **Types**: `frontend/src/api/types.ts` — TypeScript 类型定义
- **Tests**: `backend/tests/test_foreshadow_crud.py` — 现有测试
- **Event Model**: `backend/app/event/models.py` — EventLog 模型（已有 foreshadow_change 事件记录）
- **Narrative Service**: `backend/app/narrative/service.py` — 章节审批时已有 foreshadow 状态更新和 EventLog 记录
- **Alembic**: `backend/alembic/versions/` — 数据库迁移

## 任务要求

### Part 1: 后端 — ForeshadowEvent 模型 + 状态迁移 + expired + 时间线API

1. **新增 ForeshadowEvent 模型** (`backend/app/foreshadow/models.py`)
   - 字段: id, foreshadow_id (FK), chapter_id (FK, nullable), event_type (planted/advanced/resolved/expired), note (text, nullable), created_at (datetime)
   - 表名: `foreshadow_events`

2. **状态迁移验证** (`backend/app/foreshadow/service.py`)
   - 合法迁移: planted → advanced, advanced → resolved, planted → expired, advanced → expired
   - 非法迁移返回 400 INVALID_STATUS_TRANSITION
   - 每次成功迁移自动创建 ForeshadowEvent 记录

3. **新增 `expired` 状态**
   - 在 Foreshadow model 的 status 字段支持 expired
   - 前端 STATUS_OPTIONS 也加入 expired

4. **伏笔时间线 API** (`GET /foreshadows/{id}/timeline`)
   - 返回该伏笔的所有 ForeshadowEvent 记录，按时间正序
   - 每条包含: event_type, chapter_id, chapter_title (关联查询), note, created_at

5. **伏笔列表增加 filter 参数**
   - `GET /worlds/{world_id}/foreshadows?status=planted` — 按状态过滤
   - 支持多状态: `?status=planted,advanced`

6. **陈旧伏笔检测 API** (`GET /worlds/{world_id}/foreshadows/stale`)
   - 返回所有 status=planted 且关联章节数 >= 3 章之后仍未推进的伏笔
   - 具体逻辑: 查询 status=planted 的伏笔，计算其 source_chapter_id 之后已 approve 的章节数量，如果 >= 3 则视为 stale
   - 响应包含: foreshadow 信息 + chapters_since_planted 数量 + alert_level (warning: 3-5章, critical: 6+章)

7. **章节审批时自动记录 ForeshadowEvent**
   - 在 `narrative/service.py` 的 `approve_chapter` 中，当 proposed_changes 包含 foreshadow 状态变更时，同时创建 ForeshadowEvent

8. **Alembic 迁移** — 创建 0005_add_foreshadow_events.py

9. **测试** — 在 `backend/tests/test_foreshadow_crud.py` 中添加:
   - test_foreshadow_status_transitions (合法/非法迁移)
   - test_foreshadow_timeline (时间线API)
   - test_foreshadow_filter_by_status (列表过滤)
   - test_foreshadow_stale_detection (陈旧检测)
   - test_foreshadow_event_created_on_transition (迁移时创建事件)

### Part 2: 前端 — 伏笔看板 + 生命周期 + 陈旧提醒

1. **伏笔看板视图** — 改造 ForeshadowManager.tsx
   - 添加视图切换按钮: 列表视图 / 看板视图
   - 看板视图: 4 列 (planted → advanced → resolved → expired)，伏笔卡片可拖拽改变状态
   - 每列顶部显示数量统计

2. **伏笔生命周期时间线** — 新增 ForeshadowTimeline 组件
   - 点击伏笔卡片展开详情时显示时间线
   - 每个事件节点: 时间 + 事件类型 + 关联章节标题 + 备注

3. **陈旧伏笔提醒**
   - 在 ForeshadowManager 顶部显示警告横幅
   - "⚠️ 有 N 条伏笔已超过 X 章未推进，建议尽快处理"
   - 点击跳转到看板视图的 planted 列

4. **状态颜色更新**
   - expired 状态: 红色系 (bg-red-100 text-red-800)

5. **API 调用更新** (`frontend/src/api/client.ts`)
   - getForeshadows 支持 status filter 参数
   - 新增 getForeshadowTimeline(foreshadowId)
   - 新增 getStaleForeshadows(worldId)

6. **类型更新** (`frontend/src/api/types.ts`)
   - 新增 ForeshadowEvent 类型
   - 新增 StaleForeshadow 类型
   - Foreshadow 的 status 字段类型更新为 union type

## 技术约束

- 测试环境使用 SQLite + JSONB→JSON 编译（见 conftest.py）
- 不要使用 delegate_task 或子代理，直接在当前目录执行
- 所有测试必须通过: `cd /opt/WorldSim-Writer/backend && python -m pytest tests/ -x -v`
- 前端构建必须成功: `cd /opt/WorldSim-Writer/frontend && npm run build`
- 使用 superpowers 标准流程

## 验收标准

1. 所有新测试通过
2. 前端构建成功
3. git commit 包含所有变更
4. 伏笔状态迁移有完整验证
5. 看板视图可正常切换和展示
6. 陈旧伏笔检测逻辑正确
