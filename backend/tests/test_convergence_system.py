"""Tests for the narrative convergence system."""
from app.character.models import Character
from app.foreshadow.models import Foreshadow
from app.narrative.convergence import (
    ARC_MODE_LABELS,
    build_arc_transition_report,
    build_closure_plan,
    compute_convergence_ratio,
    compute_narrative_entropy,
    derive_arc_mode,
)
from app.narrative.service import build_writer_only_messages
from app.world.models import World


def _make_chars():
    c1 = Character(); c1.id = 1; c1.name = '陈默'; c1.gender = '男'; c1.role_type = 'protagonist'
    c1.status = 'active'; c1.current_goals = ['护送妹妹']; c1.hidden_traits = {'secret': '曾在USC工作'}
    c1.public_profile = {'identity': '军医'}
    c2 = Character(); c2.id = 2; c2.name = '陈曦'; c2.gender = '女'; c2.role_type = 'support'
    c2.status = 'active'; c2.current_goals = ['不拖累哥哥']; c2.hidden_traits = {'secret': '潜伏感染'}
    c2.public_profile = {'identity': '妹妹'}
    return [c1, c2]


def _make_fores():
    f1 = Foreshadow(); f1.id = 1; f1.title = '黎明计划真相'; f1.status = 'advanced'
    f1.urgency_level = 5; f1.expected_resolution_window = '第150-200章'
    f2 = Foreshadow(); f2.id = 2; f2.title = '潜伏感染'; f2.status = 'planted'
    f2.urgency_level = 4; f2.expected_resolution_window = '第30-60章'
    f3 = Foreshadow(); f3.id = 3; f3.title = 'K7变异'; f3.status = 'planted'
    f3.urgency_level = 3; f3.expected_resolution_window = '第10-20章'
    f4 = Foreshadow(); f4.id = 4; f4.title = '假身份'; f4.status = 'resolved'
    f4.urgency_level = 4; f4.expected_resolution_window = '第2-5章'
    return [f1, f2, f3, f4]


def test_entropy_healthy():
    chars = _make_chars()
    fores = _make_fores()
    payload = compute_narrative_entropy(chars, fores, chapter_number=5)
    assert payload['entropy'] > 0
    assert payload['level'] in ('healthy', 'elevated')
    assert payload['breakdown']['open_foreshadows'] > 0
    assert len(payload['open_threads']) == 3  # only planted/advanced foreshadows
    assert any(t['classification'] == 'must_resolve' for t in payload['open_threads'])


def test_entropy_grows_with_open_threads():
    chars = _make_chars()
    fores = _make_fores()
    small = compute_narrative_entropy(chars, fores[:1], chapter_number=5)['entropy']
    large = compute_narrative_entropy(chars, fores, chapter_number=5)['entropy']
    assert large > small


def test_arc_mode_derivation():
    assert derive_arc_mode(10, 3) == 'expansion'
    assert derive_arc_mode(10, 20, 200) == 'expansion'  # 20/200 is still early
    assert derive_arc_mode(10, 100, 200) == 'pressure'  # 50% progress
    assert derive_arc_mode(10, 160, 200) == 'convergence'
    assert derive_arc_mode(10, 190, 200) == 'payoff'
    assert derive_arc_mode(10, 199, 200) == 'finale'
    assert derive_arc_mode(55, 50, 200) == 'convergence'
    assert derive_arc_mode(35, 50, 200) == 'consolidation'


def test_convergence_ratio():
    assert compute_convergence_ratio(10, 5) == 0.5
    assert compute_convergence_ratio(0, 0) == 0.0
    assert compute_convergence_ratio(10, 10, 2) == 1.2


def test_closure_plan():
    chars = _make_chars()
    fores = _make_fores()
    plan = build_closure_plan(fores, chars, approved_chapter_count=10)
    # Only unresolved foreshadows appear
    assert all(item['title'] != '假身份' for item in plan)
    # Sorted by overdue/urgency
    assert plan[0]['priority'] == 'P0'


def test_arc_transition_report():
    chars = _make_chars()
    fores = _make_fores()
    report = build_arc_transition_report((1, 10), fores, chars, 20.0, 18.0)
    assert report['chapter_range'] == '第1-10章'
    assert report['entropy_delta'] == -2.0
    assert '假身份' in report['closed_foreshadows']
    assert report['convergence_ratio'] > 0


def test_writer_prompt_includes_arc_guidance():
    w = World()
    w.id = 0; w.title = '测试'; w.genre_template = '丧尸末日'; w.tone_profile = {}
    w.truth_canon = '设定'; w.world_version = 1
    chars = _make_chars()
    fores = _make_fores()
    msgs = build_writer_only_messages(w, chars, fores, '目标', chapter_number=50, total_planned_chapters=200)
    user_content = msgs[1]['content']
    assert '叙事收束指引' in user_content
    assert '当前篇章模式' in user_content
