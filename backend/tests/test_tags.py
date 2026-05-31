from app.narrative.models import Chapter, ChapterDraft


def register(client, email='tags@example.com'):
    response = client.post('/auth/register', json={'email': email, 'password': 'strongpass123'})
    return response.json()['access_token']


def auth(token):
    return {'Authorization': f'Bearer {token}'}


def tag_world_payload():
    return {
        'title': '群星边境',
        'genre_template': 'sci_fi',
        'truth_canon': '边境殖民地依赖一座濒临失控的跃迁灯塔。',
        'tone_profile': {'style': '冷峻太空歌剧'},
        'starter_assets': {
            'characters': [
                {'name': '许砚', 'role_type': 'protagonist', 'current_goals': ['查明灯塔异常']},
            ],
            'relations': [],
            'foreshadows': [
                {
                    'title': '黑匣子脉冲',
                    'description': '废弃黑匣子收到来自未来的求救信号。',
                    'foreshadow_type': 'signal_clue',
                    'status': 'planted',
                    'urgency_level': 4,
                    'related_character_indexes': [0],
                }
            ],
        },
    }


def create_world(client, token):
    return client.post('/worlds', headers=auth(token), json=tag_world_payload()).json()


def create_approved_chapter(db_session, world_id):
    chapter = Chapter(
        world_id=world_id,
        title='第一章 灯塔低鸣',
        status='approved',
        draft_version=1,
        approved_version=1,
        base_world_version=1,
        approved_content='许砚听见跃迁灯塔深处传来低鸣。',
        chapter_goal='让许砚调查灯塔异常。',
    )
    db_session.add(chapter)
    db_session.flush()
    db_session.add(
        ChapterDraft(
            chapter_id=chapter.id,
            draft_version=1,
            content=chapter.approved_content,
            context_summary='灯塔异常推进。',
            review_hints=[],
            proposed_changes={},
            source_world_version=1,
        )
    )
    db_session.commit()
    return chapter


def test_create_and_list_world_tags(client):
    token = register(client)
    world = create_world(client, token)

    response = client.post(
        f"/worlds/{world['id']}/tags",
        headers=auth(token),
        json={'name': ' 主线 压力 ', 'color': ' amber '},
    )

    assert response.status_code == 200
    created = response.json()
    assert created['name'] == '主线 压力'
    assert created['slug'] == '主线-压力'
    assert created['color'] == 'amber'

    tags = client.get(f"/worlds/{world['id']}/tags", headers=auth(token)).json()
    assert tags['world_id'] == world['id']
    assert tags['tags'][0]['name'] == '主线 压力'
    assert tags['tags'][0]['assignment_count'] == 0
    assert tags['tags'][0]['object_type_counts'] == {}


def test_duplicate_tag_names_are_rejected_per_world(client):
    token = register(client, 'tags-duplicate@example.com')
    world = create_world(client, token)

    first = client.post(f"/worlds/{world['id']}/tags", headers=auth(token), json={'name': '主线压力'})
    duplicate = client.post(f"/worlds/{world['id']}/tags", headers=auth(token), json={'name': ' 主线压力 '})

    assert first.status_code == 200
    assert duplicate.status_code == 409
    assert duplicate.json()['detail'] == 'TAG_ALREADY_EXISTS'


def test_assign_tag_to_supported_objects_and_get_detail(client, db_session):
    token = register(client, 'tags-detail@example.com')
    world = create_world(client, token)
    overview = client.get(f"/worlds/{world['id']}/overview", headers=auth(token)).json()
    chapter = create_approved_chapter(db_session, world['id'])
    event_id = overview['recent_events'][0]['id']
    tag = client.post(f"/worlds/{world['id']}/tags", headers=auth(token), json={'name': '灯塔线'}).json()

    character_id = overview['characters'][0]['id']
    foreshadow_id = overview['foreshadows'][0]['id']
    assignments = [
        {'object_type': 'character', 'object_id': character_id},
        {'object_type': 'foreshadow', 'object_id': foreshadow_id},
        {'object_type': 'chapter', 'object_id': chapter.id},
        {'object_type': 'event', 'object_id': event_id},
    ]
    for assignment in assignments:
        response = client.post(f"/worlds/{world['id']}/tags/{tag['id']}/objects", headers=auth(token), json=assignment)
        assert response.status_code == 200
        assert response.json()['object_type'] == assignment['object_type']

    detail = client.get(f"/worlds/{world['id']}/tags/{tag['id']}", headers=auth(token)).json()

    assert detail['tag']['assignment_count'] == 4
    assert detail['tag']['object_type_counts'] == {'chapter': 1, 'character': 1, 'event': 1, 'foreshadow': 1}
    titles = {item['title'] for item in detail['objects']}
    assert {'许砚', '黑匣子脉冲', '第一章 灯塔低鸣', 'WORLD_CREATED'}.issubset(titles)
    assert any(item['object_type'] == 'character' and '查明灯塔异常' in item['snippet'] for item in detail['objects'])


def test_assigning_same_object_is_idempotent(client):
    token = register(client, 'tags-idempotent@example.com')
    world = create_world(client, token)
    overview = client.get(f"/worlds/{world['id']}/overview", headers=auth(token)).json()
    tag = client.post(f"/worlds/{world['id']}/tags", headers=auth(token), json={'name': '重点角色'}).json()
    data = {'object_type': 'character', 'object_id': overview['characters'][0]['id']}

    first = client.post(f"/worlds/{world['id']}/tags/{tag['id']}/objects", headers=auth(token), json=data)
    second = client.post(f"/worlds/{world['id']}/tags/{tag['id']}/objects", headers=auth(token), json=data)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()['id'] == first.json()['id']
    detail = client.get(f"/worlds/{world['id']}/tags/{tag['id']}", headers=auth(token)).json()
    assert detail['tag']['assignment_count'] == 1


def test_tag_assignment_validates_type_and_world_ownership(client):
    owner_token = register(client, 'tags-owner@example.com')
    other_token = register(client, 'tags-other@example.com')
    owner_world = create_world(client, owner_token)
    other_world = create_world(client, other_token)
    other_character = client.get(f"/worlds/{other_world['id']}/overview", headers=auth(other_token)).json()['characters'][0]
    tag = client.post(f"/worlds/{owner_world['id']}/tags", headers=auth(owner_token), json={'name': '边界检查'}).json()

    unsupported = client.post(
        f"/worlds/{owner_world['id']}/tags/{tag['id']}/objects",
        headers=auth(owner_token),
        json={'object_type': 'world', 'object_id': owner_world['id']},
    )
    wrong_world = client.post(
        f"/worlds/{owner_world['id']}/tags/{tag['id']}/objects",
        headers=auth(owner_token),
        json={'object_type': 'character', 'object_id': other_character['id']},
    )
    forbidden = client.get(f"/worlds/{owner_world['id']}/tags", headers=auth(other_token))

    assert unsupported.status_code == 422
    assert unsupported.json()['detail'] == 'UNSUPPORTED_TAG_OBJECT_TYPE'
    assert wrong_world.status_code == 404
    assert wrong_world.json()['detail'] == 'TAG_OBJECT_NOT_FOUND'
    assert forbidden.status_code == 403


def test_unassign_and_delete_tag_do_not_increment_world_version(client):
    token = register(client, 'tags-delete@example.com')
    world = create_world(client, token)
    overview = client.get(f"/worlds/{world['id']}/overview", headers=auth(token)).json()
    tag = client.post(f"/worlds/{world['id']}/tags", headers=auth(token), json={'name': '临时归档'}).json()
    data = {'object_type': 'character', 'object_id': overview['characters'][0]['id']}
    client.post(f"/worlds/{world['id']}/tags/{tag['id']}/objects", headers=auth(token), json=data)

    unassign = client.delete(
        f"/worlds/{world['id']}/tags/{tag['id']}/objects/character/{overview['characters'][0]['id']}",
        headers=auth(token),
    )
    delete = client.delete(f"/worlds/{world['id']}/tags/{tag['id']}", headers=auth(token))
    after = client.get(f"/worlds/{world['id']}/overview", headers=auth(token)).json()
    events = client.get(f"/worlds/{world['id']}/events", headers=auth(token)).json()

    assert unassign.status_code == 204
    assert delete.status_code == 204
    assert client.get(f"/worlds/{world['id']}/tags", headers=auth(token)).json()['tags'] == []
    assert after['world_version'] == overview['world_version']
    assert events['summary']['event_type_counts'] == {'WORLD_CREATED': 1}


def test_tag_endpoints_require_login(client):
    list_response = client.get('/worlds/1/tags')
    create_response = client.post('/worlds/1/tags', json={'name': '主线'})
    detail_response = client.get('/worlds/1/tags/1')
    assign_response = client.post('/worlds/1/tags/1/objects', json={'object_type': 'character', 'object_id': 1})
    unassign_response = client.delete('/worlds/1/tags/1/objects/character/1')
    delete_response = client.delete('/worlds/1/tags/1')

    assert list_response.status_code == 401
    assert create_response.status_code == 401
    assert detail_response.status_code == 401
    assert assign_response.status_code == 401
    assert unassign_response.status_code == 401
    assert delete_response.status_code == 401
