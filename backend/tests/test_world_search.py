from app.llm.schemas import BeatCard, ChapterGeneration, ChapterOutline, OpeningContract, OpeningEvidence
from app.narrative import service as narrative_service


class SearchLLMClient:
    def generate_outline(self, messages):
        return ChapterOutline(
            beats=[
                BeatCard(
                    beat_id='opening-1',
                    summary='许砚在灯塔核心发现黑匣子脉冲。',
                    pov_character='许砚',
                    location='跃迁灯塔核心',
                    emotional_arc='专注 -> 不安',
                    key_dialogue_hints=['黑匣子不该在这个时段发讯。'],
                )
            ],
            core_conflict='许砚必须在莱娜·周封锁甲板前追查黑匣子脉冲。',
            pov_suggestion='许砚',
            pacing='灯塔故障与安保封锁交替加压。',
            role_skill_targets=['许砚', '莱娜·周'],
            opening_contract=OpeningContract(
                background='边境殖民地依赖一座濒临失控的跃迁灯塔。',
                protagonist_identity='许砚是灯塔维修工程师。',
                motivation='他要查明黑匣子脉冲，避免殖民地航道断绝。',
                personality_evidence_plan='让许砚先抢救故障舱的供氧，再隐瞒自己篡改过日志。',
                conflict_goal='在莱娜·周封锁维修甲板前取得黑匣子记录。',
                locked_pov='许砚限知第三人称。',
            ),
        )

    def generate_chapter(self, messages):
        content = '\n\n'.join([
            '跃迁灯塔在殖民地上空发出低沉震颤，核心舱的蓝光照着许砚脚边的积水。黑匣子脉冲穿过警报声，像有人从未来敲响舱壁。',
            '许砚是灯塔维修工程师，知道一次断航就会让边境殖民地失去补给。他必须查明黑匣子脉冲来源，不能让航道在企业报告里被轻描淡写地抹去。',
            '供氧阀被震松后，许砚先跪在检修槽边锁死泄漏，又把自己篡改过事故日志的终端记录藏进工具包，才接入黑匣子。',
            '屏幕跳出一段陌生坐标，许砚没有告诉莱娜·周那串数字像旧事故编号；他只看见维修甲板的门禁正被她远程封锁。',
            '他必须在莱娜·周封锁维修甲板前取得黑匣子记录，否则脉冲会被企业收走，殖民地航道也可能在下一次跃迁中失控。',
            '隔离门落下时，许砚只能从黑匣子反射的裂光判断，信号另一端或许不是求救船，而是尚未发生的灯塔坠毁。',
        ])
        return ChapterGeneration(
            title='第一章 灯塔密令',
            draft_content=content,
            context_summary='灯塔异常第一次影响殖民地航道。',
            review_hints=['确认黑匣子脉冲伏笔推进。'],
            proposed_character_changes=[],
            proposed_foreshadow_changes=[],
            opening_evidence=[
                OpeningEvidence(check='background', paragraph_index=0, quote='跃迁灯塔在殖民地上空发出低沉震颤'),
                OpeningEvidence(check='protagonist_identity', paragraph_index=1, quote='许砚是灯塔维修工程师'),
                OpeningEvidence(check='motivation', paragraph_index=1, quote='必须查明黑匣子脉冲来源'),
                OpeningEvidence(check='personality_evidence_plan', paragraph_index=2, quote='先跪在检修槽边锁死泄漏'),
                OpeningEvidence(check='conflict_goal', paragraph_index=4, quote='必须在莱娜·周封锁维修甲板前取得黑匣子记录'),
                OpeningEvidence(check='locked_pov', paragraph_index=5, quote='许砚只能从黑匣子反射的裂光判断'),
            ],
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


def test_world_search_adds_tag_metadata_without_tag_filter(client, monkeypatch):
    token = register(client, 'search-tag-metadata@example.com')
    world, _ = create_searchable_world(client, token, monkeypatch)
    overview = client.get(f"/worlds/{world['id']}/overview", headers=auth(token)).json()
    tag = create_tag(client, token, world['id'], '灯塔线')
    assign_tag(client, token, world['id'], tag['id'], 'foreshadow', overview['foreshadows'][0]['id'])

    response = client.get(f"/worlds/{world['id']}/search?q=黑匣子", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    foreshadow_result = next(result for result in payload['results'] if result['object_type'] == 'foreshadow')
    assert foreshadow_result['metadata']['tags'] == [
        {'id': tag['id'], 'name': '灯塔线', 'slug': '灯塔线', 'color': 'amber'}
    ]


def test_world_search_tag_metadata_is_limited_to_current_world(client, monkeypatch):
    owner_token = register(client, 'search-tag-metadata-owner@example.com')
    other_token = register(client, 'search-tag-metadata-other@example.com')
    owner_world, _ = create_searchable_world(client, owner_token, monkeypatch)
    other_world, _ = create_searchable_world(client, other_token, monkeypatch)
    other_overview = client.get(f"/worlds/{other_world['id']}/overview", headers=auth(other_token)).json()
    other_tag = create_tag(client, other_token, other_world['id'], '跨界标签')
    assign_tag(client, other_token, other_world['id'], other_tag['id'], 'foreshadow', other_overview['foreshadows'][0]['id'])

    response = client.get(f"/worlds/{owner_world['id']}/search?q=黑匣子", headers=auth(owner_token))

    assert response.status_code == 200
    payload = response.json()
    foreshadow_result = next(result for result in payload['results'] if result['object_type'] == 'foreshadow')
    assert 'tags' not in foreshadow_result['metadata']


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
