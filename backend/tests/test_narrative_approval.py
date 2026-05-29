from app.llm.schemas import ChapterGeneration, ProposedCharacterChange, ProposedForeshadowChange
from app.narrative import service as narrative_service
from app.world.models import World


class FailingLLMClient:
    def generate_chapter(self, messages):
        raise RuntimeError('MODEL_REQUEST_FAILED')


class FakeLLMClient:
    def generate_chapter(self, messages):
        return ChapterGeneration(
            title='第一章 暗井回声',
            draft_content='林砚在灵井旁听见了第二个人的脚步声。',
            context_summary='林砚调查灵脉衰退，裂纹玉佩成为线索。',
            review_hints=['确认沈微霜动机是否一致'],
            proposed_character_changes=[ProposedCharacterChange(character_id=1, current_goals=['追查城主府叛乱'])],
            proposed_foreshadow_changes=[
                ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='玉佩线索被推进')
            ],
        )


def register_and_create_world(client):
    token = client.post('/auth/register', json={'email': 'writer@example.com', 'password': 'strongpass123'}).json()['access_token']
    world = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {token}'}).json()
    return token, world['id']


def test_generation_prompt_includes_expired_foreshadow_status(client, db_session):
    token, world_id = register_and_create_world(client)
    world = db_session.get(World, world_id)
    characters, foreshadows = narrative_service._load_world_context(db_session, world)

    messages = narrative_service.build_generation_messages(world, characters, foreshadows, '推进玉佩线索')

    assert 'advanced|resolved|expired' in messages[0]['content']



def test_create_draft_with_fake_llm(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())

    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    assert response.json()['title'] == '第一章 暗井回声'
    assert response.json()['source_world_version'] == 1
    assert response.json()['proposed_changes']['characters'][0]['current_goals'] == ['追查城主府叛乱']


def test_approve_chapter_updates_world_character_foreshadow_and_events(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    approve_response = client.post(f"/chapters/{draft['chapter_id']}/approve", headers={'Authorization': f'Bearer {token}'})
    overview_response = client.get(f'/worlds/{world_id}/overview', headers={'Authorization': f'Bearer {token}'})
    overview = overview_response.json()

    assert approve_response.status_code == 200
    assert overview['world_version'] == 2
    assert overview['characters'][0]['current_goals'] == ['追查城主府叛乱']
    assert overview['foreshadows'][0]['status'] == 'advanced'
    assert overview['recent_events'][0]['event_type'] == 'chapter_approved'
    assert overview['recent_events'][0]['world_version_before'] == 1
    assert overview['recent_events'][0]['world_version_after'] == 2


def test_approve_chapter_creates_foreshadow_lifecycle_event(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    response = client.post(f"/chapters/{draft['chapter_id']}/approve", headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200

    timeline = client.get('/foreshadows/1/timeline', headers={'Authorization': f'Bearer {token}'})
    assert timeline.status_code == 200
    event = timeline.json()[-1]
    assert event['event_type'] == 'advanced'
    assert event['chapter_id'] == draft['chapter_id']
    assert event['chapter_title'] == '第一章 暗井回声'
    assert event['note'] == '玉佩线索被推进'


def test_reject_chapter_does_not_approve_or_update_world(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    reject_response = client.post(f"/chapters/{draft['chapter_id']}/reject", headers={'Authorization': f'Bearer {token}'})
    overview_response = client.get(f'/worlds/{world_id}/overview', headers={'Authorization': f'Bearer {token}'})
    overview = overview_response.json()

    assert reject_response.status_code == 200
    assert reject_response.json()['status'] == 'rejected'
    assert reject_response.json()['approved_content'] is None
    assert overview['world_version'] == 1
    assert overview['recent_events'] == []


def test_create_draft_maps_model_request_failure(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FailingLLMClient())

    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 502
    assert response.json()['detail'] == 'MODEL_REQUEST_FAILED'


def test_approve_rejects_world_version_mismatch(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()
    world = db_session.get(World, world_id)
    world.world_version = 2
    db_session.commit()

    response = client.post(f"/chapters/{draft['chapter_id']}/approve", headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 409
    assert response.json()['detail'] == 'WORLD_VERSION_MISMATCH'
