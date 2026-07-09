from sqlalchemy import func, select

from app.event.models import EventLog
from app.llm.schemas import (
    BeatCard,
    ChapterGeneration,
    ChapterOutline,
    CritiqueIssue,
    CritiqueReport,
    ProposedCharacterChange,
    ProposedForeshadowChange,
)
from app.narrative import service as narrative_service
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
    )


def fake_generation() -> ChapterGeneration:
    return ChapterGeneration(
        title='第一章 暗井回声',
        draft_content='林砚在暗井旁听见了第二个人的脚步声。沈微霜说：你不该来这里。',
        context_summary='林砚调查灵脉衰退，裂纹玉佩与暗井产生共振。',
        review_hints=['确认沈微霜动机是否一致', '确认玉佩伏笔是否推进'],
        proposed_character_changes=[ProposedCharacterChange(character_id=1, current_goals=['追查城主府叛乱'])],
        proposed_foreshadow_changes=[
            ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='玉佩线索被推进')
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
    assert any(error['type'] == 'extra_forbidden' and error['loc'][-1] == 'raw_text' for error in response.json()['detail'])
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


def test_pipeline_approve_preserves_existing_world_update_invariant(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    chapter_id = create_chapter(client, token, world_id).json()['id']
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: PipelineLLMClient())

    client.post(f'/chapters/{chapter_id}/outline', headers=auth(token), json={})
    client.post(f'/chapters/{chapter_id}/write', headers=auth(token), json={})
    client.post(f'/chapters/{chapter_id}/critique', headers=auth(token), json={})
    before = client.get(f'/worlds/{world_id}/overview', headers=auth(token)).json()
    approve_response = client.post(f'/chapters/{chapter_id}/approve', headers=auth(token))
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
