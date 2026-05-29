from sqlalchemy import select

from app.character.models import Character, CharacterRelation
from app.event.models import EventLog
from app.foreshadow.models import Foreshadow
from app.llm.schemas import ChapterGeneration, ProposedCharacterChange, ProposedForeshadowChange
from app.narrative import service as narrative_service
from app.narrative.models import Chapter, ChapterDraft
from app.world.models import World


def auth(token):
    return {'Authorization': f'Bearer {token}'}


def register(client, email='writer@example.com'):
    response = client.post('/auth/register', json={'email': email, 'password': 'strongpass123'})
    return response.json()['access_token']


def register_and_create_world(client):
    token = register(client)
    world = client.post('/worlds/from-template', headers=auth(token)).json()
    return token, world['id']


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


def create_draft(client, token, world_id, monkeypatch):
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers=auth(token),
    )
    assert response.status_code == 200
    return response.json()


def test_create_world_initializes_current_projection(client, db_session):
    token, world_id = register_and_create_world(client)

    world = db_session.get(World, world_id)

    assert world.owner_id is not None
    assert world.current_characters[0]['name'] == '林砚'
    assert world.current_characters[0]['current_goals'] == ['调查青岚城灵脉衰退']
    assert world.current_foreshadows[0]['title'] == '裂纹玉佩'
    assert world.current_foreshadows[0]['status'] == 'planted'
    assert world.current_relations[0]['relation_type'] == 'uneasy_alliance'
    assert world.current_relations[0]['intensity'] == 2


def test_world_overview_returns_current_relations_projection(client, db_session):
    token, world_id = register_and_create_world(client)
    relation = db_session.scalar(select(CharacterRelation).where(CharacterRelation.world_id == world_id))

    response = client.get(f'/worlds/{world_id}/overview', headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['current_relations'] == [
        {
            'id': relation.id,
            'source_character_id': relation.source_character_id,
            'target_character_id': relation.target_character_id,
            'relation_type': 'uneasy_alliance',
            'intensity': 2,
            'visibility': 'public',
        }
    ]


def test_approve_writes_granular_events_and_projection_snapshots(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_draft(client, token, world_id, monkeypatch)
    world_before = db_session.get(World, world_id)

    assert world_before.world_version == 1
    assert world_before.current_characters[0]['current_goals'] == ['调查青岚城灵脉衰退']
    assert world_before.current_foreshadows[0]['status'] == 'planted'

    response = client.post(f"/chapters/{draft['chapter_id']}/approve", headers=auth(token))

    assert response.status_code == 200
    db_session.expire_all()
    world_after = db_session.get(World, world_id)
    character = db_session.scalar(select(Character).where(Character.world_id == world_id).order_by(Character.id))
    foreshadow = db_session.scalar(select(Foreshadow).where(Foreshadow.world_id == world_id).order_by(Foreshadow.id))
    events = list(db_session.scalars(select(EventLog).where(EventLog.world_id == world_id).order_by(EventLog.id)))

    assert world_after.world_version == 2
    assert character.current_goals == ['追查城主府叛乱']
    assert foreshadow.status == 'advanced'
    assert world_after.current_characters[0]['current_goals'] == ['追查城主府叛乱']
    assert world_after.current_foreshadows[0]['status'] == 'advanced'
    assert [event.event_type for event in events] == [
        'character_change',
        'foreshadow_change',
        'world_version_increment',
        'chapter_approved',
    ]
    assert all(event.chapter_id == draft['chapter_id'] for event in events)
    assert all(event.world_version_before == 1 for event in events)
    assert all(event.world_version_after == 2 for event in events)
    character_event = events[0]
    assert character_event.payload['before']['current_goals'] == ['调查青岚城灵脉衰退']
    assert character_event.payload['after']['current_goals'] == ['追查城主府叛乱']
    foreshadow_event = events[1]
    assert foreshadow_event.payload['before']['status'] == 'planted'
    assert foreshadow_event.payload['after']['status'] == 'advanced'
    assert events[-1].payload['chapter_id'] == draft['chapter_id']


def test_approve_rolls_back_when_any_projection_change_is_invalid(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft_payload = create_draft(client, token, world_id, monkeypatch)
    draft = db_session.get(ChapterDraft, draft_payload['draft_id'])
    draft.proposed_changes = {
        'characters': [{'character_id': 1, 'current_goals': ['不应落库的目标']}],
        'foreshadows': [{'foreshadow_id': 9999, 'status': 'advanced', 'description_note': '非法伏笔'}],
    }
    db_session.commit()

    response = client.post(f"/chapters/{draft_payload['chapter_id']}/approve", headers=auth(token))

    assert response.status_code == 502
    assert response.json()['detail'] == 'MODEL_RESPONSE_INVALID'
    db_session.expire_all()
    world = db_session.get(World, world_id)
    chapter = db_session.get(Chapter, draft_payload['chapter_id'])
    character = db_session.scalar(select(Character).where(Character.world_id == world_id).order_by(Character.id))
    events = list(db_session.scalars(select(EventLog).where(EventLog.world_id == world_id)))
    assert world.world_version == 1
    assert world.current_characters[0]['current_goals'] == ['调查青岚城灵脉衰退']
    assert chapter.status == 'reviewing'
    assert character.current_goals == ['调查青岚城灵脉衰退']
    assert events == []


def test_world_events_endpoint_filters_paginates_latest_first(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_draft(client, token, world_id, monkeypatch)
    client.post(f"/chapters/{draft['chapter_id']}/approve", headers=auth(token))

    paginated = client.get(f'/worlds/{world_id}/events?limit=2', headers=auth(token))
    filtered = client.get(f'/worlds/{world_id}/events?event_type=character_change', headers=auth(token))
    offset = client.get(f'/worlds/{world_id}/events?limit=2&offset=2', headers=auth(token))

    assert paginated.status_code == 200
    payload = paginated.json()
    assert payload['total'] == 4
    assert payload['limit'] == 2
    assert payload['offset'] == 0
    assert len(payload['items']) == 2
    assert payload['items'][0]['event_type'] == 'chapter_approved'
    assert payload['items'][0]['chapter_id'] == draft['chapter_id']
    assert filtered.status_code == 200
    assert filtered.json()['total'] == 1
    assert filtered.json()['items'][0]['event_type'] == 'character_change'
    assert offset.status_code == 200
    assert offset.json()['items'][0]['event_type'] == 'foreshadow_change'


def test_world_events_endpoint_requires_owner(client, monkeypatch):
    owner_token, world_id = register_and_create_world(client)
    other_token = register(client, 'other@example.com')
    draft = create_draft(client, owner_token, world_id, monkeypatch)
    client.post(f"/chapters/{draft['chapter_id']}/approve", headers=auth(owner_token))

    unauthenticated = client.get(f'/worlds/{world_id}/events')
    forbidden = client.get(f'/worlds/{world_id}/events', headers=auth(other_token))

    assert unauthenticated.status_code == 401
    assert unauthenticated.json()['detail'] == 'UNAUTHORIZED'
    assert forbidden.status_code == 403
    assert forbidden.json()['detail'] == 'FORBIDDEN'
