import json

from sqlalchemy import select

from app.event.models import EventLog
from app.world.models import World
from app.world.schemas import WorldCreateRequest
from app.world import service as world_service


def auth_headers(token: str) -> dict[str, str]:
    return {'Authorization': f'Bearer {token}'}


def register(client, email: str = 'brief-draft@example.com') -> str:
    response = client.post('/auth/register', json={'email': email, 'password': 'strongpass123'})
    return response.json()['access_token']


def draft_payload() -> dict:
    return {
        'title': '死因王国',
        'genre_template': 'political_fantasy',
        'truth_canon': '赫洛王国会在每个孩子出生时分配未来死因，贵族用荣耀死因维持阶级秩序。命簿最近出现空白页，暗示制度开始失效。',
        'tone_profile': {'style': '政治奇幻、命运反抗', 'pacing': '制度压力与个人选择交替推进'},
        'starter_assets': {
            'characters': [
                {
                    'name': '莉塔',
                    'role_type': 'protagonist',
                    'status': '命簿抄录员',
                    'public_profile': {'identity': '王国命簿抄录员', 'skill': '解读死因文书'},
                    'hidden_traits': {'secret': '她自己的死因栏是空白'},
                    'destiny_flag': '空白死因持有者',
                    'current_goals': ['查明空白死因是否意味着不受命簿管辖'],
                },
                {
                    'name': '维克托公爵',
                    'role_type': 'rival',
                    'status': '荣耀死因贵族',
                    'public_profile': {'identity': '王国公爵', 'skill': '操控命簿审判'},
                    'hidden_traits': {'secret': '他的荣耀死因曾被篡改'},
                    'destiny_flag': '命簿利益维护者',
                    'current_goals': ['夺回空白命簿页'],
                },
            ],
            'relations': [{'source_index': 0, 'target_index': 1, 'relation_type': 'rival', 'intensity': 4, 'visibility': 'public'}],
            'foreshadows': [
                {
                    'title': '空白命簿页',
                    'description': '命簿中出现没有名字也没有死因的空白页，每晚都会多一道血痕。',
                    'foreshadow_type': 'fate_clue',
                    'status': 'planted',
                    'urgency_level': 4,
                    'related_character_indexes': [0, 1],
                    'expected_resolution_window': '第2-5章',
                }
            ],
        },
    }


class FakeBriefLLMClient:
    def __init__(self, result: object | None = None):
        self.result = result or {
            'payload': draft_payload(),
            'first_chapter_goal': '莉塔在命簿归档夜发现自己的死因栏是空白，并带走第一张空白命簿页。',
            'rationale': '从死因制度补全政治奇幻世界、核心角色冲突和初始伏笔。',
            'assumptions': ['主角需要能接触命簿制度。', '对手代表制度既得利益。'],
            'safety_notes': ['这是原创世界创建草稿，不会自动创建世界或写入正史。'],
        }
        self.messages = None

    def expand_world_brief(self, messages):
        self.messages = messages
        return self.result


def test_expand_world_brief_returns_valid_world_create_payload_without_persistence(client, db_session, monkeypatch):
    token = register(client)
    fake_client = FakeBriefLLMClient()
    monkeypatch.setattr(world_service, 'LLMClient', lambda: fake_client)

    response = client.post(
        '/worlds/brief/expand',
        headers=auth_headers(token),
        json={'brief': '一个所有人出生时都会被分配未来死因的王国'},
    )

    assert response.status_code == 200
    data = response.json()
    payload = data['payload']
    WorldCreateRequest.model_validate(payload)
    assert payload['title'] == '死因王国'
    assert payload['genre_template'] == 'political_fantasy'
    assert len(payload['starter_assets']['characters']) == 2
    assert len(payload['starter_assets']['foreshadows']) == 1
    assert data['first_chapter_goal'] == '莉塔在命簿归档夜发现自己的死因栏是空白，并带走第一张空白命簿页。'
    assert data['rationale'] == '从死因制度补全政治奇幻世界、核心角色冲突和初始伏笔。'
    assert data['assumptions'] == ['主角需要能接触命簿制度。', '对手代表制度既得利益。']
    assert data['safety_notes'] == ['这是原创世界创建草稿，不会自动创建世界或写入正史。']
    assert fake_client.messages is not None
    assert '所有人出生时都会被分配未来死因' in fake_client.messages[-1]['content']

    assert db_session.scalars(select(World)).all() == []
    assert db_session.scalars(select(EventLog)).all() == []


def test_expand_world_brief_accepts_markdown_wrapped_model_json(client, db_session, monkeypatch):
    token = register(client, 'brief-wrapped@example.com')
    wrapped = (
        '下面是可编辑草稿：\n\n'
        '```json\n'
        f"{json.dumps({'payload': draft_payload(), 'first_chapter_goal': '莉塔发现自己的死因栏是空白。'}, ensure_ascii=False)}\n"
        '```\n'
        '请用户确认后再创建世界。'
    )
    monkeypatch.setattr(world_service, 'LLMClient', lambda: FakeBriefLLMClient(wrapped))

    response = client.post(
        '/worlds/brief/expand',
        headers=auth_headers(token),
        json={'brief': '一个所有人出生时都会被分配未来死因的王国'},
    )

    assert response.status_code == 200
    data = response.json()
    assert data['payload']['title'] == '死因王国'
    assert data['first_chapter_goal'] == '莉塔发现自己的死因栏是空白。'
    assert db_session.scalars(select(World)).all() == []
    assert db_session.scalars(select(EventLog)).all() == []


def test_expand_world_brief_repairs_light_json_formatting(client, monkeypatch):
    token = register(client, 'brief-json-repair@example.com')
    repaired_payload = draft_payload()
    repaired_payload['title'] = '单引号死因王国'
    raw = repr({'payload': repaired_payload, 'first_chapter_goal': '莉塔发现自己的死因栏是空白。'})
    raw = raw[:-1] + ',}'
    monkeypatch.setattr(world_service, 'LLMClient', lambda: FakeBriefLLMClient(raw))

    response = client.post(
        '/worlds/brief/expand',
        headers=auth_headers(token),
        json={'brief': '一个所有人出生时都会被分配未来死因的王国'},
    )

    assert response.status_code == 200
    assert response.json()['payload']['title'] == '单引号死因王国'


def test_expand_world_brief_normalizes_light_missing_fields_and_types(client, monkeypatch):
    token = register(client, 'brief-normalize@example.com')
    light = draft_payload()
    light.pop('tone_profile')
    light['starter_assets'].pop('relations')
    light['starter_assets'].pop('foreshadows')
    light['starter_assets']['characters'][0]['current_goals'] = '查清空白死因'
    light['starter_assets']['characters'][1].pop('status')
    light['starter_assets']['relations'] = [{'source_index': '0', 'target_index': '1', 'relation_type': 'rival', 'intensity': '4', 'visibility': 'public'}]
    light['starter_assets']['foreshadows'] = [
        {
            'title': '空白命簿页',
            'description': '命簿中出现没有名字也没有死因的空白页。',
            'foreshadow_type': 'fate_clue',
            'status': 'planted',
            'urgency_level': '4',
            'related_character_indexes': ['0', '1'],
        }
    ]
    monkeypatch.setattr(world_service, 'LLMClient', lambda: FakeBriefLLMClient({'payload': light}))

    response = client.post(
        '/worlds/brief/expand',
        headers=auth_headers(token),
        json={'brief': '一个所有人出生时都会被分配未来死因的王国'},
    )

    assert response.status_code == 200
    payload = response.json()['payload']
    assert payload['tone_profile'] == {}
    assert payload['starter_assets']['characters'][0]['current_goals'] == ['查清空白死因']
    assert payload['starter_assets']['relations'][0]['source_index'] == 0
    assert payload['starter_assets']['relations'][0]['intensity'] == 4
    assert payload['starter_assets']['foreshadows'][0]['urgency_level'] == 4
    assert payload['starter_assets']['foreshadows'][0]['related_character_indexes'] == [0, 1]


def test_expand_world_brief_rejects_unrepairable_model_text(client, db_session, monkeypatch):
    token = register(client, 'brief-unrepairable@example.com')
    monkeypatch.setattr(world_service, 'LLMClient', lambda: FakeBriefLLMClient('我无法给出结构化草稿。'))

    response = client.post(
        '/worlds/brief/expand',
        headers=auth_headers(token),
        json={'brief': '一个所有人出生时都会被分配未来死因的王国'},
    )

    assert response.status_code == 502
    assert response.json()['detail'] == 'MODEL_RESPONSE_INVALID'
    assert db_session.scalars(select(World)).all() == []
    assert db_session.scalars(select(EventLog)).all() == []


def test_expand_world_brief_requires_login(client):
    response = client.post('/worlds/brief/expand', json={'brief': '一个神明已经死亡但教会仍收到神谕的世界'})

    assert response.status_code == 401
    assert response.json()['detail'] == 'UNAUTHORIZED'


def test_expand_world_brief_rejects_blank_and_too_short_brief(client):
    token = register(client, 'brief-validation@example.com')

    blank = client.post('/worlds/brief/expand', headers=auth_headers(token), json={'brief': '   '})
    too_short = client.post('/worlds/brief/expand', headers=auth_headers(token), json={'brief': '王国'})

    assert blank.status_code == 422
    assert too_short.status_code == 422


def test_expand_world_brief_rejects_malformed_model_payload(client, db_session, monkeypatch):
    token = register(client, 'brief-malformed@example.com')
    monkeypatch.setattr(world_service, 'LLMClient', lambda: FakeBriefLLMClient({'payload': {'title': '缺字段'}}))

    response = client.post(
        '/worlds/brief/expand',
        headers=auth_headers(token),
        json={'brief': '一艘世代航行的星舰上，所有人都被教育说外面没有宇宙'},
    )

    assert response.status_code == 502
    assert response.json()['detail'] == 'MODEL_RESPONSE_INVALID'
    assert db_session.scalars(select(World)).all() == []
    assert db_session.scalars(select(EventLog)).all() == []


def test_expand_world_brief_rejects_invalid_starter_asset_indexes(client, db_session, monkeypatch):
    token = register(client, 'brief-index@example.com')
    malformed = draft_payload()
    malformed['starter_assets']['foreshadows'][0]['related_character_indexes'] = [0, 99]
    monkeypatch.setattr(world_service, 'LLMClient', lambda: FakeBriefLLMClient({'payload': malformed}))

    response = client.post(
        '/worlds/brief/expand',
        headers=auth_headers(token),
        json={'brief': '一个所有人出生时都会被分配未来死因的王国'},
    )

    assert response.status_code == 502
    assert response.json()['detail'] == 'MODEL_RESPONSE_INVALID'
    assert db_session.scalars(select(World)).all() == []
    assert db_session.scalars(select(EventLog)).all() == []


def test_expand_world_brief_blocks_obvious_protected_reference_terms(client, db_session, monkeypatch):
    token = register(client, 'brief-safety@example.com')
    unsafe = draft_payload()
    unsafe['starter_assets']['characters'][0]['name'] = '哈利·波特'
    unsafe['truth_canon'] = '霍格沃茨收到一封新的入学信。'
    monkeypatch.setattr(world_service, 'LLMClient', lambda: FakeBriefLLMClient({'payload': unsafe}))

    response = client.post(
        '/worlds/brief/expand',
        headers=auth_headers(token),
        json={'brief': '一个魔法学校里的少年冒险故事'},
    )

    assert response.status_code == 422
    assert response.json()['detail'] == 'PROTECTED_REFERENCE_TERMS'
    assert db_session.scalars(select(World)).all() == []
    assert db_session.scalars(select(EventLog)).all() == []


def test_expand_world_brief_blocks_protected_reference_terms_in_first_chapter_goal(client, db_session, monkeypatch):
    token = register(client, 'brief-goal-safety@example.com')
    unsafe = {
        'payload': draft_payload(),
        'first_chapter_goal': '让莉塔收到霍格沃茨来信并发现空白命簿页。',
        'safety_notes': ['这是原创世界创建草稿，不会自动创建世界或写入正史。'],
    }
    monkeypatch.setattr(world_service, 'LLMClient', lambda: FakeBriefLLMClient(unsafe))

    response = client.post(
        '/worlds/brief/expand',
        headers=auth_headers(token),
        json={'brief': '一个魔法学校里的少年冒险故事'},
    )

    assert response.status_code == 422
    assert response.json()['detail'] == 'PROTECTED_REFERENCE_TERMS'
    assert db_session.scalars(select(World)).all() == []
    assert db_session.scalars(select(EventLog)).all() == []
