from sqlalchemy import select

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


def world_state(db_session, world_id):
    db_session.expire_all()
    return db_session.get(World, world_id)


def world_events(db_session, world_id):
    db_session.expire_all()
    return list(db_session.scalars(select(EventLog).where(EventLog.world_id == world_id).order_by(EventLog.id)))


def test_character_crud_lifecycle(client):
    token = register(client)
    world_id = create_world(client, token)

    create_response = client.post(
        f'/worlds/{world_id}/characters',
        headers=auth(token),
        json={
            'name': '林七',
            'role_type': 'supporting',
            'status': 'active',
            'destiny_flag': '守门人',
            'current_goals': ['保护青岚城'],
        },
    )

    assert create_response.status_code == 200
    created = create_response.json()
    assert created['name'] == '林七'
    assert created['role_type'] == 'supporting'
    assert created['public_profile'] == {}
    assert created['hidden_traits'] == {}
    assert created['current_goals'] == ['保护青岚城']

    list_response = client.get(f'/worlds/{world_id}/characters', headers=auth(token))
    assert list_response.status_code == 200
    assert created['id'] in [item['id'] for item in list_response.json()]

    get_response = client.get(f"/characters/{created['id']}", headers=auth(token))
    assert get_response.status_code == 200
    assert get_response.json()['id'] == created['id']

    update_response = client.put(
        f"/characters/{created['id']}",
        headers=auth(token),
        json={'name': '林七改', 'current_goals': ['追查旧案']},
    )
    assert update_response.status_code == 200
    assert update_response.json()['name'] == '林七改'
    assert update_response.json()['current_goals'] == ['追查旧案']

    delete_response = client.delete(f"/characters/{created['id']}", headers=auth(token))
    assert delete_response.status_code == 204
    assert delete_response.content == b''

    missing_response = client.get(f"/characters/{created['id']}", headers=auth(token))
    assert missing_response.status_code == 404
    assert missing_response.json()['detail'] == 'NOT_FOUND'


def test_character_create_increments_world_version_refreshes_projection_and_writes_event(client, db_session):
    token = register(client)
    world_id = create_world(client, token)

    response = client.post(
        f'/worlds/{world_id}/characters',
        headers=auth(token),
        json={
            'name': '林七',
            'role_type': 'supporting',
            'status': 'active',
            'current_goals': ['保护青岚城'],
            'edit_reason': '补充守门人角色',
        },
    )

    assert response.status_code == 200
    character = response.json()
    world = world_state(db_session, world_id)
    events = world_events(db_session, world_id)
    assert world.world_version == 2
    assert world.current_characters[-1]['id'] == character['id']
    assert world.current_characters[-1]['name'] == '林七'
    assert [event.event_type for event in events] == ['character_change', 'world_version_increment']
    character_event = events[0]
    assert character_event.source_type == 'manual_edit'
    assert character_event.world_version_before == 1
    assert character_event.world_version_after == 2
    assert character_event.payload['action'] == 'created'
    assert character_event.payload['object_type'] == 'character'
    assert character_event.payload['object_id'] == character['id']
    assert character_event.payload['before'] is None
    assert character_event.payload['after']['name'] == '林七'
    assert character_event.payload['edit_reason'] == '补充守门人角色'


def test_character_update_increments_world_version_refreshes_projection_and_writes_event(client, db_session):
    token = register(client)
    world_id = create_world(client, token)
    created = client.post(
        f'/worlds/{world_id}/characters',
        headers=auth(token),
        json={'name': '林七', 'role_type': 'supporting'},
    ).json()

    response = client.put(
        f"/characters/{created['id']}",
        headers=auth(token),
        json={'name': '林七改', 'current_goals': ['追查旧案'], 'edit_reason': '修正角色目标'},
    )

    assert response.status_code == 200
    world = world_state(db_session, world_id)
    events = world_events(db_session, world_id)
    assert world.world_version == 3
    updated_projection = next(item for item in world.current_characters if item['id'] == created['id'])
    assert updated_projection['name'] == '林七改'
    assert updated_projection['current_goals'] == ['追查旧案']
    character_event = events[-2]
    assert character_event.event_type == 'character_change'
    assert character_event.source_type == 'manual_edit'
    assert character_event.world_version_before == 2
    assert character_event.world_version_after == 3
    assert character_event.payload['action'] == 'updated'
    assert character_event.payload['object_id'] == created['id']
    assert character_event.payload['before']['name'] == '林七'
    assert character_event.payload['after']['name'] == '林七改'
    assert character_event.payload['after']['current_goals'] == ['追查旧案']
    assert character_event.payload['edit_reason'] == '修正角色目标'


def test_character_delete_increments_world_version_refreshes_projection_and_writes_event(client, db_session):
    token = register(client)
    world_id = create_world(client, token)
    created = client.post(
        f'/worlds/{world_id}/characters',
        headers=auth(token),
        json={'name': '林七', 'role_type': 'supporting'},
    ).json()

    response = client.delete(
        f"/characters/{created['id']}?edit_reason=删除重复角色",
        headers=auth(token),
    )

    assert response.status_code == 204
    world = world_state(db_session, world_id)
    events = world_events(db_session, world_id)
    assert world.world_version == 3
    assert created['id'] not in [item['id'] for item in world.current_characters]
    character_event = events[-2]
    assert character_event.event_type == 'character_change'
    assert character_event.source_type == 'manual_edit'
    assert character_event.world_version_before == 2
    assert character_event.world_version_after == 3
    assert character_event.payload['action'] == 'deleted'
    assert character_event.payload['object_id'] == created['id']
    assert character_event.payload['before']['name'] == '林七'
    assert character_event.payload['after'] is None
    assert character_event.payload['edit_reason'] == '删除重复角色'


    response = client.get('/worlds/1/characters')

    assert response.status_code == 401
    assert response.json()['detail'] == 'UNAUTHORIZED'


def test_character_access_is_limited_to_owner(client):
    owner_token = register(client, 'owner@example.com')
    other_token = register(client, 'other@example.com')
    world_id = create_world(client, owner_token)
    create_response = client.post(
        f'/worlds/{world_id}/characters',
        headers=auth(owner_token),
        json={'name': '林七', 'role_type': 'supporting'},
    )
    character_id = create_response.json()['id']

    list_response = client.get(f'/worlds/{world_id}/characters', headers=auth(other_token))
    get_response = client.get(f'/characters/{character_id}', headers=auth(other_token))
    update_response = client.put(
        f'/characters/{character_id}',
        headers=auth(other_token),
        json={'name': '越权'},
    )
    delete_response = client.delete(f'/characters/{character_id}', headers=auth(other_token))

    assert list_response.status_code == 403
    assert list_response.json()['detail'] == 'FORBIDDEN'
    assert get_response.status_code == 403
    assert get_response.json()['detail'] == 'FORBIDDEN'
    assert update_response.status_code == 403
    assert update_response.json()['detail'] == 'FORBIDDEN'
    assert delete_response.status_code == 403
    assert delete_response.json()['detail'] == 'FORBIDDEN'


def test_character_create_rejects_blank_required_fields(client):
    token = register(client)
    world_id = create_world(client, token)

    response = client.post(
        f'/worlds/{world_id}/characters',
        headers=auth(token),
        json={'name': '   ', 'role_type': '   '},
    )

    assert response.status_code == 422


def test_delete_character_removes_foreshadow_reference(client):
    token = register(client)
    world_id = create_world(client, token)
    character_response = client.post(
        f'/worlds/{world_id}/characters',
        headers=auth(token),
        json={'name': '林七', 'role_type': 'supporting'},
    )
    character_id = character_response.json()['id']
    foreshadow_response = client.post(
        f'/worlds/{world_id}/foreshadows',
        headers=auth(token),
        json={
            'title': '铜铃异响',
            'description': '夜半铜铃无人自鸣。',
            'foreshadow_type': 'plot',
            'related_character_ids': [character_id],
        },
    )
    foreshadow_id = foreshadow_response.json()['id']

    delete_response = client.delete(f'/characters/{character_id}', headers=auth(token))
    get_foreshadow_response = client.get(f'/foreshadows/{foreshadow_id}', headers=auth(token))

    assert delete_response.status_code == 204
    assert get_foreshadow_response.status_code == 200
    assert get_foreshadow_response.json()['related_character_ids'] == []
