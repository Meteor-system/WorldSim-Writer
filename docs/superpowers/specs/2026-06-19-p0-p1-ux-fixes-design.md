# P0/P1 UX 修复（第一轮）设计

日期：2026-06-19
分支：feat/import-node-p0

## 背景

用户完成一次真实浏览器体验后报告了一批 P0/P1 UX 问题。从 `http://127.0.0.1:5173` 访问时 CORS 预检直接失败（Disallowed CORS origin），网络错误以裸英文 "Failed to fetch" 冒出，登录/注册无 loading 与字段校验，作品书架加载失败时错误与空状态同时出现且无重试入口，创建世界表单中角色/伏笔类型是英文自由输入、删除无确认、新增无聚焦。

本轮聚焦可验证的 P0 + 低风险 P1，**不**重写为完整五步创建向导（仅留后续建议）。

## 根因

1. **CORS**：`backend/app/main.py` 只 `allow_origins=[settings.frontend_origin]`，`config.py` 只有单值 `FRONTEND_ORIGIN`（默认 `http://localhost:5173`）。`127.0.0.1` 与 3000 端口均不在白名单，预检失败。
2. **网络错误文案**：`frontend/src/api/client.ts` 的 `apiRequest` 直接 `await fetch(...)`，fetch 抛出的 `TypeError: Failed to fetch` 未被捕获、未映射；非 2xx 仅透传后端 detail，未按状态码给出中文。
3. **登录体验**：`AuthPage.tsx` 无提交中状态、无字段校验，email input 缺 `type=email`/`required`。
4. **书架空状态**：`WorldPage.tsx` 书架视图无条件渲染"暂无活跃/归档小说"，与 `error` 并存，且无重试按钮。
5. **创建表单**：`WorldCreationForm.tsx` 角色/伏笔类型为英文 `input`；删除直接生效；新增角色无聚焦/高亮。

## 方案

### 后端

#### CORS 多源（P0-1）
- `config.py`：新增 `frontend_origins: str = Field(default='', alias='FRONTEND_ORIGINS')`，保留 `frontend_origin` 单值兼容。新增方法/属性 `cors_allow_origins` 计算最终列表：
  - 若 `FRONTEND_ORIGINS` 非空，按逗号拆分、去空白、去重，作为主列表；否则回退到 `[frontend_origin]`。
  - 始终并入开发默认四项：`http://localhost:5173`、`http://127.0.0.1:5173`、`http://localhost:3000`、`http://127.0.0.1:3000`（去重，顺序稳定）。
  - 生产可通过显式设置 `FRONTEND_ORIGINS` 收敛（开发默认项是附加的便利项，不做通配 `*`，因此不会无限放开到任意域）。
- `main.py`：`allow_origins=settings.cors_allow_origins`。
- `.env.example`：补 `FRONTEND_ORIGINS` 注释说明（逗号分隔，多值优先；留空则用 `FRONTEND_ORIGIN`）。

> 决策：开发默认四项始终并入，是为了让 `127.0.0.1`/`localhost` 两种本地访问与常见 3000 端口"开箱即用"。生产环境若需严格限制，应在反向代理层或通过部署配置处理；本轮不在应用层移除开发默认项，避免破坏本地体验，这一点在 `.env.example` 注释中说明。

#### 测试
新增 `backend/tests/test_cors.py`：
- 用 `TestClient` 发 `OPTIONS` 预检（带 `Origin: http://127.0.0.1:5173`、`Access-Control-Request-Method: POST`），断言响应含 `access-control-allow-origin` 等于该 Origin。
- 参数化覆盖四个开发 Origin。
- 直接对 `Settings` 单测 `cors_allow_origins`：多值优先、单值回退、去重、含开发默认项。

### 前端

#### 统一网络错误映射（P0-2）
`client.ts`：
- 抽出 `friendlyStatusMessage(status, detail)`：401→`登录状态已过期，请重新登录`；`>=500`→`服务暂时不可用，请稍后再试`；否则保留业务 detail（`formatApiError` 已有），避免裸英文。
- `apiRequest` 用 try/catch 包住 `fetch`：捕获 `TypeError`（含 message 含 `Failed to fetch`/`fetch`）→ 抛出 `无法连接服务器，请检查网络或稍后重试。`，开发环境（`import.meta.env.DEV`）追加 `开发提示：请检查 API_BASE_URL 或 CORS 白名单。`。
- 保留 `error.status` 供调用方分支。

#### 登录/注册（P0-3、P0-4、P1-13）
`AuthPage.tsx`：
- 加 `submitting` 状态：提交中两个按钮 `disabled`，文案改 `登录中…`/`注册中…`。
- 字段级校验（提交前拦截，不打接口）：
  - 邮箱：`type=email`、`required`；空→`请输入邮箱`，格式不符→`邮箱格式不正确`。
  - 密码：`required`；空→`请输入密码`；注册时长度 < 8→`注册密码至少 8 位`。
  - 用 `fieldErrors` 状态在字段下展示。
- 标题：`进入故事世界运营台` → `故事世界运营台`（更短，避免 `运营台` 断行突兀）。

#### 书架错误卡片 + 重试（P0-5、P1-6）
`WorldPage.tsx`：
- 区分"加载失败"与"成功返回空数组"：新增 `loadError` 状态（与现有 `error` 分离或复用 `error` + 一个 `worldsLoaded` 标志）。失败时书架渲染错误卡片：`作品书架加载失败` / `无法连接服务器，请稍后重试` / `重新加载`（按钮调用 `loadWorld`），**不**显示"暂无活跃/归档小说"。
- 仅当接口成功返回 `[]` 时显示空状态，并在活跃空状态内放 `创建新小说` CTA（调用 `startNewWorld`）。

#### 胚胎库失败文案（P1-7）
`WorldPage.tsx` `loadSeedLibrary` catch：`世界胚胎库暂不可用` → `在线胚胎库暂不可用，已为你展示本地内置模板。`（内置模板始终可见，文案不再与之冲突）。

#### 创建表单 select + 聚焦/高亮 + 删除撤销（P1-8/9/10/11/12）
`WorldCreationForm.tsx`：
- 新增常量 `CHARACTER_ROLE_OPTIONS`、`FORESHADOW_TYPE_OPTIONS`（中文 label / 英文 value）。
- 角色类型、伏笔类型 `input` → `select`（保存英文值；若现值不在选项内，附加一个"当前值"option 兜底，避免胚胎/草稿自定义值丢失）。
- 添加角色后：滚动并聚焦新卡片姓名输入框（`ref` + `useEffect` 跟踪新增 index），新卡片加短暂高亮 class（计时清除）。
- 删除角色/伏笔：改为撤销 toast —— 删除后展示 `已删除角色「X」[撤销]` / `已删除伏笔「Y」[撤销]`，点撤销恢复；一定时间后 toast 消失即永久删除。撤销需保存被删项及其原索引。

> 五步向导：**不做**。仅在本设计"后续建议"记录。

## 测试策略（TDD：先红后绿）

- 后端：`test_cors.py`（OPTIONS 预检 + Settings 单测）。运行相关与全量 `pytest`。
- 前端（先写失败测试再实现）：
  - `client.test.ts`：fetch TypeError→中文；401/500 映射。
  - `AuthPage.test.tsx`：loading 禁用、字段校验拦截、标题文案。
  - `WorldPage.test.tsx`：书架加载失败错误卡片 + 重试、空数组空状态 + CTA、胚胎库失败文案。
  - `WorldCreationForm.test.tsx`：角色/伏笔类型 select 中文显示且保存英文值、添加角色聚焦、删除撤销。
- `npm run test -- --run` 全绿，`npm run build` 通过。
- curl/Python 验证 OPTIONS `Origin: http://127.0.0.1:5173` 返回允许头。

## 不做（本轮）

- 完整五步创建向导（仅记录后续建议）。
- 改业务 API 语义。
- 触碰 cc-work worktree、push/merge、泄露 .env secret。

## 后续建议（五步向导铺垫）

将"一句话开书 / 选胚胎 / 模板 / 表单编辑 / 确认创建"重组为带进度指示的分步向导：第 1 步入口选择 → 第 2 步世界底层设定 → 第 3 步角色 → 第 4 步关系/伏笔 → 第 5 步确认与第一章目标。需单独 spec/plan，避免本轮大改爆炸。
