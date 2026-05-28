def register(client, email='writer@example.com'):
    response = client.post('/auth/register', json={'email': email, 'password': 'strongpass123'})
    return response.json()['access_token']


def create_world(client, token):
    response = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {token}'})
    return response.json()['id']


def auth(token):
    return {'Authorization': f'Bearer {token}'}


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


def test_character_endpoints_require_login(client):
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
