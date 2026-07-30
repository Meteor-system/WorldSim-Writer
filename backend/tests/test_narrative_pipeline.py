from sqlalchemy import func, select

from app.character.models import Character
from app.event.models import EventLog
from app.llm.schemas import (
    BeatCard,
    ChapterGeneration,
    ChapterOutline,
    CritiqueIssue,
    OpeningContract,
    OpeningEvidence,
    CritiqueReport,
    ProposedCharacterChange,
    ProposedForeshadowChange,
)
from app.narrative import service as narrative_service
from app.narrative.schemas import ApproveRequest
from app.narrative.models import Chapter, ChapterDraft
from app.world.models import World


def auth(token):
    return {'Authorization': f'Bearer {token}'}


def register(client, email='writer@example.com'):
    response = client.post('/auth/register', json={'email': email, 'password': 'strongpass123'})
    return response.json()['access_token']


def register_and_create_world(client):
    token = register(client)
    world = client.post('/worlds/from-template', headers=auth(token)).json()
    return token, world['id']


def create_chapter(client, token, world_id, goal='推进裂纹玉佩线索'):
    response = client.post(
        f'/worlds/{world_id}/chapters',
        json={'chapter_goal': goal, 'title': '第一章 暗井回声'},
        headers=auth(token),
    )
    return response


def opening_contract() -> OpeningContract:
    return OpeningContract(
        background='青岚城灵脉衰退，暗井在雨夜发出异响。',
        protagonist_identity='林砚是为师门奔走的外门弟子。',
        motivation='他必须查清玉佩线索以保护师妹。',
        personality_evidence_plan='让林砚先救下药箱再继续追查。',
        conflict_goal='在巡夜人抵达前确认玉佩的主人。',
        locked_pov='林砚限知第三人称。',
    )


def opening_body() -> str:
    return '\n\n'.join([
        '林砚在暗井旁听见了第二个人的脚步声。雨水压低了青岚城的屋檐，废弃灵井却在巷尾吐出温热白雾；城里人人都说灵脉衰退只是旱灾，他知道那是谎话。',
        '他是欠着师门药债的外门弟子，今夜原该回去照看师妹。可城主府的文书写明天亮前要带走她问话，林砚只能追查玉佩与失踪师兄的名字，哪怕这会把自己送进巡夜人的眼里。',
        '巷口的药箱被雨水冲翻，他先扑进泥水把药瓶一只只捡回，又把割裂的手藏进袖中。沈微霜问他为何不逃，林砚只说师妹还在等药，这不是能算清的账。',
        '灵井底下传来铁链拖地声，玉佩映出师兄惯用的云纹。林砚没有告诉沈微霜自己看见了什么，只沿着井壁摸到一道新鲜的靴印，听见城主府巡夜人的铜铃越来越近。',
        '他必须在铜铃停在巷口前确认玉佩主人，否则师妹会被带走，师兄的失踪也会被埋进井里。林砚让沈微霜守住巷口，自己系紧绳索下井；他不确定她会不会出卖自己。',
        '林砚的靴底刚离开井沿，铜铃便在雨幕外停住。巡夜人喊出他的名字，他只能从井壁渗出的血色水痕判断，下面等着他的不是师兄，而是一场早已布好的局。',
    ])


def opening_evidence() -> list[OpeningEvidence]:
    return [
        OpeningEvidence(check='background', paragraph_index=0, quote='废弃灵井却在巷尾吐出温热白雾'),
        OpeningEvidence(check='protagonist_identity', paragraph_index=1, quote='欠着师门药债的外门弟子'),
        OpeningEvidence(check='motivation', paragraph_index=1, quote='只能追查玉佩与失踪师兄的名字'),
        OpeningEvidence(check='personality_evidence_plan', paragraph_index=2, quote='先扑进泥水把药瓶一只只捡回'),
        OpeningEvidence(check='conflict_goal', paragraph_index=4, quote='必须在铜铃停在巷口前确认玉佩主人'),
        OpeningEvidence(check='locked_pov', paragraph_index=3, quote='林砚没有告诉沈微霜自己看见了什么'),
    ]


def fake_outline() -> ChapterOutline:
    return ChapterOutline(
        core_conflict='林砚必须判断沈微霜是否可信。',
        pov_suggestion='林砚',
        pacing='悬疑推进，结尾留下密道疑问',
        role_skill_targets=['林砚', '沈微霜'],
        beats=[
            BeatCard(
                beat_id='beat-1',
                summary='林砚在暗井旁发现玉佩与灵脉共振。',
                pov_character='林砚',
                location='废弃灵井',
                emotional_arc='疑惑 -> 警觉',
                key_dialogue_hints=['这不是普通裂纹。'],
            ),
            BeatCard(
                beat_id='beat-2',
                summary='沈微霜出现并隐瞒她知道密道入口。',
                pov_character='林砚',
                location='青岚城后巷',
                emotional_arc='试探 -> 不信任',
                key_dialogue_hints=['你不该来这里。'],
            ),
        ],
        opening_contract=opening_contract(),
    )


def fake_generation() -> ChapterGeneration:
    return ChapterGeneration(
        title='第一章 暗井回声',
        draft_content=opening_body(),
        context_summary='林砚调查灵脉衰退，裂纹玉佩与暗井产生共振。',
        review_hints=['确认沈微霜动机是否一致', '确认玉佩伏笔是否推进'],
        proposed_character_changes=[ProposedCharacterChange(character_id=1, current_goals=['追查城主府叛乱'])],
        proposed_foreshadow_changes=[
            ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='玉佩线索被推进')
        ],
        opening_evidence=opening_evidence(),
    )


def late_generation() -> ChapterGeneration:
    return ChapterGeneration(
        title='迟到生成标题',
        draft_content='这段迟到正文绝不能覆盖并发请求已经提交的结果。',
        context_summary='迟到正文摘要。',
        review_hints=['迟到结果不应落库'],
        proposed_character_changes=[ProposedCharacterChange(character_id=1, current_goals=['迟到目标'])],
        proposed_foreshadow_changes=[
            ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='迟到伏笔变化')
        ],
    )


def fake_critique() -> CritiqueReport:
    return CritiqueReport(
        score=86,
        issues=[
            CritiqueIssue(category='character_voice', severity='medium', message='沈微霜台词可以更克制。'),
            CritiqueIssue(category='foreshadow', severity='low', message='玉佩与暗井的关联已推进但仍需保留疑问。'),
        ],
        suggestions=['加强林砚对师门牵连的担忧。'],
        consistency_check={
            'character_voice': 'needs_minor_revision',
            'foreshadow_usage': 'advanced',
            'world_rule_adherence': 'pass',
            'pacing': 'pass',
        },
    )


class PipelineLLMClient:
    def generate_outline(self, messages):
        return fake_outline()

    def generate_chapter(self, messages):
        joined = '\n'.join(message['content'] for message in messages)
        if '编辑后的节拍：林砚直接逼问沈微霜。' in joined:
            return ChapterGeneration(
                title='第一章 暗井回声',
                draft_content='编辑后的节拍被采用：林砚直接逼问沈微霜。',
                context_summary='林砚用更强硬的方式推进暗井线索。',
                review_hints=['确认逼问是否符合林砚性格'],
                proposed_character_changes=[ProposedCharacterChange(character_id=1, current_goals=['追查城主府叛乱'])],
                proposed_foreshadow_changes=[
                    ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='玉佩线索被推进')
                ],
            )
        return fake_generation()

    def critique_chapter(self, messages):
        return fake_critique()


class CountingPipelineLLMClient(PipelineLLMClient):
    def __init__(self):
        self.outline_calls = 0
        self.generation_calls = 0
        self.critique_calls = 0

    def generate_outline(self, messages):
        self.outline_calls += 1
        return super().generate_outline(messages)

    def generate_chapter(self, messages):
        self.generation_calls += 1
        return super().generate_chapter(messages)

    def critique_chapter(self, messages):
        self.critique_calls += 1
        return super().critique_chapter(messages)


def test_create_chapter_session_requires_login_and_sets_base_world_version(client):
    token, world_id = register_and_create_world(client)

    unauthenticated = client.post(f'/worlds/{world_id}/chapters', json={'chapter_goal': '推进玉佩线索'})
    response = create_chapter(client, token, world_id)

    assert unauthenticated.status_code == 401
    assert unauthenticated.json()['detail'] == 'UNAUTHORIZED'
    assert response.status_code == 200
    payload = response.json()
    assert payload['title'] == '第一章 暗井回声'
    assert payload['status'] == 'drafting'
    assert payload['chapter_goal'] == '推进裂纹玉佩线索'
    assert payload['base_world_version'] == 1
    assert payload['outline_beats'] == []
    assert payload['critique_report'] == {}


def test_active_chapter_session_restores_latest_unapproved_progress_without_side_effects(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    other_token = register(client, 'active-session-other@example.com')
    before_events = db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id))

    empty_response = client.get(f'/worlds/{world_id}/chapters/active', headers=auth(token))
    forbidden_response = client.get(f'/worlds/{world_id}/chapters/active', headers=auth(other_token))
    chapter_id = create_chapter(client, token, world_id).json()['id']
    drafting_response = client.get(f'/worlds/{world_id}/chapters/active', headers=auth(token))

    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: PipelineLLMClient())
    client.post(f'/chapters/{chapter_id}/outline', headers=auth(token), json={})
    outlined_response = client.get(f'/worlds/{world_id}/chapters/active', headers=auth(token))
    client.post(f'/chapters/{chapter_id}/write', headers=auth(token), json={})
    reviewing_response = client.get(f'/worlds/{world_id}/chapters/active', headers=auth(token))

    assert empty_response.status_code == 200
    assert empty_response.json() == {'chapter': None, 'draft': None, 'draft_versions': [], 'recent_approval': None}
    assert forbidden_response.status_code == 403
    assert forbidden_response.json()['detail'] == 'FORBIDDEN'
    assert drafting_response.status_code == 200
    assert drafting_response.json()['chapter']['id'] == chapter_id
    assert drafting_response.json()['chapter']['status'] == 'drafting'
    assert drafting_response.json()['draft'] is None
    assert drafting_response.json()['draft_versions'] == []
    assert outlined_response.json()['chapter']['status'] == 'outlined'
    assert outlined_response.json()['chapter']['outline_beats'][0]['beat_id'] == 'beat-1'
    assert outlined_response.json()['draft'] is None
    assert outlined_response.json()['draft_versions'] == []
    assert reviewing_response.json()['chapter']['status'] == 'reviewing'
    assert reviewing_response.json()['draft']['chapter_id'] == chapter_id
    assert reviewing_response.json()['draft']['content'].startswith('林砚在暗井旁')
    assert reviewing_response.json()['draft_versions'] == [1]

    db_session.expire_all()
    world = db_session.get(World, world_id)
    assert world.world_version == 1
    assert db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id)) == before_events


def test_active_chapter_session_returns_recent_approval_without_side_effects_and_prefers_new_work(
    client, db_session, monkeypatch, opening_approval_payload
):
    token, world_id = register_and_create_world(client)
    chapter_id = create_chapter(client, token, world_id).json()['id']
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: PipelineLLMClient())
    client.post(f'/chapters/{chapter_id}/outline', headers=auth(token), json={})
    draft = client.post(f'/chapters/{chapter_id}/write', headers=auth(token), json={}).json()
    client.post(
        f'/chapters/{chapter_id}/approve',
        headers=auth(token),
        json=opening_approval_payload({'chapter_id': chapter_id, **draft}),
    )
    before_event_count = db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id))

    approval_response = client.get(f'/worlds/{world_id}/chapters/active', headers=auth(token))

    assert approval_response.status_code == 200
    assert approval_response.json() == {
        'chapter': None,
        'draft': None,
        'draft_versions': [],
        'recent_approval': {
            'chapter_id': chapter_id,
            'title': '第一章 暗井回声',
            'approved_version': 1,
            'world_version_before': 1,
            'world_version_after': 2,
            'character_change_count': 1,
            'foreshadow_change_count': 1,
        },
    }
    db_session.expire_all()
    assert db_session.get(World, world_id).world_version == 2
    assert db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id)) == before_event_count

    new_chapter_id = create_chapter(client, token, world_id, '继续追查暗井密道').json()['id']
    active_response = client.get(f'/worlds/{world_id}/chapters/active', headers=auth(token))

    assert active_response.status_code == 200
    assert active_response.json()['chapter']['id'] == new_chapter_id
    assert active_response.json()['recent_approval'] is None


def test_outline_generates_and_persists_beat_cards(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    chapter_id = create_chapter(client, token, world_id).json()['id']
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: PipelineLLMClient())

    response = client.post(
        f'/chapters/{chapter_id}/outline',
        json={'chapter_context': '强调沈微霜的迟疑。'},
        headers=auth(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == 'outlined'
    assert payload['outline_context']['core_conflict'] == '林砚必须判断沈微霜是否可信。'
    assert payload['outline_beats'][0]['beat_id'] == 'beat-1'
    chapter = db_session.get(Chapter, chapter_id)
    assert chapter.outline_beats[1]['summary'] == '沈微霜出现并隐瞒她知道密道入口。'


def test_late_outline_cannot_restore_approved_chapter_to_outlined(
    client, db_session, monkeypatch, opening_approval_payload
):
    token, world_id = register_and_create_world(client)
    chapter_id = create_chapter(client, token, world_id).json()['id']
    user = db_session.get(World, world_id).owner
    narrative_service.generate_chapter_outline(db_session, user, chapter_id, llm_client=PipelineLLMClient())
    narrative_service.write_chapter_from_outline(db_session, user, chapter_id, llm_client=PipelineLLMClient())

    class ApprovingOutlineLLM(PipelineLLMClient):
        def generate_outline(self, messages):
            outline = super().generate_outline(messages)
            approved = narrative_service.approve_chapter(
                db_session,
                user,
                chapter_id,
                ApproveRequest.model_validate(opening_approval_payload({'chapter_id': chapter_id})),
            )
            assert approved.status == 'approved'
            return outline

    try:
        narrative_service.generate_chapter_outline(db_session, user, chapter_id, llm_client=ApprovingOutlineLLM())
    except Exception as error:
        assert getattr(error, 'status_code', None) == 409
        assert getattr(error, 'detail', None) == 'ALREADY_APPROVED'
    else:
        raise AssertionError('expected ALREADY_APPROVED')

    db_session.expire_all()
    chapter = db_session.get(Chapter, chapter_id)
    assert chapter.status == 'approved'
    assert chapter.approved_version == 1
    assert chapter.approved_content == fake_generation().draft_content
    assert db_session.get(World, world_id).world_version == 2
    assert db_session.query(EventLog).filter_by(world_id=world_id, event_type='chapter_approved').count() == 1


def test_late_outline_cannot_restore_abandoned_chapter_to_outlined(client, db_session):
    token, world_id = register_and_create_world(client)
    chapter_id = create_chapter(client, token, world_id).json()['id']
    user = db_session.get(World, world_id).owner
    before_events = db_session.query(EventLog).filter_by(world_id=world_id).count()

    class AbandoningOutlineLLM(PipelineLLMClient):
        def generate_outline(self, messages):
            outline = super().generate_outline(messages)
            abandoned = narrative_service.abandon_chapter(db_session, user, chapter_id)
            assert abandoned.status == 'abandoned'
            return outline

    try:
        narrative_service.generate_chapter_outline(db_session, user, chapter_id, llm_client=AbandoningOutlineLLM())
    except Exception as error:
        assert getattr(error, 'status_code', None) == 409
        assert getattr(error, 'detail', None) == 'CHAPTER_ABANDONED'
    else:
        raise AssertionError('expected CHAPTER_ABANDONED')

    db_session.expire_all()
    chapter = db_session.get(Chapter, chapter_id)
    assert chapter.status == 'abandoned'
    assert chapter.outline_beats == []
    assert chapter.outline_context == {}
    assert db_session.get(World, world_id).world_version == 1
    assert db_session.query(EventLog).filter_by(world_id=world_id).count() == before_events


def test_late_outline_rejects_world_version_change_without_overwriting_chapter(client, db_session):
    token, world_id = register_and_create_world(client)
    chapter_id = create_chapter(client, token, world_id).json()['id']
    user = db_session.get(World, world_id).owner
    before_events = db_session.query(EventLog).filter_by(world_id=world_id).count()

    class AdvancingWorldOutlineLLM(PipelineLLMClient):
        def generate_outline(self, messages):
            outline = super().generate_outline(messages)
            world = db_session.get(World, world_id)
            world.world_version += 1
            db_session.commit()
            return outline

    try:
        narrative_service.generate_chapter_outline(db_session, user, chapter_id, llm_client=AdvancingWorldOutlineLLM())
    except Exception as error:
        assert getattr(error, 'status_code', None) == 409
        assert getattr(error, 'detail', None) == 'WORLD_VERSION_MISMATCH'
    else:
        raise AssertionError('expected WORLD_VERSION_MISMATCH')

    db_session.expire_all()
    chapter = db_session.get(Chapter, chapter_id)
    assert chapter.status == 'drafting'
    assert chapter.outline_beats == []
    assert chapter.outline_context == {}
    assert db_session.get(World, world_id).world_version == 2
    assert db_session.query(EventLog).filter_by(world_id=world_id).count() == before_events


def test_late_outline_rejects_chapter_status_change_without_overwriting_new_state(client, db_session):
    token, world_id = register_and_create_world(client)
    chapter_id = create_chapter(client, token, world_id).json()['id']
    user = db_session.get(World, world_id).owner
    before_events = db_session.query(EventLog).filter_by(world_id=world_id).count()
    preserved_beats = [{'beat_id': 'concurrent', 'summary': '另一请求已生成大纲。'}]
    preserved_context = {'core_conflict': '保留并发请求结果'}

    class AdvancingChapterOutlineLLM(PipelineLLMClient):
        def generate_outline(self, messages):
            outline = super().generate_outline(messages)
            chapter = db_session.get(Chapter, chapter_id)
            chapter.status = 'outlined'
            chapter.outline_beats = preserved_beats
            chapter.outline_context = preserved_context
            db_session.commit()
            return outline

    try:
        narrative_service.generate_chapter_outline(db_session, user, chapter_id, llm_client=AdvancingChapterOutlineLLM())
    except Exception as error:
        assert getattr(error, 'status_code', None) == 409
        assert getattr(error, 'detail', None) == 'CHAPTER_STATUS_MISMATCH'
    else:
        raise AssertionError('expected CHAPTER_STATUS_MISMATCH')

    db_session.expire_all()
    chapter = db_session.get(Chapter, chapter_id)
    assert chapter.status == 'outlined'
    assert chapter.outline_beats == preserved_beats
    assert chapter.outline_context == preserved_context
    assert db_session.get(World, world_id).world_version == 1
    assert db_session.query(EventLog).filter_by(world_id=world_id).count() == before_events


def test_late_outline_rejects_draft_version_change_without_overwriting_new_draft(client, db_session):
    token, world_id = register_and_create_world(client)
    chapter_id = create_chapter(client, token, world_id).json()['id']
    user = db_session.get(World, world_id).owner
    narrative_service.generate_chapter_outline(db_session, user, chapter_id, llm_client=PipelineLLMClient())
    draft = narrative_service.write_chapter_from_outline(db_session, user, chapter_id, llm_client=PipelineLLMClient())
    preserved_beats = list(db_session.get(Chapter, chapter_id).outline_beats)
    before_events = db_session.query(EventLog).filter_by(world_id=world_id).count()

    class StashingOutlineLLM(PipelineLLMClient):
        def generate_outline(self, messages):
            outline = super().generate_outline(messages)
            stashed = narrative_service.stash_chapter_draft(db_session, user, chapter_id, '模型调用期间暂存')
            assert stashed['draft_version'] == 2
            return outline

    try:
        narrative_service.generate_chapter_outline(db_session, user, chapter_id, llm_client=StashingOutlineLLM())
    except Exception as error:
        assert getattr(error, 'status_code', None) == 409
        assert getattr(error, 'detail', None) == 'DRAFT_VERSION_MISMATCH'
    else:
        raise AssertionError('expected DRAFT_VERSION_MISMATCH')

    db_session.expire_all()
    chapter = db_session.get(Chapter, chapter_id)
    drafts = list(db_session.scalars(select(ChapterDraft).where(ChapterDraft.chapter_id == chapter_id).order_by(ChapterDraft.draft_version)))
    assert chapter.status == 'reviewing'
    assert chapter.draft_version == 2
    assert chapter.outline_beats == preserved_beats
    assert [item.draft_version for item in drafts] == [1, 2]
    assert drafts[0].content == drafts[1].content == draft['content']
    assert db_session.get(World, world_id).world_version == 1
    assert db_session.query(EventLog).filter_by(world_id=world_id).count() == before_events


def test_abandoned_chapter_rejects_outline_write_and_critique_before_model_calls(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    chapter_id = create_chapter(client, token, world_id).json()['id']
    llm_client = CountingPipelineLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm_client)
    abandoned = client.post(f'/chapters/{chapter_id}/abandon', headers=auth(token), json={})
    assert abandoned.status_code == 200

    responses = [
        client.post(f'/chapters/{chapter_id}/outline', headers=auth(token), json={}),
        client.post(f'/chapters/{chapter_id}/write', headers=auth(token), json={}),
        client.post(f'/chapters/{chapter_id}/critique', headers=auth(token), json={}),
    ]

    for response in responses:
        assert response.status_code == 409
        assert response.json()['detail'] == 'CHAPTER_ABANDONED'
    assert llm_client.outline_calls == 0
    assert llm_client.generation_calls == 0
    assert llm_client.critique_calls == 0
    db_session.expire_all()
    chapter = db_session.get(Chapter, chapter_id)
    assert chapter.status == 'abandoned'
    assert chapter.outline_beats == []
    assert db_session.query(ChapterDraft).filter_by(chapter_id=chapter_id).count() == 0
    assert db_session.get(World, world_id).world_version == 1


def test_outline_rejects_extra_body_fields_without_side_effects(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    chapter_id = create_chapter(client, token, world_id).json()['id']
    llm_client = CountingPipelineLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm_client)
    before_events = db_session.scalar(select(func.count()).select_from(EventLog))
    before_world_version = db_session.get(World, world_id).world_version

    response = client.post(
        f'/chapters/{chapter_id}/outline',
        headers=auth(token),
        json={'chapter_context': '强调沈微霜的迟疑。', 'raw_text': 'outline endpoint must not accept runtime source text'},
    )

    assert response.status_code == 422
    assert any(
        error['type'] == 'extra_forbidden' and error['loc'] == ['body', 'raw_text']
        for error in response.json()['detail']
    )
    assert llm_client.outline_calls == 0
    db_session.expire_all()
    world = db_session.get(World, world_id)
    chapter = db_session.get(Chapter, chapter_id)
    assert world.world_version == before_world_version
    assert chapter.status == 'drafting'
    assert chapter.outline_beats == []
    assert chapter.outline_context == {}
    assert db_session.scalar(select(func.count()).select_from(EventLog)) == before_events


def test_write_requires_outline_for_pipeline_endpoint(client):
    token, world_id = register_and_create_world(client)
    chapter_id = create_chapter(client, token, world_id).json()['id']

    response = client.post(f'/chapters/{chapter_id}/write', headers=auth(token), json={})

    assert response.status_code == 409
    assert response.json()['detail'] == 'OUTLINE_REQUIRED'


def test_write_rejects_extra_body_fields_without_side_effects(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    chapter_id = create_chapter(client, token, world_id).json()['id']
    llm_client = CountingPipelineLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm_client)
    outline_response = client.post(f'/chapters/{chapter_id}/outline', headers=auth(token), json={})
    assert outline_response.status_code == 200
    assert llm_client.outline_calls == 1
    before_events = db_session.scalar(select(func.count()).select_from(EventLog))
    before_world_version = db_session.get(World, world_id).world_version
    before_drafts = db_session.scalar(
        select(func.count()).select_from(ChapterDraft).where(ChapterDraft.chapter_id == chapter_id)
    )
    existing_outline = db_session.get(Chapter, chapter_id).outline_beats

    response = client.post(
        f'/chapters/{chapter_id}/write',
        headers=auth(token),
        json={'outline_beats': existing_outline, 'raw_text': 'write endpoint must not accept runtime source text'},
    )

    assert response.status_code == 422
    assert any(
        error['type'] == 'extra_forbidden' and error['loc'] == ['body', 'raw_text']
        for error in response.json()['detail']
    )
    assert llm_client.generation_calls == 0
    db_session.expire_all()
    world = db_session.get(World, world_id)
    chapter = db_session.get(Chapter, chapter_id)
    after_drafts = db_session.scalar(
        select(func.count()).select_from(ChapterDraft).where(ChapterDraft.chapter_id == chapter_id)
    )
    assert world.world_version == before_world_version
    assert chapter.status == 'outlined'
    assert after_drafts == before_drafts
    assert db_session.scalar(select(func.count()).select_from(EventLog)) == before_events


def test_write_uses_edited_beats_and_creates_draft(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    chapter_id = create_chapter(client, token, world_id).json()['id']
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: PipelineLLMClient())
    client.post(f'/chapters/{chapter_id}/outline', headers=auth(token), json={})
    edited_beats = [
        {
            'beat_id': 'beat-1',
            'summary': '编辑后的节拍：林砚直接逼问沈微霜。',
            'pov_character': '林砚',
            'location': '废弃灵井',
            'emotional_arc': '怀疑 -> 施压',
            'key_dialogue_hints': ['你到底隐瞒了什么？'],
        }
    ]

    response = client.post(f'/chapters/{chapter_id}/write', headers=auth(token), json={'outline_beats': edited_beats})

    assert response.status_code == 200
    payload = response.json()
    assert payload['content'] == '编辑后的节拍被采用：林砚直接逼问沈微霜。'
    assert payload['outline_beats'][0]['summary'] == '编辑后的节拍：林砚直接逼问沈微霜。'
    chapter = db_session.get(Chapter, chapter_id)
    draft = db_session.query(ChapterDraft).filter_by(chapter_id=chapter_id).one()
    assert chapter.status == 'reviewing'
    assert chapter.outline_beats[0]['summary'] == '编辑后的节拍：林砚直接逼问沈微霜。'
    assert draft.source_world_version == 1


def test_late_write_cannot_overwrite_approved_chapter(client, db_session, opening_approval_payload):
    token, world_id = register_and_create_world(client)
    chapter_id = create_chapter(client, token, world_id).json()['id']
    user = db_session.get(World, world_id).owner
    narrative_service.generate_chapter_outline(db_session, user, chapter_id, llm_client=PipelineLLMClient())
    original = narrative_service.write_chapter_from_outline(db_session, user, chapter_id, llm_client=PipelineLLMClient())

    class ApprovingWriteLLM(PipelineLLMClient):
        def generate_chapter(self, messages):
            approved = narrative_service.approve_chapter(
                db_session,
                user,
                chapter_id,
                ApproveRequest.model_validate(opening_approval_payload({'chapter_id': chapter_id})),
            )
            assert approved.status == 'approved'
            return late_generation()

    try:
        narrative_service.write_chapter_from_outline(db_session, user, chapter_id, llm_client=ApprovingWriteLLM())
    except Exception as error:
        assert getattr(error, 'status_code', None) == 409
        assert getattr(error, 'detail', None) == 'ALREADY_APPROVED'
    else:
        raise AssertionError('expected ALREADY_APPROVED')

    db_session.expire_all()
    chapter = db_session.get(Chapter, chapter_id)
    drafts = list(db_session.scalars(select(ChapterDraft).where(ChapterDraft.chapter_id == chapter_id)))
    assert chapter.status == 'approved'
    assert chapter.title == original['title']
    assert chapter.approved_content == original['content']
    assert len(drafts) == 1
    assert drafts[0].content == original['content']
    assert drafts[0].content != late_generation().draft_content
    assert db_session.get(World, world_id).world_version == 2
    assert db_session.query(EventLog).filter_by(world_id=world_id, event_type='chapter_approved').count() == 1


def test_late_write_rejects_world_version_change_without_creating_draft(client, db_session):
    token, world_id = register_and_create_world(client)
    chapter_id = create_chapter(client, token, world_id).json()['id']
    user = db_session.get(World, world_id).owner
    narrative_service.generate_chapter_outline(db_session, user, chapter_id, llm_client=PipelineLLMClient())
    before_events = db_session.query(EventLog).filter_by(world_id=world_id).count()
    original_title = db_session.get(Chapter, chapter_id).title

    class AdvancingWorldWriteLLM(PipelineLLMClient):
        def generate_chapter(self, messages):
            world = db_session.get(World, world_id)
            world.world_version += 1
            db_session.commit()
            return late_generation()

    try:
        narrative_service.write_chapter_from_outline(db_session, user, chapter_id, llm_client=AdvancingWorldWriteLLM())
    except Exception as error:
        assert getattr(error, 'status_code', None) == 409
        assert getattr(error, 'detail', None) == 'WORLD_VERSION_MISMATCH'
    else:
        raise AssertionError('expected WORLD_VERSION_MISMATCH')

    db_session.expire_all()
    chapter = db_session.get(Chapter, chapter_id)
    assert chapter.status == 'outlined'
    assert chapter.title == original_title
    assert db_session.query(ChapterDraft).filter_by(chapter_id=chapter_id).count() == 0
    assert db_session.get(World, world_id).world_version == 2
    assert db_session.query(EventLog).filter_by(world_id=world_id).count() == before_events


def test_late_write_rejects_status_change_without_persisting_edited_beats(client, db_session):
    token, world_id = register_and_create_world(client)
    chapter_id = create_chapter(client, token, world_id).json()['id']
    user = db_session.get(World, world_id).owner
    narrative_service.generate_chapter_outline(db_session, user, chapter_id, llm_client=PipelineLLMClient())
    original_beats = list(db_session.get(Chapter, chapter_id).outline_beats)
    edited_beats = [
        BeatCard(
            beat_id='late-edit',
            summary='这组编辑节拍在冲突时不得提前提交。',
            pov_character='林砚',
            location='暗井',
            emotional_arc='警惕 -> 决断',
            key_dialogue_hints=['不能提前提交。'],
        )
    ]

    class RejectingWriteLLM(PipelineLLMClient):
        def generate_chapter(self, messages):
            chapter = db_session.get(Chapter, chapter_id)
            chapter.status = 'rejected'
            db_session.commit()
            return late_generation()

    try:
        narrative_service.write_chapter_from_outline(
            db_session,
            user,
            chapter_id,
            outline_beats=edited_beats,
            llm_client=RejectingWriteLLM(),
        )
    except Exception as error:
        assert getattr(error, 'status_code', None) == 409
        assert getattr(error, 'detail', None) == 'CHAPTER_STATUS_MISMATCH'
    else:
        raise AssertionError('expected CHAPTER_STATUS_MISMATCH')

    db_session.expire_all()
    chapter = db_session.get(Chapter, chapter_id)
    assert chapter.status == 'rejected'
    assert chapter.outline_beats == original_beats
    assert chapter.outline_beats != [beat.model_dump() for beat in edited_beats]
    assert db_session.query(ChapterDraft).filter_by(chapter_id=chapter_id).count() == 0
    assert db_session.get(World, world_id).world_version == 1


def test_write_rolls_back_after_revalidated_model_ids_become_invalid(client, db_session):
    token, world_id = register_and_create_world(client)
    chapter_id = create_chapter(client, token, world_id).json()['id']
    user = db_session.get(World, world_id).owner
    narrative_service.generate_chapter_outline(db_session, user, chapter_id, llm_client=PipelineLLMClient())
    original_beats = list(db_session.get(Chapter, chapter_id).outline_beats)
    edited_beats = [
        BeatCard(
            beat_id='invalid-id-edit',
            summary='二次 ID 校验失败时不得提交。',
            pov_character='林砚',
            location='暗井',
            emotional_arc='迟疑 -> 停止',
            key_dialogue_hints=['停止写入。'],
        )
    ]

    class RemovingCharacterWriteLLM(PipelineLLMClient):
        def generate_chapter(self, messages):
            generation = late_generation()
            character = db_session.get(Character, 1)
            db_session.delete(character)
            db_session.commit()
            return generation

    try:
        narrative_service.write_chapter_from_outline(
            db_session,
            user,
            chapter_id,
            outline_beats=edited_beats,
            llm_client=RemovingCharacterWriteLLM(),
        )
    except Exception as error:
        assert getattr(error, 'status_code', None) == 502
        assert getattr(error, 'detail', None) == 'MODEL_RESPONSE_INVALID'
    else:
        raise AssertionError('expected MODEL_RESPONSE_INVALID')

    chapter = db_session.get(Chapter, chapter_id)
    assert chapter.status == 'outlined'
    assert chapter.outline_beats == original_beats
    assert db_session.query(ChapterDraft).filter_by(chapter_id=chapter_id).count() == 0
    assert db_session.get(World, world_id).world_version == 1


def test_late_first_write_cannot_overwrite_competing_draft(client, db_session):
    token, world_id = register_and_create_world(client)
    chapter_id = create_chapter(client, token, world_id).json()['id']
    user = db_session.get(World, world_id).owner
    narrative_service.generate_chapter_outline(db_session, user, chapter_id, llm_client=PipelineLLMClient())
    concurrent_content = '另一请求已经完成的正文。'

    class CompetingDraftWriteLLM(PipelineLLMClient):
        def generate_chapter(self, messages):
            chapter = db_session.get(Chapter, chapter_id)
            db_session.add(
                ChapterDraft(
                    chapter_id=chapter_id,
                    draft_version=chapter.draft_version,
                    content=concurrent_content,
                    context_summary='并发请求摘要。',
                    review_hints=[],
                    proposed_changes={},
                    source_world_version=1,
                    execution_context=chapter.execution_context,
                )
            )
            db_session.commit()
            return late_generation()

    try:
        narrative_service.write_chapter_from_outline(db_session, user, chapter_id, llm_client=CompetingDraftWriteLLM())
    except Exception as error:
        assert getattr(error, 'status_code', None) == 409
        assert getattr(error, 'detail', None) == 'DRAFT_VERSION_MISMATCH'
    else:
        raise AssertionError('expected DRAFT_VERSION_MISMATCH')

    db_session.expire_all()
    chapter = db_session.get(Chapter, chapter_id)
    drafts = list(db_session.scalars(select(ChapterDraft).where(ChapterDraft.chapter_id == chapter_id)))
    assert chapter.status == 'outlined'
    assert chapter.title == '第一章 暗井回声'
    assert len(drafts) == 1
    assert drafts[0].content == concurrent_content
    assert drafts[0].content != late_generation().draft_content
    assert db_session.get(World, world_id).world_version == 1


def test_late_rewrite_cannot_overwrite_stashed_draft(client, db_session):
    token, world_id = register_and_create_world(client)
    chapter_id = create_chapter(client, token, world_id).json()['id']
    user = db_session.get(World, world_id).owner
    narrative_service.generate_chapter_outline(db_session, user, chapter_id, llm_client=PipelineLLMClient())
    original = narrative_service.write_chapter_from_outline(db_session, user, chapter_id, llm_client=PipelineLLMClient())

    class StashingWriteLLM(PipelineLLMClient):
        def generate_chapter(self, messages):
            stashed = narrative_service.stash_chapter_draft(db_session, user, chapter_id, '正文生成期间暂存')
            assert stashed['draft_version'] == 2
            return late_generation()

    try:
        narrative_service.write_chapter_from_outline(db_session, user, chapter_id, llm_client=StashingWriteLLM())
    except Exception as error:
        assert getattr(error, 'status_code', None) == 409
        assert getattr(error, 'detail', None) == 'DRAFT_VERSION_MISMATCH'
    else:
        raise AssertionError('expected DRAFT_VERSION_MISMATCH')

    db_session.expire_all()
    chapter = db_session.get(Chapter, chapter_id)
    drafts = list(
        db_session.scalars(
            select(ChapterDraft).where(ChapterDraft.chapter_id == chapter_id).order_by(ChapterDraft.draft_version)
        )
    )
    assert chapter.status == 'reviewing'
    assert chapter.draft_version == 2
    assert chapter.title == original['title']
    assert [draft.draft_version for draft in drafts] == [1, 2]
    assert drafts[0].content == drafts[1].content == original['content']
    assert all(draft.content != late_generation().draft_content for draft in drafts)
    assert db_session.get(World, world_id).world_version == 1


def test_critique_requires_draft_and_persists_report(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    chapter_id = create_chapter(client, token, world_id).json()['id']
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: PipelineLLMClient())

    missing_draft = client.post(f'/chapters/{chapter_id}/critique', headers=auth(token), json={})
    client.post(f'/chapters/{chapter_id}/outline', headers=auth(token), json={})
    client.post(f'/chapters/{chapter_id}/write', headers=auth(token), json={})
    response = client.post(f'/chapters/{chapter_id}/critique', headers=auth(token), json={})

    assert missing_draft.status_code == 409
    assert missing_draft.json()['detail'] == 'DRAFT_REQUIRED'
    assert response.status_code == 200
    payload = response.json()
    assert payload['critique_report']['score'] == 86
    assert payload['critique_report']['issues'][0]['category'] == 'character_voice'
    chapter = db_session.get(Chapter, chapter_id)
    assert chapter.critique_report['consistency_check']['world_rule_adherence'] == 'pass'


def test_critique_rejects_extra_body_fields_without_side_effects(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    chapter_id = create_chapter(client, token, world_id).json()['id']
    llm_client = CountingPipelineLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm_client)
    client.post(f'/chapters/{chapter_id}/outline', headers=auth(token), json={})
    client.post(f'/chapters/{chapter_id}/write', headers=auth(token), json={})
    assert llm_client.critique_calls == 0

    response = client.post(
        f'/chapters/{chapter_id}/critique',
        headers=auth(token),
        json={'raw_text': 'critique endpoint must not accept runtime source text'},
    )

    assert response.status_code == 422
    assert any(error['type'] == 'extra_forbidden' and error['loc'] == ['body', 'raw_text'] for error in response.json()['detail'])
    assert llm_client.critique_calls == 0
    db_session.expire_all()
    world = db_session.get(World, world_id)
    chapter = db_session.get(Chapter, chapter_id)
    event_types = list(db_session.scalars(select(EventLog.event_type).where(EventLog.world_id == world_id).order_by(EventLog.id)))
    assert world.world_version == 1
    assert chapter.critique_report == {}
    assert event_types == ['WORLD_CREATED']


def test_archived_world_rejects_pipeline_mutations(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    chapter_id = create_chapter(client, token, world_id).json()['id']
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: PipelineLLMClient())
    setup_outline = client.post(f'/chapters/{chapter_id}/outline', headers=auth(token), json={})
    assert setup_outline.status_code == 200

    archive_response = client.patch(f'/worlds/{world_id}/status', headers=auth(token), json={'status': 'archived'})
    assert archive_response.status_code == 200

    outline_response = client.post(f'/chapters/{chapter_id}/outline', headers=auth(token), json={})
    write_response = client.post(f'/chapters/{chapter_id}/write', headers=auth(token), json={})
    critique_response = client.post(f'/chapters/{chapter_id}/critique', headers=auth(token), json={})

    assert outline_response.status_code == 409
    assert outline_response.json()['detail'] == 'WORLD_ARCHIVED'
    assert write_response.status_code == 409
    assert write_response.json()['detail'] == 'WORLD_ARCHIVED'
    assert critique_response.status_code == 409
    assert critique_response.json()['detail'] == 'WORLD_ARCHIVED'

    db_session.expire_all()
    world = db_session.get(World, world_id)
    chapter = db_session.get(Chapter, chapter_id)
    draft_count = db_session.scalar(select(func.count()).select_from(ChapterDraft).where(ChapterDraft.chapter_id == chapter_id))
    assert world.world_version == 1
    assert chapter.status == 'outlined'
    assert draft_count == 0


def test_pipeline_approve_preserves_existing_world_update_invariant(client, monkeypatch, opening_approval_payload):
    token, world_id = register_and_create_world(client)
    chapter_id = create_chapter(client, token, world_id).json()['id']
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: PipelineLLMClient())

    client.post(f'/chapters/{chapter_id}/outline', headers=auth(token), json={})
    draft = client.post(f'/chapters/{chapter_id}/write', headers=auth(token), json={}).json()
    client.post(f'/chapters/{chapter_id}/critique', headers=auth(token), json={})
    before = client.get(f'/worlds/{world_id}/overview', headers=auth(token)).json()
    approve_response = client.post(
        f'/chapters/{chapter_id}/approve',
        headers=auth(token),
        json=opening_approval_payload({'chapter_id': chapter_id, **draft}),
    )
    after = client.get(f'/worlds/{world_id}/overview', headers=auth(token)).json()

    assert before['world_version'] == 1
    assert before['characters'][0]['current_goals'] == ['调查青岚城灵脉衰退']
    assert approve_response.status_code == 200
    assert after['world_version'] == 2
    assert after['characters'][0]['current_goals'] == ['追查城主府叛乱']
    assert after['foreshadows'][0]['status'] == 'advanced'
    assert after['recent_events'][0]['event_type'] == 'chapter_approved'


def test_pipeline_access_is_limited_to_owner(client, monkeypatch):
    owner_token, world_id = register_and_create_world(client)
    other_token = register(client, 'other@example.com')
    chapter_id = create_chapter(client, owner_token, world_id).json()['id']
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: PipelineLLMClient())

    outline = client.post(f'/chapters/{chapter_id}/outline', headers=auth(other_token), json={})
    write = client.post(f'/chapters/{chapter_id}/write', headers=auth(other_token), json={})
    critique = client.post(f'/chapters/{chapter_id}/critique', headers=auth(other_token), json={})

    assert outline.status_code == 403
    assert outline.json()['detail'] == 'FORBIDDEN'
    assert write.status_code == 403
    assert write.json()['detail'] == 'FORBIDDEN'
    assert critique.status_code == 403
    assert critique.json()['detail'] == 'FORBIDDEN'
