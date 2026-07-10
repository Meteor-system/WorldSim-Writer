from sqlalchemy import func, select

from app.character.models import Character
from app.event.models import EventLog
from app.foreshadow.models import Foreshadow, ForeshadowEvent
from app.llm.schemas import BeatCard, ChapterGeneration, ChapterOutline, ProposedCharacterChange, ProposedForeshadowChange
from app.narrative import service as narrative_service
from app.narrative.models import Chapter, ChapterDraft
from app.world.models import World


class FailingLLMClient:
    def generate_chapter(self, messages):
        raise RuntimeError('MODEL_REQUEST_FAILED')


class AuthFailingLLMClient:
    def generate_chapter(self, messages):
        raise RuntimeError('MODEL_AUTH_FAILED')


class UnknownFailingLLMClient:
    def generate_chapter(self, messages):
        raise RuntimeError('provider secret text')


class FakeLLMClient:
    def __init__(self):
        self.outline_messages = []
        self.generation_messages = []
        self.revision_messages = []
        self.paragraph_messages = []

    def generate_outline(self, messages):
        self.outline_messages.append(messages)
        return ChapterOutline(
            beats=[
                BeatCard(
                    beat_id='beat-1',
                    summary='林砚抵达灵井。',
                    pov_character='林砚',
                    location='灵井',
                    emotional_arc='疑惑到警觉',
                    key_dialogue_hints=['湿信是谁留下的？'],
                )
            ],
            core_conflict='林砚必须确认灵井异响是否与玉佩有关。',
            pacing='紧凑推进',
            role_skill_targets=['保持线索压力'],
        )

    def generate_chapter(self, messages):
        self.generation_messages.append(messages)
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

    def revise_chapter(self, messages):
        self.revision_messages.append(messages)
        return self.generate_chapter(messages)

    def revise_paragraph(self, messages):
        self.paragraph_messages.append(messages)
        raise AssertionError('revise_paragraph should not be called for invalid request payload')


class MultiChangeLLMClient:
    def generate_chapter(self, messages):
        return ChapterGeneration(
            title='第一章 雨巷密谈',
            draft_content='林砚停在雨巷口，沈微霜递来一封湿透的信。',
            context_summary='林砚与沈微霜交换线索。',
            review_hints=['确认角色状态与伏笔推进是否都应提交'],
            proposed_character_changes=[
                ProposedCharacterChange(character_id=1, status='开始调查密信', current_goals=['追查湿信来源']),
                ProposedCharacterChange(character_id=2, status='隐瞒湿信来历', current_goals=['观察林砚反应']),
            ],
            proposed_foreshadow_changes=[
                ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='湿信推进玉佩线索'),
            ],
        )


class RollbackForeshadowLLMClient:
    def generate_chapter(self, messages):
        return ChapterGeneration(
            title='第二章 玉佩回潮',
            draft_content='裂纹玉佩已经被解释清楚，却又在雨夜重新发出旧光。',
            context_summary='已解决伏笔被重新推进。',
            review_hints=['确认伏笔是否允许倒退'],
            proposed_character_changes=[],
            proposed_foreshadow_changes=[
                ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='尝试重新推进已解决伏笔'),
            ],
        )


class CharacterJumpLLMClient:
    def generate_chapter(self, messages):
        return ChapterGeneration(
            title='第二章 急转',
            draft_content='林砚放弃旧案，转而追查城主府密信。',
            context_summary='角色目标发生明显切换。',
            review_hints=['确认角色目标跳变是否有铺垫'],
            proposed_character_changes=[
                ProposedCharacterChange(character_id=1, status='转向追查密信', current_goals=['追查城主府密信']),
            ],
            proposed_foreshadow_changes=[],
        )


def event_logs(db_session, world_id):
    return list(
        db_session.scalars(
            select(EventLog)
            .where(EventLog.world_id == world_id)
            .order_by(EventLog.id)
        )
    )


def chapter_approved_event(db_session, world_id):
    return next(event for event in event_logs(db_session, world_id) if event.event_type == 'chapter_approved')


def set_foreshadow_status(db_session, foreshadow_id: int, status: str) -> None:
    from app.foreshadow.models import Foreshadow

    foreshadow = db_session.get(Foreshadow, foreshadow_id)
    assert foreshadow is not None
    foreshadow.status = status
    db_session.commit()


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


def test_archived_world_rejects_core_narrative_writes_but_allows_review_reads(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    archive_response = client.patch(f'/worlds/{world_id}/status', headers={'Authorization': f'Bearer {token}'}, json={'status': 'archived'})
    assert archive_response.status_code == 200

    session_response = client.post(
        f'/worlds/{world_id}/chapters',
        json={'chapter_goal': '归档后开章'},
        headers={'Authorization': f'Bearer {token}'},
    )
    draft_response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '归档后草稿'},
        headers={'Authorization': f'Bearer {token}'},
    )
    approve_response = client.post(f"/chapters/{draft['chapter_id']}/approve", headers={'Authorization': f'Bearer {token}'})
    reject_response = client.post(
        f"/chapters/{draft['chapter_id']}/reject",
        json={'feedback': '归档后不应驳回'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert session_response.status_code == 409
    assert session_response.json()['detail'] == 'WORLD_ARCHIVED'
    assert draft_response.status_code == 409
    assert draft_response.json()['detail'] == 'WORLD_ARCHIVED'
    assert approve_response.status_code == 409
    assert approve_response.json()['detail'] == 'WORLD_ARCHIVED'
    assert reject_response.status_code == 409
    assert reject_response.json()['detail'] == 'WORLD_ARCHIVED'

    preview_response = client.get(f"/chapters/{draft['chapter_id']}/approval-preview", headers={'Authorization': f'Bearer {token}'})
    readiness_response = client.get(f"/chapters/{draft['chapter_id']}/approval-readiness", headers={'Authorization': f'Bearer {token}'})
    assert preview_response.status_code == 200
    assert readiness_response.status_code == 200

    db_session.expire_all()
    world = db_session.get(World, world_id)
    chapter = db_session.get(Chapter, draft['chapter_id'])
    assert world.world_version == 1
    assert chapter.status == 'reviewing'


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


def test_approve_chapter_rejects_second_commit_without_duplicate_side_effects(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()
    headers = {'Authorization': f'Bearer {token}'}

    first = client.post(f"/chapters/{draft['chapter_id']}/approve", headers=headers)
    assert first.status_code == 200
    db_session.expire_all()
    world = db_session.get(World, world_id)
    chapter = db_session.get(Chapter, draft['chapter_id'])
    character = db_session.get(Character, 1)
    foreshadow = db_session.get(Foreshadow, 1)
    before_world_version = world.world_version
    before_approved_version = chapter.approved_version
    before_character_goals = list(character.current_goals)
    before_foreshadow_status = foreshadow.status
    before_description = foreshadow.description
    before_events = db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id))
    before_foreshadow_events = db_session.scalar(
        select(func.count()).select_from(ForeshadowEvent).where(ForeshadowEvent.chapter_id == draft['chapter_id'])
    )

    second = client.post(f"/chapters/{draft['chapter_id']}/approve", headers=headers)

    assert second.status_code == 409
    assert second.json()['detail'] == 'ALREADY_APPROVED'
    db_session.expire_all()
    assert db_session.get(World, world_id).world_version == before_world_version == 2
    assert db_session.get(Chapter, draft['chapter_id']).approved_version == before_approved_version == draft['draft_version']
    assert db_session.get(Character, 1).current_goals == before_character_goals == ['追查城主府叛乱']
    assert db_session.get(Foreshadow, 1).status == before_foreshadow_status == 'advanced'
    assert db_session.get(Foreshadow, 1).description == before_description
    assert db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id)) == before_events
    assert db_session.scalar(
        select(func.count()).select_from(ForeshadowEvent).where(ForeshadowEvent.chapter_id == draft['chapter_id'])
    ) == before_foreshadow_events


def test_abandon_endpoint_rejects_unauthorized_forbidden_extra_body_and_approved_chapter(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()
    headers = {'Authorization': f'Bearer {token}'}

    unauthorized = client.post(f"/chapters/{draft['chapter_id']}/abandon")
    assert unauthorized.status_code == 401

    other_token = client.post(
        '/auth/register',
        json={'email': 'abandon-other@example.com', 'password': 'strongpass123'},
    ).json()['access_token']
    forbidden = client.post(
        f"/chapters/{draft['chapter_id']}/abandon",
        headers={'Authorization': f'Bearer {other_token}'},
        json={},
    )
    assert forbidden.status_code == 403
    assert forbidden.json()['detail'] == 'FORBIDDEN'

    extra_body = client.post(
        f"/chapters/{draft['chapter_id']}/abandon",
        headers=headers,
        json={'raw_text': '废弃请求不能夹带正文'},
    )
    assert extra_body.status_code == 422
    assert any(
        error['type'] == 'extra_forbidden' and error['loc'] == ['body', 'raw_text']
        for error in extra_body.json()['detail']
    )

    approve_response = client.post(f"/chapters/{draft['chapter_id']}/approve", headers=headers)
    assert approve_response.status_code == 200

    approved_abandon = client.post(f"/chapters/{draft['chapter_id']}/abandon", headers=headers, json={})
    assert approved_abandon.status_code == 409
    assert approved_abandon.json()['detail'] == 'ALREADY_APPROVED'
def test_approve_chapter_rejects_extra_fields_without_side_effects(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()
    before_events = len(event_logs(db_session, world_id))

    response = client.post(
        f"/chapters/{draft['chapter_id']}/approve",
        json={'draft_version': draft['draft_version'], 'raw_text': '审核请求不能夹带草稿原文'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 422
    assert any(
        error['type'] == 'extra_forbidden' and error['loc'] == ['body', 'raw_text']
        for error in response.json()['detail']
    )
    db_session.expire_all()
    world = db_session.get(World, world_id)
    chapter = db_session.get(Chapter, draft['chapter_id'])
    assert world.world_version == 1
    assert chapter.status == 'reviewing'
    assert chapter.approved_version is None
    assert chapter.approved_content is None
    assert len(event_logs(db_session, world_id)) == before_events


def test_revise_draft_rejects_extra_fields_without_side_effects(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    llm = FakeLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()
    before_drafts = db_session.scalar(select(func.count()).select_from(ChapterDraft).where(ChapterDraft.chapter_id == draft['chapter_id']))
    before_events = len(event_logs(db_session, world_id))

    response = client.post(
        f"/chapters/{draft['chapter_id']}/draft/revise",
        json={'instruction': '补足试探过程', 'raw_text': '修订请求不能夹带草稿原文', 'internal_score': 0.9},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 422
    assert any(
        error['type'] == 'extra_forbidden' and error['loc'] == ['body', 'raw_text']
        for error in response.json()['detail']
    )
    assert llm.revision_messages == []
    db_session.expire_all()
    chapter = db_session.get(Chapter, draft['chapter_id'])
    assert chapter.draft_version == draft['draft_version']
    assert db_session.scalar(select(func.count()).select_from(ChapterDraft).where(ChapterDraft.chapter_id == draft['chapter_id'])) == before_drafts
    assert len(event_logs(db_session, world_id)) == before_events


def test_revise_paragraph_rejects_extra_fields_without_side_effects(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    llm = FakeLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()
    before_drafts = db_session.scalar(select(func.count()).select_from(ChapterDraft).where(ChapterDraft.chapter_id == draft['chapter_id']))
    before_events = len(event_logs(db_session, world_id))

    response = client.post(
        f"/chapters/{draft['chapter_id']}/draft/paragraph",
        json={
            'paragraph_index': 0,
            'mode': 'rewrite',
            'instruction': '增强悬念',
            'raw_text': '段落修订请求不能夹带草稿原文',
            'internal_score': 0.9,
        },
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 422
    assert any(
        error['type'] == 'extra_forbidden' and error['loc'] == ['body', 'raw_text']
        for error in response.json()['detail']
    )
    assert llm.paragraph_messages == []
    db_session.expire_all()
    chapter = db_session.get(Chapter, draft['chapter_id'])
    assert chapter.draft_version == draft['draft_version']
    assert db_session.scalar(select(func.count()).select_from(ChapterDraft).where(ChapterDraft.chapter_id == draft['chapter_id'])) == before_drafts
    assert len(event_logs(db_session, world_id)) == before_events


def test_reject_request_rejects_extra_fields_without_side_effects(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    llm = FakeLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()
    before_events = len(event_logs(db_session, world_id))
    before_generation_count = len(llm.generation_messages)
    chapter = db_session.get(Chapter, draft['chapter_id'])
    latest_draft = db_session.get(ChapterDraft, draft['draft_id'])
    before_status = chapter.status
    before_feedback = latest_draft.rejection_feedback

    response = client.post(
        f"/chapters/{draft['chapter_id']}/reject",
        json={
            'feedback': '需要补足动机',
            'raw_text': '驳回请求不能夹带草稿原文',
            'internal_score': 0.9,
        },
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 422
    assert any(
        error['type'] == 'extra_forbidden' and error['loc'] == ['body', 'raw_text']
        for error in response.json()['detail']
    )
    assert len(llm.generation_messages) == before_generation_count
    assert llm.revision_messages == []
    assert llm.paragraph_messages == []
    db_session.expire_all()
    chapter = db_session.get(Chapter, draft['chapter_id'])
    latest_draft = db_session.get(ChapterDraft, draft['draft_id'])
    assert chapter.status == before_status
    assert latest_draft.rejection_feedback == before_feedback
    assert len(event_logs(db_session, world_id)) == before_events


def test_edit_draft_request_rejects_extra_fields_without_side_effects(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    llm = FakeLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()
    chapter = db_session.get(Chapter, draft['chapter_id'])
    latest_draft = db_session.get(ChapterDraft, draft['draft_id'])
    before_drafts = db_session.scalar(select(func.count()).select_from(ChapterDraft).where(ChapterDraft.chapter_id == draft['chapter_id']))
    before_events = len(event_logs(db_session, world_id))
    before_generation_count = len(llm.generation_messages)
    before_draft_version = chapter.draft_version
    before_content = latest_draft.content
    before_change_summary = latest_draft.change_summary

    response = client.put(
        f"/chapters/{draft['chapter_id']}/draft",
        json={
            'content': '林砚在灵井旁听见了第二个人的脚步声。',
            'change_summary': '补足动机',
            'raw_text': '编辑请求不能夹带草稿原文',
            'internal_score': 0.9,
        },
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 422
    assert any(
        error['type'] == 'extra_forbidden' and error['loc'] == ['body', 'raw_text']
        for error in response.json()['detail']
    )
    assert len(llm.generation_messages) == before_generation_count
    assert llm.revision_messages == []
    assert llm.paragraph_messages == []
    db_session.expire_all()
    chapter = db_session.get(Chapter, draft['chapter_id'])
    latest_draft = db_session.get(ChapterDraft, draft['draft_id'])
    assert chapter.draft_version == before_draft_version
    assert latest_draft.content == before_content
    assert latest_draft.change_summary == before_change_summary
    assert db_session.scalar(select(func.count()).select_from(ChapterDraft).where(ChapterDraft.chapter_id == draft['chapter_id'])) == before_drafts
    assert len(event_logs(db_session, world_id)) == before_events


def test_stash_draft_request_rejects_extra_fields_without_side_effects(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    llm = FakeLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()
    chapter = db_session.get(Chapter, draft['chapter_id'])
    latest_draft = db_session.get(ChapterDraft, draft['draft_id'])
    before_drafts = db_session.scalar(select(func.count()).select_from(ChapterDraft).where(ChapterDraft.chapter_id == draft['chapter_id']))
    before_events = len(event_logs(db_session, world_id))
    before_generation_count = len(llm.generation_messages)
    before_draft_version = chapter.draft_version
    before_change_type = latest_draft.change_type
    before_change_summary = latest_draft.change_summary

    response = client.post(
        f"/chapters/{draft['chapter_id']}/draft/stash",
        json={
            'note': '暂存当前草稿',
            'raw_text': '暂存请求不能夹带草稿原文',
            'internal_score': 0.9,
        },
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 422
    assert any(
        error['type'] == 'extra_forbidden' and error['loc'] == ['body', 'raw_text']
        for error in response.json()['detail']
    )
    assert len(llm.generation_messages) == before_generation_count
    assert llm.revision_messages == []
    assert llm.paragraph_messages == []
    db_session.expire_all()
    chapter = db_session.get(Chapter, draft['chapter_id'])
    latest_draft = db_session.get(ChapterDraft, draft['draft_id'])
    assert chapter.draft_version == before_draft_version
    assert latest_draft.change_type == before_change_type
    assert latest_draft.change_summary == before_change_summary
    assert db_session.scalar(select(func.count()).select_from(ChapterDraft).where(ChapterDraft.chapter_id == draft['chapter_id'])) == before_drafts
    assert len(event_logs(db_session, world_id)) == before_events


def test_outline_request_rejects_extra_fields_without_side_effects(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    llm = FakeLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    chapter_response = client.post(
        f'/worlds/{world_id}/chapters',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert chapter_response.status_code == 200
    chapter_id = chapter_response.json()['id']
    chapter = db_session.get(Chapter, chapter_id)
    before_outline_beats = chapter.outline_beats
    before_outline_context = chapter.outline_context
    before_status = chapter.status
    before_drafts = db_session.scalar(select(func.count()).select_from(ChapterDraft).where(ChapterDraft.chapter_id == chapter_id))
    before_events = len(event_logs(db_session, world_id))

    response = client.post(
        f'/chapters/{chapter_id}/outline',
        json={
            'chapter_context': '强调灵井裂纹与湿信。',
            'raw_text': '提纲请求不能夹带原文。',
            'internal_score': 0.9,
        },
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 422
    assert any(
        error['type'] == 'extra_forbidden' and error['loc'] == ['body', 'raw_text']
        for error in response.json()['detail']
    )
    assert llm.outline_messages == []
    assert llm.generation_messages == []
    db_session.expire_all()
    chapter = db_session.get(Chapter, chapter_id)
    assert chapter.outline_beats == before_outline_beats
    assert chapter.outline_context == before_outline_context
    assert chapter.status == before_status
    assert db_session.scalar(select(func.count()).select_from(ChapterDraft).where(ChapterDraft.chapter_id == chapter_id)) == before_drafts
    assert len(event_logs(db_session, world_id)) == before_events


def test_write_request_rejects_extra_fields_without_side_effects(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    llm = FakeLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    chapter_response = client.post(
        f'/worlds/{world_id}/chapters',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert chapter_response.status_code == 200
    chapter_id = chapter_response.json()['id']
    chapter = db_session.get(Chapter, chapter_id)
    before_outline_beats = chapter.outline_beats
    before_outline_context = chapter.outline_context
    before_status = chapter.status
    before_draft_version = chapter.draft_version
    before_drafts = db_session.scalar(select(func.count()).select_from(ChapterDraft).where(ChapterDraft.chapter_id == chapter_id))
    before_events = len(event_logs(db_session, world_id))

    response = client.post(
        f'/chapters/{chapter_id}/write',
        json={
            'outline_beats': [
                {
                    'beat_id': 'beat-1',
                    'summary': '林砚抵达灵井。',
                    'pov_character': '林砚',
                    'location': '灵井',
                    'emotional_arc': '疑惑到警觉',
                    'key_dialogue_hints': ['湿信是谁留下的？'],
                }
            ],
            'raw_text': '按提纲写作请求不能夹带原文。',
            'internal_score': 0.9,
        },
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 422
    assert any(
        error['type'] == 'extra_forbidden' and error['loc'] == ['body', 'raw_text']
        for error in response.json()['detail']
    )
    assert llm.outline_messages == []
    assert llm.generation_messages == []
    db_session.expire_all()
    chapter = db_session.get(Chapter, chapter_id)
    assert chapter.outline_beats == before_outline_beats
    assert chapter.outline_context == before_outline_context
    assert chapter.status == before_status
    assert chapter.draft_version == before_draft_version
    assert db_session.scalar(select(func.count()).select_from(ChapterDraft).where(ChapterDraft.chapter_id == chapter_id)) == before_drafts
    assert len(event_logs(db_session, world_id)) == before_events


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


def test_approval_preview_exposes_change_indexes_and_default_selection(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    response = client.get(f"/chapters/{draft['chapter_id']}/approval-preview", headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    body = response.json()
    assert body['character_changes'][0]['change_index'] == 0
    assert body['character_changes'][0]['selected_by_default'] is True
    assert body['foreshadow_changes'][0]['change_index'] == 0
    assert body['foreshadow_changes'][0]['selected_by_default'] is True


def test_approve_chapter_applies_only_selected_character_and_foreshadow_changes(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: MultiChangeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进雨巷密谈'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    response = client.post(
        f"/chapters/{draft['chapter_id']}/approve",
        json={
            'draft_version': draft['draft_version'],
            'selected_character_change_indexes': [1],
            'selected_foreshadow_change_indexes': [0],
        },
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    overview = client.get(f'/worlds/{world_id}/overview', headers={'Authorization': f'Bearer {token}'}).json()
    assert overview['world_version'] == 2
    characters_by_id = {character['id']: character for character in overview['characters']}
    foreshadows_by_id = {foreshadow['id']: foreshadow for foreshadow in overview['foreshadows']}
    assert characters_by_id[1]['status'] == 'active'
    assert characters_by_id[2]['status'] == '隐瞒湿信来历'
    assert foreshadows_by_id[1]['status'] == 'advanced'

    events = event_logs(db_session, world_id)
    assert [event.event_type for event in events].count('character_change') == 1
    assert [event.event_type for event in events].count('foreshadow_change') == 1
    approved = chapter_approved_event(db_session, world_id)
    assert approved.payload['applied_change_indexes'] == {'characters': [1], 'foreshadows': [0]}
    assert approved.payload['applied_changes']['characters'] == [draft['proposed_changes']['characters'][1]]
    assert approved.payload['applied_changes']['foreshadows'] == [draft['proposed_changes']['foreshadows'][0]]
    assert 'proposed_changes' not in approved.payload


def test_approve_chapter_allows_empty_selection_without_object_changes(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    response = client.post(
        f"/chapters/{draft['chapter_id']}/approve",
        json={
            'draft_version': draft['draft_version'],
            'selected_character_change_indexes': [],
            'selected_foreshadow_change_indexes': [],
        },
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    overview = client.get(f'/worlds/{world_id}/overview', headers={'Authorization': f'Bearer {token}'}).json()
    assert overview['world_version'] == 2
    assert overview['characters'][0]['current_goals'] == ['调查青岚城灵脉衰退']
    assert overview['foreshadows'][0]['status'] == 'planted'
    events = event_logs(db_session, world_id)
    assert 'character_change' not in [event.event_type for event in events]
    assert 'foreshadow_change' not in [event.event_type for event in events]
    approved = chapter_approved_event(db_session, world_id)
    assert approved.payload['applied_changes'] == {'characters': [], 'foreshadows': []}


def test_approve_chapter_rejects_invalid_change_selection(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    response = client.post(
        f"/chapters/{draft['chapter_id']}/approve",
        json={'draft_version': draft['draft_version'], 'selected_character_change_indexes': [0, 0]},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 400
    assert response.json()['detail'] == 'INVALID_CHANGE_SELECTION'


def test_approve_chapter_rejects_stale_draft_version_selection(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    response = client.post(
        f"/chapters/{draft['chapter_id']}/approve",
        json={'draft_version': draft['draft_version'] + 1, 'selected_character_change_indexes': [0]},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 409
    assert response.json()['detail'] == 'DRAFT_VERSION_MISMATCH'


def test_approval_preview_includes_consistency_summary_and_warnings(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    set_foreshadow_status(db_session, 1, 'resolved')
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: RollbackForeshadowLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '重新推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    response = client.get(f"/chapters/{draft['chapter_id']}/approval-preview", headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    body = response.json()
    assert body['consistency_summary']['status'] == 'blocked'
    assert body['consistency_summary']['blocking_count'] == 1
    assert body['consistency_warnings'][0]['severity'] == 'blocking'
    assert body['consistency_warnings'][0]['category'] == 'foreshadow_transition'
    assert body['consistency_warnings'][0]['object_type'] == 'foreshadow'
    assert body['consistency_warnings'][0]['object_id'] == 1
    assert body['consistency_warnings'][0]['change_index'] == 0


def test_approval_consistency_recalculates_for_selected_change_set(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    set_foreshadow_status(db_session, 1, 'resolved')
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: RollbackForeshadowLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '重新推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    response = client.post(
        f"/chapters/{draft['chapter_id']}/approval-consistency",
        json={
            'draft_version': draft['draft_version'],
            'selected_character_change_indexes': [],
            'selected_foreshadow_change_indexes': [],
        },
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    body = response.json()
    assert body['selected_change_indexes'] == {'characters': [], 'foreshadows': []}
    assert body['consistency_summary']['status'] == 'clear'
    assert body['consistency_warnings'] == []


def test_approve_chapter_blocks_selected_consistency_violations(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    set_foreshadow_status(db_session, 1, 'resolved')
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: RollbackForeshadowLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '重新推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    response = client.post(
        f"/chapters/{draft['chapter_id']}/approve",
        json={'draft_version': draft['draft_version'], 'selected_foreshadow_change_indexes': [0]},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 409
    detail = response.json()['detail']
    assert detail['code'] == 'CONSISTENCY_BLOCKED'
    assert detail['summary']['blocking_count'] == 1
    assert detail['warnings'][0]['category'] == 'foreshadow_transition'


def test_approve_chapter_allows_warning_only_consistency_and_records_summary(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: CharacterJumpLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '切换角色目标'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    response = client.post(
        f"/chapters/{draft['chapter_id']}/approve",
        json={'draft_version': draft['draft_version'], 'selected_character_change_indexes': [0]},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    approved = chapter_approved_event(db_session, world_id)
    assert approved.payload['consistency_summary']['status'] == 'needs_review'
    assert approved.payload['consistency_summary']['warning_count'] == 1
    assert approved.payload['consistency_warnings'][0]['severity'] == 'warning'
    assert approved.payload['consistency_warnings'][0]['category'] == 'character_jump'


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
    assert [event['event_type'] for event in overview['recent_events']] == ['WORLD_CREATED']


def test_create_draft_maps_model_request_failure(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    chapter_goal = '推进玉佩线索'
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FailingLLMClient())

    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': chapter_goal},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 502
    assert response.json()['detail'] == 'MODEL_REQUEST_FAILED'

    db_session.expire_all()
    world = db_session.get(World, world_id)
    assert world is not None
    assert world.world_version == 1
    assert [event.event_type for event in event_logs(db_session, world_id)] == ['WORLD_CREATED']
    assert db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id)) == 0
    assert db_session.scalar(select(func.count()).select_from(ChapterDraft)) == 0

    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    retry_response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': chapter_goal},
        headers={'Authorization': f'Bearer {token}'},
    )
    retry = retry_response.json()

    assert retry_response.status_code == 200
    assert retry['status'] == 'reviewing'
    assert retry['source_world_version'] == 1

    db_session.expire_all()
    world = db_session.get(World, world_id)
    chapter = db_session.get(Chapter, retry['chapter_id'])
    assert world.world_version == 1
    assert chapter.chapter_goal == chapter_goal
    assert chapter.status == 'reviewing'
    assert [event.event_type for event in event_logs(db_session, world_id)] == ['WORLD_CREATED']
    assert db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id)) == 1
    assert db_session.scalar(select(func.count()).select_from(ChapterDraft)) == 1


def test_create_draft_preserves_safe_model_runtime_error_detail(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: AuthFailingLLMClient())

    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 502
    assert response.json()['detail'] == 'MODEL_AUTH_FAILED'


def test_create_draft_masks_unknown_model_runtime_error_detail(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: UnknownFailingLLMClient())

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


def readiness_execution_context(source_world_version: int = 1) -> dict:
    return {
        'source': 'next_chapter_prep',
        'source_world_version': source_world_version,
        'next_chapter_number': 1,
        'goal': '推进玉佩线索',
        'recommended_pov': {'character_id': 1, 'name': '林砚'},
        'source_signals': ['character_arc_progression_hint'],
        'priority_characters': [
            {'character_id': 1, 'name': '林砚', 'role_type': 'protagonist', 'status': 'active', 'reason': '主角需要推进'}
        ],
        'priority_foreshadows': [
            {'foreshadow_id': 1, 'title': '裂纹玉佩', 'status': 'planted', 'urgency_level': 3, 'reason': '伏笔需要推进'}
        ],
        'progression_hints': [
            {
                'hint_type': 'character',
                'priority': 'high',
                'title': '追查玉佩来源',
                'rationale': '上一章已经设置玉佩线索',
                'suggested_next_beat': '林砚带着玉佩询问沈微霜',
                'related_character_ids': [1],
                'related_foreshadow_ids': [1],
                'can_seed_next_chapter_goal': True,
            }
        ],
        'continuity_warnings': [],
        'recent_events': [],
    }


def add_current_review_reports(db_session, chapter_id: int, high_risk: bool = False) -> None:
    chapter = db_session.get(Chapter, chapter_id)
    assert chapter is not None
    critic_issue = {
        'severity': 'high' if high_risk else 'medium',
        'dimension': 'character_consistency',
        'message': '林砚突然信任沈微霜，与当前谨慎状态冲突。',
        'paragraph_index': 0,
        'suggested_action': '补足信任建立过程。',
    }
    chapter.critique_report = {
        'chapter_id': chapter.id,
        'draft_version': chapter.draft_version,
        'current_draft_version': chapter.draft_version,
        'is_stale': False,
        'overall_score': 82,
        'summary': '整体可批准。',
        'dimensions': {},
        'issues': [critic_issue] if high_risk else [],
        'suggestions': [],
        'created_at': '2026-05-30T00:00:00Z',
    }
    chapter.character_arc_report = {
        'chapter_id': chapter.id,
        'draft_version': chapter.draft_version,
        'current_draft_version': chapter.draft_version,
        'is_stale': False,
        'summary': '角色弧线连续。',
        'character_arcs': [
            {
                'character_id': 1,
                'name': '林砚',
                'continuity_risk': 'high' if high_risk else 'low',
                'risk_reason': '选择转折缺少铺垫。' if high_risk else None,
            }
        ],
        'relationship_notes': [],
        'progression_hints': [],
        'created_at': '2026-05-30T00:00:00Z',
    }
    db_session.commit()


def test_approval_readiness_ready_when_all_checks_pass(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索', 'execution_context': readiness_execution_context()},
        headers={'Authorization': f'Bearer {token}'},
    ).json()
    add_current_review_reports(db_session, draft['chapter_id'])

    response = client.get(f"/chapters/{draft['chapter_id']}/approval-readiness", headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'ready'
    assert body['summary'] == '草稿已通过所有审批准备检查。'
    assert body['world_version']['matches'] is True
    assert {check['status'] for check in body['checks']} == {'pass'}


def test_approval_readiness_blocks_world_version_mismatch(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索', 'execution_context': readiness_execution_context()},
        headers={'Authorization': f'Bearer {token}'},
    ).json()
    world = db_session.get(World, world_id)
    world.world_version = 2
    db_session.commit()

    response = client.get(f"/chapters/{draft['chapter_id']}/approval-readiness", headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'blocked'
    version_check = next(check for check in body['checks'] if check['key'] == 'world_version')
    assert version_check['status'] == 'fail'
    assert version_check['message'] == '世界版本已变化，请重新生成草稿后再批准。'


def test_approval_readiness_needs_review_for_missing_reports_and_uncovered_priorities(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    context = readiness_execution_context()
    context['priority_characters'].append(
        {'character_id': 2, 'name': '沈微霜', 'role_type': 'ally', 'status': 'active', 'reason': '需要回应主角试探'}
    )
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索', 'execution_context': context},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    response = client.get(f"/chapters/{draft['chapter_id']}/approval-readiness", headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'needs_review'
    priority_check = next(check for check in body['checks'] if check['key'] == 'priority_coverage')
    assert priority_check['status'] == 'warning'
    assert priority_check['details']['missing_character_ids'] == [2]
    assert next(check for check in body['checks'] if check['key'] == 'critic_high_risk')['status'] == 'warning'
    assert next(check for check in body['checks'] if check['key'] == 'character_arc_risk')['status'] == 'warning'


def test_approval_readiness_reports_high_risk_items(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索', 'execution_context': readiness_execution_context()},
        headers={'Authorization': f'Bearer {token}'},
    ).json()
    add_current_review_reports(db_session, draft['chapter_id'], high_risk=True)

    response = client.get(f"/chapters/{draft['chapter_id']}/approval-readiness", headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    body = response.json()
    assert body['status'] == 'needs_review'
    assert body['high_risk_items'] == [
        {
            'source': 'critic',
            'severity': 'high',
            'message': '林砚突然信任沈微霜，与当前谨慎状态冲突。',
            'details': {'dimension': 'character_consistency', 'paragraph_index': 0},
        },
        {
            'source': 'character_arc',
            'severity': 'high',
            'message': '林砚：选择转折缺少铺垫。',
            'details': {'character_id': 1, 'risk_reason': '选择转折缺少铺垫。'},
        },
    ]
