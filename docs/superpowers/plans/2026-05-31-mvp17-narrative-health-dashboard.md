# MVP17 Narrative Health Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only Narrative Health dashboard that aggregates critic, character arc, foreshadow pressure, chapter history, and event signals at world level.

**Architecture:** Backend extends the existing `narrative_control_center` domain with a world-scoped health endpoint and deterministic heuristics over existing tables/JSON reports. Frontend adds typed API access and a focused panel mounted in `WorldPage` next to Next Chapter Prep, Timeline, Search, and Archive panels.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, React, TypeScript, Vitest, Testing Library, Vite.

---

## File Structure

- Create: `backend/tests/test_narrative_health.py`
  - Backend TDD coverage for baseline health, risk aggregation, foreshadow pressure, and owner scope.
- Modify: `backend/app/narrative_control_center/schemas.py`
  - Add health metric/risk/response schemas.
- Modify: `backend/app/narrative_control_center/service.py`
  - Add `get_narrative_health()` and small scoring/risk helper functions.
- Modify: `backend/app/narrative_control_center/router.py`
  - Add `GET /worlds/{world_id}/narrative-health`.
- Modify: `frontend/src/api/types.ts`
  - Add health response types.
- Modify: `frontend/src/api/client.ts`
  - Add `getNarrativeHealth()` helper.
- Modify: `frontend/src/api/client.test.ts`
  - Add helper URL-construction test.
- Create: `frontend/src/world/NarrativeHealthPanel.tsx`
  - Render score, status, metric cards, risks, actions, loading/error/empty states.
- Create: `frontend/src/world/NarrativeHealthPanel.test.tsx`
  - Component behavior tests.
- Modify: `frontend/src/world/WorldPage.tsx`
  - Load and mount the panel.
- Modify: `frontend/src/world/WorldPage.test.tsx`
  - Mock API and assert panel is present.

---

### Task 1: Backend Narrative Health Endpoint

**Files:**
- Create: `backend/tests/test_narrative_health.py`
- Modify: `backend/app/narrative_control_center/schemas.py`
- Modify: `backend/app/narrative_control_center/service.py`
- Modify: `backend/app/narrative_control_center/router.py`

- [ ] **Step 1: Write failing backend tests**

Create `backend/tests/test_narrative_health.py`:

```python
from app.narrative.models import Chapter, ChapterDraft
from app.world.service import count_approved_chapters


def register(client, email='health@example.com'):
    response = client.post('/auth/register', json={'email': email, 'password': 'strongpass123'})
    return response.json()['access_token']


def auth(token):
    return {'Authorization': f'Bearer {token}'}


def custom_world_payload():
    return {
        'title': '群星边境',
        'genre_template': 'sci_fi',
        'truth_canon': '边境殖民地依赖一座濒临失控的跃迁灯塔。',
        'tone_profile': {'style': '冷峻太空歌剧'},
        'starter_assets': {
            'characters': [
                {'name': '许砚', 'role_type': 'protagonist', 'current_goals': ['查明灯塔异常']},
                {'name': '莱娜·周', 'role_type': 'rival', 'current_goals': ['封锁维修甲板']},
            ],
            'relations': [],
            'foreshadows': [
                {
                    'title': '黑匣子脉冲',
                    'description': '废弃黑匣子收到来自未来的求救信号。',
                    'foreshadow_type': 'signal_clue',
                    'status': 'planted',
                    'urgency_level': 5,
                    'related_character_indexes': [0, 1],
                }
            ],
        },
    }


def create_approved_chapter_with_reports(db_session, world_id, character_id, foreshadow_id):
    chapter = Chapter(
        world_id=world_id,
        title='第一章 灯塔密令',
        status='approved',
        draft_version=1,
        approved_version=1,
        base_world_version=1,
        approved_content='许砚发现灯塔核心的黑匣子脉冲。',
        chapter_goal='推进灯塔异常。',
        critique_report={
            'overall_score': 52,
            'summary': '节奏和对白存在明显风险。',
            'issues': [
                {'severity': 'high', 'dimension': 'pacing', 'message': '开头缺少抓力。'},
                {'severity': 'medium', 'dimension': 'dialogue_quality', 'message': '对白功能化。'},
            ],
            'dimensions': {},
            'suggestions': ['重写开头钩子。'],
            'draft_version': 1,
            'current_draft_version': 1,
            'is_stale': False,
        },
        character_arc_report={
            'summary': '许砚弧线存在跳跃。',
            'character_arcs': [
                {
                    'character_id': character_id,
                    'name': '许砚',
                    'continuity_risk': 'high',
                    'risk_reason': '突然接受企业安保帮助，缺少铺垫。',
                }
            ],
            'relationship_notes': [
                {
                    'source_character_id': character_id,
                    'target_character_id': character_id,
                    'source_name': '许砚',
                    'target_name': '许砚',
                    'risk_level': 'medium',
                    'risk_reason': '内心转折缺少承接。',
                }
            ],
            'progression_hints': [],
            'draft_version': 1,
            'current_draft_version': 1,
            'is_stale': False,
        },
    )
    db_session.add(chapter)
    db_session.flush()
    db_session.add(
        ChapterDraft(
            chapter_id=chapter.id,
            draft_version=1,
            content=chapter.approved_content,
            context_summary='灯塔异常推进。',
            review_hints=[],
            proposed_changes={'foreshadows': [{'foreshadow_id': foreshadow_id, 'status': 'advanced'}]},
            source_world_version=1,
        )
    )
    db_session.commit()
    return chapter


def test_narrative_health_returns_baseline_for_new_world(client):
    token = register(client)
    world = client.post('/worlds', headers=auth(token), json=custom_world_payload()).json()

    response = client.get(f"/worlds/{world['id']}/narrative-health", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['world_id'] == world['id']
    assert payload['health_score'] >= 80
    assert payload['status'] in {'healthy', 'watch'}
    assert any(metric['key'] == 'approved_chapters' for metric in payload['metrics'])
    assert any(action['action_key'] == 'write_first_chapter' for action in payload['suggested_actions'])


def test_narrative_health_aggregates_critic_and_arc_risks(client, db_session):
    token = register(client, 'health-risks@example.com')
    world = client.post('/worlds', headers=auth(token), json=custom_world_payload()).json()
    overview = client.get(f"/worlds/{world['id']}/overview", headers=auth(token)).json()
    character_id = overview['characters'][0]['id']
    foreshadow_id = overview['foreshadows'][0]['id']
    create_approved_chapter_with_reports(db_session, world['id'], character_id, foreshadow_id)

    response = client.get(f"/worlds/{world['id']}/narrative-health", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'at_risk'
    assert payload['health_score'] < 80
    assert payload['summary']['approved_chapter_count'] == count_approved_chapters(db_session, world['id'])
    risk_sources = {risk['source'] for risk in payload['risks']}
    assert {'critic', 'character_arc'}.issubset(risk_sources)
    assert any('开头缺少抓力' in risk['message'] for risk in payload['risks'])
    assert any(action['action_key'] == 'revise_latest_chapter' for action in payload['suggested_actions'])


def test_narrative_health_surfaces_high_pressure_foreshadow(client):
    token = register(client, 'health-foreshadow@example.com')
    world = client.post('/worlds', headers=auth(token), json=custom_world_payload()).json()

    response = client.get(f"/worlds/{world['id']}/narrative-health", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert any(risk['source'] == 'foreshadow' and risk['object_title'] == '黑匣子脉冲' for risk in payload['risks'])
    assert any(metric['key'] == 'high_pressure_foreshadows' and metric['value'] >= 1 for metric in payload['metrics'])


def test_narrative_health_is_limited_to_owner(client):
    owner_token = register(client, 'health-owner@example.com')
    other_token = register(client, 'health-other@example.com')
    world = client.post('/worlds', headers=auth(owner_token), json=custom_world_payload()).json()

    response = client.get(f"/worlds/{world['id']}/narrative-health", headers=auth(other_token))

    assert response.status_code == 403
    assert response.json()['detail'] == 'FORBIDDEN'
```

- [ ] **Step 2: Run backend tests to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_health.py -v
```

Expected: FAIL because `/worlds/{world_id}/narrative-health` is not implemented.

- [ ] **Step 3: Add backend schemas**

Append to `backend/app/narrative_control_center/schemas.py`:

```python
class NarrativeHealthMetric(BaseModel):
    key: str
    label: str
    value: int | float
    status: str
    detail: str


class NarrativeHealthRisk(BaseModel):
    severity: str
    source: str
    message: str
    object_type: str | None = None
    object_id: int | None = None
    object_title: str | None = None
    suggested_action: str


class NarrativeHealthAction(BaseModel):
    action_key: str
    label: str
    detail: str


class NarrativeHealthResponse(BaseModel):
    world_id: int
    world_version: int
    health_score: int
    status: str
    summary: dict
    metrics: list[NarrativeHealthMetric]
    risks: list[NarrativeHealthRisk]
    suggested_actions: list[NarrativeHealthAction]
```

- [ ] **Step 4: Add backend health service**

Modify `backend/app/narrative_control_center/service.py` after `_recent_events()`:

```python
def _clamp_score(score: int) -> int:
    return max(0, min(100, score))


def _health_metric(key: str, label: str, value: int | float, metric_status: str, detail: str) -> dict:
    return {'key': key, 'label': label, 'value': value, 'status': metric_status, 'detail': detail}


def _health_risk(severity: str, source: str, message: str, suggested_action: str, object_type=None, object_id=None, object_title=None) -> dict:
    return {
        'severity': severity,
        'source': source,
        'message': message,
        'object_type': object_type,
        'object_id': object_id,
        'object_title': object_title,
        'suggested_action': suggested_action,
    }


def _critic_reports(chapters: list[Chapter]) -> list[dict]:
    return [chapter.critique_report for chapter in chapters if chapter.critique_report]


def _arc_reports(chapters: list[Chapter]) -> list[dict]:
    return [chapter.character_arc_report for chapter in chapters if chapter.character_arc_report]


def _average_score(reports: list[dict]) -> int | None:
    scores = [int(report.get('overall_score')) for report in reports if report.get('overall_score') is not None]
    if not scores:
        return None
    return round(sum(scores) / len(scores))


def get_narrative_health(db: Session, user: User, world_id: int) -> dict:
    world = require_owned_world(db, user, world_id)
    approved_chapters = list(db.scalars(_approved_chapters_query(world.id)))
    latest_chapter = approved_chapters[-1] if approved_chapters else None
    critic_reports = _critic_reports(approved_chapters)
    arc_reports = _arc_reports(approved_chapters)
    average_critic_score = _average_score(critic_reports)
    ledger = build_foreshadow_ledger(db, world)
    recent_event_count = db.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world.id)) or 0

    risks: list[dict] = []
    high_critic_count = 0
    medium_critic_count = 0
    for chapter in approved_chapters:
        for issue in (chapter.critique_report or {}).get('issues', []):
            severity = issue.get('severity')
            if severity == 'high':
                high_critic_count += 1
                risks.append(_health_risk('high', 'critic', issue.get('message') or 'Critic 高风险问题。', '修订最近章节或重新生成 Critic 报告。', 'chapter', chapter.id, chapter.title))
            elif severity == 'medium':
                medium_critic_count += 1
                risks.append(_health_risk('medium', 'critic', issue.get('message') or 'Critic 中风险问题。', '复核对应章节的节奏、对白或结构。', 'chapter', chapter.id, chapter.title))

    high_arc_count = 0
    medium_arc_count = 0
    for chapter in approved_chapters:
        report = chapter.character_arc_report or {}
        for arc in report.get('character_arcs', []):
            risk = arc.get('continuity_risk')
            if risk == 'high':
                high_arc_count += 1
                risks.append(_health_risk('high', 'character_arc', arc.get('risk_reason') or '角色弧线存在高风险。', '在下一章补足角色选择与转折铺垫。', 'character', arc.get('character_id'), arc.get('name')))
            elif risk == 'medium':
                medium_arc_count += 1
                risks.append(_health_risk('medium', 'character_arc', arc.get('risk_reason') or '角色弧线存在中风险。', '复核角色弧线连续性。', 'character', arc.get('character_id'), arc.get('name')))
        for note in report.get('relationship_notes', []):
            risk = note.get('risk_level')
            title = f"{note.get('source_name', '角色')} → {note.get('target_name', '角色')}"
            if risk == 'high':
                high_arc_count += 1
                risks.append(_health_risk('high', 'character_arc', note.get('risk_reason') or '关系推进存在高风险。', '补足关系变化的场景因果。', 'relationship', None, title))
            elif risk == 'medium':
                medium_arc_count += 1
                risks.append(_health_risk('medium', 'character_arc', note.get('risk_reason') or '关系推进存在中风险。', '复核关系变化承接。', 'relationship', None, title))

    high_pressure_entries = ledger['high_pressure']
    for entry in high_pressure_entries:
        foreshadow = entry['foreshadow']
        risks.append(_health_risk('medium', 'foreshadow', '；'.join(entry.get('pressure_reasons') or []) or '高压伏笔需要推进。', '优先在下一章推进或回收该伏笔。', 'foreshadow', foreshadow.id, foreshadow.title))

    score = 100
    score -= high_critic_count * 12
    score -= medium_critic_count * 6
    score -= high_arc_count * 12
    score -= medium_arc_count * 6
    score -= len(high_pressure_entries) * 5
    if not approved_chapters:
        score -= 5
    health_score = _clamp_score(score)
    has_high_risk = any(risk['severity'] == 'high' for risk in risks)
    has_medium_risk = any(risk['severity'] == 'medium' for risk in risks)
    if health_score < 60 or has_high_risk:
        health_status = 'at_risk'
    elif health_score < 80 or has_medium_risk:
        health_status = 'watch'
    else:
        health_status = 'healthy'

    metrics = [
        _health_metric('approved_chapters', '已批准章节', len(approved_chapters), 'ok' if approved_chapters else 'watch', '已正式写入世界历史的章节数量。'),
        _health_metric('average_critic_score', '平均 Critic 分', average_critic_score or 0, 'ok' if average_critic_score is None or average_critic_score >= 75 else 'watch', '来自已存储 Critic 报告的平均分。'),
        _health_metric('critic_issues', 'Critic 风险', high_critic_count + medium_critic_count, 'risk' if high_critic_count else 'watch' if medium_critic_count else 'ok', f'高风险 {high_critic_count}，中风险 {medium_critic_count}。'),
        _health_metric('character_arc_risks', '角色弧线风险', high_arc_count + medium_arc_count, 'risk' if high_arc_count else 'watch' if medium_arc_count else 'ok', f'高风险 {high_arc_count}，中风险 {medium_arc_count}。'),
        _health_metric('open_foreshadows', '开放伏笔', ledger['summary']['open_count'], 'watch' if ledger['summary']['open_count'] else 'ok', '仍未 resolved/expired 的伏笔数量。'),
        _health_metric('high_pressure_foreshadows', '高压伏笔', len(high_pressure_entries), 'watch' if high_pressure_entries else 'ok', '来自 Foreshadow Ledger 的高压伏笔。'),
        _health_metric('recent_events', '正式事件', recent_event_count, 'ok', '当前世界累计正式事件数量。'),
    ]

    actions = []
    if not approved_chapters:
        actions.append({'action_key': 'write_first_chapter', 'label': '生成第一章', 'detail': '当前世界尚无已批准章节，先完成首章闭环。'})
    if has_high_risk:
        actions.append({'action_key': 'revise_latest_chapter', 'label': '优先修订最近章节', 'detail': '存在高风险 Critic 或角色弧线问题，建议修订后再继续。'})
    if high_pressure_entries:
        actions.append({'action_key': 'advance_foreshadow', 'label': '推进高压伏笔', 'detail': '下一章目标应优先处理高压伏笔。'})
    if latest_chapter and not actions:
        actions.append({'action_key': 'continue_next_chapter', 'label': '继续下一章', 'detail': '当前没有高风险阻塞，可以进入下一章准备台。'})

    risks.sort(key=lambda item: {'high': 0, 'medium': 1, 'low': 2}.get(item['severity'], 3))
    return {
        'world_id': world.id,
        'world_version': world.world_version,
        'health_score': health_score,
        'status': health_status,
        'summary': {
            'approved_chapter_count': len(approved_chapters),
            'latest_chapter_id': latest_chapter.id if latest_chapter else None,
            'latest_chapter_title': latest_chapter.title if latest_chapter else None,
            'average_critic_score': average_critic_score,
            'high_risk_count': sum(1 for risk in risks if risk['severity'] == 'high'),
            'medium_risk_count': sum(1 for risk in risks if risk['severity'] == 'medium'),
            'open_foreshadow_count': ledger['summary']['open_count'],
            'high_pressure_foreshadow_count': len(high_pressure_entries),
        },
        'metrics': metrics,
        'risks': risks[:10],
        'suggested_actions': actions,
    }
```

- [ ] **Step 5: Add backend route**

Modify `backend/app/narrative_control_center/router.py`:

1. Import `NarrativeHealthResponse`.
2. Import `get_narrative_health`.
3. Add route:

```python
@router.get('/worlds/{world_id}/narrative-health', response_model=NarrativeHealthResponse)
def narrative_health(
    world_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> NarrativeHealthResponse:
    return NarrativeHealthResponse.model_validate(get_narrative_health(db, current_user, world_id))
```

- [ ] **Step 6: Run backend tests to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_health.py -v
```

Expected: PASS.

---

### Task 2: Frontend API Helper and Types

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/api/client.test.ts`

- [ ] **Step 1: Write failing API helper test**

Modify `frontend/src/api/client.test.ts`:

1. Add `getNarrativeHealth` to the import list.
2. Add this test near other narrative control center API tests:

```ts
it('calls narrative health endpoint', async () => {
  const fetchMock = vi.fn().mockResolvedValueOnce(jsonResponse({
    world_id: 7,
    world_version: 2,
    health_score: 84,
    status: 'watch',
    summary: {},
    metrics: [],
    risks: [],
    suggested_actions: [],
  }));
  vi.stubGlobal('fetch', fetchMock);

  const response = await getNarrativeHealth(7);

  expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/worlds/7/narrative-health', expect.any(Object));
  expect(response.health_score).toBe(84);
});
```

- [ ] **Step 2: Run API test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts
```

Expected: FAIL because `getNarrativeHealth` is not exported.

- [ ] **Step 3: Add frontend health types**

Append after `NextChapterPrepResponse` in `frontend/src/api/types.ts`:

```ts
export type NarrativeHealthMetric = {
  key: string;
  label: string;
  value: number;
  status: string;
  detail: string;
};

export type NarrativeHealthRisk = {
  severity: string;
  source: string;
  message: string;
  object_type: string | null;
  object_id: number | null;
  object_title: string | null;
  suggested_action: string;
};

export type NarrativeHealthAction = {
  action_key: string;
  label: string;
  detail: string;
};

export type NarrativeHealthResponse = {
  world_id: number;
  world_version: number;
  health_score: number;
  status: 'healthy' | 'watch' | 'at_risk';
  summary: Record<string, unknown>;
  metrics: NarrativeHealthMetric[];
  risks: NarrativeHealthRisk[];
  suggested_actions: NarrativeHealthAction[];
};
```

- [ ] **Step 4: Add `getNarrativeHealth()` helper**

Modify `frontend/src/api/client.ts`:

1. Add `NarrativeHealthResponse` to imports.
2. Add after `getNextChapterPrep()`:

```ts
export function getNarrativeHealth(worldId: number) {
  return apiRequest<NarrativeHealthResponse>(`/worlds/${worldId}/narrative-health`);
}
```

- [ ] **Step 5: Run API test to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts
```

Expected: PASS.

---

### Task 3: Narrative Health Panel

**Files:**
- Create: `frontend/src/world/NarrativeHealthPanel.tsx`
- Create: `frontend/src/world/NarrativeHealthPanel.test.tsx`

- [ ] **Step 1: Write failing panel tests**

Create `frontend/src/world/NarrativeHealthPanel.test.tsx`:

```tsx
import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import type { NarrativeHealthResponse } from '../api/types';
import { NarrativeHealthPanel } from './NarrativeHealthPanel';

const health: NarrativeHealthResponse = {
  world_id: 7,
  world_version: 3,
  health_score: 58,
  status: 'at_risk',
  summary: { approved_chapter_count: 1, high_risk_count: 1 },
  metrics: [
    { key: 'approved_chapters', label: '已批准章节', value: 1, status: 'ok', detail: '已正式写入世界历史的章节数量。' },
    { key: 'critic_issues', label: 'Critic 风险', value: 2, status: 'risk', detail: '高风险 1，中风险 1。' },
  ],
  risks: [
    {
      severity: 'high',
      source: 'critic',
      message: '开头缺少抓力。',
      object_type: 'chapter',
      object_id: 11,
      object_title: '第一章 灯塔密令',
      suggested_action: '修订最近章节或重新生成 Critic 报告。',
    },
  ],
  suggested_actions: [
    { action_key: 'revise_latest_chapter', label: '优先修订最近章节', detail: '存在高风险问题。' },
  ],
};

afterEach(() => cleanup());

describe('NarrativeHealthPanel', () => {
  it('renders score, metrics, risks, and actions', () => {
    render(<NarrativeHealthPanel health={health} loading={false} error="" />);

    expect(screen.getByText('Narrative Health')).toBeInTheDocument();
    expect(screen.getByText('58/100')).toBeInTheDocument();
    expect(screen.getByText('高风险')).toBeInTheDocument();
    expect(screen.getByText('Critic 风险')).toBeInTheDocument();
    expect(screen.getByText('开头缺少抓力。')).toBeInTheDocument();
    expect(screen.getByText('优先修订最近章节')).toBeInTheDocument();
  });

  it('renders no-risk state', () => {
    render(<NarrativeHealthPanel health={{ ...health, health_score: 92, status: 'healthy', risks: [] }} loading={false} error="" />);

    expect(screen.getByText('健康')).toBeInTheDocument();
    expect(screen.getByText('当前没有高风险叙事问题。')).toBeInTheDocument();
  });

  it('renders loading and error states', () => {
    const { rerender } = render(<NarrativeHealthPanel health={null} loading error="" />);
    expect(screen.getByRole('status')).toHaveTextContent('正在加载叙事健康度...');

    rerender(<NarrativeHealthPanel health={null} loading={false} error="health down" />);
    expect(screen.getByRole('alert')).toHaveTextContent('health down');
  });
});
```

- [ ] **Step 2: Run panel tests to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/NarrativeHealthPanel.test.tsx
```

Expected: FAIL because `NarrativeHealthPanel` does not exist.

- [ ] **Step 3: Implement panel**

Create `frontend/src/world/NarrativeHealthPanel.tsx`:

```tsx
import type { NarrativeHealthResponse } from '../api/types';

type Props = {
  health: NarrativeHealthResponse | null;
  loading?: boolean;
  error?: string;
};

const STATUS_LABELS: Record<NarrativeHealthResponse['status'], string> = {
  healthy: '健康',
  watch: '观察',
  at_risk: '高风险',
};

const STATUS_CLASS: Record<NarrativeHealthResponse['status'], string> = {
  healthy: 'bg-emerald-50 text-emerald-900 border-emerald-200',
  watch: 'bg-orange-50 text-orange-950 border-orange-200',
  at_risk: 'bg-red-50 text-red-950 border-red-200',
};

function riskClass(severity: string): string {
  if (severity === 'high') return 'border-red-300 bg-red-50 text-red-950';
  if (severity === 'medium') return 'border-orange-300 bg-orange-50 text-orange-950';
  return 'border-amber-900/10 bg-amber-50/35 text-[#3b2511]';
}

export function NarrativeHealthPanel({ health, loading, error }: Props) {
  if (loading) {
    return (
      <section className="book-card p-5">
        <p className="ink-muted" role="status">正在加载叙事健康度...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="book-card p-5">
        <p className="paper-error" role="alert">{error}</p>
      </section>
    );
  }

  if (!health) {
    return (
      <section className="book-card p-5">
        <p className="ink-muted">叙事健康度暂无数据。</p>
      </section>
    );
  }

  return (
    <section className="book-card space-y-5 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="chapter-kicker">Risk Dashboard</p>
          <h2 className="text-2xl font-black text-[#34210f]">Narrative Health</h2>
          <p className="manuscript mt-2 text-sm text-[#5e3b1c]">汇总 Critic、角色弧线、伏笔压力与正式事件信号，只提供建议，不修改世界状态。</p>
        </div>
        <div className={`rounded-2xl border px-4 py-3 text-right ${STATUS_CLASS[health.status]}`}>
          <p className="text-3xl font-black">{health.health_score}/100</p>
          <p className="text-sm font-bold">{STATUS_LABELS[health.status]}</p>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        {health.metrics.map((metric) => (
          <article key={metric.key} className="rounded-2xl border border-amber-900/10 bg-white/35 p-4">
            <div className="flex items-start justify-between gap-2">
              <h3 className="font-black text-[#3b2511]">{metric.label}</h3>
              <span className="rounded-full bg-amber-100 px-3 py-1 text-sm font-bold text-[#5e3b1c]">{metric.value}</span>
            </div>
            <p className="manuscript mt-2 text-sm">{metric.detail}</p>
          </article>
        ))}
      </div>

      <div className="rounded-2xl bg-white/35 p-4">
        <h3 className="font-black text-[#3b2511]">叙事风险</h3>
        {health.risks.length === 0 ? (
          <p className="ink-muted mt-2 text-sm">当前没有高风险叙事问题。</p>
        ) : (
          <div className="mt-3 space-y-3">
            {health.risks.map((risk, index) => (
              <article key={`${risk.source}-${risk.object_id ?? index}`} className={`rounded-xl border p-3 ${riskClass(risk.severity)}`}>
                <p className="text-sm font-black">[{risk.severity}] {risk.source}{risk.object_title ? ` · ${risk.object_title}` : ''}</p>
                <p className="manuscript mt-2 text-sm">{risk.message}</p>
                <p className="manuscript mt-1 text-sm">建议：{risk.suggested_action}</p>
              </article>
            ))}
          </div>
        )}
      </div>

      {health.suggested_actions.length > 0 && (
        <div className="rounded-2xl bg-amber-50/60 p-4">
          <h3 className="font-black text-[#3b2511]">建议下一步</h3>
          <div className="mt-3 space-y-2">
            {health.suggested_actions.map((action) => (
              <p key={action.action_key} className="manuscript text-sm"><strong>{action.label}</strong>：{action.detail}</p>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
```

- [ ] **Step 4: Run panel tests to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/NarrativeHealthPanel.test.tsx
```

Expected: PASS.

---

### Task 4: WorldPage Integration

**Files:**
- Modify: `frontend/src/world/WorldPage.tsx`
- Modify: `frontend/src/world/WorldPage.test.tsx`

- [ ] **Step 1: Write failing WorldPage integration test**

Modify `frontend/src/world/WorldPage.test.tsx`:

1. Import `getNarrativeHealth`.
2. Add `getNarrativeHealth: vi.fn(),` to `vi.mock('../api/client', ...)`.
3. Reset it in `beforeEach()`.
4. Mock a resolved response in `beforeEach()`:

```ts
vi.mocked(getNarrativeHealth).mockResolvedValue({
  world_id: 7,
  world_version: 2,
  health_score: 88,
  status: 'healthy',
  summary: {},
  metrics: [{ key: 'approved_chapters', label: '已批准章节', value: 1, status: 'ok', detail: '已正式写入世界历史的章节数量。' }],
  risks: [],
  suggested_actions: [{ action_key: 'continue_next_chapter', label: '继续下一章', detail: '当前没有高风险阻塞。' }],
});
```

5. In the `loads and displays Chapter History and Next Chapter Prep panels` test, add:

```ts
expect(getNarrativeHealth).toHaveBeenCalledWith(7);
expect(await screen.findByText('Narrative Health')).toBeInTheDocument();
```

- [ ] **Step 2: Run WorldPage test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: FAIL because panel is not mounted or API is not called.

- [ ] **Step 3: Integrate health loading into `WorldPage`**

Modify `frontend/src/world/WorldPage.tsx`:

1. Import `getNarrativeHealth`.
2. Import `NarrativeHealthResponse` type.
3. Import `NarrativeHealthPanel`.
4. Add state:

```ts
const [narrativeHealth, setNarrativeHealth] = useState<NarrativeHealthResponse | null>(null);
const [narrativeHealthLoading, setNarrativeHealthLoading] = useState(false);
const [narrativeHealthError, setNarrativeHealthError] = useState('');
```

5. In `loadNarrativeControlCenter()`, load health with its own degraded error path:

```ts
setNarrativeHealthLoading(true);
setNarrativeHealthError('');
try {
  setNarrativeHealth(await getNarrativeHealth(worldId));
} catch {
  setNarrativeHealth(null);
  setNarrativeHealthError('叙事健康度暂不可用');
} finally {
  setNarrativeHealthLoading(false);
}
```

6. Mount before `NextChapterPrepPanel`:

```tsx
<NarrativeHealthPanel health={narrativeHealth} loading={narrativeHealthLoading} error={narrativeHealthError} />
```

- [ ] **Step 4: Run WorldPage test to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: PASS.

---

### Task 5: Final Verification, Commit, Merge

**Files:**
- All files changed above.

- [ ] **Step 1: Run backend targeted tests**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_health.py tests/test_narrative_control_center.py tests/test_foreshadow_crud.py -v
```

Expected: PASS.

- [ ] **Step 2: Run frontend targeted tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts src/world/NarrativeHealthPanel.test.tsx src/world/WorldPage.test.tsx
```

Expected: PASS.

- [ ] **Step 3: Run frontend build**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: PASS.

- [ ] **Step 4: Inline self-review**

Check:

```text
- Endpoint is read-only.
- Endpoint calls require_owned_world before aggregating data.
- No new model call is made.
- High-risk dashboard states are deterministic.
- WorldPage error for health does not break other panels.
- No dynamic workflows or subagents were used.
```

- [ ] **Step 5: Commit implementation**

Run:

```bash
git add backend/tests/test_narrative_health.py backend/app/narrative_control_center/schemas.py backend/app/narrative_control_center/service.py backend/app/narrative_control_center/router.py frontend/src/api/types.ts frontend/src/api/client.ts frontend/src/api/client.test.ts frontend/src/world/NarrativeHealthPanel.tsx frontend/src/world/NarrativeHealthPanel.test.tsx frontend/src/world/WorldPage.tsx frontend/src/world/WorldPage.test.tsx docs/superpowers/plans/2026-05-31-mvp17-narrative-health-dashboard.md
git commit -m "feat: add narrative health dashboard

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 6: Merge to main without push**

Run:

```bash
git switch main
git merge feat/mvp17-narrative-health-dashboard
git status --short --branch
```

Expected: on `main`, ahead of origin, clean worktree. Do not push.

- [ ] **Step 7: Post-merge verification**

Run backend targeted, frontend targeted, and frontend build again:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_narrative_health.py tests/test_narrative_control_center.py tests/test_foreshadow_crud.py -v
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts src/world/NarrativeHealthPanel.test.tsx src/world/WorldPage.test.tsx
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: all pass.

---

## Plan Self-Review

- Spec coverage: Backend endpoint, aggregation, owner scope, frontend helper, UI panel, WorldPage mount, and verification are covered.
- Placeholder scan: No placeholders, TODOs, or vague steps remain.
- Type consistency: `NarrativeHealthResponse`, `getNarrativeHealth`, and `NarrativeHealthPanel` match across backend/frontend tasks.
- Scope check: Plan stays read-only, uses existing reports/ledger, and avoids migrations, model calls, rollback, or auto-fix behavior.
