from sqlalchemy import select

from app.character.models import Character, CharacterRelation
from app.event.models import EventLog
from app.llm.schemas import ChapterGeneration, ProposedCharacterChange, ProposedForeshadowChange
from app.narrative import service as narrative_service
from app.narrative.models import Chapter, ChapterDraft
from app.world.models import World


class StoryBibleDraftLLMClient:
    def generate_chapter(self, messages):
        return ChapterGeneration(
            title='第一章 雨巷密谈',
            draft_content='第一段：林砚停在雨巷口。\n\n第二段：沈微霜递来一封湿透的信。',
            context_summary='林砚与沈微霜交换线索。',
            review_hints=['确认第二段信息揭示是否过快'],
            proposed_character_changes=[
                ProposedCharacterChange(character_id=1, status='开始调查密信', current_goals=['追查湿信来源'])
            ],
            proposed_foreshadow_changes=[
                ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='湿信推进玉佩线索')
            ],
        )


def register_user(client, email='story-bible@example.com'):
    return client.post('/auth/register', json={'email': email, 'password': 'strongpass123'}).json()['access_token']


def auth(token):
    return {'Authorization': f'Bearer {token}'}


def create_world(client, token):
    return client.post('/worlds/from-template', headers=auth(token)).json()


def first_character(db_session, world_id):
    return db_session.scalar(select(Character).where(Character.world_id == world_id).order_by(Character.id))


def second_character(db_session, world_id):
    return list(db_session.scalars(select(Character).where(Character.world_id == world_id).order_by(Character.id)))[1]


def first_relation(db_session, world_id):
    return db_session.scalar(select(CharacterRelation).where(CharacterRelation.world_id == world_id).order_by(CharacterRelation.id))


def manual_events(db_session, world_id):
    return list(
        db_session.scalars(
            select(EventLog)
            .where(EventLog.world_id == world_id)
            .where(EventLog.source_type == 'manual_edit')
            .order_by(EventLog.id)
        )
    )


def create_reviewing_draft(client, token, world_id, monkeypatch):
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: StoryBibleDraftLLMClient())
    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进雨巷密谈'},
        headers=auth(token),
    )
    assert response.status_code == 200
    return response.json()


def test_update_character_increments_world_version_refreshes_projection_and_writes_events(client, db_session):
    token = register_user(client)
    world_payload = create_world(client, token)
    world_id = world_payload['id']
    character = first_character(db_session, world_id)

    response = client.put(
        f'/characters/{character.id}',
        json={
            'status': '谨慎调查密信',
            'current_goals': ['验证沈微霜是否可信', '追查湿信来源'],
            'edit_reason': '同步 Story Bible 设定',
        },
        headers=auth(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == '谨慎调查密信'
    assert payload['current_goals'] == ['验证沈微霜是否可信', '追查湿信来源']

    db_session.expire_all()
    world = db_session.get(World, world_id)
    updated = db_session.get(Character, character.id)
    events = manual_events(db_session, world_id)

    assert world.world_version == 2
    assert updated.status == '谨慎调查密信'
    assert updated.current_goals == ['验证沈微霜是否可信', '追查湿信来源']
    projected = next(item for item in world.current_characters if item['id'] == character.id)
    assert projected['status'] == '谨慎调查密信'
    assert projected['current_goals'] == ['验证沈微霜是否可信', '追查湿信来源']
    assert [event.event_type for event in events] == ['character_change', 'world_version_increment']
    assert events[0].payload['action'] == 'updated'
    assert events[0].payload['edit_reason'] == '同步 Story Bible 设定'
    assert events[0].world_version_before == 1
    assert events[0].world_version_after == 2


def test_non_owner_cannot_update_character(client, db_session):
    owner_token = register_user(client, 'owner-story-bible@example.com')
    other_token = register_user(client, 'intruder-story-bible@example.com')
    world_payload = create_world(client, owner_token)
    character = first_character(db_session, world_payload['id'])

    response = client.put(
        f'/characters/{character.id}',
        json={'status': '非法修改'},
        headers=auth(other_token),
    )

    assert response.status_code == 403
    assert response.json()['detail'] == 'FORBIDDEN'


def test_missing_character_update_returns_not_found(client):
    token = register_user(client)

    response = client.put('/characters/999999', json={'status': '不存在'}, headers=auth(token))

    assert response.status_code == 404
    assert response.json()['detail'] == 'NOT_FOUND'


def test_create_relation_increments_world_version_refreshes_projection_and_writes_events(client, db_session):
    token = register_user(client)
    world_payload = create_world(client, token)
    world_id = world_payload['id']
    source = first_character(db_session, world_id)
    target = second_character(db_session, world_id)

    response = client.post(
        f'/worlds/{world_id}/relations',
        json={
            'source_character_id': source.id,
            'target_character_id': target.id,
            'relation_type': 'cautious_alliance',
            'intensity': 3,
            'visibility': 'private',
            'edit_reason': '补充试探关系',
        },
        headers=auth(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['relation_type'] == 'cautious_alliance'
    assert payload['intensity'] == 3
    assert payload['visibility'] == 'private'

    db_session.expire_all()
    world = db_session.get(World, world_id)
    events = manual_events(db_session, world_id)

    assert world.world_version == 2
    assert any(item['id'] == payload['id'] and item['relation_type'] == 'cautious_alliance' for item in world.current_relations)
    assert [event.event_type for event in events] == ['relation_change', 'world_version_increment']
    assert events[0].payload['action'] == 'created'
    assert events[0].payload['edit_reason'] == '补充试探关系'


def test_update_relation_increments_world_version_and_refreshes_projection(client, db_session):
    token = register_user(client)
    world_payload = create_world(client, token)
    world_id = world_payload['id']
    relation = first_relation(db_session, world_id)

    response = client.put(
        f'/relations/{relation.id}',
        json={'relation_type': 'trusted_ally', 'intensity': 4, 'visibility': 'public', 'edit_reason': '关系升温'},
        headers=auth(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['relation_type'] == 'trusted_ally'
    assert payload['intensity'] == 4

    db_session.expire_all()
    world = db_session.get(World, world_id)
    updated = db_session.get(CharacterRelation, relation.id)
    events = manual_events(db_session, world_id)

    assert world.world_version == 2
    assert updated.relation_type == 'trusted_ally'
    projected = next(item for item in world.current_relations if item['id'] == relation.id)
    assert projected['relation_type'] == 'trusted_ally'
    assert projected['intensity'] == 4
    assert [event.event_type for event in events] == ['relation_change', 'world_version_increment']
    assert events[0].payload['action'] == 'updated'


def test_relation_create_and_update_reject_invalid_or_cross_world_characters(client, db_session):
    token = register_user(client)
    first_world = create_world(client, token)
    second_world = create_world(client, token)
    source = first_character(db_session, first_world['id'])
    cross_world_character = first_character(db_session, second_world['id'])
    relation = first_relation(db_session, first_world['id'])

    self_response = client.post(
        f"/worlds/{first_world['id']}/relations",
        json={'source_character_id': source.id, 'target_character_id': source.id, 'relation_type': 'mirror'},
        headers=auth(token),
    )
    cross_create = client.post(
        f"/worlds/{first_world['id']}/relations",
        json={'source_character_id': source.id, 'target_character_id': cross_world_character.id, 'relation_type': 'impossible'},
        headers=auth(token),
    )
    cross_update = client.put(
        f'/relations/{relation.id}',
        json={'source_character_id': source.id, 'target_character_id': cross_world_character.id},
        headers=auth(token),
    )

    assert self_response.status_code == 400
    assert self_response.json()['detail'] == 'INVALID_SELF_RELATION'
    assert cross_create.status_code == 404
    assert cross_create.json()['detail'] == 'RELATED_CHARACTER_NOT_FOUND'
    assert cross_update.status_code == 404
    assert cross_update.json()['detail'] == 'RELATED_CHARACTER_NOT_FOUND'


def test_story_bible_edit_does_not_mutate_reviewing_draft_and_readiness_reports_version_mismatch(client, db_session, monkeypatch):
    token = register_user(client)
    world_payload = create_world(client, token)
    world_id = world_payload['id']
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)
    character = first_character(db_session, world_id)

    response = client.put(
        f'/characters/{character.id}',
        json={'status': '手动更新后的正式状态', 'current_goals': ['正式目标']},
        headers=auth(token),
    )
    assert response.status_code == 200

    db_session.expire_all()
    world = db_session.get(World, world_id)
    chapter = db_session.get(Chapter, draft['chapter_id'])
    stored_draft = db_session.scalar(select(ChapterDraft).where(ChapterDraft.id == draft['draft_id']))

    assert world.world_version == 2
    assert chapter.status == 'reviewing'
    assert chapter.draft_version == draft['draft_version']
    assert stored_draft.content == draft['content']
    assert stored_draft.source_world_version == 1

    readiness = client.get(f"/chapters/{draft['chapter_id']}/approval-readiness", headers=auth(token))
    preview = client.get(f"/chapters/{draft['chapter_id']}/approval-preview", headers=auth(token))

    assert readiness.status_code == 200
    readiness_payload = readiness.json()
    assert readiness_payload['world_version']['source_world_version'] == 1
    assert readiness_payload['world_version']['current_world_version'] == 2
    assert readiness_payload['world_version']['matches'] is False
    assert readiness_payload['status'] == 'blocked'
    assert readiness_payload['ready'] is False
    assert readiness_payload['blocking_reasons'] == ['世界版本已变化，请重新生成草稿后再批准。']
    assert isinstance(readiness_payload['warnings'], list)

    assert preview.status_code == 200
    preview_payload = preview.json()
    assert preview_payload['source_world_version'] == 1
    assert preview_payload['current_world_version'] == 2
    assert preview_payload['version_conflict'] is True


def test_approval_readiness_exposes_direct_ready_status(client, monkeypatch):
    token = register_user(client, 'readiness-direct@example.com')
    world_payload = create_world(client, token)
    draft = create_reviewing_draft(client, token, world_payload['id'], monkeypatch)

    response = client.get(f"/chapters/{draft['chapter_id']}/approval-readiness", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['ready'] is False
    assert payload['status'] in {'needs_review', 'blocked'}
    assert isinstance(payload['blocking_reasons'], list)
    assert isinstance(payload['warnings'], list)
