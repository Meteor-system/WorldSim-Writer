def register(client, email='writer@example.com'):
    response = client.post('/auth/register', json={'email': email, 'password': 'strongpass123'})
    return response.json()['access_token']


def create_world(client, token):
    response = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {token}'})
    return response.json()['id']


def auth(token):
    return {'Authorization': f'Bearer {token}'}


def first_character_id(client, token, world_id):
    response = client.get(f'/worlds/{world_id}/characters', headers=auth(token))
    return response.json()[0]['id']


def create_chapter(db_session, world_id):
    from app.narrative.models import Chapter

    chapter = Chapter(
        world_id=world_id,
        title='测试章节',
        status='reviewing',
        draft_version=1,
        base_world_version=1,
    )
    db_session.add(chapter)
    db_session.commit()
    db_session.refresh(chapter)
    return chapter.id


def test_foreshadow_crud_lifecycle(client, db_session):
    token = register(client)
    world_id = create_world(client, token)
    character_id = first_character_id(client, token, world_id)
    chapter_id = create_chapter(db_session, world_id)

    create_response = client.post(
        f'/worlds/{world_id}/foreshadows',
        headers=auth(token),
        json={
            'source_chapter_id': chapter_id,
            'title': '铜铃异响',
            'description': '夜半铜铃无人自鸣。',
            'foreshadow_type': 'plot',
            'status': 'planted',
            'urgency_level': 4,
            'related_character_ids': [character_id],
            'expected_resolution_window': '第三幕',
        },
    )

    assert create_response.status_code == 200
    created = create_response.json()
    assert created['title'] == '铜铃异响'
    assert created['urgency_level'] == 4
    assert created['related_character_ids'] == [character_id]

    list_response = client.get(f'/worlds/{world_id}/foreshadows', headers=auth(token))
    assert list_response.status_code == 200
    assert created['id'] in [item['id'] for item in list_response.json()]

    get_response = client.get(f"/foreshadows/{created['id']}", headers=auth(token))
    assert get_response.status_code == 200
    assert get_response.json()['id'] == created['id']

    update_response = client.put(
        f"/foreshadows/{created['id']}",
        headers=auth(token),
        json={'status': 'advanced', 'urgency_level': 5, 'related_character_ids': []},
    )
    assert update_response.status_code == 200
    assert update_response.json()['status'] == 'advanced'
    assert update_response.json()['urgency_level'] == 5
    assert update_response.json()['related_character_ids'] == []

    delete_response = client.delete(f"/foreshadows/{created['id']}", headers=auth(token))
    assert delete_response.status_code == 204
    assert delete_response.content == b''

    missing_response = client.get(f"/foreshadows/{created['id']}", headers=auth(token))
    assert missing_response.status_code == 404
    assert missing_response.json()['detail'] == 'NOT_FOUND'


def test_foreshadow_endpoints_require_login(client):
    response = client.get('/worlds/1/foreshadows')

    assert response.status_code == 401
    assert response.json()['detail'] == 'UNAUTHORIZED'


def test_foreshadow_access_is_limited_to_owner(client):
    owner_token = register(client, 'owner@example.com')
    other_token = register(client, 'other@example.com')
    world_id = create_world(client, owner_token)
    create_response = client.post(
        f'/worlds/{world_id}/foreshadows',
        headers=auth(owner_token),
        json={
            'title': '铜铃异响',
            'description': '夜半铜铃无人自鸣。',
            'foreshadow_type': 'plot',
        },
    )
    foreshadow_id = create_response.json()['id']

    list_response = client.get(f'/worlds/{world_id}/foreshadows', headers=auth(other_token))
    get_response = client.get(f'/foreshadows/{foreshadow_id}', headers=auth(other_token))
    update_response = client.put(
        f'/foreshadows/{foreshadow_id}',
        headers=auth(other_token),
        json={'status': 'resolved'},
    )
    delete_response = client.delete(f'/foreshadows/{foreshadow_id}', headers=auth(other_token))

    assert list_response.status_code == 403
    assert list_response.json()['detail'] == 'FORBIDDEN'
    assert get_response.status_code == 403
    assert get_response.json()['detail'] == 'FORBIDDEN'
    assert update_response.status_code == 403
    assert update_response.json()['detail'] == 'FORBIDDEN'
    assert delete_response.status_code == 403
    assert delete_response.json()['detail'] == 'FORBIDDEN'


def test_foreshadow_rejects_blank_required_fields_and_bad_urgency(client):
    token = register(client)
    world_id = create_world(client, token)

    blank_response = client.post(
        f'/worlds/{world_id}/foreshadows',
        headers=auth(token),
        json={'title': ' ', 'description': ' ', 'foreshadow_type': ' '},
    )
    low_urgency_response = client.post(
        f'/worlds/{world_id}/foreshadows',
        headers=auth(token),
        json={
            'title': '铜铃异响',
            'description': '夜半铜铃无人自鸣。',
            'foreshadow_type': 'plot',
            'urgency_level': 0,
        },
    )
    high_urgency_response = client.post(
        f'/worlds/{world_id}/foreshadows',
        headers=auth(token),
        json={
            'title': '铜铃异响',
            'description': '夜半铜铃无人自鸣。',
            'foreshadow_type': 'plot',
            'urgency_level': 6,
        },
    )

    assert blank_response.status_code == 422
    assert low_urgency_response.status_code == 422
    assert high_urgency_response.status_code == 422


def test_foreshadow_rejects_unknown_related_character(client):
    token = register(client)
    world_id = create_world(client, token)

    response = client.post(
        f'/worlds/{world_id}/foreshadows',
        headers=auth(token),
        json={
            'title': '铜铃异响',
            'description': '夜半铜铃无人自鸣。',
            'foreshadow_type': 'plot',
            'related_character_ids': [99999],
        },
    )

    assert response.status_code == 404
    assert response.json()['detail'] == 'RELATED_CHARACTER_NOT_FOUND'


def test_foreshadow_rejects_foreign_related_character(client):
    owner_token = register(client, 'owner@example.com')
    other_token = register(client, 'other@example.com')
    owner_world_id = create_world(client, owner_token)
    other_world_id = create_world(client, other_token)
    foreign_character_id = first_character_id(client, other_token, other_world_id)

    response = client.post(
        f'/worlds/{owner_world_id}/foreshadows',
        headers=auth(owner_token),
        json={
            'title': '铜铃异响',
            'description': '夜半铜铃无人自鸣。',
            'foreshadow_type': 'plot',
            'related_character_ids': [foreign_character_id],
        },
    )

    assert response.status_code == 404
    assert response.json()['detail'] == 'RELATED_CHARACTER_NOT_FOUND'


def test_foreshadow_rejects_unknown_source_chapter(client):
    token = register(client)
    world_id = create_world(client, token)

    response = client.post(
        f'/worlds/{world_id}/foreshadows',
        headers=auth(token),
        json={
            'source_chapter_id': 99999,
            'title': '铜铃异响',
            'description': '夜半铜铃无人自鸣。',
            'foreshadow_type': 'plot',
        },
    )

    assert response.status_code == 404
    assert response.json()['detail'] == 'SOURCE_CHAPTER_NOT_FOUND'


def test_foreshadow_rejects_foreign_source_chapter(client, db_session):
    owner_token = register(client, 'owner@example.com')
    other_token = register(client, 'other@example.com')
    owner_world_id = create_world(client, owner_token)
    other_world_id = create_world(client, other_token)
    foreign_chapter_id = create_chapter(db_session, other_world_id)

    response = client.post(
        f'/worlds/{owner_world_id}/foreshadows',
        headers=auth(owner_token),
        json={
            'source_chapter_id': foreign_chapter_id,
            'title': '铜铃异响',
            'description': '夜半铜铃无人自鸣。',
            'foreshadow_type': 'plot',
        },
    )

    assert response.status_code == 404
    assert response.json()['detail'] == 'SOURCE_CHAPTER_NOT_FOUND'
