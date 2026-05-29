from sqlalchemy import func, select

from app.event.models import EventLog
from app.llm.schemas import ChapterGeneration, ProposedCharacterChange, ProposedForeshadowChange
from app.narrative import service as narrative_service
from app.narrative.models import Chapter
from app.world.models import World


class NarrativeControlLLMClient:
    def generate_chapter(self, messages):
        return ChapterGeneration(
            title='第一章 雨巷密谈',
            draft_content='林砚停在雨巷口，掌心玉佩微微发烫。\n\n沈微霜递来一封湿透的信，信尾写着城主府外墙。',
            context_summary='林砚与沈微霜在雨巷交换湿信线索。',
            review_hints=['确认沈微霜的动机是否可信'],
            proposed_character_changes=[
                ProposedCharacterChange(character_id=1, status='开始调查密信', current_goals=['追查湿信来源'])
            ],
            proposed_foreshadow_changes=[
                ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='湿信推进玉佩线索')
            ],
        )


def register_and_create_world(client, email='ncc@example.com'):
    token = client.post('/auth/register', json={'email': email, 'password': 'strongpass123'}).json()['access_token']
    world = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {token}'}).json()
    return token, world['id']


def create_draft(client, token, world_id, monkeypatch):
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: NarrativeControlLLMClient())
    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进雨巷密谈'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == 200
    return response.json()


def approve_draft(client, token, draft):
    response = client.post(f"/chapters/{draft['chapter_id']}/approve", headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    return response.json()


def approve_chapter(client, token, world_id, monkeypatch):
    draft = create_draft(client, token, world_id, monkeypatch)
    return approve_draft(client, token, draft)


def test_chapter_history_returns_only_approved_chapters(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    approved = approve_chapter(client, token, world_id, monkeypatch)
    create_draft(client, token, world_id, monkeypatch)

    response = client.get(f'/worlds/{world_id}/chapters/history', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    payload = response.json()
    assert payload['world_id'] == world_id
    assert [chapter['id'] for chapter in payload['chapters']] == [approved['id']]
    assert payload['chapters'][0]['status'] == 'approved'


def test_chapter_history_item_includes_excerpt_and_event_counts(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    approved = approve_chapter(client, token, world_id, monkeypatch)

    response = client.get(f'/worlds/{world_id}/chapters/history', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    item = response.json()['chapters'][0]
    assert item['id'] == approved['id']
    assert item['approved_version'] == 1
    assert item['base_world_version'] == 1
    assert item['world_version_after'] == 2
    assert item['approved_excerpt'].startswith('林砚停在雨巷口')
    assert item['event_count'] == 4
    assert item['character_change_count'] == 1
    assert item['foreshadow_change_count'] == 1


def test_chapter_history_detail_returns_approved_content_and_event_changes(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    approved = approve_chapter(client, token, world_id, monkeypatch)

    response = client.get(f"/chapters/{approved['id']}/history", headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    payload = response.json()
    assert payload['id'] == approved['id']
    assert payload['world_id'] == world_id
    assert payload['approved_content'].startswith('林砚停在雨巷口')
    assert payload['approved_version'] == 1
    assert payload['base_world_version'] == 1
    assert payload['world_version_before'] == 1
    assert payload['world_version_after'] == 2
    assert payload['character_changes'][0]['event_type'] == 'character_change'
    assert payload['character_changes'][0]['object_type'] == 'character'
    assert payload['character_changes'][0]['before']['status'] == 'active'
    assert payload['character_changes'][0]['after']['status'] == '开始调查密信'
    assert payload['foreshadow_changes'][0]['event_type'] == 'foreshadow_change'
    assert payload['foreshadow_changes'][0]['object_type'] == 'foreshadow'
    assert payload['foreshadow_changes'][0]['after']['status'] == 'advanced'
    assert any(event['event_type'] == 'chapter_approved' for event in payload['events'])


def test_unapproved_chapter_history_detail_returns_conflict(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_draft(client, token, world_id, monkeypatch)

    response = client.get(f"/chapters/{draft['chapter_id']}/history", headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 409
    assert response.json()['detail'] == 'CHAPTER_NOT_APPROVED'


def test_next_chapter_prep_uses_high_priority_character_arc_progression_hint(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    approved = approve_chapter(client, token, world_id, monkeypatch)
    chapter = db_session.get(Chapter, approved['id'])
    chapter.character_arc_report = {
        'summary': '林砚从被动等待转向主动追查。',
        'draft_version': 1,
        'current_draft_version': 1,
        'is_stale': False,
        'character_arcs': [
            {
                'character_id': 1,
                'name': '林砚',
                'role_type': 'protagonist',
                'current_status': '开始调查密信',
                'current_goals': ['追查湿信来源'],
                'presence_level': 'major',
                'arc_stage': 'choice',
                'chapter_function': '承担调查者功能。',
                'observed_shift': '开始主动追问。',
                'proposed_state_change': None,
                'continuity_risk': 'medium',
                'risk_reason': '下一章需要补足试探过程。',
                'suggested_revision': None,
                'next_chapter_setup': '前往城主府外墙。',
            }
        ],
        'relationship_notes': [],
        'progression_hints': [
            {
                'hint_type': 'character',
                'priority': 'high',
                'title': '试探沈微霜是否可信',
                'rationale': '上一章已经建立湿信线索。',
                'suggested_next_beat': '林砚带着湿信赴城主府外墙，并设置一次试探。',
                'related_character_ids': [1],
                'related_foreshadow_ids': [1],
                'can_seed_next_chapter_goal': True,
            }
        ],
        'created_at': '2026-05-29T00:00:00Z',
    }
    db_session.commit()

    response = client.get(f'/worlds/{world_id}/next-chapter-prep', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    payload = response.json()
    assert payload['world_id'] == world_id
    assert payload['world_version'] == 2
    assert payload['next_chapter_number'] == 2
    assert payload['suggested_goal'] == '林砚带着湿信赴城主府外墙，并设置一次试探。'
    assert payload['recommended_pov_character_id'] == 1
    assert payload['recommended_pov_character_name'] == '林砚'
    assert 'character_arc_progression_hint' in payload['source_signals']
    assert payload['priority_characters'][0]['character_id'] == 1
    assert payload['priority_foreshadows'][0]['foreshadow_id'] == 1
    assert payload['progression_hints'][0]['title'] == '试探沈微霜是否可信'
    assert payload['continuity_warnings'][0]['category'] == 'character_arc'


def test_next_chapter_prep_falls_back_to_next_story_arc_summary(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    approve_chapter(client, token, world_id, monkeypatch)
    world = db_session.get(World, world_id)
    world.story_arc = [
        {'chapter_number': 2, 'summary': '林砚潜入城主府外墙，发现密道入口。', 'pov_suggestion': '林砚'}
    ]
    db_session.commit()

    response = client.get(f'/worlds/{world_id}/next-chapter-prep', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    payload = response.json()
    assert payload['suggested_goal'] == '林砚潜入城主府外墙，发现密道入口。'
    assert payload['recommended_pov_character_name'] == '林砚'
    assert 'story_arc' in payload['source_signals']


def test_next_chapter_prep_falls_back_to_highest_urgency_foreshadow(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    approve_chapter(client, token, world_id, monkeypatch)
    world = db_session.get(World, world_id)
    world.story_arc = []
    db_session.commit()

    response = client.get(f'/worlds/{world_id}/next-chapter-prep', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    payload = response.json()
    assert payload['suggested_goal'].startswith('推进伏笔《')
    assert 'urgent_foreshadow' in payload['source_signals']
    assert payload['priority_foreshadows'][0]['urgency_level'] >= 1


def test_next_chapter_prep_does_not_mutate_world_version_or_write_events(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    approve_chapter(client, token, world_id, monkeypatch)
    db_session.expire_all()
    world_before = db_session.get(World, world_id)
    version_before = world_before.world_version
    event_count_before = db_session.scalar(select(func.count()).select_from(EventLog))

    response = client.get(f'/worlds/{world_id}/next-chapter-prep', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    db_session.expire_all()
    world_after = db_session.get(World, world_id)
    event_count_after = db_session.scalar(select(func.count()).select_from(EventLog))
    assert world_after.world_version == version_before
    assert event_count_after == event_count_before


def test_narrative_control_center_rejects_non_owner_access(client, monkeypatch):
    owner_token, world_id = register_and_create_world(client, 'owner-ncc@example.com')
    approved = approve_chapter(client, owner_token, world_id, monkeypatch)
    other_token = client.post('/auth/register', json={'email': 'other-ncc@example.com', 'password': 'strongpass123'}).json()['access_token']

    history_response = client.get(f'/worlds/{world_id}/chapters/history', headers={'Authorization': f'Bearer {other_token}'})
    detail_response = client.get(f"/chapters/{approved['id']}/history", headers={'Authorization': f'Bearer {other_token}'})
    prep_response = client.get(f'/worlds/{world_id}/next-chapter-prep', headers={'Authorization': f'Bearer {other_token}'})

    assert history_response.status_code == 403
    assert history_response.json()['detail'] == 'FORBIDDEN'
    assert detail_response.status_code == 403
    assert detail_response.json()['detail'] == 'FORBIDDEN'
    assert prep_response.status_code == 403
    assert prep_response.json()['detail'] == 'FORBIDDEN'
