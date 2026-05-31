from app.narrative.models import Chapter, ChapterDraft


def register(client, email='threads@example.com'):
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
                {
                    'name': '许砚',
                    'role_type': 'protagonist',
                    'status': '灯塔维修工程师',
                    'public_profile': {'identity': '灯塔维修工程师'},
                    'hidden_traits': {'secret': '篡改过灯塔事故日志'},
                    'destiny_flag': '灯塔核心密钥持有者',
                    'current_goals': ['查明黑匣子脉冲来源'],
                },
                {
                    'name': '莱娜·周',
                    'role_type': 'rival',
                    'status': '企业安保监察官',
                    'public_profile': {'identity': '企业安保监察官'},
                    'hidden_traits': {'fear': '害怕边境全面断航'},
                    'destiny_flag': '企业命令执行者',
                    'current_goals': ['夺取灯塔维护权限'],
                },
            ],
            'relations': [
                {
                    'source_index': 0,
                    'target_index': 1,
                    'relation_type': 'mutual_suspicion',
                    'intensity': 3,
                    'visibility': 'private',
                }
            ],
            'foreshadows': [
                {
                    'title': '黑匣子脉冲',
                    'description': '废弃黑匣子收到来自未来的求救信号。',
                    'foreshadow_type': 'signal_clue',
                    'status': 'planted',
                    'urgency_level': 5,
                    'related_character_indexes': [0, 1],
                    'expected_resolution_window': '第3-5章',
                }
            ],
        },
    }


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
            'progression_hints': [
                {
                    'hint_type': 'character',
                    'priority': 'high',
                    'title': '让许砚主动质疑企业封锁',
                    'rationale': '上一章已经暴露企业安保压力。',
                    'suggested_next_beat': '许砚绕开莱娜·周的封锁，追查黑匣子脉冲来源。',
                    'related_character_ids': [character_id],
                    'related_foreshadow_ids': [],
                    'can_seed_next_chapter_goal': True,
                }
            ],
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


def test_open_threads_returns_character_goal_and_foreshadow_threads(client):
    token = register(client)
    world = client.post('/worlds', headers=auth(token), json=custom_world_payload()).json()

    response = client.get(f"/worlds/{world['id']}/open-threads", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['world_id'] == world['id']
    assert payload['summary']['total_open_threads'] >= 2
    assert payload['summary']['should_advance_count'] >= 1
    assert payload['summary']['narrative_entropy_level'] in {'low', 'medium', 'high'}
    thread_types = {thread['thread_type'] for thread in payload['threads']}
    assert {'foreshadow', 'character_goal'}.issubset(thread_types)
    assert any(thread['title'] == '黑匣子脉冲' for thread in payload['threads'])
    assert any(thread['can_seed_next_chapter_goal'] for thread in payload['threads'])


def test_open_threads_surfaces_high_pressure_foreshadow_as_should_advance(client):
    token = register(client, 'threads-pressure@example.com')
    world = client.post('/worlds', headers=auth(token), json=custom_world_payload()).json()

    response = client.get(f"/worlds/{world['id']}/open-threads", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    foreshadow_thread = next(thread for thread in payload['threads'] if thread['thread_type'] == 'foreshadow')
    assert foreshadow_thread['priority'] in {'should_advance', 'must_close'}
    assert foreshadow_thread['pressure_level'] in {'high', 'critical'}
    assert foreshadow_thread['related_foreshadow_ids']


def test_open_threads_surfaces_health_risks_as_must_close(client, db_session):
    token = register(client, 'threads-health-risk@example.com')
    world = client.post('/worlds', headers=auth(token), json=custom_world_payload()).json()
    overview = client.get(f"/worlds/{world['id']}/overview", headers=auth(token)).json()
    character_id = overview['characters'][0]['id']
    create_approved_chapter_with_high_risk_report(db_session, world['id'], character_id)

    response = client.get(f"/worlds/{world['id']}/open-threads", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['summary']['must_close_count'] >= 1
    assert any(thread['thread_type'] == 'health_risk' and thread['priority'] == 'must_close' for thread in payload['threads'])
    assert any(thread['thread_type'] == 'progression_hint' and thread['can_seed_next_chapter_goal'] for thread in payload['threads'])


def test_open_threads_is_limited_to_owner(client):
    owner_token = register(client, 'threads-owner@example.com')
    other_token = register(client, 'threads-other@example.com')
    world = client.post('/worlds', headers=auth(owner_token), json=custom_world_payload()).json()

    response = client.get(f"/worlds/{world['id']}/open-threads", headers=auth(other_token))

    assert response.status_code == 403
    assert response.json()['detail'] == 'FORBIDDEN'
