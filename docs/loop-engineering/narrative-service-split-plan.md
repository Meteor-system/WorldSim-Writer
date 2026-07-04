# narrative/service.py 上帝文件拆分重构计划（planning only）

状态：计划，不实现。目标是把 `backend/app/narrative/service.py`（1823 行，全项目最大源文件）
按职责拆成若干模块，同时保持 `router.py` 与全部后端测试零改动、全绿。

## 0. 现状盘点（已核对代码，非推测）

- `service.py` 目前承载：LLM 客户端封装、错误映射、归属/激活校验、世界上下文加载、执行上下文构造、
  prompt 构造（outline/writer/critique/critic/arc/revision/paragraph）、timeline_diff、草稿版本化、
  chapter session/draft 生成、大纲、写作、审稿（critique/critic/character-arc）、驳回、编辑、stash、
  diff、段落修订、整章修订、审批预览/一致性/就绪度、以及唯一写正史入口 `approve_chapter`。
- `router.py` 通过 `from app.narrative.service import (...)` 导入约 20 个函数；这是唯一的非测试导入方。
- 测试约束（红线级）：
  - **`monkeypatch.setattr(narrative_service, 'LLMClient', ...)` 出现 51 次**，全部指向
    `app.narrative.service.LLMClient`。当前能生效，是因为 `_model_client()` 在调用时从
    **自身所在模块的全局名字空间**解析 `LLMClient`。函数一旦搬到别的模块，就会解析到别的模块的
    `LLMClient`，monkeypatch 静默失效 → 这是拆分最大的风险点。
  - 直接符号导入只有一处：`from app.narrative.service import DEFAULT_ENTROPY_BUDGET, compute_timeline_diff`。
  - 以属性方式访问的私有 helper 只有 `_load_world_context`（3 次）。其余 `_model_client / _latest_draft /
    _draft_payload / _approval_change_set` 等测试都不直接访问。
- 三条业务红线：
  1. `approve_chapter` 是唯一写正史边界，内部 `select(World).with_for_update()` 行锁 +
     `world.owner_id != user.id → 403`，必须逐字保留。
  2. `_require_owned_chapter` 被 17 个端点复用，签名/行为不变。
  3. `compute_timeline_diff` / critique / critic / character-arc 只是审稿参考元数据，绝不能写
     `truth_canon` / projection / `world_version` / 正式 `EventLog`。

## 1. 目标模块划分

包结构（`backend/app/narrative/` 下）：

```
narrative/
  service.py          # 变为纯 re-export 门面（facade），对外契约不变
  llm_support.py      # LLM 客户端解析 + 模型错误映射（含 monkeypatch 兼容机制）
  timeline.py         # 确定性 timeline_diff / 熵预算（纯函数，审稿参考）
  prompts.py          # 所有 build_*_messages + 执行上下文格式化（纯函数）
  context.py          # 执行上下文构造/归一化
  shared.py           # 归属/激活校验 + 世界加载 + 草稿版本化 + _draft_payload 等共享 helper
  draft_service.py    # session/outline/draft/write 生成路径
  review_service.py   # critique / critic-report / character-arc-report
  approval_service.py # 审批分析：change-set / 一致性 / preview / consistency / readiness
  approval_commit.py  # approve_chapter（唯一写正史，红线 #1 独占一个文件）
  editing_service.py  # reject / edit / stash / diff / get_version / 段落修订 / 整章修订
```

分层为一个单向 DAG（下层不 import 上层），避免循环 import：

- **Layer 0（叶子，无 narrative 内部依赖）**：`timeline.py`、`prompts.py`、`llm_support.py`
- **Layer 1**：`shared.py`（import timeline）、`context.py`
- **Layer 2**：`draft_service`、`review_service`、`approval_service`（import shared/prompts/context/llm_support/timeline）
- **Layer 3**：`approval_commit`（import approval_service 的 change-set/一致性）、
  `editing_service`（仅 `revise_chapter_draft` import `approval_service.get_approval_readiness`）
- **门面**：`service.py` import 上述所有模块并 re-export

### 各模块承载的函数/常量

**llm_support.py**
- `SAFE_MODEL_RUNTIME_ERRORS`、`_map_model_error`、`_model_client`
- 理由：LLM 边界集中一处；`_model_client` 是 51 处 monkeypatch 的落点，需要专门的兼容机制（见 §2）。

**timeline.py**
- `DEFAULT_ENTROPY_BUDGET`、`_RESOLVED_FORESHADOW_STATUSES`、`compute_timeline_diff`
- 理由：纯函数、无 db、无副作用；红线 #3 的"审稿参考"语义在此隔离，物理上远离 approve 路径。

**prompts.py**
- `build_outline_messages`、`build_generation_messages`、`build_critique_messages`、
  `build_critic_report_messages`、`build_character_arc_report_messages`、`build_revision_messages`、
  `format_execution_context_for_prompt`、`_outline_context_payload`、`_jsonish`
- 理由：全部是对 model 对象只读的纯函数，天然可独立；集中后 prompt 迭代不再触碰业务逻辑。

**context.py**
- `build_manual_execution_context`、`normalize_execution_context`
- 理由：执行上下文的构造/版本校验自成一域（`WORLD_VERSION_MISMATCH` 在此产生）。

**shared.py**（共享 helper，见 §2）
- 校验/加载：`_require_owned_chapter`、`_ensure_world_is_active`、`_world_for_chapter`、`_load_world_context`
- 草稿：`_latest_draft`、`_create_draft_version`、`_split_paragraphs`、`_approved_chapter_count`、`_draft_payload`
- 通用：`_model_dump`、`validate_generation_ids`
- 理由：这些被 2 个以上服务模块复用；集中在最低层，任何服务模块都能安全 import 且不产生环。

**draft_service.py**
- `create_chapter_session`、`generate_chapter_outline`、`create_chapter_draft`、`write_chapter_from_outline`

**review_service.py**
- `CRITIC_DIMENSIONS`、`critique_chapter`、`generate_critic_report`、`get_critic_report`、
  `generate_character_arc_report`、`get_character_arc_report`、
  `_critic_report_payload`、`_character_arc_report_payload`、`_validate_character_arc_report_ids`

**approval_service.py**（只读分析，不写状态）
- change-set：`_change_index_set`、`_selected_changes`、`_approval_change_set`
- 一致性：`FORESHADOW_STATUS_ORDER`、`_consistency_warning`、`_consistency_summary`、`_goals_overlap`、
  `_evaluate_approval_consistency`
- 就绪度：`_readiness_check`、`_report_is_stale`、`_approval_readiness_summary`
- 端点：`get_approval_preview`、`get_approval_consistency`、`get_approval_readiness`

**approval_commit.py**（红线 #1 独占）
- `approve_chapter`
- 理由：唯一写正史入口单独成文件，行锁 + owner 校验 + world_version 自增 + EventLog 写入逐字迁移，
  review/patch 时"哪里能写正史"一目了然。import approval_service 复用 `_approval_change_set` 与
  `_evaluate_approval_consistency`（单向依赖）。

**editing_service.py**
- `reject_chapter`、`edit_chapter_draft`、`stash_chapter_draft`、`get_draft_diff`、
  `get_chapter_draft_version`、`revise_chapter_paragraph`、`revise_chapter_draft`、
  `_approval_readiness_for_revision`
- 理由：草稿态的非生成型改动集中在此；仅 `revise_chapter_draft` 需要 readiness，单向 import
  `approval_service`。

## 2. 共享 helper 归属与循环 import 规避

**归属**
- `_require_owned_chapter`、`_latest_draft`、`_draft_payload`、`_load_world_context` 等纯共享 helper →
  `shared.py`（Layer 1，最低可复用层）。
- `_approval_change_set` / `_evaluate_approval_consistency` 归属 `approval_service.py`，由
  `approval_commit.py` 单向 import——它们是"审批语义"而非通用 helper，放在审批域更内聚。
- `_model_client` 归属 `llm_support.py`。

**LLMClient monkeypatch 兼容机制（本次拆分的关键技术点）**

现状：`_model_client` 里 `client = llm_client or LLMClient()`，`LLMClient` 从 `service` 模块全局解析，
所以 `monkeypatch.setattr(narrative_service, 'LLMClient', ...)` 能生效。

拆分后所有生成函数会散落到 draft/review/editing 各模块，但它们仍统一走 `_model_client()`。为保证 51 处
patch 继续命中，`_model_client` 必须始终从**门面 `service` 模块**解析 `LLMClient`：

```python
# llm_support.py
def _model_client(llm_client: LLMClient | None = None) -> LLMClient:
    from app.narrative import service as _facade   # 调用时惰性 import，避免加载期循环
    settings = get_settings()
    client = llm_client or _facade.LLMClient()      # 始终读门面上被 patch 的 LLMClient
    if hasattr(client, 'mock'):
        client.mock = settings.llm_mock
    return client
```

配套：`service.py` 门面必须保留顶层名字 `from app.llm.client import LLMClient`，使 `service.LLMClient`
存在且可被 patch。惰性 import 只在函数调用时触发（此时所有模块已加载完毕），因此不构成加载期循环。
`llm_support.py` 模块顶层也 `from app.llm.client import LLMClient` 仅用于类型标注。

**循环规避总结**
- 依赖方向严格自上而下（Layer 3 → 2 → 1 → 0），门面在最上层。
- 唯一"反向"引用是 `_model_client` → `service`，且是函数体内惰性 import，加载期不触发。
- `approval_commit → approval_service`、`editing_service → approval_service` 均为单向，无回边。

## 3. 向后兼容策略：service.py 作为 re-export 门面

`service.py` 最终只做导入与再导出，对外契约（`router.py` 的 20 个导入、测试的
`narrative_service.<attr>` 与 `from app.narrative.service import X`）完全不变。

**关键实现细节：不要用 `from x import *`。** 星号 import 不会带入下划线前缀名字（如
`_load_world_context`，测试以属性方式访问），也无法保证覆盖直接导入的 `DEFAULT_ENTROPY_BUDGET`。
门面必须**显式**列出所有对外/被测试触及的名字（含私有），例如：

```python
# service.py（门面，示意）
from app.llm.client import LLMClient  # 保持可 patch

from app.narrative.timeline import (
    DEFAULT_ENTROPY_BUDGET, _RESOLVED_FORESHADOW_STATUSES, compute_timeline_diff,
)
from app.narrative.llm_support import SAFE_MODEL_RUNTIME_ERRORS, _map_model_error, _model_client
from app.narrative.prompts import (
    build_outline_messages, build_generation_messages, build_critique_messages,
    build_critic_report_messages, build_character_arc_report_messages,
    build_revision_messages, format_execution_context_for_prompt,
    _outline_context_payload, _jsonish,
)
from app.narrative.context import build_manual_execution_context, normalize_execution_context
from app.narrative.shared import (
    _require_owned_chapter, _ensure_world_is_active, _world_for_chapter, _load_world_context,
    _latest_draft, _create_draft_version, _split_paragraphs, _approved_chapter_count,
    _draft_payload, _model_dump, validate_generation_ids,
)
from app.narrative.draft_service import (
    create_chapter_session, generate_chapter_outline, create_chapter_draft, write_chapter_from_outline,
)
from app.narrative.review_service import (
    CRITIC_DIMENSIONS, critique_chapter, generate_critic_report, get_critic_report,
    generate_character_arc_report, get_character_arc_report,
    _critic_report_payload, _character_arc_report_payload, _validate_character_arc_report_ids,
)
from app.narrative.approval_service import (
    FORESHADOW_STATUS_ORDER, _change_index_set, _selected_changes, _approval_change_set,
    _consistency_warning, _consistency_summary, _goals_overlap, _evaluate_approval_consistency,
    _readiness_check, _report_is_stale, _approval_readiness_summary,
    get_approval_preview, get_approval_consistency, get_approval_readiness,
)
from app.narrative.approval_commit import approve_chapter
from app.narrative.editing_service import (
    reject_chapter, edit_chapter_draft, stash_chapter_draft, get_draft_diff,
    get_chapter_draft_version, revise_chapter_paragraph, revise_chapter_draft,
    _approval_readiness_for_revision,
)
```

`router.py` **不改动**——继续从 `service` 导入即可。（可选的后续清理：把 router 指向子模块，本次不做，降风险。）

## 4. 分步迁移顺序（每步独立跑通全绿）

每一步都是"移动代码 + 门面显式 re-export"的纯搬迁，不改逻辑。每步结束跑全量测试；改到 LLM 边界的步骤
额外跑 LLM 相关子集。

统一验证命令：
```
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && pytest -q'
```

- **Step 0 — 基线**：跑全量测试，记录绿色基线（约 363 个测试函数 / ~370 计数）。以"全绿"为门槛，
  不以固定数字为准（CLAUDE.md 记的 370 与实际收集数存在小差异，属参数化所致）。
- **Step 1 — timeline.py**：迁 `DEFAULT_ENTROPY_BUDGET`、`_RESOLVED_FORESHADOW_STATUSES`、
  `compute_timeline_diff`；门面 re-export。
  验证：`pytest -q` + 重点 `pytest tests/test_timeline_diff.py -q`（它 `from service import` 两个符号）。
- **Step 2 — prompts.py**：迁全部 `build_*` + `format_execution_context_for_prompt` +
  `_outline_context_payload` + `_jsonish`；re-export。
  验证：`pytest -q` + `pytest tests/test_chapter_execution_context.py tests/test_narrative_pipeline.py -q`。
- **Step 3 — llm_support.py（最高风险）**：迁 `_model_client`、`_map_model_error`、
  `SAFE_MODEL_RUNTIME_ERRORS`，并落地 §2 的门面惰性 import 兼容机制；门面保留 `LLMClient` 顶层名。
  验证：`pytest -q` **且** 专门跑所有含 `setattr(..., 'LLMClient', ...)` 的文件，重点
  `pytest tests/test_narrative_approval.py tests/test_narrative_pipeline.py tests/test_critic_reports.py tests/test_character_arc_reports.py -q`。
  确认 51 处 patch 全部仍生效（若失效会表现为真实/错误 client 被调用）。
- **Step 4 — shared.py**：迁校验/加载/草稿版本化/`_draft_payload`/`_model_dump`/`validate_generation_ids`；
  `_draft_payload` import timeline。re-export（含 `_load_world_context` 显式导出）。
  验证：`pytest -q`。
- **Step 5 — context.py**：迁 `build_manual_execution_context`、`normalize_execution_context`。
  验证：`pytest -q`。
- **Step 6 — draft_service.py**：迁 session/outline/draft/write。验证：`pytest -q`。
- **Step 7 — review_service.py**：迁 critique/critic/arc + 其 payload/校验 helper + `CRITIC_DIMENSIONS`。
  验证：`pytest -q` + `pytest tests/test_critic_reports.py tests/test_character_arc_reports.py -q`。
- **Step 8 — approval_service.py**：迁 change-set/一致性/就绪度 helper + preview/consistency/readiness 端点。
  验证：`pytest -q` + `pytest tests/test_state_consistency.py tests/test_narrative_approval.py -q`。
- **Step 9 — approval_commit.py（红线 #1）**：`approve_chapter` **逐字**迁移，行锁与 owner 校验不动。
  验证：`pytest -q` + `pytest tests/test_narrative_approval.py -q`，并单点验证
  `test_approve_chapter_updates_world_character_foreshadow_and_events`。
- **Step 10 — editing_service.py + 门面收尾**：迁 reject/edit/stash/diff/get_version/段落修订/整章修订；
  `service.py` 仅剩 import 与 re-export。
  验证：全量 `pytest -q` + 冒烟：
  `LLM_MOCK=true` 后台起 backend，`BASE_URL=http://localhost:8000 PYTHONIOENCODING=utf-8 python scripts/e2e_smoke.py`。

## 5. 风险与回滚点

| 风险 | 说明 | 缓解 | 回滚点 |
|---|---|---|---|
| LLMClient monkeypatch 失效 | 51 处 patch 指向 `narrative_service.LLMClient`；函数搬家后可能读到未 patch 的类 | §2 门面惰性 import；Step 3 专项验证 LLM 测试子集 | Step 3 单独成 commit，失败即 revert |
| 星号 re-export 漏下划线名 | `_load_world_context` 等以属性访问，`import *` 不带入 | 门面显式列名，不用 `*` | 补齐缺失名字即可 |
| 循环 import | 门面 import 子模块、`_model_client` 反指门面 | 严格分层 DAG + 惰性 import；每步 `python -c "import app.narrative.service"` 冒烟 | revert 当步 commit |
| approve_chapter 语义漂移 | 行锁/owner/version/EventLog 任何细节改动都破坏正史边界 | 逐字迁移、独占 `approval_commit.py`、Step 9 专项测试 | revert Step 9 |
| 审稿元数据误写正史 | timeline_diff/critique/arc 若被接入 approve | 物理隔离于独立模块；approve 路径不 import timeline/review | code review + 现有一致性测试 |
| 直接符号导入断裂 | `from service import DEFAULT_ENTROPY_BUDGET, compute_timeline_diff` | 门面 re-export；Step 1 即验证 | revert Step 1 |

**总体回滚策略**：每个 Step 是一个独立 commit，且是"纯代码搬迁 + 门面 re-export"，行为等价。任一步 `pytest`
不全绿，直接 `git revert` 该 commit 即恢复上一步的全绿状态，无需跨步骤联动回退。
