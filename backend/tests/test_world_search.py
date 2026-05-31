from app.llm.schemas import ChapterGeneration
from app.narrative import service as narrative_service


class SearchLLMClient:
    def generate_chapter(self, messages):
        return ChapterGeneration(
            title='第一章 灯塔密令',
            draft_content='许砚在灯塔核心发现黑匣子脉冲，莱娜·周封锁了维修甲板。',
            context_summary='灯塔异常第一次影响殖民地航道。',
            review_hints=['确认黑匣子脉冲伏笔推进。'],
            proposed_character_changes=[],
            proposed_foreshadow_changes=[],
        )


def register(client, email='search@example.com'):
    response = client.post('/auth/register', json={'email': email, 'password': 'strongpass123'})
    return response.json()['access_token']


def auth(token):
    return {'Authorization': f'Bearer {token}'}


def custom_world_payload():
    return {
        'title': '群星边境',
        'genre_template': 'sci_fi',
        'truth_canon': '边境殖民地依赖一座濒临失控的跃迁灯塔。',
        'tone_profile': {'style': '冷峻太空歌剧'},
        'starter_assets': {
            'characters': [
                {
                    'name': '许砚',
                    'role_type': 'protagonist',
                    'status': '灯塔维修工程师',
                    'public_profile': {'identity': '灯塔维修工程师'},
                    'hidden_traits': {'secret': '篡改过灯塔事故日志'},
                    'destiny_flag': '灯塔核心密钥持有者',
                    'current_goals': ['查明黑匣子脉冲来源'],
                },
                {
                    'name': '莱娜·周',
                    'role_type': 'rival',
                    'status': '企业安保监察官',
                    'public_profile': {'identity': '企业安保监察官'},
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
                    'description': '废弃黑匣子收到来自未来的求救信号。',
                    'foreshadow_type': 'signal_clue',
                    'status': 'planted',
                    'urgency_level': 4,
                    'related_character_indexes': [0, 1],
                    'expected_resolution_window': '第3-5章',
                }
            ],
        },
    }


def create_searchable_world(client, token, monkeypatch):
    world = client.post('/worlds', headers=auth(token), json=custom_world_payload()).json()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: SearchLLMClient())
    draft = client.post(
        f"/worlds/{world['id']}/chapters/draft",
        headers=auth(token),
        json={'chapter_goal': '让许砚第一次追查黑匣子脉冲'},
    ).json()
    return world, draft


def test_world_search_finds_characters_foreshadows_chapters_and_events(client, monkeypatch):
    token = register(client)
    world, draft = create_searchable_world(client, token, monkeypatch)

    response = client.get(f"/worlds/{world['id']}/search?q=黑匣子", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['world_id'] == world['id']
    assert payload['query'] == '黑匣子'
    result_types = {result['object_type'] for result in payload['results']}
    assert {'character', 'foreshadow', 'chapter', 'event'}.issubset(result_types)
    assert payload['object_type_counts']['character'] == 1
    assert payload['object_type_counts']['foreshadow'] == 1
    assert payload['object_type_counts']['chapter'] == 1
    assert payload['object_type_counts']['event'] >= 1
    assert any(result['title'] == '黑匣子脉冲' and '废弃黑匣子' in result['snippet'] for result in payload['results'])
    assert any(result['object_type'] == 'chapter' and result['object_id'] == draft['chapter_id'] for result in payload['results'])


def test_world_search_filters_object_types(client, monkeypatch):
    token = register(client, 'search-filter@example.com')
    world, _ = create_searchable_world(client, token, monkeypatch)

    response = client.get(f"/worlds/{world['id']}/search?q=篡改&object_types=character", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert {result['object_type'] for result in payload['results']} == {'character'}
    assert payload['object_type_counts'] == {'character': 1}


def create_tag(client, token, world_id, name='灯塔线'):
    response = client.post(f'/worlds/{world_id}/tags', headers=auth(token), json={'name': name, 'color': 'amber'})
    assert response.status_code == 200
    return response.json()


def assign_tag(client, token, world_id, tag_id, object_type, object_id):
    response = client.post(
        f'/worlds/{world_id}/tags/{tag_id}/objects',
        headers=auth(token),
        json={'object_type': object_type, 'object_id': object_id},
    )
    assert response.status_code == 200
    return response.json()


def test_world_search_filters_by_tag_name_and_adds_tag_metadata(client, monkeypatch):
    token = register(client, 'search-tag-name@example.com')
    world, _ = create_searchable_world(client, token, monkeypatch)
    overview = client.get(f"/worlds/{world['id']}/overview", headers=auth(token)).json()
    tag = create_tag(client, token, world['id'], '灯塔线')
    assign_tag(client, token, world['id'], tag['id'], 'foreshadow', overview['foreshadows'][0]['id'])

    response = client.get(f"/worlds/{world['id']}/search?q=黑匣子&tags=灯塔线", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['object_type_counts'] == {'foreshadow': 1}
    assert [(result['object_type'], result['object_id']) for result in payload['results']] == [
        ('foreshadow', overview['foreshadows'][0]['id'])
    ]
    assert payload['results'][0]['metadata']['tags'] == [
        {'id': tag['id'], 'name': '灯塔线', 'slug': '灯塔线', 'color': 'amber'}
    ]


def test_world_search_filters_by_tag_id(client, monkeypatch):
    token = register(client, 'search-tag-id@example.com')
    world, _ = create_searchable_world(client, token, monkeypatch)
    overview = client.get(f"/worlds/{world['id']}/overview", headers=auth(token)).json()
    tag = create_tag(client, token, world['id'], '角色线')
    assign_tag(client, token, world['id'], tag['id'], 'character', overview['characters'][0]['id'])

    response = client.get(f"/worlds/{world['id']}/search?q=许砚&tags={tag['id']}", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['object_type_counts'] == {'character': 1}
    assert payload['results'][0]['object_type'] == 'character'
    assert payload['results'][0]['metadata']['tags'][0]['name'] == '角色线'


def test_world_search_unknown_tag_filter_returns_no_results(client, monkeypatch):
    token = register(client, 'search-tag-missing@example.com')
    world, _ = create_searchable_world(client, token, monkeypatch)

    response = client.get(f"/worlds/{world['id']}/search?q=黑匣子&tags=missing-tag", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['object_type_counts'] == {}
    assert payload['results'] == []


def test_world_search_tag_filter_is_limited_to_current_world(client, monkeypatch):
    owner_token = register(client, 'search-tag-owner@example.com')
    other_token = register(client, 'search-tag-other@example.com')
    owner_world, _ = create_searchable_world(client, owner_token, monkeypatch)
    other_world, _ = create_searchable_world(client, other_token, monkeypatch)
    other_overview = client.get(f"/worlds/{other_world['id']}/overview", headers=auth(other_token)).json()
    other_tag = create_tag(client, other_token, other_world['id'], '跨界标签')
    assign_tag(client, other_token, other_world['id'], other_tag['id'], 'foreshadow', other_overview['foreshadows'][0]['id'])

    response = client.get(f"/worlds/{owner_world['id']}/search?q=黑匣子&tags={other_tag['id']}", headers=auth(owner_token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['object_type_counts'] == {}
    assert payload['results'] == []


def test_world_search_is_limited_to_owner(client):
    owner_token = register(client, 'search-owner@example.com')
    other_token = register(client, 'search-other@example.com')
    world = client.post('/worlds', headers=auth(owner_token), json=custom_world_payload()).json()

    response = client.get(f"/worlds/{world['id']}/search?q=灯塔", headers=auth(other_token))

    assert response.status_code == 403
    assert response.json()['detail'] == 'FORBIDDEN'


def test_world_search_rejects_blank_query(client):
    token = register(client, 'search-blank@example.com')
    world = client.post('/worlds', headers=auth(token), json=custom_world_payload()).json()

    response = client.get(f"/worlds/{world['id']}/search?q=   ", headers=auth(token))

    assert response.status_code == 422
    assert response.json()['detail'] == 'SEARCH_QUERY_REQUIRED'
