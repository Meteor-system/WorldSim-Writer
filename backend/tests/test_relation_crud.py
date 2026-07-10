from sqlalchemy import select

from app.character.models import Character, CharacterRelation
from app.event.models import EventLog
from app.world.models import World


def register(client, email='writer@example.com'):
    response = client.post('/auth/register', json={'email': email, 'password': 'strongpass123'})
    return response.json()['access_token']


def create_world(client, token):
    response = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {token}'})
    return response.json()['id']


def auth(token):
    return {'Authorization': f'Bearer {token}'}


def character_ids(client, token, world_id):
    response = client.get(f'/worlds/{world_id}/characters', headers=auth(token))
    return [item['id'] for item in response.json()]


def world_state(db_session, world_id):
    db_session.expire_all()
    return db_session.get(World, world_id)


def world_events(db_session, world_id):
    db_session.expire_all()
    return list(db_session.scalars(select(EventLog).where(EventLog.world_id == world_id).order_by(EventLog.id)))


def test_relation_crud_lifecycle_uses_world_governance(client, db_session):
    token = register(client)
    world_id = create_world(client, token)
    source_id, target_id = character_ids(client, token, world_id)[:2]

    create_response = client.post(
        f'/worlds/{world_id}/relations',
        headers=auth(token),
        json={
            'source_character_id': source_id,
            'target_character_id': target_id,
            'relation_type': 'secret_ally',
            'intensity': 4,
            'visibility': 'private',
            'edit_reason': '补充隐藏盟友关系',
        },
    )

    assert create_response.status_code == 200
    created = create_response.json()
    assert created['source_character_id'] == source_id
    assert created['target_character_id'] == target_id
    assert created['relation_type'] == 'secret_ally'
    world_after_create = world_state(db_session, world_id)
    events_after_create = world_events(db_session, world_id)
    assert world_after_create.world_version == 2
    assert world_after_create.current_relations[-1]['id'] == created['id']
    assert world_after_create.current_relations[-1]['relation_type'] == 'secret_ally'
    assert [event.event_type for event in events_after_create] == ['WORLD_CREATED', 'relation_change', 'world_version_increment']
    create_event = events_after_create[1]
    assert create_event.source_type == 'manual_edit'
    assert create_event.world_version_before == 1
    assert create_event.world_version_after == 2
    assert create_event.payload['action'] == 'created'
    assert create_event.payload['object_type'] == 'relation'
    assert create_event.payload['object_id'] == created['id']
    assert create_event.payload['before'] is None
    assert create_event.payload['after']['relation_type'] == 'secret_ally'
    assert create_event.payload['edit_reason'] == '补充隐藏盟友关系'

    list_response = client.get(f'/worlds/{world_id}/relations', headers=auth(token))
    get_response = client.get(f"/relations/{created['id']}", headers=auth(token))
    assert list_response.status_code == 200
    assert created['id'] in [item['id'] for item in list_response.json()]
    assert get_response.status_code == 200
    assert get_response.json()['id'] == created['id']

    update_response = client.put(
        f"/relations/{created['id']}",
        headers=auth(token),
        json={'relation_type': 'rival', 'intensity': 5, 'visibility': 'public', 'edit_reason': '剧情转为对立'},
    )

    assert update_response.status_code == 200
    assert update_response.json()['relation_type'] == 'rival'
    world_after_update = world_state(db_session, world_id)
    events_after_update = world_events(db_session, world_id)
    assert world_after_update.world_version == 3
    updated_projection = next(item for item in world_after_update.current_relations if item['id'] == created['id'])
    assert updated_projection['relation_type'] == 'rival'
    assert updated_projection['intensity'] == 5
    update_event = events_after_update[-2]
    assert update_event.event_type == 'relation_change'
    assert update_event.source_type == 'manual_edit'
    assert update_event.world_version_before == 2
    assert update_event.world_version_after == 3
    assert update_event.payload['action'] == 'updated'
    assert update_event.payload['before']['relation_type'] == 'secret_ally'
    assert update_event.payload['after']['relation_type'] == 'rival'
    assert update_event.payload['edit_reason'] == '剧情转为对立'

    delete_response = client.delete(f"/relations/{created['id']}?edit_reason=删除重复关系", headers=auth(token))

    assert delete_response.status_code == 204
    world_after_delete = world_state(db_session, world_id)
    events_after_delete = world_events(db_session, world_id)
    assert world_after_delete.world_version == 4
    assert created['id'] not in [item['id'] for item in world_after_delete.current_relations]
    delete_event = events_after_delete[-2]
    assert delete_event.event_type == 'relation_change'
    assert delete_event.source_type == 'manual_edit'
    assert delete_event.world_version_before == 3
    assert delete_event.world_version_after == 4
    assert delete_event.payload['action'] == 'deleted'
    assert delete_event.payload['before']['relation_type'] == 'rival'
    assert delete_event.payload['after'] is None
    assert delete_event.payload['edit_reason'] == '删除重复关系'


def test_relation_rejects_invalid_character_references(client):
    token = register(client)
    world_id = create_world(client, token)
    source_id, target_id = character_ids(client, token, world_id)[:2]

    self_response = client.post(
        f'/worlds/{world_id}/relations',
        headers=auth(token),
        json={'source_character_id': source_id, 'target_character_id': source_id, 'relation_type': 'mirror'},
    )
    missing_response = client.post(
        f'/worlds/{world_id}/relations',
        headers=auth(token),
        json={'source_character_id': source_id, 'target_character_id': 99999, 'relation_type': 'unknown'},
    )

    assert self_response.status_code == 400
    assert self_response.json()['detail'] == 'INVALID_SELF_RELATION'
    assert missing_response.status_code == 404
    assert missing_response.json()['detail'] == 'RELATED_CHARACTER_NOT_FOUND'

    assert target_id != source_id


def test_relation_rejects_foreign_character_reference(client):
    owner_token = register(client, 'owner@example.com')
    other_token = register(client, 'other@example.com')
    owner_world_id = create_world(client, owner_token)
    other_world_id = create_world(client, other_token)
    owner_character_id = character_ids(client, owner_token, owner_world_id)[0]
    foreign_character_id = character_ids(client, other_token, other_world_id)[0]

    response = client.post(
        f'/worlds/{owner_world_id}/relations',
        headers=auth(owner_token),
        json={
            'source_character_id': owner_character_id,
            'target_character_id': foreign_character_id,
            'relation_type': 'foreign_link',
        },
    )

    assert response.status_code == 404
    assert response.json()['detail'] == 'RELATED_CHARACTER_NOT_FOUND'


def test_relation_endpoints_require_owner(client, db_session):
    owner_token = register(client, 'owner@example.com')
    other_token = register(client, 'other@example.com')
    world_id = create_world(client, owner_token)
    relation_id = db_session.scalar(select(CharacterRelation.id).where(CharacterRelation.world_id == world_id))

    list_response = client.get(f'/worlds/{world_id}/relations', headers=auth(other_token))
    get_response = client.get(f'/relations/{relation_id}', headers=auth(other_token))
    update_response = client.put(
        f'/relations/{relation_id}',
        headers=auth(other_token),
        json={'relation_type': '越权'},
    )
    delete_response = client.delete(f'/relations/{relation_id}', headers=auth(other_token))

    assert list_response.status_code == 403
    assert list_response.json()['detail'] == 'FORBIDDEN'
    assert get_response.status_code == 403
    assert get_response.json()['detail'] == 'FORBIDDEN'
    assert update_response.status_code == 403
    assert update_response.json()['detail'] == 'FORBIDDEN'
    assert delete_response.status_code == 403
    assert delete_response.json()['detail'] == 'FORBIDDEN'


def test_relation_create_rejects_blank_type_and_bad_intensity(client):
    token = register(client)
    world_id = create_world(client, token)
    source_id, target_id = character_ids(client, token, world_id)[:2]

    blank_response = client.post(
        f'/worlds/{world_id}/relations',
        headers=auth(token),
        json={'source_character_id': source_id, 'target_character_id': target_id, 'relation_type': '   '},
    )
    low_intensity_response = client.post(
        f'/worlds/{world_id}/relations',
        headers=auth(token),
        json={'source_character_id': source_id, 'target_character_id': target_id, 'relation_type': 'ally', 'intensity': 0},
    )
    high_intensity_response = client.post(
        f'/worlds/{world_id}/relations',
        headers=auth(token),
        json={'source_character_id': source_id, 'target_character_id': target_id, 'relation_type': 'ally', 'intensity': 6},
    )

    assert blank_response.status_code == 422
    assert any(
        error['type'] == 'value_error'
        and error['loc'] == ['body', 'relation_type']
        and error['msg'].endswith('must not be blank')
        for error in blank_response.json()['detail']
    )
    assert low_intensity_response.status_code == 422
    assert any(
        error['type'] == 'greater_than_equal'
        and error['loc'] == ['body', 'intensity']
        and error['msg'].endswith('greater than or equal to 1')
        for error in low_intensity_response.json()['detail']
    )
    assert high_intensity_response.status_code == 422
    assert any(
        error['type'] == 'less_than_equal'
        and error['loc'] == ['body', 'intensity']
        and error['msg'].endswith('less than or equal to 5')
        for error in high_intensity_response.json()['detail']
    )


def test_relation_create_rejects_extra_fields_without_side_effects(client, db_session):
    token = register(client)
    world_id = create_world(client, token)
    source_id, target_id = character_ids(client, token, world_id)[:2]
    before_relations = client.get(f'/worlds/{world_id}/relations', headers=auth(token)).json()
    before_world_version = world_state(db_session, world_id).world_version
    before_event_ids = [event.id for event in world_events(db_session, world_id)]

    response = client.post(
        f'/worlds/{world_id}/relations',
        headers=auth(token),
        json={
            'source_character_id': source_id,
            'target_character_id': target_id,
            'relation_type': 'secret_ally',
            'raw_text': '不应被接受的运行时字段',
        },
    )

    assert response.status_code == 422
    assert any(error['type'] == 'extra_forbidden' and error['loc'] == ['body', 'raw_text'] for error in response.json()['detail'])
    after_relations = client.get(f'/worlds/{world_id}/relations', headers=auth(token)).json()
    assert after_relations == before_relations
    assert world_state(db_session, world_id).world_version == before_world_version
    assert [event.id for event in world_events(db_session, world_id)] == before_event_ids


def test_relation_update_rejects_extra_fields_without_side_effects(client, db_session):
    token = register(client)
    world_id = create_world(client, token)
    existing_id = db_session.scalar(select(CharacterRelation.id).where(CharacterRelation.world_id == world_id))
    before_relation = client.get(f'/relations/{existing_id}', headers=auth(token)).json()
    before_world_version = world_state(db_session, world_id).world_version
    before_event_ids = [event.id for event in world_events(db_session, world_id)]

    response = client.put(
        f'/relations/{existing_id}',
        headers=auth(token),
        json={'relation_type': '不应修改', 'raw_text': '不应被接受的运行时字段'},
    )

    assert response.status_code == 422
    assert any(error['type'] == 'extra_forbidden' and error['loc'] == ['body', 'raw_text'] for error in response.json()['detail'])
    after_relation = client.get(f'/relations/{existing_id}', headers=auth(token)).json()
    assert after_relation == before_relation
    assert world_state(db_session, world_id).world_version == before_world_version
    assert [event.id for event in world_events(db_session, world_id)] == before_event_ids


def test_relation_delete_rejects_extra_body_fields_without_side_effects(client, db_session):
    token = register(client)
    world_id = create_world(client, token)
    existing_id = db_session.scalar(select(CharacterRelation.id).where(CharacterRelation.world_id == world_id))
    before_relation = client.get(f'/relations/{existing_id}', headers=auth(token)).json()
    before_world_version = world_state(db_session, world_id).world_version
    before_event_ids = [event.id for event in world_events(db_session, world_id)]

    response = client.request(
        'DELETE',
        f'/relations/{existing_id}',
        headers=auth(token),
        json={'raw_text': '删除端点不应接收运行时字段'},
    )

    assert response.status_code == 422
    assert any(error['type'] == 'extra_forbidden' and error['loc'] == ['body', 'raw_text'] for error in response.json()['detail'])
    after_relation = client.get(f'/relations/{existing_id}', headers=auth(token)).json()
    assert after_relation == before_relation
    assert world_state(db_session, world_id).world_version == before_world_version
    assert [event.id for event in world_events(db_session, world_id)] == before_event_ids


def test_archived_world_rejects_relation_writes_but_allows_reads(client, db_session):
    token = register(client)
    world_id = create_world(client, token)
    source_id, target_id = character_ids(client, token, world_id)[:2]
    existing_id = db_session.scalar(select(CharacterRelation.id).where(CharacterRelation.world_id == world_id))

    archive_response = client.patch(f'/worlds/{world_id}/status', headers=auth(token), json={'status': 'archived'})
    assert archive_response.status_code == 200

    create_response = client.post(
        f'/worlds/{world_id}/relations',
        headers=auth(token),
        json={'source_character_id': source_id, 'target_character_id': target_id, 'relation_type': 'archived_link'},
    )
    update_response = client.put(
        f'/relations/{existing_id}',
        headers=auth(token),
        json={'relation_type': '不应修改'},
    )
    delete_response = client.delete(f'/relations/{existing_id}', headers=auth(token))

    assert create_response.status_code == 409
    assert create_response.json()['detail'] == 'WORLD_ARCHIVED'
    assert update_response.status_code == 409
    assert update_response.json()['detail'] == 'WORLD_ARCHIVED'
    assert delete_response.status_code == 409
    assert delete_response.json()['detail'] == 'WORLD_ARCHIVED'

    list_response = client.get(f'/worlds/{world_id}/relations', headers=auth(token))
    get_response = client.get(f'/relations/{existing_id}', headers=auth(token))
    assert list_response.status_code == 200
    assert get_response.status_code == 200
