from app.foreshadow.models import Foreshadow
from app.narrative.models import Chapter, ChapterDraft
from app.world.models import World


def register(client, email='arc@example.com'):
    response = client.post('/auth/register', json={'email': email, 'password': 'strongpass123'})
    return response.json()['access_token']


def auth(token):
    return {'Authorization': f'Bearer {token}'}


def minimal_world_payload():
    return {
        'title': '群星边境',
        'genre_template': 'sci_fi',
        'truth_canon': '边境殖民地依赖一座濒临失控的跃迁灯塔。',
        'tone_profile': {'style': '冷峻太空歌剧'},
        'starter_assets': {
            'characters': [
                {'name': '许砚', 'role_type': 'protagonist', 'current_goals': []},
            ],
            'relations': [],
            'foreshadows': [],
        },
    }


def goal_world_payload():
    payload = minimal_world_payload()
    payload['starter_assets']['characters'][0]['current_goals'] = ['查明灯塔异常']
    return payload


def foreshadow_world_payload():
    payload = goal_world_payload()
    payload['starter_assets']['foreshadows'] = [
        {
            'title': '黑匣子脉冲',
            'description': '废弃黑匣子收到来自未来的求救信号。',
            'foreshadow_type': 'signal_clue',
            'status': 'planted',
            'urgency_level': 5,
            'related_character_indexes': [0],
        }
    ]
    return payload


def create_approved_chapter(db_session, world_id, index=1, character_id=None, high_risk=False):
    character_arcs = []
    critique_issues = []
    if high_risk:
        critique_issues.append({'severity': 'high', 'dimension': 'pacing', 'message': '开头缺少抓力。'})
        character_arcs.append(
            {
                'character_id': character_id,
                'name': '许砚',
                'continuity_risk': 'high',
                'risk_reason': '突然接受企业安保帮助，缺少铺垫。',
            }
        )
    chapter = Chapter(
        world_id=world_id,
        title=f'第{index}章 灯塔密令',
        status='approved',
        draft_version=1,
        approved_version=1,
        base_world_version=index,
        approved_content=f'许砚第{index}次追查灯塔异常。',
        chapter_goal='推进灯塔异常。',
        critique_report={
            'overall_score': 50 if high_risk else 88,
            'summary': '章节报告。',
            'issues': critique_issues,
            'dimensions': {},
            'suggestions': [],
            'draft_version': 1,
            'current_draft_version': 1,
            'is_stale': False,
        },
        character_arc_report={
            'summary': '角色弧线报告。',
            'character_arcs': character_arcs,
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
            source_world_version=index,
        )
    )
    db_session.flush()
    return chapter


def set_story_arc(db_session, world_id, count=10):
    world = db_session.get(World, world_id)
    world.story_arc = [
        {
            'chapter_number': index,
            'title': f'第{index}章',
            'summary': f'推进第{index}阶段冲突。',
            'core_conflict': '灯塔控制权争夺。',
            'pov_suggestion': '许砚',
            'foreshadow_hints': [],
        }
        for index in range(1, count + 1)
    ]
    db_session.commit()


def test_arc_plan_returns_expand_mode_for_new_low_pressure_world(client):
    token = register(client)
    world = client.post('/worlds', headers=auth(token), json=minimal_world_payload()).json()

    response = client.get(f"/worlds/{world['id']}/arc-plan", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['world_id'] == world['id']
    assert payload['arc_mode'] == 'expand'
    assert payload['expansion_budget'] == 'open'
    assert payload['next_chapter_number'] == 1
    assert payload['recommended_goal']
    assert any(item['guidance_key'] == 'write_first_chapter' for item in payload['guidance'])
    assert payload['source_summary']['approved_chapter_count'] == 0


def test_arc_plan_uses_organize_mode_for_high_risk_reports(client, db_session):
    token = register(client, 'arc-risk@example.com')
    world = client.post('/worlds', headers=auth(token), json=goal_world_payload()).json()
    overview = client.get(f"/worlds/{world['id']}/overview", headers=auth(token)).json()
    create_approved_chapter(db_session, world['id'], character_id=overview['characters'][0]['id'], high_risk=True)
    db_session.commit()

    response = client.get(f"/worlds/{world['id']}/arc-plan", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['arc_mode'] == 'organize'
    assert payload['expansion_budget'] == 'locked'
    assert '高风险' in payload['mode_reason']
    assert any(item['treatment'] == 'close' for item in payload['closure_items'])
    assert any(item['guidance_key'] == 'repair_first' for item in payload['guidance'])


def test_arc_plan_converges_overdue_open_threads(client, db_session):
    token = register(client, 'arc-converge@example.com')
    world = client.post('/worlds', headers=auth(token), json=foreshadow_world_payload()).json()
    first = create_approved_chapter(db_session, world['id'], index=1)
    foreshadow = db_session.query(Foreshadow).filter(Foreshadow.world_id == world['id']).one()
    foreshadow.source_chapter_id = first.id
    for index in range(2, 8):
        create_approved_chapter(db_session, world['id'], index=index)
    db_session.commit()

    response = client.get(f"/worlds/{world['id']}/arc-plan", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['arc_mode'] == 'converge'
    assert payload['expansion_budget'] == 'locked'
    assert payload['source_summary']['must_close_count'] >= 1
    assert any(item['thread_id'] == f'foreshadow:{foreshadow.id}' and item['treatment'] == 'close' for item in payload['closure_items'])


def test_arc_plan_uses_payoff_mode_late_in_story_arc(client, db_session):
    token = register(client, 'arc-payoff@example.com')
    world = client.post('/worlds', headers=auth(token), json=goal_world_payload()).json()
    set_story_arc(db_session, world['id'], count=10)
    for index in range(1, 8):
        create_approved_chapter(db_session, world['id'], index=index)
    db_session.commit()

    response = client.get(f"/worlds/{world['id']}/arc-plan", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['arc_mode'] == 'payoff'
    assert payload['expansion_budget'] == 'limited'
    assert payload['source_summary']['story_arc_length'] == 10
    assert payload['source_summary']['approved_chapter_count'] == 7
    assert any(item['treatment'] == 'advance' for item in payload['closure_items'])


def test_arc_plan_is_limited_to_owner(client):
    owner_token = register(client, 'arc-owner@example.com')
    other_token = register(client, 'arc-other@example.com')
    world = client.post('/worlds', headers=auth(owner_token), json=minimal_world_payload()).json()

    response = client.get(f"/worlds/{world['id']}/arc-plan", headers=auth(other_token))

    assert response.status_code == 403
    assert response.json()['detail'] == 'FORBIDDEN'
