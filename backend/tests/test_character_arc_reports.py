import pytest
from fastapi import HTTPException
from sqlalchemy import func, select

from app.event.models import EventLog
from app.llm.schemas import (
    BeatCard,
    ChapterGeneration,
    ChapterOutline,
    OpeningContract,
    OpeningEvidence,
    ProposedCharacterChange,
    ProposedForeshadowChange,
)
from app.narrative import service as narrative_service
from app.narrative.models import Chapter
from app.world.models import World


def opening_outline() -> ChapterOutline:
    return ChapterOutline(
        beats=[
            BeatCard(
                beat_id='opening-1',
                summary='林砚在雨巷追查湿信与玉佩线索。',
                pov_character='林砚',
                location='青岚城雨巷',
                emotional_arc='谨慎到决断',
                key_dialogue_hints=['湿信是谁留下的？'],
            )
        ],
        core_conflict='林砚必须在巡夜人抵达前确认湿信与玉佩的主人。',
        pov_suggestion='林砚',
        pacing='雨夜悬疑，逐段增加巡夜压力。',
        role_skill_targets=['保持线索压力'],
        opening_contract=OpeningContract(
            background='青岚城灵脉衰退，雨巷尽头的废井在雨夜发出异响。',
            protagonist_identity='林砚是为师门债务奔走的外门弟子。',
            motivation='他必须查清湿信和玉佩的来历，避免师妹被城主府带走。',
            personality_evidence_plan='让林砚先救下被雨水冲走的药箱，再带伤追查。',
            conflict_goal='在城主府巡夜人发现前确认湿信与玉佩的主人。',
            locked_pov='林砚限知第三人称。',
        ),
    )


def opening_body() -> str:
    return '\n\n'.join([
        '雨水压低了青岚城的屋檐，雨巷尽头的废井却在夜里吐出温热白雾。城里人人都说灵脉衰退只是旱灾，林砚知道那是谎话，因为掌心的玉佩正隔着湿布发烫。',
        '林砚是欠着师门药债的外门弟子，今夜原该回去照看师妹。可城主府的文书写明天亮前要带走她问话，他只能追查湿信与失踪师兄的名字，哪怕会把自己送进巡夜人的眼里。',
        '巷口的药箱被雨水冲翻，他先扑进泥水把药瓶一只只捡回，又把割裂的手藏进袖中。沈微霜问他为何不逃，林砚只说师妹还在等药，这不是能算清的账。',
        '废井底下传来铁链拖地声，玉佩映出师兄惯用的云纹。林砚没有告诉沈微霜自己看见了什么，只沿着井壁摸到一道新鲜的靴印，听见城主府巡夜人的铜铃越来越近。',
        '他必须在铜铃停在巷口前确认湿信与玉佩主人，否则师妹会被带走，师兄的失踪也会被埋进井里。林砚让沈微霜守住巷口，自己系紧绳索下井；他不确定她会不会出卖自己。',
        '林砚的靴底刚离开井沿，铜铃便在雨幕外停住。巡夜人喊出他的名字，他只能从井壁渗出的血色水痕判断，下面等着他的不是师兄，而是一场早已布好的局。',
    ])


def opening_evidence() -> list[OpeningEvidence]:
    return [
        OpeningEvidence(check='background', paragraph_index=0, quote='雨巷尽头的废井却在夜里吐出温热白雾'),
        OpeningEvidence(check='protagonist_identity', paragraph_index=1, quote='欠着师门药债的外门弟子'),
        OpeningEvidence(check='motivation', paragraph_index=1, quote='只能追查湿信与失踪师兄的名字'),
        OpeningEvidence(check='personality_evidence_plan', paragraph_index=2, quote='先扑进泥水把药瓶一只只捡回'),
        OpeningEvidence(check='conflict_goal', paragraph_index=4, quote='必须在铜铃停在巷口前确认湿信与玉佩主人'),
        OpeningEvidence(check='locked_pov', paragraph_index=3, quote='林砚没有告诉沈微霜自己看见了什么'),
    ]


class CharacterArcReportLLMClient:
    def __init__(self):
        self.character_arc_report_calls = 0

    def generate_outline(self, messages):
        return opening_outline()

    def generate_chapter(self, messages):
        return ChapterGeneration(
            title='第一章 雨巷密谈',
            draft_content=opening_body(),
            context_summary='林砚与沈微霜在雨巷交换线索。',
            review_hints=['确认第二段的信息揭示是否过快'],
            proposed_character_changes=[
                ProposedCharacterChange(character_id=1, status='开始调查密信', current_goals=['追查湿信来源'])
            ],
            proposed_foreshadow_changes=[
                ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='湿信推进玉佩线索')
            ],
            opening_evidence=opening_evidence(),
        )

    def generate_character_arc_report(self, messages):
        self.character_arc_report_calls += 1
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
    event_types = list(db_session.scalars(select(EventLog.event_type).where(EventLog.world_id == world_id).order_by(EventLog.id)))
    assert world.world_version == 1
    assert chapter.character_arc_report['draft_version'] == 1
    assert chapter.character_arc_report['character_arcs'][0]['character_id'] == 1
    assert event_types == ['WORLD_CREATED']


def test_character_arc_report_rejects_extra_body_fields_without_side_effects(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    llm_client = CharacterArcReportLLMClient()
    draft = create_reviewing_draft(client, token, world_id, monkeypatch, llm_client)
    assert llm_client.character_arc_report_calls == 0

    response = client.post(
        f"/chapters/{draft['chapter_id']}/character-arc-report",
        json={'raw_text': 'character arc report endpoint must not accept runtime source text'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 422
    assert any(error['type'] == 'extra_forbidden' and error['loc'] == ['body', 'raw_text'] for error in response.json()['detail'])
    assert llm_client.character_arc_report_calls == 0
    db_session.expire_all()
    world = db_session.get(World, world_id)
    chapter = db_session.get(Chapter, draft['chapter_id'])
    event_types = list(db_session.scalars(select(EventLog.event_type).where(EventLog.world_id == world_id).order_by(EventLog.id)))
    assert world.world_version == 1
    assert chapter.character_arc_report == {}
    assert event_types == ['WORLD_CREATED']


def test_archived_world_rejects_character_arc_report_generation(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)

    archive_response = client.patch(f'/worlds/{world_id}/status', headers={'Authorization': f'Bearer {token}'}, json={'status': 'archived'})
    assert archive_response.status_code == 200

    response = client.post(
        f"/chapters/{draft['chapter_id']}/character-arc-report",
        json={},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 409
    assert response.json()['detail'] == 'WORLD_ARCHIVED'

    db_session.expire_all()
    chapter = db_session.get(Chapter, draft['chapter_id'])
    assert chapter.character_arc_report == {}


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


def test_get_character_arc_report_still_allows_read_after_chapter_abandon(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)
    post_response = client.post(
        f"/chapters/{draft['chapter_id']}/character-arc-report",
        json={},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert post_response.status_code == 200
    created_report = post_response.json()

    abandon_response = client.post(
        f"/chapters/{draft['chapter_id']}/abandon",
        json={},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert abandon_response.status_code == 200
    assert abandon_response.json()['status'] == 'abandoned'

    get_response = client.get(
        f"/chapters/{draft['chapter_id']}/character-arc-report",
        headers={'Authorization': f'Bearer {token}'},
    )

    assert get_response.status_code == 200
    assert get_response.json() == created_report


def test_get_character_arc_report_returns_404_when_report_is_missing(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)

    response = client.get(
        f"/chapters/{draft['chapter_id']}/character-arc-report",
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 404
    assert response.json()['detail'] == 'NOT_FOUND'


def test_character_arc_report_rejects_unknown_character_ids(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch, InvalidCharacterArcReportLLMClient())

    response = client.post(
        f"/chapters/{draft['chapter_id']}/character-arc-report",
        json={},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 502
    assert response.json()['detail'] == 'MODEL_RESPONSE_INVALID'
    assert not db_session.in_transaction()
    db_session.expire_all()
    assert db_session.get(Chapter, draft['chapter_id']).character_arc_report == {}


def test_post_character_arc_report_rejects_abandoned_chapter_without_calling_llm(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    llm_client = CharacterArcReportLLMClient()
    draft = create_reviewing_draft(client, token, world_id, monkeypatch, llm_client)
    assert llm_client.character_arc_report_calls == 0

    abandon_response = client.post(
        f"/chapters/{draft['chapter_id']}/abandon",
        json={},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert abandon_response.status_code == 200
    assert abandon_response.json()['status'] == 'abandoned'

    response = client.post(
        f"/chapters/{draft['chapter_id']}/character-arc-report",
        json={},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 409
    assert response.json()['detail'] == 'CHAPTER_ABANDONED'
    assert llm_client.character_arc_report_calls == 0
    db_session.expire_all()
    assert db_session.get(Chapter, draft['chapter_id']).character_arc_report == {}


def test_late_character_arc_report_rejects_abandoned_chapter_without_overwriting_report(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)
    user = db_session.get(World, world_id).owner
    chapter = db_session.get(Chapter, draft['chapter_id'])
    chapter.character_arc_report = {'existing': 'keep'}
    db_session.commit()
    before_world_version = db_session.get(World, world_id).world_version
    before_draft_version = chapter.draft_version
    before_event_count = db_session.scalar(select(func.count()).select_from(EventLog))

    class AbandoningCharacterArcLLM(CharacterArcReportLLMClient):
        def generate_character_arc_report(self, messages):
            report = super().generate_character_arc_report(messages)
            abandoned = narrative_service.abandon_chapter(db_session, user, draft['chapter_id'])
            assert abandoned.status == 'abandoned'
            return report

    with pytest.raises(HTTPException) as exc_info:
        narrative_service.generate_character_arc_report(
            db_session,
            user,
            draft['chapter_id'],
            llm_client=AbandoningCharacterArcLLM(),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == 'CHAPTER_ABANDONED'
    db_session.expire_all()
    chapter = db_session.get(Chapter, draft['chapter_id'])
    assert chapter.status == 'abandoned'
    assert chapter.character_arc_report == {'existing': 'keep'}
    assert chapter.draft_version == before_draft_version
    assert db_session.get(World, world_id).world_version == before_world_version
    assert db_session.scalar(select(func.count()).select_from(EventLog)) == before_event_count


def test_late_character_arc_report_cannot_overwrite_stashed_draft_report(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)
    user = db_session.get(World, world_id).owner
    chapter = db_session.get(Chapter, draft['chapter_id'])
    chapter.character_arc_report = {'existing': 'keep'}
    db_session.commit()

    class StashingCharacterArcLLM(CharacterArcReportLLMClient):
        def generate_character_arc_report(self, messages):
            report = super().generate_character_arc_report(messages)
            stashed = narrative_service.stash_chapter_draft(db_session, user, draft['chapter_id'], '报告生成期间暂存')
            assert stashed['draft_version'] == 2
            return report

    with pytest.raises(HTTPException) as exc_info:
        narrative_service.generate_character_arc_report(
            db_session,
            user,
            draft['chapter_id'],
            llm_client=StashingCharacterArcLLM(),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == 'DRAFT_VERSION_MISMATCH'
    db_session.expire_all()
    chapter = db_session.get(Chapter, draft['chapter_id'])
    assert chapter.status == 'reviewing'
    assert chapter.draft_version == 2
    assert chapter.character_arc_report == {'existing': 'keep'}
    assert db_session.get(World, world_id).world_version == 1


def test_late_character_arc_report_cannot_overwrite_competing_report(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)
    user = db_session.get(World, world_id).owner
    competing_report = {'source': 'competing-request'}

    class CompetingCharacterArcLLM(CharacterArcReportLLMClient):
        def generate_character_arc_report(self, messages):
            report = super().generate_character_arc_report(messages)
            chapter = db_session.get(Chapter, draft['chapter_id'])
            chapter.character_arc_report = competing_report
            db_session.commit()
            return report

    with pytest.raises(HTTPException) as exc_info:
        narrative_service.generate_character_arc_report(
            db_session,
            user,
            draft['chapter_id'],
            llm_client=CompetingCharacterArcLLM(),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == 'REPORT_VERSION_MISMATCH'
    db_session.expire_all()
    assert db_session.get(Chapter, draft['chapter_id']).character_arc_report == competing_report
