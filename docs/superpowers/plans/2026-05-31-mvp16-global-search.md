# MVP16 Global Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read-only, owner-scoped global search endpoint and World page search panel for world metadata, characters, foreshadows, chapters, and formal events.

**Architecture:** Backend search stays in the existing `world` domain and uses simple deterministic application/database matching over existing tables. Frontend adds typed API support plus a focused `WorldSearchPanel` mounted in the existing World page, with no router or mutation behavior.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, React, TypeScript, Vitest, Testing Library, Vite.

---

## File Structure

- Create: `backend/tests/test_world_search.py`
  - Backend TDD coverage for endpoint behavior, owner boundary, filters, and blank query validation.
- Modify: `backend/app/world/schemas.py`
  - Add `WorldSearchResultResponse` and `WorldSearchResponse` Pydantic schemas.
- Modify: `backend/app/world/service.py`
  - Add read-only `search_world()` service and matching helpers.
- Modify: `backend/app/world/router.py`
  - Add `GET /worlds/{world_id}/search` route.
- Modify: `frontend/src/api/types.ts`
  - Add `WorldSearchResult` and `WorldSearchResponse` types.
- Modify: `frontend/src/api/client.ts`
  - Add `searchWorld()` API helper.
- Modify: `frontend/src/api/client.test.ts`
  - Add URL-construction test for `searchWorld()`.
- Create: `frontend/src/world/WorldSearchPanel.tsx`
  - UI panel for search form, chips, result cards, loading/error/empty states.
- Create: `frontend/src/world/WorldSearchPanel.test.tsx`
  - Component behavior tests.
- Modify: `frontend/src/world/WorldPage.tsx`
  - Mount `WorldSearchPanel` and pass `searchWorld`.
- Modify: `frontend/src/world/WorldPage.test.tsx`
  - Mock `searchWorld` and assert panel is mounted.

---

### Task 1: Backend Search Endpoint

**Files:**
- Create: `backend/tests/test_world_search.py`
- Modify: `backend/app/world/schemas.py`
- Modify: `backend/app/world/service.py`
- Modify: `backend/app/world/router.py`

- [ ] **Step 1: Write failing backend search tests**

Create `backend/tests/test_world_search.py` with:

```python
from app.llm.schemas import ChapterGeneration
from app.narrative import service as narrative_service


class SearchLLMClient:
    def generate_chapter(self, messages):
        return ChapterGeneration(
            title='第一章 灯塔密令',
            draft_content='许砚在灯塔核心发现黑匣子脉冲，莱娜·周封锁了维修甲板。',
            context_summary='灯塔异常第一次影响殖民地航道。',
            review_hints=['确认黑匣子脉冲伏笔推进。'],
            proposed_character_changes=[],
            proposed_foreshadow_changes=[],
        )


def register(client, email='search@example.com'):
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
                {
                    'name': '许砚',
                    'role_type': 'protagonist',
                    'status': '灯塔维修工程师',
                    'public_profile': {'identity': '灯塔维修工程师'},
                    'hidden_traits': {'secret': '篡改过灯塔事故日志'},
                    'destiny_flag': '灯塔核心密钥持有者',
                    'current_goals': ['查明黑匣子脉冲来源'],
                },
                {
                    'name': '莱娜·周',
                    'role_type': 'rival',
                    'status': '企业安保监察官',
                    'public_profile': {'identity': '企业安保监察官'},
                    'hidden_traits': {'fear': '害怕边境全面断航'},
                    'destiny_flag': '企业命令执行者',
                    'current_goals': ['夺取灯塔维护权限'],
                },
            ],
            'relations': [
                {
                    'source_index': 0,
                    'target_index': 1,
                    'relation_type': 'mutual_suspicion',
                    'intensity': 3,
                    'visibility': 'private',
                }
            ],
            'foreshadows': [
                {
                    'title': '黑匣子脉冲',
                    'description': '废弃黑匣子收到来自未来的求救信号。',
                    'foreshadow_type': 'signal_clue',
                    'status': 'planted',
                    'urgency_level': 4,
                    'related_character_indexes': [0, 1],
                    'expected_resolution_window': '第3-5章',
                }
            ],
        },
    }


def create_searchable_world(client, token, monkeypatch):
    world = client.post('/worlds', headers=auth(token), json=custom_world_payload()).json()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: SearchLLMClient())
    draft = client.post(
        f"/worlds/{world['id']}/chapters/draft",
        headers=auth(token),
        json={'chapter_goal': '让许砚第一次追查黑匣子脉冲'},
    ).json()
    return world, draft


def test_world_search_finds_characters_foreshadows_chapters_and_events(client, monkeypatch):
    token = register(client)
    world, draft = create_searchable_world(client, token, monkeypatch)

    response = client.get(f"/worlds/{world['id']}/search?q=黑匣子", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['world_id'] == world['id']
    assert payload['query'] == '黑匣子'
    result_types = {result['object_type'] for result in payload['results']}
    assert {'character', 'foreshadow', 'chapter', 'event'}.issubset(result_types)
    assert payload['object_type_counts']['character'] == 1
    assert payload['object_type_counts']['foreshadow'] == 1
    assert payload['object_type_counts']['chapter'] == 1
    assert payload['object_type_counts']['event'] >= 1
    assert any(result['title'] == '黑匣子脉冲' and '废弃黑匣子' in result['snippet'] for result in payload['results'])
    assert any(result['object_type'] == 'chapter' and result['object_id'] == draft['chapter_id'] for result in payload['results'])


def test_world_search_filters_object_types(client, monkeypatch):
    token = register(client, 'search-filter@example.com')
    world, _ = create_searchable_world(client, token, monkeypatch)

    response = client.get(f"/worlds/{world['id']}/search?q=灯塔&object_types=character", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert {result['object_type'] for result in payload['results']} == {'character'}
    assert payload['object_type_counts'] == {'character': 1}


def test_world_search_is_limited_to_owner(client):
    owner_token = register(client, 'search-owner@example.com')
    other_token = register(client, 'search-other@example.com')
    world = client.post('/worlds', headers=auth(owner_token), json=custom_world_payload()).json()

    response = client.get(f"/worlds/{world['id']}/search?q=灯塔", headers=auth(other_token))

    assert response.status_code == 403
    assert response.json()['detail'] == 'FORBIDDEN'


def test_world_search_rejects_blank_query(client):
    token = register(client, 'search-blank@example.com')
    world = client.post('/worlds', headers=auth(token), json=custom_world_payload()).json()

    response = client.get(f"/worlds/{world['id']}/search?q=   ", headers=auth(token))

    assert response.status_code == 422
    assert response.json()['detail'] == 'SEARCH_QUERY_REQUIRED'
```

- [ ] **Step 2: Run backend test to verify RED**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_world_search.py -v'
```

Expected: FAIL because `/worlds/{world_id}/search` does not exist yet or the response lacks expected search fields.

- [ ] **Step 3: Add backend search schemas**

Modify `backend/app/world/schemas.py` imports and append these classes after `WorldOverviewResponse`:

```python
class WorldSearchResultResponse(BaseModel):
    object_type: str
    object_id: int | None
    title: str
    subtitle: str
    snippet: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorldSearchResponse(BaseModel):
    world_id: int
    query: str
    object_type_counts: dict[str, int]
    results: list[WorldSearchResultResponse]
```

- [ ] **Step 4: Add backend search service**

Modify `backend/app/world/service.py`:

1. Add import at the top:

```python
import json
```

2. Add these helpers and service function after `list_world_events()`:

```python
SEARCH_OBJECT_TYPES = {'world', 'character', 'foreshadow', 'chapter', 'event'}


def _json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _matches(text: str, needle: str) -> bool:
    return needle in text.lower()


def _snippet(text: str, query: str, size: int = 140) -> str:
    compact = ' '.join(text.split())
    index = compact.lower().find(query.lower())
    if index == -1:
        return compact[:size]
    start = max(0, index - 40)
    end = min(len(compact), index + len(query) + 100)
    prefix = '…' if start > 0 else ''
    suffix = '…' if end < len(compact) else ''
    return f'{prefix}{compact[start:end]}{suffix}'


def _parse_object_types(object_types: str | None) -> set[str]:
    if object_types is None or object_types.strip() == '':
        return set(SEARCH_OBJECT_TYPES)
    requested = {item.strip() for item in object_types.split(',') if item.strip()}
    return requested & SEARCH_OBJECT_TYPES


def search_world(db: Session, user: User, world_id: int, query: str, object_types: str | None = None, limit: int = 20) -> dict:
    world = require_owned_world(db, user, world_id)
    normalized_query = query.strip()
    if not normalized_query:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail='SEARCH_QUERY_REQUIRED')
    needle = normalized_query.lower()
    allowed_types = _parse_object_types(object_types)
    results: list[dict] = []

    if 'world' in allowed_types:
        world_text = ' '.join([world.title, world.genre_template, world.truth_canon, _json_text(world.tone_profile)])
        if _matches(world_text, needle):
            results.append(
                {
                    'object_type': 'world',
                    'object_id': world.id,
                    'title': world.title,
                    'subtitle': f'World · {world.genre_template}',
                    'snippet': _snippet(world_text, normalized_query),
                    'metadata': {'world_version': world.world_version},
                }
            )

    if 'character' in allowed_types:
        characters = list(db.scalars(select(Character).where(Character.world_id == world.id).order_by(Character.id)))
        for character in characters:
            text = ' '.join(
                [
                    character.name,
                    character.role_type,
                    character.status,
                    character.destiny_flag or '',
                    _json_text(character.public_profile),
                    _json_text(character.hidden_traits),
                    _json_text(character.current_goals),
                ]
            )
            if _matches(text, needle):
                results.append(
                    {
                        'object_type': 'character',
                        'object_id': character.id,
                        'title': character.name,
                        'subtitle': f'Character · {character.role_type}',
                        'snippet': _snippet(text, normalized_query),
                        'metadata': {'status': character.status},
                    }
                )

    if 'foreshadow' in allowed_types:
        foreshadows = list(db.scalars(select(Foreshadow).where(Foreshadow.world_id == world.id).order_by(Foreshadow.id)))
        for foreshadow in foreshadows:
            text = ' '.join(
                [
                    foreshadow.title,
                    foreshadow.description,
                    foreshadow.foreshadow_type,
                    foreshadow.status,
                    foreshadow.expected_resolution_window or '',
                    _json_text(foreshadow.related_character_ids),
                ]
            )
            if _matches(text, needle):
                results.append(
                    {
                        'object_type': 'foreshadow',
                        'object_id': foreshadow.id,
                        'title': foreshadow.title,
                        'subtitle': f'Foreshadow · {foreshadow.status} · urgency {foreshadow.urgency_level}',
                        'snippet': _snippet(text, normalized_query),
                        'metadata': {'status': foreshadow.status, 'urgency_level': foreshadow.urgency_level},
                    }
                )

    if 'chapter' in allowed_types:
        chapters = list(db.scalars(select(Chapter).where(Chapter.world_id == world.id).order_by(Chapter.id)))
        for chapter in chapters:
            text = ' '.join([chapter.title, chapter.chapter_goal or '', chapter.approved_content or ''])
            if _matches(text, needle):
                results.append(
                    {
                        'object_type': 'chapter',
                        'object_id': chapter.id,
                        'title': chapter.title,
                        'subtitle': f'Chapter · {chapter.status} · world v{chapter.base_world_version}',
                        'snippet': _snippet(text, normalized_query),
                        'metadata': {'status': chapter.status, 'draft_version': chapter.draft_version},
                    }
                )

    if 'event' in allowed_types:
        events = list(db.scalars(select(EventLog).where(EventLog.world_id == world.id).order_by(EventLog.id)))
        for event in events:
            text = ' '.join([event.event_type, event.source_type, _json_text(event.payload)])
            if _matches(text, needle):
                results.append(
                    {
                        'object_type': 'event',
                        'object_id': event.id,
                        'title': event.event_type,
                        'subtitle': f'Event · {event.source_type} · world {event.world_version_before} → {event.world_version_after}',
                        'snippet': _snippet(text, normalized_query),
                        'metadata': {'world_version_after': event.world_version_after, 'chapter_id': event.chapter_id},
                    }
                )

    counts: dict[str, int] = {}
    for result in results:
        counts[result['object_type']] = counts.get(result['object_type'], 0) + 1

    return {
        'world_id': world.id,
        'query': normalized_query,
        'object_type_counts': counts,
        'results': results[:limit],
    }
```

- [ ] **Step 5: Add backend search route**

Modify `backend/app/world/router.py`:

1. Add imports:

```python
from app.world.schemas import StoryArcResponse, WorldCreateRequest, WorldOverviewResponse, WorldResponse, WorldSearchResponse
```

2. Add `search_world` to service imports.

3. Append route after the events route:

```python
@router.get('/{world_id}/search', response_model=WorldSearchResponse)
def search(
    world_id: int,
    q: str,
    object_types: str | None = None,
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> WorldSearchResponse:
    return WorldSearchResponse.model_validate(search_world(db, current_user, world_id, q, object_types, limit))
```

- [ ] **Step 6: Run backend search tests to verify GREEN**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_world_search.py -v'
```

Expected: PASS for all tests in `test_world_search.py`.

---

### Task 2: Frontend API Types and Helper

**Files:**
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/api/client.test.ts`

- [ ] **Step 1: Write failing API helper test**

Modify `frontend/src/api/client.test.ts` to import `searchWorld` and add this test near other world API helper tests:

```ts
describe('world search API helper', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('worldsim_token', 'test-token');
    vi.restoreAllMocks();
  });

  it('calls world search endpoint with query, object filters, and limit', async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce(jsonResponse({
      world_id: 7,
      query: '灯塔',
      object_type_counts: { character: 1 },
      results: [],
    }));
    vi.stubGlobal('fetch', fetchMock);

    const response = await searchWorld(7, { q: '灯塔', object_types: ['character', 'event'], limit: 10 });

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/worlds/7/search?q=%E7%81%AF%E5%A1%94&object_types=character%2Cevent&limit=10',
      expect.any(Object),
    );
    expect(response.object_type_counts).toEqual({ character: 1 });
  });
});
```

- [ ] **Step 2: Run frontend API test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts
```

Expected: FAIL because `searchWorld` is not exported.

- [ ] **Step 3: Add frontend search types**

Modify `frontend/src/api/types.ts` after `EventLogListResponse`:

```ts
export type WorldSearchResult = {
  object_type: string;
  object_id: number | null;
  title: string;
  subtitle: string;
  snippet: string;
  metadata: Record<string, unknown>;
};

export type WorldSearchResponse = {
  world_id: number;
  query: string;
  object_type_counts: Record<string, number>;
  results: WorldSearchResult[];
};
```

- [ ] **Step 4: Add `searchWorld()` API helper**

Modify `frontend/src/api/client.ts`:

1. Add `WorldSearchResponse` to the type import list.

2. Add helper after `getWorldEvents()`:

```ts
export function searchWorld(worldId: number, params: { q: string; object_types?: string[]; limit?: number }) {
  const search = new URLSearchParams({ q: params.q });
  if (params.object_types?.length) search.set('object_types', params.object_types.join(','));
  if (params.limit !== undefined) search.set('limit', String(params.limit));
  return apiRequest<WorldSearchResponse>(`/worlds/${worldId}/search?${search.toString()}`);
}
```

- [ ] **Step 5: Run frontend API test to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts
```

Expected: PASS.

---

### Task 3: Frontend Search Panel

**Files:**
- Create: `frontend/src/world/WorldSearchPanel.tsx`
- Create: `frontend/src/world/WorldSearchPanel.test.tsx`

- [ ] **Step 1: Write failing search panel tests**

Create `frontend/src/world/WorldSearchPanel.test.tsx` with:

```tsx
import '@testing-library/jest-dom/vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { WorldSearchResponse } from '../api/types';
import { WorldSearchPanel } from './WorldSearchPanel';

const searchResponse: WorldSearchResponse = {
  world_id: 7,
  query: '灯塔',
  object_type_counts: { character: 1, foreshadow: 1 },
  results: [
    {
      object_type: 'character',
      object_id: 1,
      title: '许砚',
      subtitle: 'Character · protagonist',
      snippet: '灯塔维修工程师正在查明黑匣子脉冲来源。',
      metadata: { status: 'active' },
    },
    {
      object_type: 'foreshadow',
      object_id: 2,
      title: '黑匣子脉冲',
      subtitle: 'Foreshadow · planted · urgency 4',
      snippet: '废弃黑匣子收到来自未来的求救信号。',
      metadata: { status: 'planted' },
    },
  ],
};

afterEach(() => cleanup());

describe('WorldSearchPanel', () => {
  it('renders search results with counts and snippets', async () => {
    const user = userEvent.setup();
    const onSearch = vi.fn().mockResolvedValue(searchResponse);
    render(<WorldSearchPanel worldId={7} onSearch={onSearch} />);

    expect(screen.getByText('Global Search')).toBeInTheDocument();
    await user.type(screen.getByLabelText('搜索世界资料'), '灯塔');
    await user.click(screen.getByRole('button', { name: '搜索' }));

    await waitFor(() => expect(onSearch).toHaveBeenCalledWith(7, { q: '灯塔', object_types: [], limit: 20 }));
    expect(await screen.findByText('找到 2 条结果')).toBeInTheDocument();
    expect(screen.getByText('character × 1')).toBeInTheDocument();
    expect(screen.getByText('foreshadow × 1')).toBeInTheDocument();
    expect(screen.getByText('许砚')).toBeInTheDocument();
    expect(screen.getByText('废弃黑匣子收到来自未来的求救信号。')).toBeInTheDocument();
  });

  it('sends selected object type filters', async () => {
    const user = userEvent.setup();
    const onSearch = vi.fn().mockResolvedValue(searchResponse);
    render(<WorldSearchPanel worldId={7} onSearch={onSearch} />);

    await user.type(screen.getByLabelText('搜索世界资料'), '灯塔');
    await user.click(screen.getByRole('button', { name: '角色' }));
    await user.click(screen.getByRole('button', { name: '搜索' }));

    await waitFor(() => expect(onSearch).toHaveBeenCalledWith(7, { q: '灯塔', object_types: ['character'], limit: 20 }));
  });

  it('does not search blank queries', async () => {
    const user = userEvent.setup();
    const onSearch = vi.fn().mockResolvedValue(searchResponse);
    render(<WorldSearchPanel worldId={7} onSearch={onSearch} />);

    await user.click(screen.getByRole('button', { name: '搜索' }));

    expect(onSearch).not.toHaveBeenCalled();
    expect(screen.getByText('请输入关键词后再搜索。')).toBeInTheDocument();
  });

  it('shows localized API errors', async () => {
    const user = userEvent.setup();
    const onSearch = vi.fn().mockRejectedValue(new Error('search down'));
    render(<WorldSearchPanel worldId={7} onSearch={onSearch} />);

    await user.type(screen.getByLabelText('搜索世界资料'), '灯塔');
    await user.click(screen.getByRole('button', { name: '搜索' }));

    expect(await screen.findByRole('alert')).toHaveTextContent('search down');
  });
});
```

- [ ] **Step 2: Run panel tests to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldSearchPanel.test.tsx
```

Expected: FAIL because `WorldSearchPanel` does not exist.

- [ ] **Step 3: Implement `WorldSearchPanel`**

Create `frontend/src/world/WorldSearchPanel.tsx` with:

```tsx
import { FormEvent, useState } from 'react';
import type { WorldSearchResponse } from '../api/types';

type Props = {
  worldId: number;
  onSearch: (worldId: number, params: { q: string; object_types?: string[]; limit?: number }) => Promise<WorldSearchResponse>;
};

const LIMIT = 20;
const FILTERS = [
  { label: '角色', value: 'character' },
  { label: '伏笔', value: 'foreshadow' },
  { label: '章节', value: 'chapter' },
  { label: '事件', value: 'event' },
];

function totalCount(response: WorldSearchResponse): number {
  return Object.values(response.object_type_counts).reduce((sum, count) => sum + count, 0);
}

export function WorldSearchPanel({ worldId, onSearch }: Props) {
  const [query, setQuery] = useState('');
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [response, setResponse] = useState<WorldSearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [hasSearched, setHasSearched] = useState(false);

  function toggleType(type: string) {
    setSelectedTypes((current) => current.includes(type) ? current.filter((item) => item !== type) : [...current, type]);
  }

  async function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) {
      setNotice('请输入关键词后再搜索。');
      setError('');
      return;
    }
    setLoading(true);
    setError('');
    setNotice('');
    setHasSearched(true);
    try {
      setResponse(await onSearch(worldId, { q: trimmed, object_types: selectedTypes, limit: LIMIT }));
    } catch (err) {
      setResponse(null);
      setError(err instanceof Error ? err.message : '搜索暂不可用');
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="book-card space-y-5 p-5">
      <div>
        <p className="chapter-kicker">Tools Workspace</p>
        <h2 className="text-2xl font-black text-[#34210f]">Global Search</h2>
        <p className="manuscript mt-2 text-sm text-[#5e3b1c]">跨世界设定、角色、章节、伏笔与正式事件查找资料。</p>
      </div>

      <form className="space-y-3" onSubmit={submitSearch}>
        <label className="block text-sm font-bold text-[#3b2511]" htmlFor="world-search-input">搜索世界资料</label>
        <div className="flex flex-col gap-2 md:flex-row">
          <input
            id="world-search-input"
            className="w-full rounded-2xl border border-amber-900/20 bg-white/60 px-4 py-3 text-sm text-[#2f1b0c] outline-none focus:border-amber-800"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="输入角色、伏笔、章节或事件关键词"
          />
          <button className="primary-button" disabled={loading} type="submit">搜索</button>
        </div>
      </form>

      <div className="flex flex-wrap gap-2">
        {FILTERS.map((filter) => (
          <button
            key={filter.value}
            className={`secondary-button text-sm ${selectedTypes.includes(filter.value) ? 'bg-amber-100' : ''}`}
            type="button"
            onClick={() => toggleType(filter.value)}
          >
            {filter.label}
          </button>
        ))}
      </div>

      {notice && <p className="ink-muted">{notice}</p>}
      {loading && <p className="ink-muted" role="status">正在搜索...</p>}
      {error && <p className="paper-error" role="alert">{error}</p>}

      {response && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-2 text-sm font-bold text-[#5e3b1c]">
            <span>找到 {totalCount(response)} 条结果</span>
            {Object.entries(response.object_type_counts).map(([type, count]) => (
              <span key={type} className="rounded-full bg-amber-50 px-3 py-1">{type} × {count}</span>
            ))}
          </div>

          {response.results.length === 0 ? (
            <p className="ink-muted">没有找到匹配结果。</p>
          ) : (
            <div className="space-y-3">
              {response.results.map((result) => (
                <article key={`${result.object_type}-${result.object_id ?? result.title}`} className="rounded-2xl border border-amber-900/15 bg-white/35 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-black uppercase tracking-[0.2em] text-[#8a5a2b]">{result.object_type}</p>
                      <h3 className="mt-1 font-black text-[#3b2511]">{result.title}</h3>
                    </div>
                    <p className="text-xs font-bold text-[#5e3b1c]">{result.subtitle}</p>
                  </div>
                  <p className="manuscript mt-3 text-sm">{result.snippet}</p>
                </article>
              ))}
            </div>
          )}
        </div>
      )}

      {hasSearched && response === null && !loading && !error && <p className="ink-muted">没有找到匹配结果。</p>}
    </section>
  );
}
```

- [ ] **Step 4: Run panel tests to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldSearchPanel.test.tsx
```

Expected: PASS.

---

### Task 4: Mount Search Panel in World Page

**Files:**
- Modify: `frontend/src/world/WorldPage.tsx`
- Modify: `frontend/src/world/WorldPage.test.tsx`

- [ ] **Step 1: Write/update failing WorldPage integration test**

Modify `frontend/src/world/WorldPage.test.tsx`:

1. Add `searchWorld` to the import from `../api/client`.
2. Add `searchWorld: vi.fn(),` to the `vi.mock('../api/client', ...)` object.
3. Add `vi.mocked(searchWorld).mockReset();` in `beforeEach()`.
4. In the `loads and displays Chapter History and Next Chapter Prep panels` test, add:

```ts
expect(await screen.findByText('Global Search')).toBeInTheDocument();
```

- [ ] **Step 2: Run WorldPage test to verify RED**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: FAIL because `Global Search` is not mounted.

- [ ] **Step 3: Mount panel in `WorldPage`**

Modify `frontend/src/world/WorldPage.tsx`:

1. Add `searchWorld` to the API import.
2. Add:

```ts
import { WorldSearchPanel } from './WorldSearchPanel';
```

3. Mount near `WorldTimelinePanel`:

```tsx
<WorldSearchPanel worldId={world.id} onSearch={searchWorld} />
```

- [ ] **Step 4: Run WorldPage test to verify GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/world/WorldPage.test.tsx
```

Expected: PASS.

---

### Task 5: Final Verification, Inline Self-Review, Commit, Merge

**Files:**
- All files changed above.

- [ ] **Step 1: Run backend targeted verification**

Run:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_world_search.py tests/test_world_template.py -v'
```

Expected: PASS.

- [ ] **Step 2: Run frontend targeted verification**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts src/world/WorldSearchPanel.test.tsx src/world/WorldPage.test.tsx
```

Expected: PASS.

- [ ] **Step 3: Run frontend build**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: PASS.

- [ ] **Step 4: Inline self-review**

Review changed files for:

```text
- Search is read-only and calls require_owned_world before scanning.
- Blank query is rejected.
- object_types filter cannot expose unsupported types.
- Frontend does not call API for blank input.
- WorldPage mocks include searchWorld.
- No dynamic workflows or subagents were used.
```

- [ ] **Step 5: Commit implementation**

Run:

```bash
git status --short
git add backend/tests/test_world_search.py backend/app/world/schemas.py backend/app/world/service.py backend/app/world/router.py frontend/src/api/types.ts frontend/src/api/client.ts frontend/src/api/client.test.ts frontend/src/world/WorldSearchPanel.tsx frontend/src/world/WorldSearchPanel.test.tsx frontend/src/world/WorldPage.tsx frontend/src/world/WorldPage.test.tsx docs/superpowers/plans/2026-05-31-mvp16-global-search.md
git commit -m "feat: add global world search

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 6: Merge to main without push**

Run:

```bash
git switch main
git merge feat/mvp16-global-search
git status --short --branch
```

Expected: on `main`, ahead of origin, clean worktree. Do not push.

- [ ] **Step 7: Post-merge verification**

Run backend targeted, frontend targeted, and frontend build again:

```bash
PYTHONIOENCODING=utf-8 conda run -n worldsim bash -lc 'cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 pytest tests/test_world_search.py tests/test_world_template.py -v'
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts src/world/WorldSearchPanel.test.tsx src/world/WorldPage.test.tsx
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: all pass.

---

## Plan Self-Review

- Spec coverage: Backend endpoint, schemas, service, owner scope, query validation, object-type filters, frontend helper, UI panel, WorldPage mount, and verification are covered.
- Placeholder scan: No placeholders, TODOs, or vague implementation steps remain.
- Type consistency: `WorldSearchResponse`, `WorldSearchResult`, `searchWorld`, `WorldSearchPanel`, and route paths are consistent across backend and frontend tasks.
- Scope check: Plan stays read-only and avoids tags, router navigation, indexing, cross-world search, and mutation tools.
