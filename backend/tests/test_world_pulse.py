from app.narrative.models import Chapter, ChapterDraft


def register(client, email='pulse@example.com'):
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
                    'urgency_level': 3,
                    'related_character_indexes': [0, 1],
                }
            ],
        },
    }


def high_pressure_world_payload():
    payload = custom_world_payload()
    payload['starter_assets']['foreshadows'][0]['urgency_level'] = 5
    return payload


def create_approved_chapter_with_high_risk_report(db_session, world_id, character_id):
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
            'overall_score': 50,
            'summary': '开头抓力不足。',
            'issues': [
                {'severity': 'high', 'dimension': 'pacing', 'message': '开头缺少抓力。'},
            ],
            'dimensions': {},
            'suggestions': ['重写开头钩子。'],
            'draft_version': 1,
            'current_draft_version': 1,
            'is_stale': False,
        },
        character_arc_report={
            'summary': '许砚弧线需要承接。',
            'character_arcs': [
                {
                    'character_id': character_id,
                    'name': '许砚',
                    'continuity_risk': 'high',
                    'risk_reason': '突然接受企业安保帮助，缺少铺垫。',
                }
            ],
            'relationship_notes': [],
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
            proposed_changes={},
            source_world_version=1,
        )
    )
    db_session.commit()
    return chapter


def test_world_pulse_returns_watchful_baseline_for_new_world(client):
    token = register(client)
    world = client.post('/worlds', headers=auth(token), json=custom_world_payload()).json()

    response = client.get(f"/worlds/{world['id']}/pulse", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['world_id'] == world['id']
    assert payload['pulse_status'] == 'watch'
    assert payload['primary_mode'] == 'draft'
    assert payload['headline']
    indicator_keys = {indicator['key'] for indicator in payload['indicators']}
    assert {'narrative_health', 'open_threads', 'next_chapter', 'recent_events', 'archive_freshness'}.issubset(indicator_keys)
    assert any(action['action_key'] == 'write_first_chapter' for action in payload['next_actions'])


def test_world_pulse_uses_repair_mode_for_high_risk_reports(client, db_session):
    token = register(client, 'pulse-risk@example.com')
    world = client.post('/worlds', headers=auth(token), json=custom_world_payload()).json()
    overview = client.get(f"/worlds/{world['id']}/overview", headers=auth(token)).json()
    create_approved_chapter_with_high_risk_report(db_session, world['id'], overview['characters'][0]['id'])

    response = client.get(f"/worlds/{world['id']}/pulse", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['pulse_status'] == 'urgent'
    assert payload['primary_mode'] == 'repair'
    assert any(focus['focus_key'] == 'repair_health' and focus['priority'] == 'urgent' for focus in payload['focus'])
    assert any(action['action_key'] == 'repair_narrative_health' for action in payload['next_actions'])


def test_world_pulse_surfaces_convergence_focus_for_open_threads(client):
    token = register(client, 'pulse-converge@example.com')
    world = client.post('/worlds', headers=auth(token), json=high_pressure_world_payload()).json()

    response = client.get(f"/worlds/{world['id']}/pulse", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['pulse_status'] in {'watch', 'urgent'}
    assert any(focus['focus_key'] == 'converge_threads' for focus in payload['focus'])
    assert any(action['action_key'] == 'open_threads_board' for action in payload['next_actions'])


def test_world_pulse_reports_snapshot_freshness(client):
    token = register(client, 'pulse-snapshot@example.com')
    world = client.post('/worlds', headers=auth(token), json=custom_world_payload()).json()

    response = client.get(f"/worlds/{world['id']}/pulse", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    archive_indicator = next(indicator for indicator in payload['indicators'] if indicator['key'] == 'archive_freshness')
    assert archive_indicator['status'] == 'watch'
    assert payload['source_summary']['snapshot_count'] == 0


def test_world_pulse_is_limited_to_owner(client):
    owner_token = register(client, 'pulse-owner@example.com')
    other_token = register(client, 'pulse-other@example.com')
    world = client.post('/worlds', headers=auth(owner_token), json=custom_world_payload()).json()

    response = client.get(f"/worlds/{world['id']}/pulse", headers=auth(other_token))

    assert response.status_code == 403
    assert response.json()['detail'] == 'FORBIDDEN'
