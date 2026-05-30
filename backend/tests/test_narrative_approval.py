from app.llm.schemas import ChapterGeneration, ProposedCharacterChange, ProposedForeshadowChange
from app.narrative import service as narrative_service
from app.narrative.models import Chapter
from app.world.models import World


class FailingLLMClient:
    def generate_chapter(self, messages):
        raise RuntimeError('MODEL_REQUEST_FAILED')


class FakeLLMClient:
    def generate_chapter(self, messages):
        return ChapterGeneration(
            title='第一章 暗井回声',
            draft_content='林砚在灵井旁听见了第二个人的脚步声。',
            context_summary='林砚调查灵脉衰退，裂纹玉佩成为线索。',
            review_hints=['确认沈微霜动机是否一致'],
            proposed_character_changes=[ProposedCharacterChange(character_id=1, current_goals=['追查城主府叛乱'])],
            proposed_foreshadow_changes=[
                ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='玉佩线索被推进')
            ],
        )


def register_and_create_world(client):
    token = client.post('/auth/register', json={'email': 'writer@example.com', 'password': 'strongpass123'}).json()['access_token']
    world = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {token}'}).json()
    return token, world['id']


def test_generation_prompt_includes_expired_foreshadow_status(client, db_session):
    token, world_id = register_and_create_world(client)
    world = db_session.get(World, world_id)
    characters, foreshadows = narrative_service._load_world_context(db_session, world)

    messages = narrative_service.build_generation_messages(world, characters, foreshadows, '推进玉佩线索')

    assert 'advanced|resolved|expired' in messages[0]['content']



def test_create_draft_with_fake_llm(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())

    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    assert response.json()['title'] == '第一章 暗井回声'
    assert response.json()['source_world_version'] == 1
    assert response.json()['proposed_changes']['characters'][0]['current_goals'] == ['追查城主府叛乱']


def test_approve_chapter_updates_world_character_foreshadow_and_events(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    approve_response = client.post(f"/chapters/{draft['chapter_id']}/approve", headers={'Authorization': f'Bearer {token}'})
    overview_response = client.get(f'/worlds/{world_id}/overview', headers={'Authorization': f'Bearer {token}'})
    overview = overview_response.json()

    assert approve_response.status_code == 200
    assert overview['world_version'] == 2
    assert overview['characters'][0]['current_goals'] == ['追查城主府叛乱']
    assert overview['foreshadows'][0]['status'] == 'advanced'
    assert overview['recent_events'][0]['event_type'] == 'chapter_approved'
    assert overview['recent_events'][0]['world_version_before'] == 1
    assert overview['recent_events'][0]['world_version_after'] == 2


def test_approve_chapter_creates_foreshadow_lifecycle_event(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    response = client.post(f"/chapters/{draft['chapter_id']}/approve", headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200

    timeline = client.get('/foreshadows/1/timeline', headers={'Authorization': f'Bearer {token}'})
    assert timeline.status_code == 200
    event = timeline.json()[-1]
    assert event['event_type'] == 'advanced'
    assert event['chapter_id'] == draft['chapter_id']
    assert event['chapter_title'] == '第一章 暗井回声'
    assert event['note'] == '玉佩线索被推进'


def test_reject_chapter_does_not_approve_or_update_world(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    reject_response = client.post(f"/chapters/{draft['chapter_id']}/reject", headers={'Authorization': f'Bearer {token}'})
    overview_response = client.get(f'/worlds/{world_id}/overview', headers={'Authorization': f'Bearer {token}'})
    overview = overview_response.json()

    assert reject_response.status_code == 200
    assert reject_response.json()['status'] == 'rejected'
    assert reject_response.json()['approved_content'] is None
    assert overview['world_version'] == 1
    assert overview['recent_events'] == []


def test_create_draft_maps_model_request_failure(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FailingLLMClient())

    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 502
    assert response.json()['detail'] == 'MODEL_REQUEST_FAILED'


def test_approve_rejects_world_version_mismatch(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()
    world = db_session.get(World, world_id)
    world.world_version = 2
    db_session.commit()

    response = client.post(f"/chapters/{draft['chapter_id']}/approve", headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 409
    assert response.json()['detail'] == 'WORLD_VERSION_MISMATCH'


def readiness_execution_context(source_world_version: int = 1) -> dict:
    return {
        'source': 'next_chapter_prep',
        'source_world_version': source_world_version,
        'next_chapter_number': 1,
        'goal': '推进玉佩线索',
        'recommended_pov': {'character_id': 1, 'name': '林砚'},
        'source_signals': ['character_arc_progression_hint'],
        'priority_characters': [
            {'character_id': 1, 'name': '林砚', 'role_type': 'protagonist', 'status': 'active', 'reason': '主角需要推进'}
        ],
        'priority_foreshadows': [
            {'foreshadow_id': 1, 'title': '裂纹玉佩', 'status': 'planted', 'urgency_level': 3, 'reason': '伏笔需要推进'}
        ],
        'progression_hints': [
            {
                'hint_type': 'character',
                'priority': 'high',
                'title': '追查玉佩来源',
                'rationale': '上一章已经设置玉佩线索',
                'suggested_next_beat': '林砚带着玉佩询问沈微霜',
                'related_character_ids': [1],
                'related_foreshadow_ids': [1],
                'can_seed_next_chapter_goal': True,
            }
        ],
        'continuity_warnings': [],
        'recent_events': [],
    }


def add_current_review_reports(db_session, chapter_id: int, high_risk: bool = False) -> None:
    chapter = db_session.get(Chapter, chapter_id)
    assert chapter is not None
    critic_issue = {
        'severity': 'high' if high_risk else 'medium',
        'dimension': 'character_consistency',
        'message': '林砚突然信任沈微霜，与当前谨慎状态冲突。',
        'paragraph_index': 0,
        'suggested_action': '补足信任建立过程。',
    }
    chapter.critique_report = {
        'chapter_id': chapter.id,
        'draft_version': chapter.draft_version,
        'current_draft_version': chapter.draft_version,
        'is_stale': False,
        'overall_score': 82,
        'summary': '整体可批准。',
        'dimensions': {},
        'issues': [critic_issue] if high_risk else [],
        'suggestions': [],
        'created_at': '2026-05-30T00:00:00Z',
    }
    chapter.character_arc_report = {
        'chapter_id': chapter.id,
        'draft_version': chapter.draft_version,
        'current_draft_version': chapter.draft_version,
        'is_stale': False,
        'summary': '角色弧线连续。',
        'character_arcs': [
            {
                'character_id': 1,
                'name': '林砚',
                'continuity_risk': 'high' if high_risk else 'low',
                'risk_reason': '选择转折缺少铺垫。' if high_risk else None,
            }
        ],
        'relationship_notes': [],
        'progression_hints': [],
        'created_at': '2026-05-30T00:00:00Z',
    }
    db_session.commit()


def test_approval_readiness_ready_when_all_checks_pass(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索', 'execution_context': readiness_execution_context()},
        headers={'Authorization': f'Bearer {token}'},
    ).json()
    add_current_review_reports(db_session, draft['chapter_id'])

    response = client.get(f"/chapters/{draft['chapter_id']}/approval-readiness", headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'ready'
    assert body['summary'] == '草稿已通过所有审批准备检查。'
    assert body['world_version']['matches'] is True
    assert {check['status'] for check in body['checks']} == {'pass'}


def test_approval_readiness_blocks_world_version_mismatch(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索', 'execution_context': readiness_execution_context()},
        headers={'Authorization': f'Bearer {token}'},
    ).json()
    world = db_session.get(World, world_id)
    world.world_version = 2
    db_session.commit()

    response = client.get(f"/chapters/{draft['chapter_id']}/approval-readiness", headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'blocked'
    version_check = next(check for check in body['checks'] if check['key'] == 'world_version')
    assert version_check['status'] == 'fail'
    assert version_check['message'] == '世界版本已变化，请重新生成草稿后再批准。'


def test_approval_readiness_needs_review_for_missing_reports_and_uncovered_priorities(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    context = readiness_execution_context()
    context['priority_characters'].append(
        {'character_id': 2, 'name': '沈微霜', 'role_type': 'ally', 'status': 'active', 'reason': '需要回应主角试探'}
    )
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索', 'execution_context': context},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    response = client.get(f"/chapters/{draft['chapter_id']}/approval-readiness", headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'needs_review'
    priority_check = next(check for check in body['checks'] if check['key'] == 'priority_coverage')
    assert priority_check['status'] == 'warning'
    assert priority_check['details']['missing_character_ids'] == [2]
    assert next(check for check in body['checks'] if check['key'] == 'critic_high_risk')['status'] == 'warning'
    assert next(check for check in body['checks'] if check['key'] == 'character_arc_risk')['status'] == 'warning'


def test_approval_readiness_reports_high_risk_items(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索', 'execution_context': readiness_execution_context()},
        headers={'Authorization': f'Bearer {token}'},
    ).json()
    add_current_review_reports(db_session, draft['chapter_id'], high_risk=True)

    response = client.get(f"/chapters/{draft['chapter_id']}/approval-readiness", headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'needs_review'
    assert body['high_risk_items'] == [
        {
            'source': 'critic',
            'severity': 'high',
            'message': '林砚突然信任沈微霜，与当前谨慎状态冲突。',
            'details': {'dimension': 'character_consistency', 'paragraph_index': 0},
        },
        {
            'source': 'character_arc',
            'severity': 'high',
            'message': '林砚：选择转折缺少铺垫。',
            'details': {'character_id': 1, 'risk_reason': '选择转折缺少铺垫。'},
        },
    ]
