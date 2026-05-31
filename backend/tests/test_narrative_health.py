from app.narrative.models import Chapter, ChapterDraft
from app.world.service import count_approved_chapters


def register(client, email='health@example.com'):
    response = client.post('/auth/register', json={'email': email, 'password': 'strongpass123'})
    return response.json()['access_token']


def auth(token):
    return {'Authorization': f'Bearer {token}'}


def custom_world_payload():
    return {
        'title': '群星边境',
        'genre_template': 'sci_fi',
        'truth_canon': '边境殖民地依赖一座濒临失控的跃迁灯塔。',
        'tone_profile': {'style': '冷峻太空歌剧'},
        'starter_assets': {
            'characters': [
                {'name': '许砚', 'role_type': 'protagonist', 'current_goals': ['查明灯塔异常']},
                {'name': '莱娜·周', 'role_type': 'rival', 'current_goals': ['封锁维修甲板']},
            ],
            'relations': [],
            'foreshadows': [
                {
                    'title': '黑匣子脉冲',
                    'description': '废弃黑匣子收到来自未来的求救信号。',
                    'foreshadow_type': 'signal_clue',
                    'status': 'planted',
                    'urgency_level': 5,
                    'related_character_indexes': [0, 1],
                }
            ],
        },
    }


def create_approved_chapter_with_reports(db_session, world_id, character_id, foreshadow_id):
    chapter = Chapter(
        world_id=world_id,
        title='第一章 灯塔密令',
        status='approved',
        draft_version=1,
        approved_version=1,
        base_world_version=1,
        approved_content='许砚发现灯塔核心的黑匣子脉冲。',
        chapter_goal='推进灯塔异常。',
        critique_report={
            'overall_score': 52,
            'summary': '节奏和对白存在明显风险。',
            'issues': [
                {'severity': 'high', 'dimension': 'pacing', 'message': '开头缺少抓力。'},
                {'severity': 'medium', 'dimension': 'dialogue_quality', 'message': '对白功能化。'},
            ],
            'dimensions': {},
            'suggestions': ['重写开头钩子。'],
            'draft_version': 1,
            'current_draft_version': 1,
            'is_stale': False,
        },
        character_arc_report={
            'summary': '许砚弧线存在跳跃。',
            'character_arcs': [
                {
                    'character_id': character_id,
                    'name': '许砚',
                    'continuity_risk': 'high',
                    'risk_reason': '突然接受企业安保帮助，缺少铺垫。',
                }
            ],
            'relationship_notes': [
                {
                    'source_character_id': character_id,
                    'target_character_id': character_id,
                    'source_name': '许砚',
                    'target_name': '许砚',
                    'risk_level': 'medium',
                    'risk_reason': '内心转折缺少承接。',
                }
            ],
            'progression_hints': [],
            'draft_version': 1,
            'current_draft_version': 1,
            'is_stale': False,
        },
    )
    db_session.add(chapter)
    db_session.flush()
    db_session.add(
        ChapterDraft(
            chapter_id=chapter.id,
            draft_version=1,
            content=chapter.approved_content,
            context_summary='灯塔异常推进。',
            review_hints=[],
            proposed_changes={'foreshadows': [{'foreshadow_id': foreshadow_id, 'status': 'advanced'}]},
            source_world_version=1,
        )
    )
    db_session.commit()
    return chapter


def test_narrative_health_returns_baseline_for_new_world(client):
    token = register(client)
    world = client.post('/worlds', headers=auth(token), json=custom_world_payload()).json()

    response = client.get(f"/worlds/{world['id']}/narrative-health", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['world_id'] == world['id']
    assert payload['health_score'] >= 80
    assert payload['status'] in {'healthy', 'watch'}
    assert any(metric['key'] == 'approved_chapters' for metric in payload['metrics'])
    assert any(action['action_key'] == 'write_first_chapter' for action in payload['suggested_actions'])


def test_narrative_health_aggregates_critic_and_arc_risks(client, db_session):
    token = register(client, 'health-risks@example.com')
    world = client.post('/worlds', headers=auth(token), json=custom_world_payload()).json()
    overview = client.get(f"/worlds/{world['id']}/overview", headers=auth(token)).json()
    character_id = overview['characters'][0]['id']
    foreshadow_id = overview['foreshadows'][0]['id']
    create_approved_chapter_with_reports(db_session, world['id'], character_id, foreshadow_id)

    response = client.get(f"/worlds/{world['id']}/narrative-health", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'at_risk'
    assert payload['health_score'] < 80
    assert payload['summary']['approved_chapter_count'] == count_approved_chapters(db_session, world['id'])
    risk_sources = {risk['source'] for risk in payload['risks']}
    assert {'critic', 'character_arc'}.issubset(risk_sources)
    assert any('开头缺少抓力' in risk['message'] for risk in payload['risks'])
    assert any(action['action_key'] == 'revise_latest_chapter' for action in payload['suggested_actions'])


def test_narrative_health_surfaces_high_pressure_foreshadow(client):
    token = register(client, 'health-foreshadow@example.com')
    world = client.post('/worlds', headers=auth(token), json=custom_world_payload()).json()

    response = client.get(f"/worlds/{world['id']}/narrative-health", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert any(risk['source'] == 'foreshadow' and risk['object_title'] == '黑匣子脉冲' for risk in payload['risks'])
    assert any(metric['key'] == 'high_pressure_foreshadows' and metric['value'] >= 1 for metric in payload['metrics'])


def test_narrative_health_is_limited_to_owner(client):
    owner_token = register(client, 'health-owner@example.com')
    other_token = register(client, 'health-other@example.com')
    world = client.post('/worlds', headers=auth(owner_token), json=custom_world_payload()).json()

    response = client.get(f"/worlds/{world['id']}/narrative-health", headers=auth(other_token))

    assert response.status_code == 403
    assert response.json()['detail'] == 'FORBIDDEN'
