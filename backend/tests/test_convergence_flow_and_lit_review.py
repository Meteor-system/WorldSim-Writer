"""Tests for convergence flow integration and literary review."""
from app.llm.client import LLMClient
from app.llm.schemas import LiteraryReviewReport, parse_literary_review
from app.narrative.service import build_literary_review_messages


class _MiniWorld:
    title = '测试世界'


def test_literary_review_messages_shape():
    msgs = build_literary_review_messages(_MiniWorld(), '找到安全区', '他在发抖。他感到害怕。')
    assert len(msgs) == 2
    assert msgs[0]['role'] == 'system'
    assert 'over_explaining' in msgs[0]['content']
    assert '找到安全区' in msgs[1]['content']
    assert '他在发抖' in msgs[1]['content']


def test_parse_literary_review_roundtrip():
    report = LiteraryReviewReport(
        literary_score=4,
        over_explaining=['a'],
        emotional_telling=['b'],
        functional_dialogue=['c'],
        cliche_hooks=['d'],
        voice_notes=['e'],
        rewrite_suggestions=['f'],
    )
    raw = report.model_dump_json()
    parsed = parse_literary_review(raw)
    assert parsed.literary_score == 4
    assert parsed.over_explaining == ['a']
    assert parsed.rewrite_suggestions == ['f']


def test_literary_review_mock_is_present():
    client = LLMClient()
    client.mock = True
    result = client.generate_literary_review([])
    assert isinstance(result, LiteraryReviewReport)
    assert 1 <= result.literary_score <= 5
