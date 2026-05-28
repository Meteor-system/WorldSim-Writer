def register(client, email='writer@example.com'):
    response = client.post('/auth/register', json={'email': email, 'password': 'strongpass123'})
    return response.json()['access_token']


def test_create_sample_world_and_overview(client):
    token = register(client)

    create_response = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {token}'})

    assert create_response.status_code == 200
    world_id = create_response.json()['id']
    assert create_response.json()['world_version'] == 1

    overview_response = client.get(f'/worlds/{world_id}/overview', headers={'Authorization': f'Bearer {token}'})
    overview = overview_response.json()

    assert overview_response.status_code == 200
    assert overview['title'] == '青岚城风云'
    assert len(overview['characters']) == 2
    assert len(overview['relations']) == 1
    assert len(overview['foreshadows']) == 1
    assert overview['recent_events'] == []

    list_response = client.get('/worlds', headers={'Authorization': f'Bearer {token}'})
    assert list_response.status_code == 200
    assert [world['id'] for world in list_response.json()] == [world_id]

    get_response = client.get(f'/worlds/{world_id}', headers={'Authorization': f'Bearer {token}'})
    assert get_response.status_code == 200
    assert get_response.json()['id'] == world_id


def test_world_access_is_limited_to_owner(client):
    owner_token = register(client, 'owner@example.com')
    other_token = register(client, 'other@example.com')
    create_response = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {owner_token}'})
    world_id = create_response.json()['id']

    get_response = client.get(f'/worlds/{world_id}', headers={'Authorization': f'Bearer {other_token}'})
    overview_response = client.get(f'/worlds/{world_id}/overview', headers={'Authorization': f'Bearer {other_token}'})

    assert get_response.status_code == 403
    assert get_response.json()['detail'] == 'FORBIDDEN'
    assert overview_response.status_code == 403
    assert overview_response.json()['detail'] == 'FORBIDDEN'


def test_world_endpoints_require_login(client):
    response = client.post('/worlds/from-template')

    assert response.status_code == 401
    assert response.json()['detail'] == 'UNAUTHORIZED'
