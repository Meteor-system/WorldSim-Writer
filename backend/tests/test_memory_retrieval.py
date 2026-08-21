"""Tests for long-term memory retrieval priority."""
from app.narrative.memory_retrieval import (
    _query_text_from_state,
    _tokenize,
    retrieve_summaries,
)
from app.narrative.models import WorldMemorySummary


def _mk_summary(start, end, summary, key_facts=None, open_threads=None):
    s = WorldMemorySummary()
    s.chapter_start = start
    s.chapter_end = end
    s.summary = summary
    s.key_facts = key_facts or []
    s.open_threads = open_threads or []
    return s


def test_tokenize_chinese():
    tokens = _tokenize('陈默逃出安全区')
    assert '陈默' in tokens
    assert '安全' in tokens
    assert '全' in tokens or '区' in tokens


def test_query_text_from_state_builds_signal():
    from app.character.models import Character
    from app.foreshadow.models import Foreshadow
    f = Foreshadow(); f.title = '黎明计划'; f.status = 'advanced'; f.description = '解药是幌子'
    c = Character(); c.name = '陈默'; c.current_goals = ['找到解药']
    query = _query_text_from_state('冲进研究所', [f], [c])
    assert '冲进研究所' in query
    assert '黎明计划' in query
    assert '解药' in query
    assert '陈默' in query


def test_retrieval_ranks_relevant_summary_first():
    summaries = [
        _mk_summary(1, 5, '兄妹二人从废弃城市出发寻找安全区', ['陈默是军医'], ['陈曦隐藏感染']),
        _mk_summary(6, 10, '进入第七安全区后被方凛审讯', ['方凛怀疑陈默身份'], ['方凛的调查']),
        _mk_summary(11, 15, '实验室深处发现了黎明计划的原始数据', ['黎明计划是幌子'], ['解药不存在']),
    ]
    plan = retrieve_summaries(
        summaries,
        '陈默要揭开黎明计划的真相，寻找解药',
        current_chapter=16,
        limit=2,
        budget_chars=3000,
        entities={'foreshadow': ['黎明计划'], 'character': ['陈默']},
    )
    assert len(plan['retrieved']) == 2
    first = plan['retrieved'][0]
    assert first.chapter_start == 11  # most relevant: 黎明计划/解药
    assert plan['ranked'][0]['covered'] is True
    assert plan['used_chars'] <= plan['budget_chars']


def test_retrieval_budget_limits_usage():
    summaries = [_mk_summary(i, i, '非常长的摘要' * 100) for i in range(1, 9)]
    plan = retrieve_summaries(
        summaries,
        '搜索',
        current_chapter=10,
        limit=8,
        budget_chars=800,
    )
    assert plan['used_chars'] <= 800
    assert len(plan['retrieved']) < 8


def test_retrieval_cold_audit():
    summaries = [
        _mk_summary(1, 5, '早期故事', ['A'], ['a']),
        _mk_summary(6, 10, '中期故事', ['B'], ['b']),
    ]
    plan = retrieve_summaries(
        summaries,
        '完全无关的新事件',
        current_chapter=40,
        limit=1,
        budget_chars=3000,
    )
    # One summary is covered, the other is cold
    assert len(plan['retrieved']) == 1
    assert len(plan['cold']) == 1
