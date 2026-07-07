from sqlalchemy import func, select

from app.event.models import EventLog
from app.llm.schemas import ChapterGeneration, WorldCreationDraftPayload
from app.narrative import service as narrative_service
from app.world import service as world_service
from app.world.models import World


class DraftWorldLLMClient:
    def generate_world_creation_draft(self, messages):
        return WorldCreationDraftPayload(
            draft=custom_world_payload(),
            first_chapter_goal='让许砚第一次听见跃迁灯塔低鸣。',
            generation_notes=['已根据一句话脑洞生成可编辑世界草稿。'],
            safety_notes=['确认前不会创建世界、写入正史或推进世界进度。'],
        )


class CustomWorldLLMClient:
    def generate_chapter(self, messages):
        return ChapterGeneration(
            title='第一章 灯塔低鸣',
            draft_content='许砚听见跃迁灯塔深处传来低鸣。',
            context_summary='许砚开始追查灯塔异常。',
            review_hints=['确认灯塔异常是否推进黑匣子脉冲伏笔。'],
            proposed_character_changes=[],
            proposed_foreshadow_changes=[],
        )


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
    assert [event['event_type'] for event in overview['recent_events']] == ['WORLD_CREATED']

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
    assert [event['event_type'] for event in overview['recent_events']] == ['WORLD_CREATED']

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


def test_create_custom_world_records_world_created_event_and_export_timeline(client):
    token = register(client, 'world-created@example.com')

    create_response = client.post('/worlds', headers=auth(token), json=custom_world_payload())

    assert create_response.status_code == 200
    world_id = create_response.json()['id']
    overview = client.get(f'/worlds/{world_id}/overview', headers=auth(token)).json()
    assert overview['recent_events'][0]['event_type'] == 'WORLD_CREATED'
    assert overview['recent_events'][0]['source_type'] == 'world_creation'
    assert overview['recent_events'][0]['world_version_before'] == 0
    assert overview['recent_events'][0]['world_version_after'] == 1
    assert overview['recent_events'][0]['payload']['starter_counts'] == {
        'characters': 2,
        'relations': 1,
        'foreshadows': 1,
    }

    events = client.get(f'/worlds/{world_id}/events', headers=auth(token)).json()
    assert events['total'] == 1
    assert events['items'][0]['event_type'] == 'WORLD_CREATED'

    export = client.post(f'/worlds/{world_id}/export/markdown', headers=auth(token)).json()
    timeline = next(file for file in export['files'] if file['path'] == 'Timeline.md')['content']
    assert 'WORLD_CREATED' in timeline
    assert '0 → 1' in timeline


def test_world_events_include_summary_counts_and_latest_world_version(client):
    token = register(client, 'timeline-summary@example.com')
    create_response = client.post('/worlds', headers=auth(token), json=custom_world_payload())
    world_id = create_response.json()['id']

    events = client.get(f'/worlds/{world_id}/events', headers=auth(token)).json()

    assert events['total'] == 1
    assert events['summary']['total'] == 1
    assert events['summary']['event_type_counts'] == {'WORLD_CREATED': 1}
    assert events['summary']['latest_world_version'] == 1


def test_world_events_filter_items_but_keep_all_world_summary(client):
    token = register(client, 'timeline-filter@example.com')
    create_response = client.post('/worlds', headers=auth(token), json=custom_world_payload())
    world_id = create_response.json()['id']
    character_id = client.get(f'/worlds/{world_id}/overview', headers=auth(token)).json()['characters'][0]['id']
    update_response = client.put(
        f'/characters/{character_id}',
        headers=auth(token),
        json={'status': '追查灯塔异常', 'edit_reason': '推进角色线索'},
    )
    assert update_response.status_code == 200

    events = client.get(f'/worlds/{world_id}/events?event_type=character_change', headers=auth(token)).json()

    assert events['total'] == 1
    assert [event['event_type'] for event in events['items']] == ['character_change']
    assert events['summary']['total'] == 3
    assert events['summary']['event_type_counts'] == {
        'WORLD_CREATED': 1,
        'character_change': 1,
        'world_version_increment': 1,
    }
    assert events['summary']['latest_world_version'] == 2


def test_world_events_summary_is_limited_to_owner(client):
    owner_token = register(client, 'timeline-owner@example.com')
    other_token = register(client, 'timeline-other@example.com')
    world_id = client.post('/worlds/from-template', headers=auth(owner_token)).json()['id']

    response = client.get(f'/worlds/{world_id}/events', headers=auth(other_token))

    assert response.status_code == 403
    assert response.json()['detail'] == 'FORBIDDEN'


def test_create_custom_world_rejects_relation_self_reference(client):
    token = register(client, 'world-self-relation@example.com')
    payload = custom_world_payload()
    payload['starter_assets']['relations'][0]['target_index'] = 0

    response = client.post('/worlds', headers=auth(token), json=payload)

    assert response.status_code == 422
    assert response.json()['detail'] == 'INVALID_RELATION_SELF_REFERENCE'
    assert client.get('/worlds', headers=auth(token)).json() == []


def test_create_custom_world_rejects_invalid_relation_intensity(client):
    token = register(client, 'world-relation-intensity@example.com')
    payload = custom_world_payload()
    payload['starter_assets']['relations'][0]['intensity'] = 9

    response = client.post('/worlds', headers=auth(token), json=payload)

    assert response.status_code == 422
    assert client.get('/worlds', headers=auth(token)).json() == []


def test_create_custom_world_rejects_invalid_foreshadow_status(client):
    token = register(client, 'world-foreshadow-status@example.com')
    payload = custom_world_payload()
    payload['starter_assets']['foreshadows'][0]['status'] = 'partially_resolved'

    response = client.post('/worlds', headers=auth(token), json=payload)

    assert response.status_code == 400
    assert response.json()['detail'] == 'INVALID_STATUS'
    assert client.get('/worlds', headers=auth(token)).json() == []


def test_create_custom_world_rejects_invalid_foreshadow_urgency(client):
    token = register(client, 'world-foreshadow-urgency@example.com')
    payload = custom_world_payload()
    payload['starter_assets']['foreshadows'][0]['urgency_level'] = 9

    response = client.post('/worlds', headers=auth(token), json=payload)

    assert response.status_code == 422
    assert client.get('/worlds', headers=auth(token)).json() == []


def test_custom_world_can_create_reviewing_draft(client, monkeypatch):
    token = register(client, 'world-draft@example.com')
    world = client.post('/worlds', headers=auth(token), json=custom_world_payload()).json()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: CustomWorldLLMClient())

    response = client.post(
        f"/worlds/{world['id']}/chapters/draft",
        headers=auth(token),
        json={'chapter_goal': '让许砚第一次听见灯塔低鸣'},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'reviewing'
    assert payload['title'] == '第一章 灯塔低鸣'
    assert payload['source_world_version'] == 1


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


def test_draft_world_from_brief_returns_editable_payload_without_creating_world(client, db_session, monkeypatch):
    token = register(client, 'brief-draft@example.com')
    monkeypatch.setattr(world_service, 'LLMClient', lambda: DraftWorldLLMClient())

    response = client.post(
        '/worlds/draft-from-brief',
        headers=auth(token),
        json={'brief': '一个边境殖民地依赖濒临失控的跃迁灯塔'},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['source_brief'] == '一个边境殖民地依赖濒临失控的跃迁灯塔'
    assert payload['draft']['title'] == '群星边境'
    assert payload['first_chapter_goal'] == '让许砚第一次听见跃迁灯塔低鸣。'
    assert payload['safety_notes'] == ['确认前不会创建世界、写入正史或推进世界进度。']
    assert db_session.scalar(select(func.count()).select_from(World)) == 0
    assert db_session.scalar(select(func.count()).select_from(EventLog)) == 0


def test_draft_world_from_brief_requires_login(client):
    response = client.post('/worlds/draft-from-brief', json={'brief': '一个所有人出生时都会被分配死因的王国'})

    assert response.status_code == 401
    assert response.json()['detail'] == 'UNAUTHORIZED'


def test_world_endpoints_require_login(client):
    response = client.post('/worlds/from-template')

    assert response.status_code == 401
    assert response.json()['detail'] == 'UNAUTHORIZED'
