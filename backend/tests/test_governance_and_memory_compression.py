"""Tests for the three long-term features:
1. Structured context compression (memory compression helpers)
2. Quality engine (schema + client mock)
3. Data governance tools (character filters, batch ops, anomaly detection)
"""
import pytest
from app.character.models import Character, CharacterRelation
from app.character.schemas import CharacterBatchUpdateRequest
from app.character.service import batch_update_characters, detect_world_anomalies
from app.foreshadow.models import Foreshadow
from app.llm.schemas import ChapterQualityReport, MemoryCompression, parse_quality_report, parse_memory_compression
from app.narrative.models import Chapter, ChapterDraft, WorldMemorySummary
from app.narrative.service import (
    _build_memory_compression_messages,
    _format_recent_memories,
    _format_world_summaries,
    _visible_truth_canon,
    build_quality_messages,
)
from app.world.models import World


def test_visible_truth_canon_with_layers():
    w = World()
    w.truth_canon = 'fallback'
    w.truth_layers = [
        {'content': '层1', 'reveal_at_chapter': 1},
        {'content': '层2', 'reveal_at_chapter': 5},
        {'content': '层3', 'reveal_at_chapter': 30},
    ]
    assert '层1' in _visible_truth_canon(w, chapter_number=1)
    assert '层2' not in _visible_truth_canon(w, chapter_number=1)
    assert '层2' in _visible_truth_canon(w, chapter_number=5)
    assert '层3' not in _visible_truth_canon(w, chapter_number=5)
    assert '层3' in _visible_truth_canon(w, chapter_number=30)
    # No layers -> fallback
    w2 = World()
    w2.truth_canon = 'fallback'
    assert _visible_truth_canon(w2, chapter_number=3) == 'fallback'


def test_memory_compression_messages_and_formatting():
    cards = [
        {'chapter_number': 1, 'facts': ['f1', 'f2'], 'emotional_arc': '紧张'},
        {'chapter_number': 2, 'facts': ['f3'], 'emotional_arc': '释然'},
    ]
    msgs = _build_memory_compression_messages(cards, '测试世界')
    assert '第1章' in msgs[1]['content']
    assert 'f1' in msgs[1]['content']
    assert msgs[0]['role'] == 'system'

    text = _format_recent_memories(cards)
    assert '近期已批准章节记忆' in text
    assert '第1章' in text and 'f1' in text

    class FakeSummary:
        chapter_start = 1
        chapter_end = 2
        summary = '前情摘要'
        key_facts = ['kf1']
        open_threads = ['ot1']

    text2 = _format_world_summaries([FakeSummary()])
    assert '世界前情摘要' in text2
    assert '第1-2章' in text2
    assert 'kf1' in text2 and 'ot1' in text2


def test_quality_report_parse_and_messages():
    raw = '{"theme_advancement": 4, "character_arc_progress": 3, "anti_cliche_risks": ["俗套"], "rhythm_score": 4, "voice_consistency": 5, "overall_score": 4}'
    report = parse_quality_report(raw)
    assert report.theme_advancement == 4
    assert report.anti_cliche_risks == ['俗套']
    assert report.overall_score == 4

    w = World()
    w.title = '测试'
    w.genre_template = '丧尸末日'
    w.world_version = 1
    chars = []
    c = Character(); c.id = 1; c.name = 'A'; c.gender = '男'; c.role_type = 'protagonist'; c.current_goals = ['g1']
    chars.append(c)
    f = Foreshadow(); f.id = 1; f.title = 'F1'; f.status = 'planted'; f.expected_resolution_window = '第2-5章'
    msgs = build_quality_messages(w, chars, [f], 'goal', '正文内容')
    assert '质量引擎' in msgs[0]['content']
    assert '正文内容' in msgs[1]['content']


def test_compression_schema_parse():
    raw = '{"summary": "摘要", "key_facts": ["k1"], "open_threads": ["o1"]}'
    comp = parse_memory_compression(raw)
    assert isinstance(comp, MemoryCompression)
    assert comp.summary == '摘要'
    assert comp.key_facts == ['k1']


def test_character_filter_and_batch(client, db_session):
    """End-to-end test of governance tools via HTTP API."""
    from app.auth.models import User
    from sqlalchemy import select

    token = client.post('/auth/register', json={'email': 'gov@example.com', 'password': 'strongpass123'}).json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    world = client.post('/worlds/from-template', headers=headers).json()
    world_id = world['id']

    # Create two duplicate-name characters and one normal character
    c1 = client.post(
        f'/worlds/{world_id}/characters',
        json={'name': '陈默', 'role_type': 'protagonist', 'public_profile': {'identity': '军医'}, 'current_goals': ['g1'], 'edit_reason': 'test'},
        headers=headers,
    ).json()
    c2 = client.post(
        f'/worlds/{world_id}/characters',
        json={'name': '陈默', 'role_type': 'rival', 'public_profile': {}, 'current_goals': [], 'edit_reason': 'test'},
        headers=headers,
    ).json()
    c3 = client.post(
        f'/worlds/{world_id}/characters',
        json={'name': '方凛', 'role_type': 'rival', 'public_profile': {'identity': '上尉'}, 'current_goals': ['g2'], 'edit_reason': 'test'},
        headers=headers,
    ).json()

    # Batch archive c1 and tag c3
    resp = client.post(
        f'/worlds/{world_id}/characters/batch',
        json={'operations': [
            {'character_id': c1['id'], 'action': 'archive'},
            {'character_id': c3['id'], 'action': 'tag', 'value': '核心'},
        ]},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert any(ch['id'] == c1['id'] and ch['status'] == 'archived' for ch in body)
    assert any(ch['id'] == c3['id'] and '核心' in ch['public_profile'].get('tags', []) for ch in body)

    # Filter characters by role_type
    resp = client.get(f'/worlds/{world_id}/characters?role_type=rival', headers=headers)
    assert resp.status_code == 200
    rivals = resp.json()
    assert all(ch['role_type'] == 'rival' for ch in rivals)
    assert len(rivals) == 2

    # Add three approved chapters so the foreshadow window (1-2) is in the past
    for idx in range(1, 4):
        db_session.add(Chapter(
            world_id=world_id, title=f'已批准章节{idx}', status='approved',
            draft_version=1, approved_version=1, base_world_version=1,
        ))
    # Add a stale foreshadow and a broken relation directly
    db_session.add(Foreshadow(
        world_id=world_id, title='旧伏笔', description='d', foreshadow_type='t',
        status='planted', urgency_level=3, expected_resolution_window='第1-2章',
    ))
    db_session.add(CharacterRelation(
        world_id=world_id, source_character_id=c1['id'],
        target_character_id=99999, relation_type='rival', intensity=1, visibility='public',
    ))
    db_session.commit()
    anomalies = client.get(f'/worlds/{world_id}/anomalies', headers=headers).json()
    kinds = {a['kind'] for a in anomalies}
    assert 'duplicate_character_name' in kinds
    assert 'broken_relation' in kinds
    assert 'stale_foreshadow' in kinds
    assert 'empty_character' in kinds
