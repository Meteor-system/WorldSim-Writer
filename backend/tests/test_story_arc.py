import json

import pytest

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
    captured_payloads = []

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                'choices': [
                    {'message': {'content': json.dumps(valid_story_arc_payload())}}
                ]
            }

    def fake_post(*args, **kwargs):
        captured_payloads.append(kwargs['json'])
        return FakeResponse()

    monkeypatch.setattr('app.llm.client.httpx.post', fake_post)

    chapters = LLMClient(mock=False).generate_story_arc([{'role': 'user', 'content': '返回数组'}])

    assert len(chapters) == 10
    assert 'response_format' not in captured_payloads[0]


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
