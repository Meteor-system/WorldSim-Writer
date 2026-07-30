import json

import pytest
from sqlalchemy import func, select

from app.llm.schemas import StoryArcChapter, parse_story_arc


def valid_story_arc_payload(title_suffix: str = '') -> list[dict]:
    return [
        {
            'chapter_number': index,
            'title': f'第{index}章 暗潮{title_suffix}',
            'summary': f'第{index}章推进灵脉危机，并让林砚面对新的选择。',
            'core_conflict': '林砚必须在自保与揭露城主府秘密之间做选择。',
            'pov_suggestion': '林砚',
            'foreshadow_hints': ['裂纹玉佩'],
        }
        for index in range(1, 11)
    ]


def test_parse_story_arc_accepts_strict_ten_chapter_array():
    parsed = parse_story_arc(json.dumps(valid_story_arc_payload()))

    assert len(parsed) == 10
    assert parsed[0].chapter_number == 1
    assert parsed[-1].chapter_number == 10
    assert parsed[0].foreshadow_hints == ['裂纹玉佩']


@pytest.mark.parametrize(
    'payload',
    [
        {'story_arc': valid_story_arc_payload()},
        valid_story_arc_payload()[:9],
        valid_story_arc_payload() + [valid_story_arc_payload()[0] | {'chapter_number': 11}],
        [valid_story_arc_payload()[0] | {'chapter_number': 2}] + valid_story_arc_payload()[1:],
        [valid_story_arc_payload()[0] | {'title': '   '}] + valid_story_arc_payload()[1:],
    ],
)
def test_parse_story_arc_rejects_invalid_shape(payload):
    with pytest.raises(ValueError, match='MODEL_RESPONSE_INVALID'):
        parse_story_arc(json.dumps(payload))


from app.llm.client import LLMClient


def test_llm_client_mock_generates_ten_chapter_story_arc():
    chapters = LLMClient(mock=True).generate_story_arc([])

    assert len(chapters) == 10
    assert chapters[0].chapter_number == 1
    assert chapters[-1].chapter_number == 10
    assert chapters[0].summary


def test_story_arc_client_call_does_not_force_json_object_response(monkeypatch):
    captured_requests = []
    messages = [{'role': 'user', 'content': '返回数组'}]

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                'output': [
                    {
                        'type': 'message',
                        'content': [
                            {'type': 'output_text', 'text': json.dumps(valid_story_arc_payload())}
                        ],
                    }
                ]
            }

    def fake_post(url, *args, **kwargs):
        captured_requests.append({'url': url, 'payload': kwargs['json']})
        return FakeResponse()

    monkeypatch.setattr('app.llm.client.httpx.post', fake_post)

    chapters = LLMClient(mock=False).generate_story_arc(messages)

    request = captured_requests[0]
    assert len(chapters) == 10
    assert request['url'].endswith('/responses')
    assert 'text' not in request['payload']
    assert request['payload']['store'] is False
    assert request['payload']['input'] == messages
    assert 'response_format' not in request['payload']


from app.event.models import EventLog
from app.foreshadow.models import Foreshadow
from app.narrative.models import Chapter
from app.world.models import World


def register_and_create_world(client):
    token = client.post('/auth/register', json={'email': 'arc-writer@example.com', 'password': 'strongpass123'}).json()['access_token']
    world = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {token}'}).json()
    return token, world['id']


def test_world_overview_includes_story_arc_and_approved_chapter_count(client, db_session):
    token, world_id = register_and_create_world(client)
    world = db_session.get(World, world_id)
    world.story_arc = [chapter.model_dump() for chapter in parse_story_arc(json.dumps(valid_story_arc_payload()))]
    db_session.add_all(
        [
            Chapter(world_id=world_id, title='批准章', status='approved', draft_version=1, base_world_version=1),
            Chapter(world_id=world_id, title='草稿章', status='drafting', draft_version=1, base_world_version=1),
            Chapter(world_id=world_id, title='驳回章', status='rejected', draft_version=1, base_world_version=1),
        ]
    )
    db_session.commit()

    response = client.get(f'/worlds/{world_id}/overview', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    payload = response.json()
    assert payload['story_arc'][0]['chapter_number'] == 1
    assert payload['approved_chapter_count'] == 1


from app.world import story_arc as story_arc_service


class FakeStoryArcLLMClient:
    def __init__(self, title_suffix: str = ''):
        self.title_suffix = title_suffix
        self.messages = []

    def generate_story_arc(self, messages):
        self.messages = messages
        return parse_story_arc(json.dumps(valid_story_arc_payload(self.title_suffix)))


class FailingStoryArcLLMClient:
    def generate_story_arc(self, messages):
        raise RuntimeError('MODEL_REQUEST_FAILED')


class InvalidStoryArcLLMClient:
    def generate_story_arc(self, messages):
        raise ValueError('MODEL_RESPONSE_INVALID')


class CountingWorldPlanningLLMClient:
    def __init__(self):
        self.story_arc_calls = 0
        self.suggest_goal_calls = 0

    def generate_story_arc(self, messages):
        self.story_arc_calls += 1
        return parse_story_arc(json.dumps(valid_story_arc_payload('新')))

    def suggest_goal(self, messages):
        self.suggest_goal_calls += 1
        return {'goal': '让林砚追查裂纹玉佩的来源。'}


def test_build_story_arc_messages_include_world_context(client, db_session):
    token, world_id = register_and_create_world(client)
    world = db_session.get(World, world_id)
    characters = list(world.characters)
    foreshadows = list(world.foreshadows)

    messages = story_arc_service.build_story_arc_messages(world, characters, foreshadows, approved_chapter_count=0)
    combined = '\n'.join(message['content'] for message in messages)

    assert '严格 JSON 数组' in combined
    assert '正好 10 章' in combined
    assert world.truth_canon in combined
    assert characters[0].name in combined
    assert foreshadows[0].title in combined


def test_generate_story_arc_api_persists_and_returns_ten_chapters(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(story_arc_service, 'LLMClient', lambda: FakeStoryArcLLMClient())

    response = client.post(f'/worlds/{world_id}/story-arc', headers={'Authorization': f'Bearer {token}'})
    overview = client.get(f'/worlds/{world_id}/overview', headers={'Authorization': f'Bearer {token}'}).json()

    assert response.status_code == 200
    assert response.json()['world_id'] == world_id
    assert len(response.json()['story_arc']) == 10
    assert overview['story_arc'] == response.json()['story_arc']


def test_generate_story_arc_overwrites_existing_arc(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(story_arc_service, 'LLMClient', lambda: FakeStoryArcLLMClient('旧'))
    first = client.post(f'/worlds/{world_id}/story-arc', headers={'Authorization': f'Bearer {token}'}).json()

    monkeypatch.setattr(story_arc_service, 'LLMClient', lambda: FakeStoryArcLLMClient('新'))
    second = client.post(f'/worlds/{world_id}/story-arc', headers={'Authorization': f'Bearer {token}'}).json()

    assert first['story_arc'][0]['title'].endswith('旧')
    assert second['story_arc'][0]['title'].endswith('新')
    assert len(second['story_arc']) == 10


def test_generate_story_arc_rejects_extra_body_fields_without_side_effects(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(story_arc_service, 'LLMClient', lambda: FakeStoryArcLLMClient('旧'))
    original_arc = client.post(f'/worlds/{world_id}/story-arc', headers={'Authorization': f'Bearer {token}'}).json()['story_arc']
    llm = CountingWorldPlanningLLMClient()
    monkeypatch.setattr(story_arc_service, 'LLMClient', lambda: llm)
    before_events = db_session.scalar(select(func.count()).select_from(EventLog))
    before_world_version = db_session.get(World, world_id).world_version

    response = client.post(
        f'/worlds/{world_id}/story-arc',
        headers={'Authorization': f'Bearer {token}'},
        json={'raw_text': '故事大纲规划端点只接受空请求体。'},
    )

    assert response.status_code == 422
    assert any(
        error['type'] == 'extra_forbidden' and error['loc'] == ['body', 'raw_text']
        for error in response.json()['detail']
    )
    db_session.expire_all()
    assert llm.story_arc_calls == 0
    assert db_session.get(World, world_id).story_arc == original_arc
    assert db_session.get(World, world_id).world_version == before_world_version
    assert db_session.scalar(select(func.count()).select_from(EventLog)) == before_events


def test_suggest_goal_rejects_extra_body_fields_without_side_effects(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    llm = CountingWorldPlanningLLMClient()
    monkeypatch.setattr(story_arc_service, 'LLMClient', lambda: llm)
    before_events = db_session.scalar(select(func.count()).select_from(EventLog))
    before_world_version = db_session.get(World, world_id).world_version

    response = client.post(
        f'/worlds/{world_id}/suggest-goal',
        headers={'Authorization': f'Bearer {token}'},
        json={'raw_text': '章节目标建议端点只接受空请求体。'},
    )

    assert response.status_code == 422
    assert any(
        error['type'] == 'extra_forbidden' and error['loc'] == ['body', 'raw_text']
        for error in response.json()['detail']
    )
    db_session.expire_all()
    assert llm.suggest_goal_calls == 0
    assert db_session.get(World, world_id).world_version == before_world_version
    assert db_session.scalar(select(func.count()).select_from(EventLog)) == before_events


def test_serial_plan_preview_returns_next_chapter_queue_without_writing_canon_or_events(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(story_arc_service, 'LLMClient', lambda: FakeStoryArcLLMClient())
    arc = client.post(f'/worlds/{world_id}/story-arc', headers={'Authorization': f'Bearer {token}'}).json()['story_arc']
    db_session.add(Chapter(world_id=world_id, title='已批准第一章', status='approved', draft_version=1, base_world_version=1))
    db_session.commit()
    before_events = db_session.scalar(select(func.count()).select_from(EventLog))
    before_world_version = db_session.get(World, world_id).world_version

    response = client.get(f'/worlds/{world_id}/serial-plan?limit=3', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    payload = response.json()
    assert payload['world_id'] == world_id
    assert payload['world_version'] == before_world_version
    assert payload['approved_chapter_count'] == 1
    assert [item['chapter_number'] for item in payload['queue']] == [2, 3, 4]
    assert payload['queue'][0]['title'] == arc[1]['title']
    assert '核心冲突' in payload['queue'][0]['goal']
    assert '每章仍需单独进入 Studio' in payload['safety_notes'][1]
    assert payload['review_guardrails'] == list(story_arc_service.SERIAL_PLAN_REVIEW_GUARDRAILS)
    assert '未写入正史' in payload['review_guardrails'][2]
    assert payload['convergence_guidance']['mode'] == 'balanced'
    assert payload['convergence_guidance']['open_foreshadow_count'] == 1
    assert payload['convergence_guidance']['priority_foreshadows'] == []
    assert '不会写入正史' in payload['convergence_guidance']['guidance_notes'][1]
    assert db_session.scalar(select(func.count()).select_from(EventLog)) == before_events
    assert db_session.scalar(select(func.count()).select_from(Chapter)) == 1
    assert db_session.get(World, world_id).world_version == before_world_version


def test_serial_plan_preview_requires_existing_story_arc(client):
    token, world_id = register_and_create_world(client)

    response = client.get(f'/worlds/{world_id}/serial-plan', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    assert response.json()['queue'] == []
    assert '不会一次性生成正文' in response.json()['safety_notes'][0]
    assert '未写入正史' in response.json()['review_guardrails'][2]


def test_serial_plan_preview_surfaces_read_only_convergence_pressure(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(story_arc_service, 'LLMClient', lambda: FakeStoryArcLLMClient())
    client.post(f'/worlds/{world_id}/story-arc', headers={'Authorization': f'Bearer {token}'})
    db_session.add(
        Foreshadow(
            world_id=world_id,
            title='血月密约',
            description='血月升起时旧盟约会吞掉一个证人。',
            foreshadow_type='deadline_secret',
            status='advanced',
            urgency_level=5,
            related_character_ids=[],
            expected_resolution_window='第2章',
        )
    )
    db_session.commit()
    before_events = db_session.scalar(select(func.count()).select_from(EventLog))
    before_world_version = db_session.get(World, world_id).world_version

    response = client.get(f'/worlds/{world_id}/serial-plan?limit=1', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    guidance = response.json()['convergence_guidance']
    assert guidance['mode'] == 'pressure'
    assert guidance['mode_label'] == '继续加压'
    assert guidance['open_foreshadow_count'] == 2
    assert guidance['high_pressure_count'] == 1
    assert guidance['priority_foreshadows'][0]['title'] == '血月密约'
    assert guidance['priority_foreshadows'][0]['pressure_reasons'] == ['高紧迫度：5', '预期收束窗口：第2章']
    assert '不会写入正史' in guidance['guidance_notes'][1]
    assert db_session.scalar(select(func.count()).select_from(EventLog)) == before_events
    assert db_session.get(World, world_id).world_version == before_world_version


def test_archived_world_rejects_story_arc_regeneration_without_overwriting_existing_arc(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(story_arc_service, 'LLMClient', lambda: FakeStoryArcLLMClient('旧'))
    first = client.post(f'/worlds/{world_id}/story-arc', headers={'Authorization': f'Bearer {token}'})
    assert first.status_code == 200
    original_arc = first.json()['story_arc']

    archive_response = client.patch(f'/worlds/{world_id}/status', headers={'Authorization': f'Bearer {token}'}, json={'status': 'archived'})
    assert archive_response.status_code == 200

    monkeypatch.setattr(story_arc_service, 'LLMClient', lambda: FakeStoryArcLLMClient('新'))
    response = client.post(f'/worlds/{world_id}/story-arc', headers={'Authorization': f'Bearer {token}'})
    overview = client.get(f'/worlds/{world_id}/overview', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 409
    assert response.json()['detail'] == 'WORLD_ARCHIVED'
    assert overview.status_code == 200
    assert overview.json()['story_arc'] == original_arc

    db_session.expire_all()
    world = db_session.get(World, world_id)
    assert world.story_arc == original_arc


def test_generate_story_arc_maps_model_request_failure(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(story_arc_service, 'LLMClient', lambda: FailingStoryArcLLMClient())

    response = client.post(f'/worlds/{world_id}/story-arc', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 502
    assert response.json()['detail'] == 'MODEL_REQUEST_FAILED'


def test_generate_story_arc_maps_invalid_model_response(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(story_arc_service, 'LLMClient', lambda: InvalidStoryArcLLMClient())

    response = client.post(f'/worlds/{world_id}/story-arc', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 502
    assert response.json()['detail'] == 'MODEL_RESPONSE_INVALID'
