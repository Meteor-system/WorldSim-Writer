from sqlalchemy import func, select

from app.event.models import EventLog
from app.llm.schemas import ChapterGeneration, ProposedCharacterChange, ProposedForeshadowChange
from app.narrative import service as narrative_service
from app.narrative.models import Chapter
from app.world.models import World


class CharacterArcReportLLMClient:
    def generate_chapter(self, messages):
        return ChapterGeneration(
            title='第一章 雨巷密谈',
            draft_content='第一段：林砚停在雨巷口。\n\n第二段：沈微霜递来一封湿透的信。',
            context_summary='林砚与沈微霜在雨巷交换线索。',
            review_hints=['确认第二段的信息揭示是否过快'],
            proposed_character_changes=[
                ProposedCharacterChange(character_id=1, status='开始调查密信', current_goals=['追查湿信来源'])
            ],
            proposed_foreshadow_changes=[
                ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='湿信推进玉佩线索')
            ],
        )

    def generate_character_arc_report(self, messages):
        return {
            'summary': '本章推动林砚从被动等待转向主动追查湿信来源。',
            'character_arcs': [
                {
                    'character_id': 1,
                    'name': '林砚',
                    'role_type': 'protagonist',
                    'current_status': 'active',
                    'current_goals': [],
                    'presence_level': 'major',
                    'arc_stage': 'choice',
                    'chapter_function': '在雨巷会面中承担调查者与选择者功能。',
                    'observed_shift': '从谨慎观察转向主动追问湿信来源。',
                    'proposed_state_change': {'status': '开始调查密信', 'current_goals': ['追查湿信来源']},
                    'continuity_risk': 'medium',
                    'risk_reason': '如果立刻信任沈微霜，需要补足信任建立过程。',
                    'suggested_revision': '增加林砚犹疑和试探沈微霜的动作。',
                    'next_chapter_setup': '让林砚以湿信为线索试探城主府密道。',
                }
            ],
            'relationship_notes': [],
            'progression_hints': [
                {
                    'hint_type': 'character',
                    'priority': 'high',
                    'title': '让林砚做出是否相信沈微霜的选择',
                    'rationale': '本章已经建立湿信线索，下一章需要把怀疑转化为行动。',
                    'suggested_next_beat': '林砚带着湿信赴城主府外墙，并设置一次试探。',
                    'related_character_ids': [1],
                    'related_foreshadow_ids': [1],
                    'can_seed_next_chapter_goal': True,
                }
            ],
        }


class InvalidCharacterArcReportLLMClient(CharacterArcReportLLMClient):
    def generate_character_arc_report(self, messages):
        report = super().generate_character_arc_report(messages)
        report['character_arcs'][0]['character_id'] = 9999
        report['progression_hints'][0]['related_character_ids'] = [9999]
        return report


def register_and_create_world(client, email='character-arc@example.com'):
    token = client.post('/auth/register', json={'email': email, 'password': 'strongpass123'}).json()['access_token']
    world = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {token}'}).json()
    return token, world['id']


def create_reviewing_draft(client, token, world_id, monkeypatch, llm_client=None):
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm_client or CharacterArcReportLLMClient())
    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进雨巷密谈'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == 200
    return response.json()


def test_post_character_arc_report_generates_structured_report_without_mutating_world(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)

    response = client.post(
        f"/chapters/{draft['chapter_id']}/character-arc-report",
        json={},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['chapter_id'] == draft['chapter_id']
    assert payload['draft_version'] == 1
    assert payload['current_draft_version'] == 1
    assert payload['is_stale'] is False
    assert payload['summary'] == '本章推动林砚从被动等待转向主动追查湿信来源。'
    assert payload['character_arcs'][0]['character_id'] == 1
    assert payload['character_arcs'][0]['presence_level'] == 'major'
    assert payload['character_arcs'][0]['arc_stage'] == 'choice'
    assert payload['character_arcs'][0]['continuity_risk'] == 'medium'
    assert payload['progression_hints'][0]['priority'] == 'high'
    assert payload['progression_hints'][0]['can_seed_next_chapter_goal'] is True
    assert isinstance(payload['created_at'], str)

    db_session.expire_all()
    world = db_session.get(World, world_id)
    chapter = db_session.get(Chapter, draft['chapter_id'])
    event_count = db_session.scalar(select(func.count()).select_from(EventLog))
    assert world.world_version == 1
    assert chapter.character_arc_report['draft_version'] == 1
    assert chapter.character_arc_report['character_arcs'][0]['character_id'] == 1
    assert event_count == 0


def test_get_character_arc_report_marks_stale_after_draft_version_changes(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)
    post_response = client.post(
        f"/chapters/{draft['chapter_id']}/character-arc-report",
        json={},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert post_response.status_code == 200

    get_response = client.get(
        f"/chapters/{draft['chapter_id']}/character-arc-report",
        headers={'Authorization': f'Bearer {token}'},
    )
    assert get_response.status_code == 200
    assert get_response.json()['is_stale'] is False

    edit_response = client.put(
        f"/chapters/{draft['chapter_id']}/draft",
        json={'content': '第一段：林砚停在雨巷口，玉佩微微发烫。\n\n第二段：沈微霜递来一封湿透的信。'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert edit_response.status_code == 200

    stale_response = client.get(
        f"/chapters/{draft['chapter_id']}/character-arc-report",
        headers={'Authorization': f'Bearer {token}'},
    )
    assert stale_response.status_code == 200
    stale_payload = stale_response.json()
    assert stale_payload['draft_version'] == 1
    assert stale_payload['current_draft_version'] == 2
    assert stale_payload['is_stale'] is True


def test_get_character_arc_report_returns_404_when_report_is_missing(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)

    response = client.get(
        f"/chapters/{draft['chapter_id']}/character-arc-report",
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 404
    assert response.json()['detail'] == 'NOT_FOUND'


def test_character_arc_report_rejects_unknown_character_ids(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch, InvalidCharacterArcReportLLMClient())

    response = client.post(
        f"/chapters/{draft['chapter_id']}/character-arc-report",
        json={},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 502
    assert response.json()['detail'] == 'MODEL_RESPONSE_INVALID'
