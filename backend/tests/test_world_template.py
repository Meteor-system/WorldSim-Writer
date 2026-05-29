def register(client, email='writer@example.com'):
    response = client.post('/auth/register', json={'email': email, 'password': 'strongpass123'})
    return response.json()['access_token']


def auth(token):
    return {'Authorization': f'Bearer {token}'}


def custom_world_payload():
    return {
        'title': '群星边境',
        'genre_template': 'sci_fi',
        'truth_canon': '人类边境殖民地依赖一座濒临失控的跃迁灯塔，企业安保、走私船团与殖民议会围绕灯塔控制权暗中角力。',
        'tone_profile': {'style': '冷峻太空歌剧', 'pacing': '高压悬疑'},
        'starter_assets': {
            'characters': [
                {
                    'name': '许砚',
                    'role_type': 'protagonist',
                    'status': 'active',
                    'public_profile': {'identity': '灯塔维修工程师', 'skill': '跃迁阵列校准'},
                    'hidden_traits': {'secret': '曾篡改灯塔事故日志'},
                    'destiny_flag': '灯塔核心密钥持有者',
                    'current_goals': ['查明灯塔异常脉冲来源'],
                },
                {
                    'name': '莱娜·周',
                    'role_type': 'rival',
                    'status': 'active',
                    'public_profile': {'identity': '企业安保监察官', 'skill': '审讯与战术部署'},
                    'hidden_traits': {'fear': '害怕边境全面断航'},
                    'destiny_flag': '企业命令执行者',
                    'current_goals': ['夺取灯塔维护权限'],
                },
            ],
            'relations': [
                {
                    'source_index': 0,
                    'target_index': 1,
                    'relation_type': 'mutual_suspicion',
                    'intensity': 3,
                    'visibility': 'private',
                }
            ],
            'foreshadows': [
                {
                    'title': '黑匣子脉冲',
                    'description': '每次跃迁灯塔校准失败后，废弃黑匣子都会收到一段来自未来的求救信号。',
                    'foreshadow_type': 'signal_clue',
                    'status': 'planted',
                    'urgency_level': 4,
                    'related_character_indexes': [0, 1],
                    'expected_resolution_window': '第3-5章',
                }
            ],
        },
    }


def test_create_sample_world_and_overview(client):
    token = register(client)

    create_response = client.post('/worlds/from-template', headers=auth(token))

    assert create_response.status_code == 200
    world_id = create_response.json()['id']
    assert create_response.json()['world_version'] == 1

    overview_response = client.get(f'/worlds/{world_id}/overview', headers=auth(token))
    overview = overview_response.json()

    assert overview_response.status_code == 200
    assert overview['title'] == '青岚城风云'
    assert len(overview['characters']) == 2
    assert len(overview['relations']) == 1
    assert len(overview['foreshadows']) == 1
    assert overview['recent_events'] == []

    list_response = client.get('/worlds', headers=auth(token))
    assert list_response.status_code == 200
    assert [world['id'] for world in list_response.json()] == [world_id]

    get_response = client.get(f'/worlds/{world_id}', headers=auth(token))
    assert get_response.status_code == 200
    assert get_response.json()['id'] == world_id


def test_create_custom_world_from_template_payload(client):
    token = register(client)

    create_response = client.post('/worlds', headers=auth(token), json=custom_world_payload())

    assert create_response.status_code == 200
    created = create_response.json()
    assert created['title'] == '群星边境'
    assert created['genre_template'] == 'sci_fi'
    assert created['truth_canon_version'] == 1
    assert created['world_version'] == 1
    assert created['status'] == 'active'
    assert created['tone_profile'] == {'style': '冷峻太空歌剧', 'pacing': '高压悬疑'}

    overview_response = client.get(f"/worlds/{created['id']}/overview", headers=auth(token))
    overview = overview_response.json()

    assert overview_response.status_code == 200
    assert overview['title'] == '群星边境'
    assert len(overview['characters']) == 2
    assert len(overview['relations']) == 1
    assert len(overview['foreshadows']) == 1
    assert overview['recent_events'] == []

    character_ids = [character['id'] for character in overview['characters']]
    relation = overview['relations'][0]
    assert relation['source_character_id'] == character_ids[0]
    assert relation['target_character_id'] == character_ids[1]
    assert relation['relation_type'] == 'mutual_suspicion'

    foreshadow = overview['foreshadows'][0]
    assert foreshadow['title'] == '黑匣子脉冲'
    assert foreshadow['related_character_ids'] == character_ids


def test_template_foreshadows_get_initial_timeline_event(client):
    token = register(client)

    create_response = client.post('/worlds', headers=auth(token), json=custom_world_payload())
    assert create_response.status_code == 200
    world_id = create_response.json()['id']
    overview = client.get(f'/worlds/{world_id}/overview', headers=auth(token)).json()
    foreshadow_id = overview['foreshadows'][0]['id']

    timeline = client.get(f'/foreshadows/{foreshadow_id}/timeline', headers=auth(token))

    assert timeline.status_code == 200
    assert [event['event_type'] for event in timeline.json()] == ['planted']


def test_create_custom_world_requires_login(client):
    response = client.post('/worlds', json=custom_world_payload())

    assert response.status_code == 401
    assert response.json()['detail'] == 'UNAUTHORIZED'


def test_create_custom_world_rejects_missing_characters(client):
    token = register(client)
    payload = custom_world_payload()
    payload['starter_assets']['characters'] = []

    response = client.post('/worlds', headers=auth(token), json=payload)

    assert response.status_code == 422
    list_response = client.get('/worlds', headers=auth(token))
    assert list_response.json() == []


def test_create_custom_world_rejects_invalid_relation_character_index(client):
    token = register(client)
    payload = custom_world_payload()
    payload['starter_assets']['relations'][0]['target_index'] = 99

    response = client.post('/worlds', headers=auth(token), json=payload)

    assert response.status_code == 422
    assert response.json()['detail'] == 'INVALID_CHARACTER_INDEX'
    list_response = client.get('/worlds', headers=auth(token))
    assert list_response.json() == []


def test_create_custom_world_rejects_invalid_foreshadow_character_index(client):
    token = register(client)
    payload = custom_world_payload()
    payload['starter_assets']['foreshadows'][0]['related_character_indexes'] = [0, 99]

    response = client.post('/worlds', headers=auth(token), json=payload)

    assert response.status_code == 422
    assert response.json()['detail'] == 'INVALID_CHARACTER_INDEX'
    list_response = client.get('/worlds', headers=auth(token))
    assert list_response.json() == []


def test_world_access_is_limited_to_owner(client):
    owner_token = register(client, 'owner@example.com')
    other_token = register(client, 'other@example.com')
    create_response = client.post('/worlds/from-template', headers=auth(owner_token))
    world_id = create_response.json()['id']

    get_response = client.get(f'/worlds/{world_id}', headers=auth(other_token))
    overview_response = client.get(f'/worlds/{world_id}/overview', headers=auth(other_token))

    assert get_response.status_code == 403
    assert get_response.json()['detail'] == 'FORBIDDEN'
    assert overview_response.status_code == 403
    assert overview_response.json()['detail'] == 'FORBIDDEN'


def test_world_endpoints_require_login(client):
    response = client.post('/worlds/from-template')

    assert response.status_code == 401
    assert response.json()['detail'] == 'UNAUTHORIZED'
