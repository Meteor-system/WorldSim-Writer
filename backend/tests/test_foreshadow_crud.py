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


def create_foreshadow(client, token, world_id, title='铜铃异响', status='planted', source_chapter_id=None):
    payload = {
        'title': title,
        'description': '夜半铜铃无人自鸣。',
        'foreshadow_type': 'plot',
        'status': status,
    }
    if source_chapter_id is not None:
        payload['source_chapter_id'] = source_chapter_id
    response = client.post(f'/worlds/{world_id}/foreshadows', headers=auth(token), json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_foreshadow_event_model_is_registered(db_session):
    from app.foreshadow.models import ForeshadowEvent

    with db_session.bind.connect() as connection:
        table_names = set(db_session.bind.dialect.get_table_names(connection))
    assert 'foreshadow_events' in table_names
    assert ForeshadowEvent.__tablename__ == 'foreshadow_events'


def test_foreshadow_status_transitions(client):
    token = register(client)
    world_id = create_world(client, token)
    foreshadow = create_foreshadow(client, token, world_id)

    advanced = client.put(f"/foreshadows/{foreshadow['id']}", headers=auth(token), json={'status': 'advanced'})
    assert advanced.status_code == 200
    assert advanced.json()['status'] == 'advanced'

    backwards = client.put(f"/foreshadows/{foreshadow['id']}", headers=auth(token), json={'status': 'planted'})
    assert backwards.status_code == 400
    assert backwards.json()['detail'] == 'INVALID_STATUS_TRANSITION'

    resolved = client.put(f"/foreshadows/{foreshadow['id']}", headers=auth(token), json={'status': 'resolved'})
    assert resolved.status_code == 200
    assert resolved.json()['status'] == 'resolved'

    terminal = client.put(f"/foreshadows/{foreshadow['id']}", headers=auth(token), json={'status': 'expired'})
    assert terminal.status_code == 400
    assert terminal.json()['detail'] == 'INVALID_STATUS_TRANSITION'

    expiring = create_foreshadow(client, token, world_id, title='井中红光')
    expired = client.put(f"/foreshadows/{expiring['id']}", headers=auth(token), json={'status': 'expired'})
    assert expired.status_code == 200
    assert expired.json()['status'] == 'expired'


def test_foreshadow_rejects_invalid_status(client):
    token = register(client)
    world_id = create_world(client, token)

    create_response = client.post(
        f'/worlds/{world_id}/foreshadows',
        headers=auth(token),
        json={'title': '铜铃异响', 'description': '夜半铜铃无人自鸣。', 'foreshadow_type': 'plot', 'status': 'bad'},
    )
    assert create_response.status_code == 400
    assert create_response.json()['detail'] == 'INVALID_STATUS'

    foreshadow = create_foreshadow(client, token, world_id)
    update_response = client.put(f"/foreshadows/{foreshadow['id']}", headers=auth(token), json={'status': 'bad'})
    assert update_response.status_code == 400
    assert update_response.json()['detail'] == 'INVALID_STATUS'


def test_foreshadow_timeline(client):
    token = register(client)
    world_id = create_world(client, token)
    foreshadow = create_foreshadow(client, token, world_id)

    update = client.put(f"/foreshadows/{foreshadow['id']}", headers=auth(token), json={'status': 'advanced'})
    assert update.status_code == 200

    timeline = client.get(f"/foreshadows/{foreshadow['id']}/timeline", headers=auth(token))
    assert timeline.status_code == 200
    events = timeline.json()
    assert [event['event_type'] for event in events] == ['planted', 'advanced']
    assert events[0]['chapter_id'] is None
    assert events[0]['chapter_title'] is None
    assert events[0]['note'] is None
    assert events[0]['created_at']


def test_foreshadow_event_created_on_transition(client):
    token = register(client)
    world_id = create_world(client, token)
    foreshadow = create_foreshadow(client, token, world_id)

    before = client.get(f"/foreshadows/{foreshadow['id']}/timeline", headers=auth(token))
    assert before.status_code == 200
    assert len(before.json()) == 1

    response = client.put(f"/foreshadows/{foreshadow['id']}", headers=auth(token), json={'status': 'advanced'})
    assert response.status_code == 200

    after = client.get(f"/foreshadows/{foreshadow['id']}/timeline", headers=auth(token))
    assert after.status_code == 200
    assert len(after.json()) == 2
    assert after.json()[-1]['event_type'] == 'advanced'


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
