import json

import httpx
import pytest

from app.core.config import Settings
from app.llm.client import LLMClient
from app.llm.schemas import parse_chapter_generation, parse_world_creation_draft


def valid_generation_json() -> str:
    return json.dumps({
        'title': '第一章 暗井回声',
        'draft_content': '林砚在灵井旁听见了第二个人的脚步声。',
        'context_summary': '林砚调查灵脉衰退，裂纹玉佩成为线索。',
        'review_hints': ['确认沈微霜动机是否一致'],
        'proposed_character_changes': [{'character_id': 1, 'current_goals': ['追查城主府叛乱']}],
        'proposed_foreshadow_changes': [{'foreshadow_id': 1, 'status': 'triggered', 'description_note': '玉佩线索被推进'}],
    })


def test_parse_chapter_generation_accepts_valid_json():
    result = parse_chapter_generation(valid_generation_json())

    assert result.title == '第一章 暗井回声'
    assert result.proposed_character_changes[0].character_id == 1
    assert result.proposed_foreshadow_changes[0].status == 'triggered'


def test_parse_chapter_generation_rejects_non_json():
    with pytest.raises(ValueError, match='MODEL_RESPONSE_INVALID'):
        parse_chapter_generation('not json')


def test_parse_chapter_generation_rejects_missing_fields():
    with pytest.raises(ValueError, match='MODEL_RESPONSE_INVALID'):
        parse_chapter_generation(json.dumps({'title': '缺字段'}))


def valid_world_creation_draft_json() -> str:
    return json.dumps({
        'draft': {
            'title': '死因王国',
            'genre_template': 'fantasy',
            'truth_canon': '每个人出生时都会获得一个未来死因，死因记录支撑王国秩序。',
            'tone_profile': {'style': '黑暗奇幻悬疑'},
            'starter_assets': {
                'characters': [
                    {'name': '伊莱', 'role_type': 'protagonist', 'current_goals': ['查明自己的死因为何被改写']},
                    {'name': '维拉', 'role_type': 'rival', 'current_goals': ['封锁命运档案']},
                ],
                'relations': [{'source_index': 0, 'target_index': 1, 'relation_type': 'mutual_suspicion', 'intensity': 4}],
                'foreshadows': [
                    {
                        'title': '空白死因页',
                        'description': '伊莱的死因记录被银火烧穿。',
                        'foreshadow_type': 'fate_record_clue',
                        'status': 'planted',
                        'urgency_level': 4,
                        'related_character_indexes': [0, 1],
                    }
                ],
            },
        },
        'first_chapter_goal': '让伊莱发现自己的死因记录被烧穿。',
        'generation_notes': ['已生成可编辑草稿。'],
        'safety_notes': ['确认前不会写入正史。'],
    }, ensure_ascii=False)


def test_parse_world_creation_draft_accepts_valid_json():
    result = parse_world_creation_draft(valid_world_creation_draft_json())

    assert result.draft['title'] == '死因王国'
    assert result.first_chapter_goal == '让伊莱发现自己的死因记录被烧穿。'
    assert result.safety_notes == ['确认前不会写入正史。']


def test_parse_world_creation_draft_rejects_missing_goal():
    with pytest.raises(ValueError, match='MODEL_RESPONSE_INVALID'):
        parse_world_creation_draft(json.dumps({'draft': {}}))


def test_llm_client_posts_openai_compatible_request(monkeypatch):
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured['url'] = url
        captured['headers'] = headers
        captured['json'] = json
        captured['timeout'] = timeout
        return httpx.Response(200, request=httpx.Request('POST', url), json={'choices': [{'message': {'content': valid_generation_json()}}]})

    monkeypatch.setattr(httpx, 'post', fake_post)
    settings = Settings(
        DATABASE_URL='postgresql+psycopg://test:test@localhost:5432/test',
        SECRET_KEY='test-secret',
        LLM_BASE_URL='https://llm.example/v1/',
        LLM_API_KEY='test-key',
        LLM_MODEL='test-model',
        LLM_TIMEOUT_SECONDS=12,
    )

    result = LLMClient(settings).generate_chapter([{'role': 'user', 'content': '写第一章'}])

    assert result.title == '第一章 暗井回声'
    assert captured['url'] == 'https://llm.example/v1/chat/completions'
    assert captured['headers'] == {'Authorization': 'Bearer test-key'}
    assert captured['json']['model'] == 'test-model'
    assert captured['json']['response_format'] == {'type': 'json_object'}
    assert captured['timeout'] == 12


def test_llm_client_posts_world_creation_draft_request(monkeypatch):
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured['json'] = json
        return httpx.Response(200, request=httpx.Request('POST', url), json={'choices': [{'message': {'content': valid_world_creation_draft_json()}}]})

    monkeypatch.setattr(httpx, 'post', fake_post)
    settings = Settings(
        DATABASE_URL='postgresql+psycopg://test:test@localhost:5432/test',
        SECRET_KEY='test-secret',
        LLM_BASE_URL='https://llm.example/v1',
        LLM_API_KEY='test-key',
        LLM_MODEL='test-model',
    )

    result = LLMClient(settings).generate_world_creation_draft([{'role': 'user', 'content': '一个所有人出生时都有死因的王国'}])

    assert result.draft['title'] == '死因王国'
    assert captured['json']['response_format'] == {'type': 'json_object'}


def test_llm_client_rejects_invalid_json_response(monkeypatch):
    monkeypatch.setattr(
        httpx,
        'post',
        lambda url, **kwargs: httpx.Response(200, request=httpx.Request('POST', url), content=b'not json'),
    )
    settings = Settings(
        DATABASE_URL='postgresql+psycopg://test:test@localhost:5432/test',
        SECRET_KEY='test-secret',
        LLM_BASE_URL='https://llm.example/v1',
        LLM_API_KEY='test-key',
        LLM_MODEL='test-model',
    )

    with pytest.raises(ValueError, match='MODEL_RESPONSE_INVALID'):
        LLMClient(settings).generate_chapter([{'role': 'user', 'content': '写第一章'}])


def test_llm_client_reports_auth_failure_for_unauthorized_provider_response(monkeypatch):
    monkeypatch.setattr(
        httpx,
        'post',
        lambda url, **kwargs: httpx.Response(401, request=httpx.Request('POST', url), text='unauthorized'),
    )
    settings = Settings(
        DATABASE_URL='postgresql+psycopg://test:test@localhost:5432/test',
        SECRET_KEY='test-secret',
        LLM_BASE_URL='https://llm.example/v1',
        LLM_API_KEY='test-key',
        LLM_MODEL='test-model',
    )

    with pytest.raises(RuntimeError, match='MODEL_AUTH_FAILED'):
        LLMClient(settings).generate_chapter([{'role': 'user', 'content': '写第一章'}])


def test_llm_client_reports_rate_limit_for_provider_429_response(monkeypatch):
    monkeypatch.setattr(
        httpx,
        'post',
        lambda url, **kwargs: httpx.Response(429, request=httpx.Request('POST', url), text='rate limited'),
    )
    settings = Settings(
        DATABASE_URL='postgresql+psycopg://test:test@localhost:5432/test',
        SECRET_KEY='test-secret',
        LLM_BASE_URL='https://llm.example/v1',
        LLM_API_KEY='test-key',
        LLM_MODEL='test-model',
    )

    with pytest.raises(RuntimeError, match='MODEL_RATE_LIMITED'):
        LLMClient(settings).generate_chapter([{'role': 'user', 'content': '写第一章'}])
