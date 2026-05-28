import json

import httpx
import pytest

from app.core.config import Settings
from app.llm.client import LLMClient
from app.llm.schemas import parse_chapter_generation


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
