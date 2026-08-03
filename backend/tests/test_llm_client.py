import json
import logging
import re

import httpx
import pytest

from app.character.models import Character
from app.core.config import Settings
from app.foreshadow.models import Foreshadow
from app.llm.client import LLMClient
from app.llm.schemas import (
    _DIAGNOSTIC_SNIPPET_LIMIT,
    _shape_snippet,
    parse_chapter_generation,
    parse_chapter_outline,
    parse_character_arc_report,
    parse_critique_report,
    parse_literary_critic_report,
    parse_paragraph_revision,
    parse_story_arc,
    parse_world_creation_draft,
)
from app.narrative.models import Chapter, ChapterDraft
from app.narrative.service import (
    build_character_arc_report_messages,
    build_critic_report_messages,
    build_critique_messages,
    build_generation_messages,
    build_outline_messages,
    build_revision_messages,
)
from app.world.models import World
from app.world.service import build_world_creation_draft_messages
from app.world.story_arc import build_story_arc_messages, build_suggest_goal_messages


def valid_generation_json() -> str:
    return json.dumps({
        'title': '第一章 暗井回声',
        'draft_content': '林砚在灵井旁听见了第二个人的脚步声。',
        'context_summary': '林砚调查灵脉衰退，裂纹玉佩成为线索。',
        'review_hints': ['确认沈微霜动机是否一致'],
        'proposed_character_changes': [{'character_id': 1, 'current_goals': ['追查城主府叛乱']}],
        'proposed_foreshadow_changes': [{'foreshadow_id': 1, 'status': 'triggered', 'description_note': '玉佩线索被推进'}],
    })


def repair_body() -> str:
    return '\n\n'.join([
        '雾港钟楼在雨夜忽然敲响，整座城市都听见了不该出现的第十三声钟。',
        '林雾是修表学徒，她丢失了昨夜的记忆，却仍记得银表在雨声中倒转了一分钟。',
        '她必须在午夜前找回记忆，否则钟楼停摆后，昨夜发生过什么将永远无人能够证明。',
        '林雾先把停摆的秒针重新拨正，再把湿透的工具袋系紧，决定沿着钟声追到塔顶。',
        '周砚即将封锁钟楼，林雾必须在他关上铁门前找到裂纹银表的入口。',
        '林雾无法判断钟声来自哪一层，只能依靠表针倒转的触感决定下一步。',
    ])


def repair_evidence_payload(valid: bool) -> list[dict]:
    evidence = [
        {'check': 'background', 'paragraph_index': 0, 'quote': '雾港钟楼在雨夜忽然敲响'},
        {'check': 'protagonist_identity', 'paragraph_index': 1, 'quote': '林雾是修表学徒'},
        {'check': 'motivation', 'paragraph_index': 2, 'quote': '必须在午夜前找回记忆'},
        {'check': 'personality_evidence_plan', 'paragraph_index': 3, 'quote': '先把停摆的秒针重新拨正'},
        {'check': 'conflict_goal', 'paragraph_index': 4, 'quote': '必须在他关上铁门前找到裂纹银表的入口'},
        {'check': 'locked_pov', 'paragraph_index': 5, 'quote': '林雾无法判断钟声来自哪一层'},
    ]
    if not valid:
        evidence[0]['quote'] = '正文中不存在的背景引文'
    return evidence


def opening_generation_json(evidence: list[dict]) -> str:
    return json.dumps({
        'title': '第一章 第十三声钟',
        'draft_content': repair_body(),
        'context_summary': '林雾追查雨夜钟声与失去的记忆。',
        'review_hints': [],
        'proposed_character_changes': [],
        'proposed_foreshadow_changes': [],
        'opening_evidence': evidence,
    }, ensure_ascii=False)


def opening_generation_messages() -> list[dict[str, str]]:
    return [
        {'role': 'system', 'content': '你是 Writer Agent。'},
        {
            'role': 'user',
            'content': "Outliner上下文：{'opening_contract': {'background': '雾港钟楼规则'}}\n请写第一章。",
        },
    ]


def valid_world_creation_draft_json() -> str:
    return json.dumps({
        'draft': {
            'title': '死因王国',
            'genre_template': 'fantasy',
            'truth_canon': '每个人出生时都会获得一个未来死因，死因记录支撑王国秩序。',
            'tone_profile': {
                'style': '黑暗奇幻悬疑',
                'pacing': '高张力冷启动',
                'theme': '命运是否可以被审判',
            },
            'starter_assets': {
                'characters': [
                    {
                        'name': '伊莱',
                        'role_type': 'protagonist',
                        'status': 'active',
                        'public_profile': {
                            'identity': '低阶命运抄写员',
                            'skill': '辨认死因纹章',
                            'public_motivation': '维护死因档案的可信度',
                        },
                        'hidden_traits': {
                            'secret': '出生记录缺失了最后一页',
                            'fear': '自己的命运从未被登记',
                            'private_agenda': '找到原始命运账本',
                            'weakness': '过度相信书面记录',
                        },
                        'destiny_flag': '死因被篡改者',
                        'current_goals': ['查明自己的死因为何被改写'],
                    },
                    {
                        'name': '维拉',
                        'role_type': 'rival',
                        'status': 'active',
                        'public_profile': {
                            'identity': '王国命运官',
                            'skill': '审判死因合法性',
                            'public_motivation': '维持命运秩序',
                        },
                        'hidden_traits': {
                            'secret': '掌握旧账本钥匙',
                            'fear': '命运账本公开崩塌',
                            'private_agenda': '阻止王室篡改记录曝光',
                            'weakness': '无法容忍失控',
                        },
                        'destiny_flag': '旧账本守门人',
                        'current_goals': ['封锁命运档案'],
                    },
                ],
                'relations': [{
                    'source_index': 0,
                    'target_index': 1,
                    'relation_type': 'mutual_suspicion',
                    'intensity': 4,
                    'visibility': 'private',
                }],
                'foreshadows': [{
                    'title': '空白死因页',
                    'description': '伊莱的死因记录被银火烧穿。',
                    'foreshadow_type': 'fate_record_clue',
                    'status': 'planted',
                    'urgency_level': 4,
                    'related_character_indexes': [0, 1],
                    'expected_resolution_window': '第3-5章',
                }],
            },
        },
        'first_chapter_goal': '让伊莱发现自己的死因记录被烧穿。',
        'generation_notes': ['已生成可编辑草稿。'],
        'safety_notes': ['确认前不会写入正史。'],
        'followup_questions': ['主角更想推翻秩序，还是先救一个被错误判死的人？'],
    }, ensure_ascii=False)


def responses_payload(text: str) -> dict:
    return {'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': text}]}]}


def chat_completions_payload(text: str) -> dict:
    return {'choices': [{'message': {'content': text}}]}


def provider_payload(text: str, api_mode: str) -> dict:
    return responses_payload(text) if api_mode == 'responses' else chat_completions_payload(text)


def settings(**overrides: object) -> Settings:
    values = {
        'DATABASE_URL': 'postgresql+psycopg://test:test@localhost:5432/test',
        'SECRET_KEY': 'test-secret',
        'LLM_BASE_URL': 'https://llm.example/v1/',
        'LLM_API_KEY': 'test-key',
        'LLM_MODEL': 'test-model',
        'LLM_TIMEOUT_SECONDS': 12,
    }
    values.update(overrides)
    return Settings(**values)


def assert_closed_schema_objects(schema):
    if isinstance(schema, dict):
        if schema.get('type') == 'object':
            assert schema.get('additionalProperties') is False
            assert set(schema.get('required', [])) == set(schema['properties'])
        for value in schema.values():
            assert_closed_schema_objects(value)
    elif isinstance(schema, list):
        for value in schema:
            assert_closed_schema_objects(value)


def assert_world_creation_draft_schema(schema):
    assert schema['type'] == 'object'
    assert set(schema['properties']) == {
        'draft',
        'first_chapter_goal',
        'generation_notes',
        'safety_notes',
        'followup_questions',
    }
    assert_closed_schema_objects(schema)

    draft = schema['properties']['draft']
    assert set(draft['properties']) == {'title', 'genre_template', 'truth_canon', 'tone_profile', 'starter_assets'}
    assert draft['properties']['tone_profile']['type'] == 'object'

    starter_assets = draft['properties']['starter_assets']
    character = starter_assets['properties']['characters']['items']
    assert set(character['properties']) == {
        'name',
        'role_type',
        'status',
        'public_profile',
        'hidden_traits',
        'destiny_flag',
        'current_goals',
    }
    assert character['properties']['public_profile']['type'] == 'object'
    assert character['properties']['hidden_traits']['type'] == 'object'
    assert character['properties']['destiny_flag'] == {'type': 'string'}
    assert character['properties']['current_goals']['items'] == {'type': 'string'}

    relation = starter_assets['properties']['relations']['items']
    assert relation['properties']['intensity']['enum'] == [1, 2, 3, 4, 5]

    foreshadow = starter_assets['properties']['foreshadows']['items']
    assert foreshadow['properties']['status']['enum'] == ['planted', 'advanced', 'resolved', 'expired']
    assert foreshadow['properties']['urgency_level']['enum'] == [1, 2, 3, 4, 5]
    assert foreshadow['properties']['related_character_indexes']['items'] == {'type': 'integer'}


def test_parse_chapter_generation_accepts_valid_json():
    result = parse_chapter_generation(valid_generation_json())

    assert result.title == '第一章 暗井回声'
    assert result.proposed_character_changes[0].character_id == 1
    assert result.proposed_foreshadow_changes[0].status == 'triggered'


def test_parse_chapter_generation_rejects_non_json():
    with pytest.raises(ValueError, match='MODEL_RESPONSE_INVALID'):
        parse_chapter_generation('not json')


@pytest.mark.parametrize(
    "raw_text",
    [
        '{"message":"ordinary benign prose 你好世界 123"}',
        '{"password":"p@ssw0rd", "token":"tok_live_abc", "client_secret":"secret-value", "cookie":"session=abc"}',
        "https://user:password@example.test/path?access_token=abc123&query=private",
        "!@#$%^&*()_+-=[]{};:'\\\",.<>/?|~`",
        "sk-!@#$%^&*()_+-=",
        "https://user:password@example.test/path?access_token=abc123&query=private",
        "\u2605\u2728\u2764\ufe0f\U0001f680",
        "\x00\x01\x1f\x7f",
        "\t\n\r   ",
    ],
)
def test_shape_snippet_is_irreversible_and_uses_only_safe_markers(raw_text):
    snippet = _shape_snippet(raw_text)

    assert len(snippet) <= _DIAGNOSTIC_SNIPPET_LIMIT
    assert raw_text not in snippet
    assert re.fullmatch(r"(?:\[(?:WS|ASCII|DIGIT|CJK|PUNCT|SYMBOL|CTRL|TEXT|OMITTED):\d+\]){0,}", snippet)


@pytest.mark.parametrize("raw_text", ["", "a!" * 1000, "a一\x00!\t🙂" * 200])
def test_shape_snippet_truncates_only_complete_markers(raw_text):
    snippet = _shape_snippet(raw_text)

    assert len(snippet) <= _DIAGNOSTIC_SNIPPET_LIMIT
    assert re.fullmatch(r"(?:\[(?:WS|ASCII|DIGIT|CJK|PUNCT|SYMBOL|CTRL|TEXT|OMITTED):\d+\]){0,}", snippet)


def test_shape_snippet_ends_and_starts_are_never_partial_markers():
    for text in ("a!" * 1000, "", "\x00\t🙂一"):
        for boundary in (text[:1], text[-1:]):
            shaped = _shape_snippet(boundary)
            assert re.fullmatch(r"(?:\[(?:WS|ASCII|DIGIT|CJK|PUNCT|SYMBOL|CTRL|TEXT|OMITTED):\d+\]){0,}", shaped)


@pytest.mark.parametrize(
    ("parser", "stage"),
    [
        (parse_chapter_generation, "chapter_generation"),
        (parse_chapter_outline, "chapter_outline"),
        (parse_world_creation_draft, "world_creation_draft"),
        (parse_paragraph_revision, "paragraph_revision"),
        (parse_story_arc, "story_arc"),
        (parse_critique_report, "critique_report"),
        (parse_literary_critic_report, "literary_critic_report"),
        (parse_character_arc_report, "character_arc_report"),
    ],
)
def test_every_parser_logs_once_with_irreversible_shape_and_error_contract(caplog, parser, stage):
    raw_text = '{"password":"p@ssw0rd", "note":"ordinary benign prose 你好世界", "url":"https://user:password@example.test/?access_token=abc123"}'

    with caplog.at_level(logging.WARNING, logger="worldsim.llm.parse"):
        with pytest.raises(ValueError) as exc_info:
            parser(raw_text)

    assert exc_info.value.args == ("MODEL_RESPONSE_INVALID",)
    records = [record for record in caplog.records if record.name == "worldsim.llm.parse"]
    assert len(records) == 1
    payload = json.loads(records[0].message)
    assert payload["event"] == "llm.parse_failed"
    assert payload["stage"] == stage
    assert payload["raw_length"] == len(raw_text)
    assert payload["fence_count"] == 0
    marker_pattern = r"(?:\[(?:WS|ASCII|DIGIT|CJK|PUNCT|SYMBOL|CTRL|TEXT|OMITTED):\d+\])+"
    assert re.fullmatch(marker_pattern, payload["starts_with"])
    assert re.fullmatch(marker_pattern, payload["ends_with"])
    assert re.fullmatch(marker_pattern, payload["snippet"])
    assert all(value not in caplog.text for value in (
        "password", "p@ssw0rd", "ordinary", "benign", "你好世界", "user",
        "example", "access_token", "abc123",
    ))


def test_parse_chapter_generation_rejects_missing_fields():
    with pytest.raises(ValueError, match='MODEL_RESPONSE_INVALID'):
        parse_chapter_generation(json.dumps({'title': '缺字段'}))


def test_parse_paragraph_revision_accepts_valid_json():
    result = parse_paragraph_revision(json.dumps({
        'paragraph': '许澜把黑匣压进潮钟下的暗格。',
        'revision_note': '收紧动作节奏。',
    }, ensure_ascii=False))

    assert result.paragraph == '许澜把黑匣压进潮钟下的暗格。'
    assert result.revision_note == '收紧动作节奏。'


@pytest.mark.parametrize('paragraph', [
    '许澜把黑匣压进潮钟下的暗格。\n\n乔墨在门外停住了脚步。',
    '许澜把黑匣压进潮钟下的暗格。\r\n\r\n乔墨在门外停住了脚步。',
])
def test_parse_paragraph_revision_rejects_multiple_paragraphs(paragraph):
    with pytest.raises(ValueError) as exc_info:
        parse_paragraph_revision(json.dumps({
            'paragraph': paragraph,
            'revision_note': '收紧动作节奏。',
        }, ensure_ascii=False))

    assert exc_info.value.args == ('MODEL_RESPONSE_INVALID',)


@pytest.mark.parametrize('raw_text', [
    '{"paragraph":',
    '许澜把黑匣压进潮钟下的暗格。',
    json.dumps({'revision_note': '缺少修订段落。'}, ensure_ascii=False),
    json.dumps({'paragraph': ' \n\t'}, ensure_ascii=False),
])
def test_parse_paragraph_revision_rejects_invalid_payload(raw_text):
    with pytest.raises(ValueError, match='MODEL_RESPONSE_INVALID'):
        parse_paragraph_revision(raw_text)


def test_parse_world_creation_draft_accepts_valid_json():
    result = parse_world_creation_draft(valid_world_creation_draft_json())

    assert result.draft['title'] == '死因王国'
    assert result.first_chapter_goal == '让伊莱发现自己的死因记录被烧穿。'
    assert result.safety_notes == ['确认前不会写入正史。']


@pytest.mark.parametrize('language', ['json', 'JSON', ''])
def test_parse_world_creation_draft_accepts_single_json_code_fence(language):
    result = parse_world_creation_draft(f'```{language}\n{valid_world_creation_draft_json()}\n```')

    assert result.draft['title'] == '死因王国'


@pytest.mark.parametrize('raw_text', [
    f'说明如下：\n```json\n{valid_world_creation_draft_json()}\n```',
    f'```json\n{valid_world_creation_draft_json()}\n```\n```json\n{{}}\n```',
    f'```javascript\n{valid_world_creation_draft_json()}\n```',
    '```json\n\n```',
])
def test_parse_world_creation_draft_rejects_invalid_json_code_fence(raw_text):
    with pytest.raises(ValueError, match='MODEL_RESPONSE_INVALID'):
        parse_world_creation_draft(raw_text)


def test_parse_world_creation_draft_rejects_missing_goal():
    with pytest.raises(ValueError, match='MODEL_RESPONSE_INVALID'):
        parse_world_creation_draft(json.dumps({'draft': {}}))


@pytest.mark.parametrize('api_mode, request_key', [
    ('responses', 'input'),
    ('chat_completions', 'messages'),
])
def test_llm_client_repairs_invalid_opening_evidence_once(monkeypatch, api_mode, request_key):
    calls = []
    initial_evidence = repair_evidence_payload(valid=False)
    repaired_evidence = repair_evidence_payload(valid=True)
    initial_generation = parse_chapter_generation(opening_generation_json(initial_evidence))

    def fake_post(url, **kwargs):
        calls.append(kwargs['json'])
        response_text = (
            opening_generation_json(initial_evidence)
            if len(calls) == 1
            else json.dumps({'opening_evidence': repaired_evidence}, ensure_ascii=False)
        )
        return httpx.Response(
            200,
            request=httpx.Request('POST', url),
            json=provider_payload(response_text, api_mode),
        )

    monkeypatch.setattr(httpx, 'post', fake_post)
    result = LLMClient(settings(LLM_API_MODE=api_mode)).generate_chapter(opening_generation_messages())

    assert len(calls) == 2
    assert result.model_dump(exclude={'opening_evidence'}) == initial_generation.model_dump(exclude={'opening_evidence'})
    assert result.draft_content == repair_body()
    assert [evidence.model_dump() for evidence in result.opening_evidence] == repaired_evidence
    assert '不可修改正文' in calls[1][request_key][-1]['content']


def test_llm_client_keeps_original_generation_when_repair_still_fails(monkeypatch):
    calls = []
    initial_evidence = repair_evidence_payload(valid=False)
    initial_generation = parse_chapter_generation(opening_generation_json(initial_evidence))

    def fake_post(url, **kwargs):
        calls.append(kwargs['json'])
        response_text = (
            opening_generation_json(initial_evidence)
            if len(calls) == 1
            else json.dumps({'opening_evidence': initial_evidence}, ensure_ascii=False)
        )
        return httpx.Response(200, request=httpx.Request('POST', url), json=responses_payload(response_text))

    monkeypatch.setattr(httpx, 'post', fake_post)
    result = LLMClient(settings()).generate_chapter(opening_generation_messages())

    assert len(calls) == 2
    assert result.model_dump(exclude={'opening_evidence'}) == initial_generation.model_dump(exclude={'opening_evidence'})
    assert [evidence.model_dump() for evidence in result.opening_evidence] == initial_evidence


def test_llm_client_rejects_repair_payload_that_reuses_evidence(monkeypatch):
    calls = []
    initial_evidence = repair_evidence_payload(valid=False)
    reused_evidence = repair_evidence_payload(valid=True)
    reused_evidence[1]['quote'] = reused_evidence[0]['quote']
    initial_generation = parse_chapter_generation(opening_generation_json(initial_evidence))

    def fake_post(url, **kwargs):
        calls.append(kwargs['json'])
        response_text = (
            opening_generation_json(initial_evidence)
            if len(calls) == 1
            else json.dumps({'opening_evidence': reused_evidence}, ensure_ascii=False)
        )
        return httpx.Response(200, request=httpx.Request('POST', url), json=responses_payload(response_text))

    monkeypatch.setattr(httpx, 'post', fake_post)
    result = LLMClient(settings()).generate_chapter(opening_generation_messages())

    assert len(calls) == 2
    assert result.model_dump(exclude={'opening_evidence'}) == initial_generation.model_dump(exclude={'opening_evidence'})
    assert [evidence.model_dump() for evidence in result.opening_evidence] == initial_evidence


def test_llm_client_rejects_repair_payload_that_attempts_to_rewrite_body(monkeypatch):
    calls = []
    initial_evidence = repair_evidence_payload(valid=False)
    initial_generation = parse_chapter_generation(opening_generation_json(initial_evidence))
    repair_payload = {
        'opening_evidence': repair_evidence_payload(valid=True),
        'draft_content': '模型试图改写正文。',
    }

    def fake_post(url, **kwargs):
        calls.append(kwargs['json'])
        response_text = (
            opening_generation_json(initial_evidence)
            if len(calls) == 1
            else json.dumps(repair_payload, ensure_ascii=False)
        )
        return httpx.Response(200, request=httpx.Request('POST', url), json=responses_payload(response_text))

    monkeypatch.setattr(httpx, 'post', fake_post)
    result = LLMClient(settings()).generate_chapter(opening_generation_messages())

    assert len(calls) == 2
    assert result.model_dump(exclude={'opening_evidence'}) == initial_generation.model_dump(exclude={'opening_evidence'})
    assert result.draft_content == repair_body()
    assert [evidence.model_dump() for evidence in result.opening_evidence] == initial_evidence


def test_llm_client_responses_request_uses_finite_default_read_timeout(monkeypatch):
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured.update(url=url, headers=headers, json=json, timeout=timeout)
        return httpx.Response(200, request=httpx.Request('POST', url), json=responses_payload(valid_generation_json()))

    monkeypatch.setattr(httpx, 'post', fake_post)
    messages = [{'role': 'system', 'content': '你是小说助手'}, {'role': 'user', 'content': '写第一章'}]

    result = LLMClient(settings()).generate_chapter(messages)

    assert result.title == '第一章 暗井回声'
    assert captured['url'] == 'https://llm.example/v1/responses'
    assert captured['headers'] == {'Authorization': 'Bearer test-key'}
    assert captured['json'] == {
        'model': 'test-model',
        'input': messages,
        'temperature': 0.7,
        'store': False,
        'text': {'format': {'type': 'json_object'}},
    }
    assert isinstance(captured['timeout'], httpx.Timeout)
    assert captured['timeout'].connect == 12
    assert captured['timeout'].write == 12
    assert captured['timeout'].pool == 12
    assert captured['timeout'].read == 300


def test_llm_client_uses_configured_finite_read_timeout(monkeypatch):
    captured = {}

    def fake_post(url, **kwargs):
        captured['timeout'] = kwargs['timeout']
        return httpx.Response(200, request=httpx.Request('POST', url), json=responses_payload(valid_generation_json()))

    monkeypatch.setattr(httpx, 'post', fake_post)

    LLMClient(settings(LLM_READ_TIMEOUT_SECONDS=167)).generate_chapter([{'role': 'user', 'content': '写第一章'}])

    assert captured['timeout'].read == 167


def test_llm_client_posts_world_creation_draft_with_responses_json_schema(monkeypatch):
    captured = {}

    def fake_post(url, **kwargs):
        captured['url'] = url
        captured['json'] = kwargs['json']
        return httpx.Response(200, request=httpx.Request('POST', url), json=responses_payload(valid_world_creation_draft_json()))

    monkeypatch.setattr(httpx, 'post', fake_post)

    result = LLMClient(settings()).generate_world_creation_draft([{'role': 'user', 'content': '一个所有人出生时都有死因的王国'}])

    request_format = captured['json']['text']['format']
    assert result.draft['title'] == '死因王国'
    assert captured['url'] == 'https://llm.example/v1/responses'
    assert request_format['type'] == 'json_schema'
    assert request_format['name'] == 'world_creation_draft_v1'
    assert request_format['strict'] is True
    assert_world_creation_draft_schema(request_format['schema'])
    assert 'messages' not in captured['json']
    assert 'response_format' not in captured['json']


def test_llm_client_posts_world_creation_draft_with_chat_completions_json_schema(monkeypatch):
    captured = {}

    def fake_post(url, **kwargs):
        captured['url'] = url
        captured['json'] = kwargs['json']
        return httpx.Response(
            200,
            request=httpx.Request('POST', url),
            json={'choices': [{'message': {'content': valid_world_creation_draft_json()}}]},
        )

    monkeypatch.setattr(httpx, 'post', fake_post)

    result = LLMClient(settings(LLM_API_MODE='chat_completions')).generate_world_creation_draft(
        [{'role': 'user', 'content': '一个所有人出生时都有死因的王国'}],
    )

    response_format = captured['json']['response_format']
    request_format = response_format['json_schema']
    assert result.draft['title'] == '死因王国'
    assert captured['url'] == 'https://llm.example/v1/chat/completions'
    assert response_format['type'] == 'json_schema'
    assert request_format['name'] == 'world_creation_draft_v1'
    assert request_format['strict'] is True
    assert_world_creation_draft_schema(request_format['schema'])
    assert 'input' not in captured['json']
    assert 'text' not in captured['json']


@pytest.mark.parametrize('api_mode, format_key', [
    ('responses', 'text'),
    ('chat_completions', 'response_format'),
])
def test_llm_client_world_creation_draft_falls_back_to_json_object_only_after_schema_rejection(
    monkeypatch,
    api_mode,
    format_key,
):
    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs['json']))
        if len(calls) == 1:
            return httpx.Response(
                400,
                request=httpx.Request('POST', url),
                text='json_schema response format is not supported',
            )
        if len(calls) == 2:
            payload = responses_payload(valid_world_creation_draft_json())
            if api_mode == 'chat_completions':
                payload = {'choices': [{'message': {'content': valid_world_creation_draft_json()}}]}
            return httpx.Response(200, request=httpx.Request('POST', url), json=payload)
        payload = responses_payload(valid_generation_json())
        if api_mode == 'chat_completions':
            payload = {'choices': [{'message': {'content': valid_generation_json()}}]}
        return httpx.Response(200, request=httpx.Request('POST', url), json=payload)

    monkeypatch.setattr(httpx, 'post', fake_post)
    client = LLMClient(settings(LLM_API_MODE=api_mode))

    draft = client.generate_world_creation_draft([{'role': 'user', 'content': '创建世界'}])
    chapter = client.generate_chapter([{'role': 'user', 'content': '写第一章'}])

    strict_format = calls[0][1][format_key]['format'] if api_mode == 'responses' else calls[0][1][format_key]
    fallback_format = calls[1][1][format_key]['format'] if api_mode == 'responses' else calls[1][1][format_key]
    chapter_format = calls[2][1][format_key]['format'] if api_mode == 'responses' else calls[2][1][format_key]
    assert draft.draft['title'] == '死因王国'
    assert chapter.title == '第一章 暗井回声'
    assert strict_format['type'] == 'json_schema'
    assert fallback_format == {'type': 'json_object'}
    assert chapter_format == {'type': 'json_object'}


@pytest.mark.parametrize('api_mode', ['responses', 'chat_completions'])
@pytest.mark.parametrize('error_text', [
    "Invalid schema for response_format 'world_creation_draft_v1': unknown property",
    'Invalid JSON schema for response_format: unsupported keyword minimum',
    'Malformed response_format json_schema: unsupported keyword oneOf',
    'Schema invalid for text.format json_schema',
    'Invalid parameter: response_format.json_schema',
])
def test_llm_client_world_creation_draft_does_not_fallback_for_invalid_schema(
    monkeypatch,
    api_mode,
    error_text,
):
    calls = []

    def fake_post(url, **kwargs):
        calls.append(kwargs['json'])
        return httpx.Response(
            400,
            request=httpx.Request('POST', url),
            text=error_text,
        )

    monkeypatch.setattr(httpx, 'post', fake_post)

    with pytest.raises(RuntimeError, match='MODEL_REQUEST_FAILED'):
        LLMClient(settings(LLM_API_MODE=api_mode)).generate_world_creation_draft(
            [{'role': 'user', 'content': '创建世界'}],
        )

    assert len(calls) == 1


def test_llm_client_omits_responses_json_format_when_not_requested(monkeypatch):
    captured = {}

    def fake_post(url, **kwargs):
        captured['json'] = kwargs['json']
        return httpx.Response(200, request=httpx.Request('POST', url), json=responses_payload('[]'))

    monkeypatch.setattr(httpx, 'post', fake_post)

    assert LLMClient(settings())._post_json([{'role': 'user', 'content': '规划故事'}], temperature=0.4, json_object=False) == '[]'
    assert 'text' not in captured['json']
    assert captured['json']['store'] is False


def test_llm_client_concatenates_responses_output_text_in_provider_order(monkeypatch):
    monkeypatch.setattr(
        httpx,
        'post',
        lambda url, **kwargs: httpx.Response(
            200,
            request=httpx.Request('POST', url),
            json={
                'output': [
                    {'type': 'message', 'content': [
                        {'type': 'output_text', 'text': '第一段'},
                        {'type': 'output_text', 'text': '第二段'},
                    ]},
                    {'type': 'message', 'content': [{'type': 'output_text', 'text': '第三段'}]},
                ]
            },
        ),
    )

    assert LLMClient(settings())._post_json([{'role': 'user', 'content': '写作'}]) == '第一段第二段第三段'


def test_llm_client_rejects_responses_refusal_even_with_nested_and_fallback_text(monkeypatch):
    monkeypatch.setattr(
        httpx,
        'post',
        lambda url, **kwargs: httpx.Response(
            200,
            request=httpx.Request('POST', url),
            json={
                'output': [{'type': 'message', 'content': [
                    {'type': 'output_text', 'text': valid_generation_json()},
                    {'type': 'refusal', 'refusal': 'ignored'},
                ]}],
                'output_text': valid_generation_json(),
            },
        ),
    )

    with pytest.raises(ValueError, match='MODEL_RESPONSE_INVALID'):
        LLMClient(settings())._post_json([{'role': 'user', 'content': '写作'}])


def test_llm_client_accepts_responses_top_level_output_text_compatibility(monkeypatch):
    monkeypatch.setattr(
        httpx,
        'post',
        lambda url, **kwargs: httpx.Response(200, request=httpx.Request('POST', url), json={'output_text': valid_generation_json()}),
    )

    result = LLMClient(settings()).generate_chapter([{'role': 'user', 'content': '写第一章'}])

    assert result.title == '第一章 暗井回声'


@pytest.mark.parametrize('provider_payload', [
    {'output': []},
    {'output': [{'type': 'message', 'content': [{'type': 'refusal', 'refusal': 'no'}]}]},
    {'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': ''}]}]},
])
def test_llm_client_rejects_responses_without_valid_output_text(monkeypatch, provider_payload):
    monkeypatch.setattr(
        httpx,
        'post',
        lambda url, **kwargs: httpx.Response(200, request=httpx.Request('POST', url), json=provider_payload),
    )

    with pytest.raises(ValueError, match='MODEL_RESPONSE_INVALID'):
        LLMClient(settings()).generate_chapter([{'role': 'user', 'content': '写第一章'}])


def test_llm_client_rejects_invalid_json_response(monkeypatch):
    monkeypatch.setattr(
        httpx,
        'post',
        lambda url, **kwargs: httpx.Response(200, request=httpx.Request('POST', url), content=b'not json'),
    )

    with pytest.raises(ValueError, match='MODEL_RESPONSE_INVALID'):
        LLMClient(settings()).generate_chapter([{'role': 'user', 'content': '写第一章'}])


def test_llm_client_rejects_non_object_response_payload(monkeypatch):
    monkeypatch.setattr(
        httpx,
        'post',
        lambda url, **kwargs: httpx.Response(200, request=httpx.Request('POST', url), json=[]),
    )

    with pytest.raises(ValueError, match='MODEL_RESPONSE_INVALID'):
        LLMClient(settings()).generate_chapter([{'role': 'user', 'content': '写第一章'}])


@pytest.mark.parametrize('status_code', [400, 500])
def test_llm_client_responses_failure_does_not_fallback_to_chat_completions(monkeypatch, status_code):
    calls = []

    def fake_post(url, **kwargs):
        calls.append(url)
        return httpx.Response(status_code, request=httpx.Request('POST', url), text='provider error')

    monkeypatch.setattr(httpx, 'post', fake_post)

    with pytest.raises(RuntimeError, match='MODEL_REQUEST_FAILED'):
        LLMClient(settings())._post_json([{'role': 'user', 'content': '写作'}])

    assert calls == ['https://llm.example/v1/responses']
    assert all('/chat/completions' not in url for url in calls)


@pytest.mark.parametrize('exception_factory, expected_error', [
    (lambda request: httpx.ReadTimeout('provider unavailable', request=request), 'MODEL_TIMEOUT'),
    (lambda request: httpx.ConnectError('provider unavailable', request=request), 'MODEL_REQUEST_FAILED'),
    (lambda request: httpx.HTTPError('provider unavailable'), 'MODEL_REQUEST_FAILED'),
])
def test_llm_client_maps_httpx_transport_errors(monkeypatch, exception_factory, expected_error):
    def fake_post(url, **kwargs):
        raise exception_factory(httpx.Request('POST', url))

    monkeypatch.setattr(httpx, 'post', fake_post)

    expected_exception = TimeoutError if expected_error == 'MODEL_TIMEOUT' else RuntimeError
    with pytest.raises(expected_exception, match=expected_error):
        LLMClient(settings())._post_json([{'role': 'user', 'content': '写作'}])


@pytest.mark.parametrize('status_code', [401, 403])
def test_llm_client_reports_auth_failure_for_provider_response(monkeypatch, status_code):
    monkeypatch.setattr(
        httpx,
        'post',
        lambda url, **kwargs: httpx.Response(status_code, request=httpx.Request('POST', url), text='provider error'),
    )

    with pytest.raises(RuntimeError, match='MODEL_AUTH_FAILED'):
        LLMClient(settings()).generate_chapter([{'role': 'user', 'content': '写第一章'}])


def test_llm_client_reports_rate_limit_for_provider_429_response(monkeypatch):
    monkeypatch.setattr(
        httpx,
        'post',
        lambda url, **kwargs: httpx.Response(429, request=httpx.Request('POST', url), text='provider error'),
    )

    with pytest.raises(RuntimeError, match='MODEL_RATE_LIMITED'):
        LLMClient(settings()).generate_chapter([{'role': 'user', 'content': '写第一章'}])


@pytest.mark.parametrize('provider_payload', [
    {},
    {'choices': {}},
    {'choices': 'invalid'},
    {'choices': []},
    {'choices': [{}]},
    {'choices': [{'message': None}]},
    {'choices': [{'message': 'invalid'}]},
    {'choices': [{'message': {}}]},
    {'choices': [{'message': {'content': None}}]},
    {'choices': [{'message': {'content': ''}}]},
    {'choices': [{'message': {'content': valid_generation_json(), 'refusal': 'blocked'}}]},
])
def test_llm_client_chat_completions_rejects_invalid_choice_content(monkeypatch, provider_payload):
    monkeypatch.setattr(
        httpx,
        'post',
        lambda url, **kwargs: httpx.Response(200, request=httpx.Request('POST', url), json=provider_payload),
    )

    with pytest.raises(ValueError, match='MODEL_RESPONSE_INVALID'):
        LLMClient(settings(LLM_API_MODE='chat_completions'))._post_json([{'role': 'user', 'content': '写作'}])


def test_llm_client_chat_completions_mode_preserves_legacy_contract(monkeypatch):
    captured = {}

    def fake_post(url, **kwargs):
        captured['url'] = url
        captured['json'] = kwargs['json']
        captured['timeout'] = kwargs['timeout']
        return httpx.Response(200, request=httpx.Request('POST', url), json={'choices': [{'message': {'content': valid_generation_json()}}]})

    monkeypatch.setattr(httpx, 'post', fake_post)
    messages = [{'role': 'user', 'content': '写第一章'}]

    result = LLMClient(settings(LLM_API_MODE='chat_completions')).generate_chapter(messages)

    assert result.title == '第一章 暗井回声'
    assert captured['url'] == 'https://llm.example/v1/chat/completions'
    assert captured['json'] == {
        'model': 'test-model',
        'messages': messages,
        'temperature': 0.7,
        'response_format': {'type': 'json_object'},
    }
    assert isinstance(captured['timeout'], httpx.Timeout)
    assert captured['timeout'].connect == 12
    assert captured['timeout'].write == 12
    assert captured['timeout'].pool == 12
    assert captured['timeout'].read == 300


def test_mock_world_creation_draft_matches_strict_profile_contract(monkeypatch):
    def unexpected_network_call(*args, **kwargs):
        raise AssertionError('LLM_MOCK=true must not call the provider')

    monkeypatch.setattr(httpx, 'post', unexpected_network_call)

    result = LLMClient(settings(LLM_MOCK=True)).generate_world_creation_draft(
        [{'role': 'user', 'content': '创建世界'}],
    )

    assert set(result.draft['tone_profile']) == {'style', 'pacing', 'theme'}
    for character in result.draft['starter_assets']['characters']:
        assert set(character['public_profile']) == {'identity', 'skill', 'public_motivation'}
        assert set(character['hidden_traits']) == {'secret', 'fear', 'private_agenda', 'weakness'}
        assert isinstance(character['destiny_flag'], str)


def test_mock_outline_and_chapter_reflect_real_prompt_context_deterministically(monkeypatch):
    def unexpected_network_call(*args, **kwargs):
        raise AssertionError('LLM_MOCK=true must not call the provider')

    monkeypatch.setattr(httpx, 'post', unexpected_network_call)
    world = World(
        id=9,
        title='镜海港',
        genre_template='海港悬疑',
        truth_canon='潮汐会倒流记忆。',
        world_version=3,
        tone_profile={'style': '冷峻'},
    )
    characters = [
        Character(
            id=17,
            world_id=world.id,
            name='苏眠',
            role_type='protagonist',
            public_profile={'identity': '引潮员'},
            hidden_traits={'secret': '听得见沉船低语'},
            destiny_flag='逆潮幸存者',
            current_goals=['找回失踪的哥哥'],
        ),
        Character(
            id=23,
            world_id=world.id,
            name='顾岚',
            role_type='rival',
            public_profile={'identity': '港务官'},
            hidden_traits={'secret': '私藏潮汐航图'},
            destiny_flag='封港令执行者',
            current_goals=['封锁北码头'],
        ),
    ]
    foreshadows = [
        Foreshadow(
            id=41,
            world_id=world.id,
            title='逆潮齿轮',
            description='沉船钟舱中的铜齿轮会在逆潮时转动。',
            foreshadow_type='artifact_clue',
            status='planted',
            urgency_level=5,
            related_character_ids=[17, 23],
            expected_resolution_window='第1章',
        ),
    ]
    chapter_goal = '首章让苏眠在逆潮前夺回逆潮齿轮，并迫使顾岚表态。'
    execution_context = {
        'next_chapter_number': 1,
        'recommended_pov': {'name': '苏眠'},
        'priority_characters': [{'name': '苏眠', 'reason': '首章主视角'}],
        'priority_foreshadows': [{'title': '逆潮齿轮', 'urgency_level': 5, 'reason': '首章推进'}],
    }
    outline_messages = build_outline_messages(
        world, characters, foreshadows, chapter_goal, execution_context=execution_context,
    )
    client = LLMClient(settings(LLM_MOCK=True))

    outline = client.generate_outline(outline_messages)
    generation_messages = build_generation_messages(
        world,
        characters,
        foreshadows,
        chapter_goal,
        outline_beats=[beat.model_dump() for beat in outline.beats],
        outline_context=outline.model_dump(exclude={'beats'}),
        execution_context=execution_context,
    )
    chapter = client.generate_chapter(generation_messages)
    repeated_chapter = client.generate_chapter(generation_messages)

    assert outline.pov_suggestion == '苏眠'
    assert {beat.pov_character for beat in outline.beats} == {'苏眠'}
    assert '苏眠' in outline.opening_contract.locked_pov
    assert '镜海港' in outline.opening_contract.background
    assert '逆潮齿轮' in outline.opening_contract.conflict_goal
    assert '镜海港' in chapter.draft_content
    assert '苏眠' in chapter.draft_content
    assert '顾岚' in chapter.draft_content
    assert '逆潮齿轮' in chapter.draft_content
    assert [change.character_id for change in chapter.proposed_character_changes] == [17]
    assert [change.foreshadow_id for change in chapter.proposed_foreshadow_changes] == [41]
    assert chapter.opening_evidence == repeated_chapter.opening_evidence
    assert all('苏眠' in evidence.quote or '镜海港' in evidence.quote for evidence in chapter.opening_evidence)


def test_mock_outline_and_chapter_keep_opening_contract_for_minimal_legal_context(monkeypatch):
    def unexpected_network_call(*args, **kwargs):
        raise AssertionError('LLM_MOCK=true must not call the provider')

    monkeypatch.setattr(httpx, 'post', unexpected_network_call)
    world = World(
        id=90,
        title='雾港',
        genre_template='悬疑',
        truth_canon='钟声会抹去记忆。',
        world_version=1,
        tone_profile={},
    )
    characters = [
        Character(
            id=170,
            world_id=world.id,
            name='岑遥',
            role_type='protagonist',
            public_profile={},
            hidden_traits={},
            current_goals=[],
        ),
    ]
    foreshadows = [
        Foreshadow(
            id=410,
            world_id=world.id,
            title='旧钟',
            description='钟面有一道裂缝。',
            foreshadow_type='clue',
            status='planted',
            urgency_level=1,
            related_character_ids=[170],
        ),
    ]
    messages = build_outline_messages(
        world,
        characters,
        foreshadows,
        '找到钟钥。',
        execution_context={'next_chapter_number': 1, 'recommended_pov': {'name': '岑遥'}},
    )
    client = LLMClient(settings(LLM_MOCK=True))

    outline = client.generate_outline(messages)
    chapter = client.generate_chapter(build_generation_messages(
        world,
        characters,
        foreshadows,
        '找到钟钥。',
        outline_beats=[beat.model_dump() for beat in outline.beats],
        outline_context=outline.model_dump(exclude={'beats'}),
        execution_context={'next_chapter_number': 1, 'recommended_pov': {'name': '岑遥'}},
    ))

    paragraphs = chapter.draft_content.split('\n\n')
    assert len(chapter.draft_content) >= 300
    assert len(paragraphs) == 6
    assert len(chapter.opening_evidence) == 6
    assert {evidence.check for evidence in chapter.opening_evidence} == {
        'background',
        'protagonist_identity',
        'motivation',
        'personality_evidence_plan',
        'conflict_goal',
        'locked_pov',
    }
    for evidence in chapter.opening_evidence:
        assert evidence.quote in paragraphs[evidence.paragraph_index]


def test_mock_paragraph_revision_uses_current_paragraph_mode_and_instruction(monkeypatch):
    def unexpected_network_call(*args, **kwargs):
        raise AssertionError('LLM_MOCK=true must not call the provider')

    monkeypatch.setattr(httpx, 'post', unexpected_network_call)
    current_paragraph = '许澜把黑匣藏进潮钟下的暗格。'
    instruction = '让动作更紧迫，但保留黑匣与潮钟。'
    messages = [
        {'role': 'system', 'content': '返回结构化段落修订结果。'},
        {
            'role': 'user',
            'content': (
                '世界设定：潮钟鸣响后，站内一人会失去记忆。\n'
                '章节标题：盐雾档案\n'
                '修订模式：rewrite\n'
                f'用户指令：{instruction}\n'
                f'待修订段落：{current_paragraph}'
            ),
        },
    ]

    result = LLMClient(settings(LLM_MOCK=True)).revise_paragraph(messages)
    rendered = json.dumps(result.model_dump(), ensure_ascii=False)

    assert current_paragraph in result.paragraph
    assert instruction in result.paragraph
    assert '重写' in (result.revision_note or '')
    assert '林砚' not in rendered
    assert '青岚城' not in rendered


def test_mock_paragraph_revision_rejects_missing_selected_paragraph(monkeypatch):
    def unexpected_network_call(*args, **kwargs):
        raise AssertionError('invalid mock input must not call the provider')

    monkeypatch.setattr(httpx, 'post', unexpected_network_call)
    messages = [{
        'role': 'user',
        'content': (
            '世界设定：潮钟鸣响后，站内一人会失去记忆。\n'
            '章节标题：盐雾档案\n'
            '修订模式：polish\n'
            '用户指令：压缩重复意象。'
        ),
    }]

    with pytest.raises(ValueError, match='MODEL_RESPONSE_INVALID'):
        LLMClient(settings(LLM_MOCK=True)).revise_paragraph(messages)


def test_mock_paragraph_revision_rejects_invalid_mode(monkeypatch):
    def unexpected_network_call(*args, **kwargs):
        raise AssertionError('invalid mock input must not call the provider')

    monkeypatch.setattr(httpx, 'post', unexpected_network_call)
    messages = [{
        'role': 'user',
        'content': (
            '世界设定：潮钟鸣响后，站内一人会失去记忆。\n'
            '章节标题：盐雾档案\n'
            '修订模式：expand\n'
            '用户指令：增加环境描写。\n'
            '待修订段落：许澜守在潮钟下。'
        ),
    }]

    with pytest.raises(ValueError, match='MODEL_RESPONSE_INVALID'):
        LLMClient(settings(LLM_MOCK=True)).revise_paragraph(messages)


def test_llm_client_paragraph_revision_parses_provider_json(monkeypatch):
    client = LLMClient(settings())
    captured = {}

    def fake_post_json(messages, temperature=0.7):
        captured['messages'] = messages
        captured['temperature'] = temperature
        return json.dumps({
            'paragraph': '许澜把黑匣压进潮钟下的暗格。',
            'revision_note': '收紧动作节奏。',
        }, ensure_ascii=False)

    monkeypatch.setattr(client, '_post_json', fake_post_json)
    messages = [{'role': 'user', 'content': '修订当前段落'}]

    result = client.revise_paragraph(messages)

    assert result.paragraph == '许澜把黑匣压进潮钟下的暗格。'
    assert result.revision_note == '收紧动作节奏。'
    assert captured == {'messages': messages, 'temperature': 0.6}


def test_mock_revision_uses_current_prompt_ids_content_and_instruction(monkeypatch):
    def unexpected_network_call(*args, **kwargs):
        raise AssertionError('LLM_MOCK=true must not call the provider')

    monkeypatch.setattr(httpx, 'post', unexpected_network_call)
    world, characters, foreshadows = production_shaped_world_context()
    chapter = Chapter(
        id=301,
        world_id=world.id,
        title='盐雾档案',
        base_world_version=world.world_version,
        chapter_goal='让许澜在潮钟前取回黑匣。',
    )
    draft = ChapterDraft(
        id=302,
        chapter_id=chapter.id,
        draft_version=2,
        content='许澜把黑匣藏进潮钟下的暗格。',
        context_summary='旧稿摘要。',
        source_world_version=world.world_version,
        proposed_changes={},
    )
    instruction = '保留黑匣，并让许澜拒绝乔墨的交易。'

    result = LLMClient(settings(LLM_MOCK=True)).revise_chapter(build_revision_messages(
        world, characters, foreshadows, chapter, draft, {}, instruction,
    ))
    rendered = json.dumps(result.model_dump(), ensure_ascii=False)

    assert [change.character_id for change in result.proposed_character_changes] == [71]
    assert [change.foreshadow_id for change in result.proposed_foreshadow_changes] == [83]
    assert draft.content in result.draft_content
    assert instruction in result.draft_content
    assert '许澜' in rendered
    assert '黑匣' in rendered
    assert '林砚' not in rendered
    assert '青岚城' not in rendered
    assert '"character_id": 1' not in rendered
    assert '"foreshadow_id": 1' not in rendered


def test_mock_character_arc_report_uses_current_prompt_character_and_related_ids(monkeypatch):
    def unexpected_network_call(*args, **kwargs):
        raise AssertionError('LLM_MOCK=true must not call the provider')

    monkeypatch.setattr(httpx, 'post', unexpected_network_call)
    world, characters, foreshadows = production_shaped_world_context()
    chapter = Chapter(
        id=303,
        world_id=world.id,
        title='盐雾档案',
        base_world_version=world.world_version,
        chapter_goal='让许澜在潮钟前取回黑匣。',
    )
    draft = ChapterDraft(
        id=304,
        chapter_id=chapter.id,
        draft_version=2,
        content='许澜在潮钟前把黑匣交给乔墨，又在最后一刻收回。',
        context_summary='旧稿摘要。',
        source_world_version=world.world_version,
        proposed_changes={},
    )

    result = LLMClient(settings(LLM_MOCK=True)).generate_character_arc_report(
        build_character_arc_report_messages(world, characters, foreshadows, [], [], chapter, draft)
    )
    rendered = json.dumps(result.model_dump(), ensure_ascii=False)

    assert [(arc.character_id, arc.name) for arc in result.character_arcs] == [(71, '许澜'), (72, '乔墨')]
    assert result.progression_hints[0].related_character_ids == [71, 72]
    assert result.progression_hints[0].related_foreshadow_ids == [83]
    assert '林砚' not in rendered
    assert '"character_id": 1' not in rendered
    assert '"related_character_ids": [1]' not in rendered
    assert '"related_foreshadow_ids": [1]' not in rendered


def test_mock_story_arc_and_goal_use_current_world_characters_and_foreshadow(monkeypatch):
    def unexpected_network_call(*args, **kwargs):
        raise AssertionError('LLM_MOCK=true must not call the provider')

    monkeypatch.setattr(httpx, 'post', unexpected_network_call)
    world, characters, foreshadows = production_shaped_world_context()
    client = LLMClient(settings(LLM_MOCK=True))

    story_arc = client.generate_story_arc(build_story_arc_messages(world, characters, foreshadows, approved_chapter_count=0))
    goal = client.suggest_goal(build_suggest_goal_messages(world, characters, foreshadows, approved_chapter_count=0))
    rendered = json.dumps([chapter.model_dump() for chapter in story_arc], ensure_ascii=False) + goal['goal']

    assert len(story_arc) == 10
    assert story_arc[0].pov_suggestion == '许澜'
    assert '盐沼站' in rendered
    assert '许澜' in rendered
    assert '乔墨' in rendered
    assert '黑匣' in rendered
    assert '青岚城' not in rendered
    assert '林砚' not in rendered


def test_mock_non_opening_without_entities_uses_no_opening_contract_or_proposed_ids(monkeypatch):
    def unexpected_network_call(*args, **kwargs):
        raise AssertionError('LLM_MOCK=true must not call the provider')

    monkeypatch.setattr(httpx, 'post', unexpected_network_call)
    world = World(
        id=95,
        title='静默站',
        genre_template='末世悬疑',
        truth_canon='广播停下时，站台会遗失一段历史。',
        world_version=2,
        tone_profile={'style': '克制'},
    )
    execution_context = {'next_chapter_number': 2, 'recommended_pov': {'name': None}}
    client = LLMClient(settings(LLM_MOCK=True))

    outline = client.generate_outline(build_outline_messages(
        world, [], [], '确认失踪广播的来源。', execution_context=execution_context,
    ))
    chapter = client.generate_chapter(build_generation_messages(
        world,
        [],
        [],
        '确认失踪广播的来源。',
        outline_beats=[beat.model_dump() for beat in outline.beats],
        outline_context=outline.model_dump(exclude={'beats'}),
        execution_context=execution_context,
    ))

    assert outline.pov_suggestion is None
    assert outline.opening_contract is None
    assert all(beat.pov_character is None for beat in outline.beats)
    assert chapter.opening_evidence == []
    assert chapter.proposed_character_changes == []
    assert chapter.proposed_foreshadow_changes == []
    assert '静默站' in chapter.draft_content
    assert '青岚城' not in chapter.draft_content
    assert '林砚' not in chapter.draft_content


@pytest.mark.parametrize(
    'messages',
    [
        [{'role': 'user', 'content': '世界标题：异常站\n角色：\n- 71: 许澜'}],
        [{'role': 'user', 'content': '世界设定：潮钟会抹去名字。\n本章目标：查明黑匣。\n角色：\n- 71: 许澜'}],
    ],
)
def test_mock_context_parse_failure_fails_closed_instead_of_using_static_world(monkeypatch, messages):
    def unexpected_network_call(*args, **kwargs):
        raise AssertionError('LLM_MOCK=true must not call the provider')

    monkeypatch.setattr(httpx, 'post', unexpected_network_call)
    client = LLMClient(settings(LLM_MOCK=True))

    with pytest.raises(ValueError, match='MODEL_RESPONSE_INVALID'):
        client.generate_outline(messages)


def test_mock_opening_without_characters_fails_with_model_response_invalid(monkeypatch):
    def unexpected_network_call(*args, **kwargs):
        raise AssertionError('LLM_MOCK=true must not call the provider')

    monkeypatch.setattr(httpx, 'post', unexpected_network_call)
    world = World(
        id=96,
        title='空塔',
        genre_template='奇幻',
        truth_canon='塔内没有任何登记过的居民。',
        world_version=1,
        tone_profile={},
    )
    execution_context = {'next_chapter_number': 1, 'recommended_pov': {'name': None}}
    client = LLMClient(settings(LLM_MOCK=True))

    with pytest.raises(ValueError, match='MODEL_RESPONSE_INVALID'):
        client.generate_outline(build_outline_messages(
            world, [], [], '打开塔顶封门。', execution_context=execution_context,
        ))
    with pytest.raises(ValueError, match='MODEL_RESPONSE_INVALID'):
        client.generate_chapter(build_generation_messages(
            world, [], [], '打开塔顶封门。', execution_context=execution_context,
        ))


def test_mock_critique_reports_use_current_draft_characters_and_foreshadow(monkeypatch):
    def unexpected_network_call(*args, **kwargs):
        raise AssertionError('LLM_MOCK=true must not call the provider')

    monkeypatch.setattr(httpx, 'post', unexpected_network_call)
    world, characters, foreshadows = production_shaped_world_context()
    chapter = Chapter(
        id=305,
        world_id=world.id,
        title='潮钟交易',
        base_world_version=world.world_version,
        chapter_goal='让许澜拒绝乔墨并保住黑匣。',
        outline_context={'core_conflict': '许澜必须决定是否相信乔墨。'},
        outline_beats=[],
    )
    draft = ChapterDraft(
        id=306,
        chapter_id=chapter.id,
        draft_version=3,
        content='许澜把黑匣按在潮钟底座上。\n\n乔墨伸出手，她却拒绝了交易。',
        context_summary='许澜拒绝交易。',
        source_world_version=world.world_version,
        proposed_changes={},
    )
    client = LLMClient(settings(LLM_MOCK=True))

    critique = client.critique_chapter(build_critique_messages(world, characters, foreshadows, chapter, draft))
    literary = client.generate_critic_report(build_critic_report_messages(world, characters, foreshadows, chapter, draft))
    rendered = json.dumps(
        {'critique': critique.model_dump(), 'literary': literary.model_dump()},
        ensure_ascii=False,
    )

    assert '许澜' in rendered
    assert '乔墨' in rendered
    assert '黑匣' in rendered
    assert '潮钟' in rendered
    assert set(literary.dimensions) == {
        'pacing',
        'tension',
        'character_consistency',
        'dialogue_quality',
        'structure',
        'world_continuity',
        'readability',
    }
    assert '林砚' not in rendered
    assert '沈微霜' not in rendered
    assert '裂纹玉佩' not in rendered


def test_mock_world_creation_draft_uses_current_brief_and_variant(monkeypatch):
    def unexpected_network_call(*args, **kwargs):
        raise AssertionError('LLM_MOCK=true must not call the provider')

    monkeypatch.setattr(httpx, 'post', unexpected_network_call)
    client = LLMClient(settings(LLM_MOCK=True))
    first_brief = '一座每天清晨都会交换居民影子的浮岛'
    second_brief = '一艘只靠乘客梦境供能的深空列车'

    first = client.generate_world_creation_draft(build_world_creation_draft_messages(
        first_brief,
        variant_label='关系悬疑',
    ))
    repeated_first = client.generate_world_creation_draft(build_world_creation_draft_messages(
        first_brief,
        variant_label='关系悬疑',
    ))
    second = client.generate_world_creation_draft(build_world_creation_draft_messages(second_brief))
    first_rendered = json.dumps(first.model_dump(), ensure_ascii=False)
    second_rendered = json.dumps(second.model_dump(), ensure_ascii=False)

    assert first == repeated_first
    assert first.draft != second.draft
    assert first_brief in first.draft['truth_canon']
    assert second_brief in second.draft['truth_canon']
    assert '关系悬疑' in first_rendered
    assert '浮岛' in first_rendered
    assert '深空列车' in second_rendered
    assert '死因王国' not in first_rendered + second_rendered
    assert '伊莱' not in first_rendered + second_rendered
    assert '维拉' not in first_rendered + second_rendered


def production_shaped_world_context():
    world = World(
        id=70,
        title='盐沼站',
        genre_template='柴油朋克悬疑',
        truth_canon='每次潮钟鸣响，站内一人会忘记最重要的名字。',
        world_version=4,
        tone_profile={'style': '冷硬'},
    )
    characters = [
        Character(
            id=71,
            world_id=world.id,
            name='许澜',
            role_type='protagonist',
            status='active',
            public_profile={'identity': '潮汐检修员'},
            hidden_traits={'secret': '曾偷走钟楼钥匙'},
            destiny_flag='钟鸣幸存者',
            current_goals=['在失忆前取回黑匣'],
        ),
        Character(
            id=72,
            world_id=world.id,
            name='乔墨',
            role_type='rival',
            status='watching',
            public_profile={'identity': '盐运监察员'},
            hidden_traits={'secret': '替议会记录失忆名单'},
            destiny_flag='名单保管人',
            current_goals=['截获黑匣'],
        ),
    ]
    foreshadows = [
        Foreshadow(
            id=83,
            world_id=world.id,
            title='黑匣',
            description='黑匣藏着上一轮钟鸣前的失忆名单。',
            foreshadow_type='artifact_clue',
            status='advanced',
            urgency_level=5,
            related_character_ids=[71, 72],
            expected_resolution_window='第2章',
        ),
    ]
    return world, characters, foreshadows


def test_mock_outline_and_chapter_support_opening_quality_validation(monkeypatch):
    def unexpected_network_call(*args, **kwargs):
        raise AssertionError('LLM_MOCK=true must not call the provider')

    monkeypatch.setattr(httpx, 'post', unexpected_network_call)
    client = LLMClient(settings(LLM_MOCK=True))

    outline = client.generate_outline([{'role': 'user', 'content': '为第一章生成提纲'}])
    chapter = client.generate_chapter([{'role': 'user', 'content': '写第一章'}])

    assert outline.opening_contract is not None
    assert set(outline.opening_contract.model_dump()) == {
        'background',
        'protagonist_identity',
        'motivation',
        'personality_evidence_plan',
        'conflict_goal',
        'locked_pov',
        # 零认知锚点：可选字段，只进质量报告的 advisories，不参与硬门禁。
        'inciting_incident',
        'prior_state',
        'grounded_emotion',
    }
    assert len(chapter.opening_evidence) == 6
    assert {evidence.check for evidence in chapter.opening_evidence} == {
        'background',
        'protagonist_identity',
        'motivation',
        'personality_evidence_plan',
        'conflict_goal',
        'locked_pov',
    }
    paragraphs = chapter.draft_content.split('\n\n')
    for evidence in chapter.opening_evidence:
        assert evidence.quote in paragraphs[evidence.paragraph_index]
