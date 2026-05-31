def register(client, email='seed@example.com'):
    response = client.post('/auth/register', json={'email': email, 'password': 'strongpass123'})
    return response.json()['access_token']


def auth(token):
    return {'Authorization': f'Bearer {token}'}


def test_world_seed_catalog_lists_official_seeds(client):
    token = register(client)

    response = client.get('/worlds/seeds', headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert len(payload['seeds']) >= 5
    keys = {seed['key'] for seed in payload['seeds']}
    assert {'forgotten-sun-city', 'dead-god-oracle', 'generation-ship-myth'}.issubset(keys)
    first = payload['seeds'][0]
    assert first['label']
    assert first['genre_template']
    assert first['hook']
    assert first['tension_profile']
    assert first['starter_summary']['character_count'] >= 1


def test_world_seed_detail_returns_creation_payload(client):
    token = register(client, 'seed-detail@example.com')

    response = client.get('/worlds/seeds/forgotten-sun-city', headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['key'] == 'forgotten-sun-city'
    assert payload['payload']['title'] == '无日城'
    assert payload['payload']['starter_assets']['characters'][0]['name'] == '沈昼'
    assert payload['payload']['starter_assets']['foreshadows'][0]['title'] == '空白日晷'


def test_create_world_from_seed_uses_formal_world_creation_pipeline(client):
    token = register(client, 'seed-create@example.com')

    response = client.post('/worlds/from-seed/dead-god-oracle', headers=auth(token))

    assert response.status_code == 200
    world = response.json()
    assert world['title'] == '死神谕教廷'
    assert world['world_version'] == 1
    overview = client.get(f"/worlds/{world['id']}/overview", headers=auth(token)).json()
    assert len(overview['characters']) >= 2
    assert len(overview['relations']) >= 1
    assert len(overview['foreshadows']) >= 1
    assert overview['recent_events'][0]['event_type'] == 'WORLD_CREATED'
    assert overview['recent_events'][0]['source_type'] == 'world_creation'
    assert overview['recent_events'][0]['payload']['starter_counts']['characters'] == len(overview['characters'])


def test_unknown_world_seed_returns_404(client):
    token = register(client, 'seed-missing@example.com')

    detail = client.get('/worlds/seeds/not-a-seed', headers=auth(token))
    create = client.post('/worlds/from-seed/not-a-seed', headers=auth(token))

    assert detail.status_code == 404
    assert detail.json()['detail'] == 'SEED_NOT_FOUND'
    assert create.status_code == 404
    assert create.json()['detail'] == 'SEED_NOT_FOUND'


def test_world_seed_endpoints_require_login(client):
    list_response = client.get('/worlds/seeds')
    detail_response = client.get('/worlds/seeds/forgotten-sun-city')
    create_response = client.post('/worlds/from-seed/forgotten-sun-city')

    assert list_response.status_code == 401
    assert detail_response.status_code == 401
    assert create_response.status_code == 401
