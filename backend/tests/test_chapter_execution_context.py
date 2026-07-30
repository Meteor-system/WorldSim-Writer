from sqlalchemy import func, inspect, select
from sqlalchemy.dialects import postgresql

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
from app.narrative.models import Chapter, ChapterDraft
from app.narrative.schemas import CreateChapterRequest, DraftRequest
from app.world.models import World


def sample_execution_context(goal='林砚带着湿信赴城主府外墙，并设置一次试探。', source_world_version: int = 1):
    return {
        'source': 'next_chapter_prep',
        'source_world_version': source_world_version,
        'next_chapter_number': 2,
        'goal': goal,
        'recommended_pov': {'character_id': 1, 'name': '林砚'},
        'source_signals': ['character_arc_progression_hint'],
        'priority_characters': [
            {
                'character_id': 1,
                'name': '林砚',
                'role_type': 'protagonist',
                'status': '开始调查密信',
                'reason': '上一章提示。',
            }
        ],
        'priority_foreshadows': [
            {
                'foreshadow_id': 1,
                'title': '裂纹玉佩',
                'status': 'advanced',
                'urgency_level': 4,
                'reason': '该伏笔需要推进。',
            }
        ],
        'progression_hints': [
            {
                'hint_type': 'character',
                'priority': 'high',
                'title': '试探沈微霜是否可信',
                'rationale': '上一章已经建立湿信线索。',
                'suggested_next_beat': goal,
                'related_character_ids': [1],
                'related_foreshadow_ids': [1],
                'can_seed_next_chapter_goal': True,
            }
        ],
        'continuity_warnings': [
            {
                'severity': 'medium',
                'category': 'character_arc',
                'message': '下一章需要补足试探过程。',
                'related_character_ids': [1],
                'related_foreshadow_ids': [],
            }
        ],
        'recent_events': [
            {
                'id': 4,
                'event_type': 'chapter_approved',
                'world_version_before': 1,
                'world_version_after': 2,
                'created_at': '2026-05-30T00:00:00Z',
            }
        ],
    }


def test_execution_context_columns_exist(db_session):
    inspector = inspect(db_session.get_bind())
    chapter_columns = {column['name'] for column in inspector.get_columns('chapters')}
    draft_columns = {column['name'] for column in inspector.get_columns('chapter_drafts')}

    assert 'execution_context' in chapter_columns
    assert 'execution_context' in draft_columns
    assert hasattr(Chapter, 'execution_context')
    assert hasattr(ChapterDraft, 'execution_context')


def test_create_and_draft_requests_accept_execution_context():
    context = sample_execution_context()

    create_payload = CreateChapterRequest(chapter_goal=context['goal'], execution_context=context)
    draft_payload = DraftRequest(chapter_goal=context['goal'], execution_context=context)

    assert create_payload.execution_context is not None
    assert create_payload.execution_context.recommended_pov.name == '林砚'
    assert draft_payload.execution_context is not None
    assert draft_payload.execution_context.priority_foreshadows[0].title == '裂纹玉佩'


class CapturingLLMClient:
    def __init__(self):
        self.messages = []
        self.outline_messages = []
        self.calls = []

    def generate_outline(self, messages):
        self.outline_messages.append(messages)
        self.calls.append('outline')
        return ChapterOutline(
            beats=[
                BeatCard(
                    beat_id='opening-1',
                    summary='林砚在雨夜的废弃灵井发现裂纹玉佩异动。',
                    pov_character='林砚',
                    location='青岚城后巷',
                    emotional_arc='焦灼到警觉',
                    key_dialogue_hints=['师妹还在等药。'],
                )
            ],
            core_conflict='林砚必须在巡夜人抵达前确认裂纹玉佩的主人。',
            pov_suggestion='林砚',
            pacing='雨夜悬疑，逐段增加巡夜压力。',
            role_skill_targets=['林砚', '沈微霜'],
            opening_contract=OpeningContract(
                background='青岚城灵脉衰退，废弃灵井在雨夜发出异响。',
                protagonist_identity='林砚是为师门债务奔走的外门弟子。',
                motivation='他必须查清裂纹玉佩为何牵连师门，避免师妹被城主府带走。',
                personality_evidence_plan='让林砚先救下被雨水冲走的药箱，再隐瞒手伤继续追查。',
                conflict_goal='在城主府巡夜人发现前，确认暗井中的玉佩是否属于失踪师兄。',
                locked_pov='林砚限知第三人称。',
            ),
        )

    def generate_chapter(self, messages):
        self.messages.append(messages)
        self.calls.append('writer')
        draft_content = '\n\n'.join(
            [
                '雨水压低了青岚城的屋檐，废弃灵井却在巷尾吐出温热白雾。林砚替师门送药归来，掌心的裂纹玉佩忽然发烫；城里人人都说灵脉衰退只是旱灾，他知道那是谎话。',
                '他是欠着师门药债的外门弟子，今夜原该回去照看师妹。可城主府的文书写明天亮前要带走她问话，林砚只能追查玉佩与失踪师兄的名字，哪怕这会把自己送进巡夜人的眼里。',
                '巷口的药箱被雨水冲翻，他先扑进泥水把药瓶一只只捡回，又把割裂的手藏进袖中。沈微霜问他为何不逃，林砚只说：师妹还在等药，这不是能算清的账。',
                '灵井底下传来铁链拖地声，玉佩映出师兄惯用的云纹。林砚没有告诉沈微霜自己看见了什么，只沿着井壁摸到一道新鲜的靴印，听见城主府巡夜人的铜铃越来越近。',
                '他必须在铜铃停在巷口前确认玉佩主人，否则师妹会被带走，师兄的失踪也会被埋进井里。林砚让沈微霜守住巷口，自己系紧绳索下井；他不确定她会不会出卖自己。',
                '林砚的靴底刚离开井沿，铜铃便在雨幕外停住。巡夜人喊出他的名字，他只能从井壁渗出的血色水痕判断，下面等着他的不是师兄，而是一场早已布好的局。',
            ]
        )
        return ChapterGeneration(
            title='第二章 城主府外墙',
            draft_content=draft_content,
            context_summary='本章执行城主府外墙试探。',
            review_hints=['确认沈微霜动机是否可信'],
            proposed_character_changes=[ProposedCharacterChange(character_id=1, current_goals=['试探沈微霜'])],
            proposed_foreshadow_changes=[
                ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='湿信线索继续推进')
            ],
            opening_evidence=[
                OpeningEvidence(check='background', paragraph_index=0, quote='废弃灵井却在巷尾吐出温热白雾'),
                OpeningEvidence(check='protagonist_identity', paragraph_index=1, quote='欠着师门药债的外门弟子'),
                OpeningEvidence(check='motivation', paragraph_index=1, quote='只能追查玉佩与失踪师兄的名字'),
                OpeningEvidence(check='personality_evidence_plan', paragraph_index=2, quote='先扑进泥水把药瓶一只只捡回'),
                OpeningEvidence(check='conflict_goal', paragraph_index=4, quote='必须在铜铃停在巷口前确认玉佩主人'),
                OpeningEvidence(check='locked_pov', paragraph_index=3, quote='林砚没有告诉沈微霜自己看见了什么'),
            ],
        )


def register_and_create_world(client, email='execution-context@example.com'):
    token = client.post('/auth/register', json={'email': email, 'password': 'strongpass123'}).json()['access_token']
    world = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {token}'}).json()
    return token, world['id']


def test_draft_request_rejects_root_extra_fields_without_side_effects(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'draft-root-extra@example.com')
    context = sample_execution_context()
    llm = CapturingLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    before_chapters = db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id))
    before_events = db_session.scalar(select(func.count()).select_from(EventLog))

    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={
            'chapter_goal': context['goal'],
            'execution_context': context,
            'raw_text': 'root raw text must be rejected',
            'internal_score': 0.9,
        },
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 422
    assert any(
        error['type'] == 'extra_forbidden' and error['loc'] == ['body', 'raw_text']
        for error in response.json()['detail']
    )
    assert llm.messages == []
    assert llm.outline_messages == []
    assert llm.calls == []
    assert db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id)) == before_chapters
    assert db_session.scalar(select(func.count()).select_from(EventLog)) == before_events


def test_create_chapter_request_rejects_root_extra_fields_without_side_effects(client, db_session):
    token, world_id = register_and_create_world(client, 'chapter-root-extra@example.com')
    context = sample_execution_context()
    before_chapters = db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id))
    before_events = db_session.scalar(select(func.count()).select_from(EventLog))

    response = client.post(
        f'/worlds/{world_id}/chapters',
        json={
            'chapter_goal': context['goal'],
            'title': '第二章 城主府外墙',
            'execution_context': context,
            'raw_text': 'root raw text must be rejected',
            'internal_score': 0.9,
        },
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 422
    assert any(
        error['type'] == 'extra_forbidden' and error['loc'] == ['body', 'raw_text']
        for error in response.json()['detail']
    )
    assert db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id)) == before_chapters
    assert db_session.scalar(select(func.count()).select_from(EventLog)) == before_events


def test_create_chapter_freezes_execution_context_without_mutating_world(client, db_session):
    token, world_id = register_and_create_world(client)
    context = sample_execution_context()
    before_events = db_session.scalar(select(func.count()).select_from(EventLog))

    response = client.post(
        f'/worlds/{world_id}/chapters',
        json={'chapter_goal': context['goal'], 'title': '第二章 城主府外墙', 'execution_context': context},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['execution_context']['source'] == 'next_chapter_prep'
    assert payload['execution_context']['recommended_pov']['name'] == '林砚'
    db_session.expire_all()
    chapter = db_session.get(Chapter, payload['id'])
    world = db_session.get(World, world_id)
    assert chapter.execution_context['goal'] == context['goal']
    assert world.world_version == 1
    assert db_session.scalar(select(func.count()).select_from(EventLog)) == before_events


def test_active_chapter_creation_lock_compiles_to_postgresql_for_update():
    sql = str(
        narrative_service._locked_world_query(7).compile(
            dialect=postgresql.dialect(),
            compile_kwargs={'literal_binds': True},
        )
    )

    assert 'WHERE worlds.id = 7' in sql
    assert 'FOR UPDATE' in sql
    assert narrative_service._locked_world_query(7).get_execution_options()['populate_existing'] is True


def test_chapter_model_write_lock_compiles_to_postgresql_for_update():
    sql = str(
        narrative_service._locked_chapter_query(11).compile(
            dialect=postgresql.dialect(),
            compile_kwargs={'literal_binds': True},
        )
    )

    assert 'WHERE chapters.id = 11' in sql
    assert 'FOR UPDATE' in sql
    assert narrative_service._locked_chapter_query(11).get_execution_options()['populate_existing'] is True


def test_generated_draft_rechecks_world_version_after_model_generation(client, db_session):
    token, world_id = register_and_create_world(client, 'draft-lock-version-recheck@example.com')
    headers = {'Authorization': f'Bearer {token}'}
    before_events = db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id))

    class AdvancingWorldLLM(CapturingLLMClient):
        def generate_chapter(self, messages):
            generation = super().generate_chapter(messages)
            world = db_session.get(World, world_id)
            world.world_version += 1
            db_session.commit()
            return generation

    response = narrative_service.create_chapter_draft
    try:
        response(
            db_session,
            db_session.get(World, world_id).owner,
            world_id,
            '模型生成期间世界被推进',
            llm_client=AdvancingWorldLLM(),
        )
    except Exception as error:
        assert getattr(error, 'status_code', None) == 409
        assert getattr(error, 'detail', None) == 'WORLD_VERSION_MISMATCH'
    else:
        raise AssertionError('expected WORLD_VERSION_MISMATCH')

    db_session.expire_all()
    assert db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id)) == 0
    assert db_session.scalar(
        select(func.count()).select_from(ChapterDraft).join(Chapter).where(Chapter.world_id == world_id)
    ) == 0
    assert db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id)) == before_events
    assert db_session.get(World, world_id).world_version == 2


def test_active_chapter_recovery_rejects_multiple_unapproved_chapters_without_side_effects(client, db_session):
    token, world_id = register_and_create_world(client, 'multiple-active-chapters@example.com')
    headers = {'Authorization': f'Bearer {token}'}
    first = client.post(
        f'/worlds/{world_id}/chapters',
        json={'chapter_goal': '第一个历史草稿', 'title': '第一个历史草稿'},
        headers=headers,
    )
    assert first.status_code == 200
    db_session.add(
        Chapter(
            world_id=world_id,
            title='第二个历史草稿',
            status='reviewing',
            draft_version=1,
            base_world_version=1,
            chapter_goal='第二个历史草稿',
            outline_beats=[],
            outline_context={},
            critique_report={},
            character_arc_report={},
            execution_context={},
        )
    )
    db_session.commit()
    before_chapters = db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id))
    before_drafts = db_session.scalar(
        select(func.count()).select_from(ChapterDraft).join(Chapter).where(Chapter.world_id == world_id)
    )
    before_events = db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id))
    before_world_version = db_session.get(World, world_id).world_version

    response = client.get(f'/worlds/{world_id}/chapters/active', headers=headers)

    assert response.status_code == 409
    assert response.json()['detail'] == 'MULTIPLE_ACTIVE_CHAPTERS'
    db_session.expire_all()
    assert db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id)) == before_chapters
    assert db_session.scalar(
        select(func.count()).select_from(ChapterDraft).join(Chapter).where(Chapter.world_id == world_id)
    ) == before_drafts
    assert db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id)) == before_events
    assert db_session.get(World, world_id).world_version == before_world_version


def test_active_chapter_guard_blocks_duplicate_create_paths_without_side_effects(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'active-chapter-guard@example.com')
    headers = {'Authorization': f'Bearer {token}'}
    first = client.post(
        f'/worlds/{world_id}/chapters',
        json={'chapter_goal': '保留当前章节', 'title': '第一章 保留当前章节'},
        headers=headers,
    )
    assert first.status_code == 200

    before_chapters = db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id))
    before_drafts = db_session.scalar(
        select(func.count()).select_from(ChapterDraft).join(Chapter).where(Chapter.world_id == world_id)
    )
    before_events = db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id))
    before_world_version = db_session.get(World, world_id).world_version
    llm = CapturingLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)

    duplicate_session = client.post(
        f'/worlds/{world_id}/chapters',
        json={'chapter_goal': '不应创建的第二章', 'title': '第二章'},
        headers=headers,
    )
    duplicate_draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '不应生成的第二章草稿'},
        headers=headers,
    )

    assert duplicate_session.status_code == 409
    assert duplicate_session.json()['detail'] == 'ACTIVE_CHAPTER_EXISTS'
    assert duplicate_draft.status_code == 409
    assert duplicate_draft.json()['detail'] == 'ACTIVE_CHAPTER_EXISTS'
    assert llm.messages == []
    assert llm.outline_messages == []
    assert llm.calls == []
    db_session.expire_all()
    assert db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id)) == before_chapters
    assert db_session.scalar(
        select(func.count()).select_from(ChapterDraft).join(Chapter).where(Chapter.world_id == world_id)
    ) == before_drafts
    assert db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id)) == before_events
    assert db_session.get(World, world_id).world_version == before_world_version


def test_active_chapter_guard_allows_one_unapproved_chapter_per_world(client, db_session):
    token, first_world_id = register_and_create_world(client, 'active-chapter-world-isolation@example.com')
    headers = {'Authorization': f'Bearer {token}'}
    second_world_id = client.post('/worlds/from-template', headers=headers).json()['id']

    first = client.post(
        f'/worlds/{first_world_id}/chapters',
        json={'chapter_goal': '第一个世界的进行中章节'},
        headers=headers,
    )
    second = client.post(
        f'/worlds/{second_world_id}/chapters',
        json={'chapter_goal': '第二个世界的进行中章节'},
        headers=headers,
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == first_world_id)) == 1
    assert db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == second_world_id)) == 1


def test_active_chapter_guard_allows_next_chapter_after_approval(client, db_session, monkeypatch, opening_approval_payload):
    token, world_id = register_and_create_world(client, 'active-chapter-after-approval@example.com')
    headers = {'Authorization': f'Bearer {token}'}
    llm = CapturingLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    first = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '完成并批准第一章'},
        headers=headers,
    )
    assert first.status_code == 200

    approved = client.post(
        f"/chapters/{first.json()['chapter_id']}/approve",
        json=opening_approval_payload(first.json()),
        headers=headers,
    )
    assert approved.status_code == 200
    assert approved.json()['status'] == 'approved'

    next_chapter = client.post(
        f'/worlds/{world_id}/chapters',
        json={'chapter_goal': '批准后创建下一章'},
        headers=headers,
    )
    assert next_chapter.status_code == 200
    db_session.expire_all()
    assert db_session.get(World, world_id).world_version == 2
    assert db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id)) == 2


def test_create_chapter_without_context_creates_manual_context(client, db_session):
    token, world_id = register_and_create_world(client, 'manual-execution-context@example.com')

    response = client.post(
        f'/worlds/{world_id}/chapters',
        json={'chapter_goal': '手动推进湿信线索', 'title': '手动推进湿信线索'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['execution_context']['source'] == 'manual'
    assert payload['execution_context']['goal'] == '手动推进湿信线索'
    assert payload['execution_context']['source_signals'] == ['manual']
    assert payload['execution_context']['source_world_version'] == 1


def test_create_chapter_rejects_stale_execution_context(client, db_session):
    token, world_id = register_and_create_world(client, 'stale-session-context@example.com')
    context = sample_execution_context(source_world_version=0)

    response = client.post(
        f'/worlds/{world_id}/chapters',
        json={'chapter_goal': context['goal'], 'title': '第二章 城主府外墙', 'execution_context': context},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 409
    assert response.json()['detail'] == 'WORLD_VERSION_MISMATCH'
    assert db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id)) == 0


def test_outline_and_writer_prompts_use_frozen_execution_context(client, db_session):
    token, world_id = register_and_create_world(client, 'prompt-context@example.com')
    context = sample_execution_context()
    chapter_response = client.post(
        f'/worlds/{world_id}/chapters',
        json={'chapter_goal': context['goal'], 'title': '第二章 城主府外墙', 'execution_context': context},
        headers={'Authorization': f'Bearer {token}'},
    )
    chapter_id = chapter_response.json()['id']
    world = db_session.get(World, world_id)
    chapter = db_session.get(Chapter, chapter_id)
    characters, foreshadows = narrative_service._load_world_context(db_session, world)

    outline_messages = narrative_service.build_outline_messages(
        world,
        characters,
        foreshadows,
        chapter.chapter_goal,
        execution_context=chapter.execution_context,
    )
    writer_messages = narrative_service.build_generation_messages(
        world,
        characters,
        foreshadows,
        chapter.chapter_goal,
        execution_context=chapter.execution_context,
    )

    outline_text = outline_messages[-1]['content']
    writer_text = writer_messages[-1]['content']
    assert '本章执行上下文' in outline_text
    assert '推荐 POV：林砚' in outline_text
    assert '试探沈微霜是否可信' in outline_text
    assert '本章执行上下文' in writer_text
    assert '优先满足执行上下文' in writer_text
    assert '裂纹玉佩' in writer_text


def test_write_chapter_copies_chapter_execution_context_to_draft(client, db_session, monkeypatch, opening_approval_payload):
    token, world_id = register_and_create_world(client, 'write-context@example.com')
    headers = {'Authorization': f'Bearer {token}'}
    monkeypatch.setenv('LLM_MOCK', 'true')
    narrative_service.get_settings.cache_clear()
    first = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '完成并批准第一章'},
        headers=headers,
    )
    assert first.status_code == 200, first.json()
    approved = client.post(
        f"/chapters/{first.json()['chapter_id']}/approve",
        json=opening_approval_payload(first.json()),
        headers=headers,
    )
    assert approved.status_code == 200

    context = sample_execution_context(source_world_version=2)
    chapter = client.post(
        f'/worlds/{world_id}/chapters',
        json={'chapter_goal': context['goal'], 'title': '第二章 城主府外墙', 'execution_context': context},
        headers=headers,
    ).json()
    assert chapter['execution_context']['next_chapter_number'] == 2
    db_chapter = db_session.get(Chapter, chapter['id'])
    db_chapter.outline_beats = [
        {
            'beat_id': 'beat-1',
            'summary': '林砚抵达城主府外墙。',
            'pov_character': '林砚',
            'location': '城主府外墙',
            'emotional_arc': '警惕到决断',
            'key_dialogue_hints': ['湿信从何而来？'],
        }
    ]
    db_session.commit()
    llm = CapturingLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)

    response = client.post(
        f"/chapters/{chapter['id']}/write",
        json={},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['execution_context']['recommended_pov']['name'] == '林砚'
    draft = db_session.scalar(select(ChapterDraft).where(ChapterDraft.chapter_id == chapter['id']))
    assert draft.execution_context['goal'] == context['goal']


def test_direct_draft_endpoint_accepts_execution_context(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'direct-context@example.com')
    context = sample_execution_context()
    llm = CapturingLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)

    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': context['goal'], 'execution_context': context},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['execution_context']['source'] == 'next_chapter_prep'
    chapter = db_session.get(Chapter, payload['chapter_id'])
    draft = db_session.get(ChapterDraft, payload['draft_id'])
    assert chapter.execution_context['goal'] == context['goal']
    assert draft.execution_context['priority_characters'][0]['name'] == '林砚'
    assert '本章执行上下文' in llm.messages[0][-1]['content']


def test_direct_draft_rejects_stale_execution_context_before_model_call(client, monkeypatch):
    token, world_id = register_and_create_world(client, 'stale-direct-context@example.com')
    context = sample_execution_context(source_world_version=0)
    llm = CapturingLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)

    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': context['goal'], 'execution_context': context},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 409
    assert response.json()['detail'] == 'WORLD_VERSION_MISMATCH'
    assert llm.messages == []
    assert llm.outline_messages == []
    assert llm.calls == []


def test_direct_draft_rejects_extra_execution_context_field_before_model_call(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'extra-root-direct-context@example.com')
    context = sample_execution_context()
    context['raw_text'] = '根对象额外字段不应进入章节执行上下文。'
    llm = CapturingLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    before_chapters = db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id))
    before_events = db_session.scalar(select(func.count()).select_from(EventLog))

    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': context['goal'], 'execution_context': context},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 422
    assert any(
        error['type'] == 'extra_forbidden'
        and error['loc'] == ['body', 'execution_context', 'raw_text']
        for error in response.json()['detail']
    )
    assert llm.messages == []
    assert llm.outline_messages == []
    assert llm.calls == []
    assert db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id)) == before_chapters
    assert db_session.scalar(select(func.count()).select_from(EventLog)) == before_events


def test_direct_draft_rejects_extra_nested_execution_context_field_before_model_call(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'extra-nested-direct-context@example.com')
    context = sample_execution_context()
    context['priority_characters'][0]['internal_score'] = 0.9
    llm = CapturingLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    before_chapters = db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id))
    before_events = db_session.scalar(select(func.count()).select_from(EventLog))

    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': context['goal'], 'execution_context': context},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 422
    assert any(
        error['type'] == 'extra_forbidden'
        and error['loc'] == ['body', 'execution_context', 'priority_characters', 0, 'internal_score']
        for error in response.json()['detail']
    )
    assert llm.messages == []
    assert llm.outline_messages == []
    assert llm.calls == []
    assert db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id)) == before_chapters
    assert db_session.scalar(select(func.count()).select_from(EventLog)) == before_events


def test_direct_draft_rejects_raw_text_material_reference_before_model_call(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'raw-material-direct-context@example.com')
    context = sample_execution_context()
    context['material_references'] = [
        {
            'asset_id': 7,
            'batch_id': 3,
            'asset_pool': 'inspiration',
            'title': '雾港钟楼候选素材',
            'summary': '钟楼倒敲十三次后，城内记忆出现错位。',
            'raw_text': '原文不应进入章节执行上下文素材引用。',
            'source_title': '导入片段',
            'source_type': 'pasted_text',
            'created_at': '2026-05-30T00:00:00Z',
            'safety_note': '导入素材参考只用于创作提示，不会自动改写正式 canon。',
        }
    ]
    llm = CapturingLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    before_chapters = db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id))
    before_events = db_session.scalar(select(func.count()).select_from(EventLog))

    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': context['goal'], 'execution_context': context},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 422
    assert any(
        error['type'] == 'extra_forbidden'
        and error['loc'] == ['body', 'execution_context', 'material_references', 0, 'raw_text']
        for error in response.json()['detail']
    )
    assert llm.messages == []
    assert llm.outline_messages == []
    assert llm.calls == []
    assert db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id)) == before_chapters
    assert db_session.scalar(select(func.count()).select_from(EventLog)) == before_events


def test_direct_draft_rejects_raw_text_style_reference_before_model_call(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'raw-style-direct-context@example.com')
    context = sample_execution_context()
    context['style_handbook_reference'] = {
        'source_title': '参考片段',
        'source_rights': 'general_reference',
        'handbook': {
            'narrative_pacing': {
                'label': '叙事节奏',
                'value': '中速推进。',
                'raw_text': '原文不应进入章节执行上下文风格引用。',
            },
            'language_density': {'label': '语言密度', 'value': '中等语言密度。'},
            'dialogue_ratio': {'label': '对白比例', 'value': '对白与叙述交替。'},
            'scene_progression': {'label': '场景推进', 'value': '用意象带动转场。'},
            'suspense_structure': {'label': '悬念结构', 'value': '每节保留待解问题。'},
            'relationship_tension': {'label': '人物关系张力', 'value': '围绕亏欠推进。'},
            'foreshadowing_pattern': {'label': '伏笔埋设/回收方式', 'value': '先给异常，再延迟解释。'},
            'do_guidelines': ['保留抽象节奏。'],
            'avoid_guidelines': ['不要复用原文句子、人物名、专有设定或标志性桥段。'],
            'originality_guidelines': ['正式章节仍需 Studio 审稿。'],
        },
        'safety_notes': ['风格手册只是写作参考，不写入 canon。'],
    }
    llm = CapturingLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    before_chapters = db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id))
    before_events = db_session.scalar(select(func.count()).select_from(EventLog))

    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': context['goal'], 'execution_context': context},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 422
    assert any(
        error['type'] == 'extra_forbidden'
        and error['loc'] == [
            'body',
            'execution_context',
            'style_handbook_reference',
            'handbook',
            'narrative_pacing',
            'raw_text',
        ]
        for error in response.json()['detail']
    )
    assert llm.messages == []
    assert llm.outline_messages == []
    assert llm.calls == []
    assert db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id)) == before_chapters
    assert db_session.scalar(select(func.count()).select_from(EventLog)) == before_events


def test_approval_requests_reject_extra_body_fields_without_side_effects(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'approval-extra@example.com')
    llm = CapturingLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '批准前额外字段应被拦截。'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    chapter = db_session.get(Chapter, draft['chapter_id'])
    world = db_session.get(World, world_id)
    before_chapter_status = chapter.status
    before_approved_content = chapter.approved_content
    before_approved_version = chapter.approved_version
    before_world_version = world.world_version
    before_events = db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id))

    cases = [
        (
            f"/chapters/{draft['chapter_id']}/approval-consistency",
            {'draft_version': draft['draft_version'], 'raw_text': 'approval consistency raw payload'},
        ),
        (
            f"/chapters/{draft['chapter_id']}/approve",
            {'draft_version': draft['draft_version'], 'raw_text': 'approval raw payload'},
        ),
    ]

    for url, payload in cases:
        response = client.post(url, json=payload, headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 422
        assert any(
            error['type'] == 'extra_forbidden' and error['loc'] == ['body', 'raw_text']
            for error in response.json()['detail']
        )

        db_session.expire_all()
        chapter = db_session.get(Chapter, draft['chapter_id'])
        world = db_session.get(World, world_id)
        assert chapter.status == before_chapter_status
        assert chapter.approved_content == before_approved_content
        assert chapter.approved_version == before_approved_version
        assert world.world_version == before_world_version
        assert db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id)) == before_events


def test_chapter_history_detail_exposes_execution_context(client, monkeypatch, opening_approval_payload):
    token, world_id = register_and_create_world(client, 'history-context@example.com')
    context = sample_execution_context()
    llm = CapturingLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': context['goal'], 'execution_context': context},
        headers={'Authorization': f'Bearer {token}'},
    ).json()
    approve = client.post(
        f"/chapters/{draft['chapter_id']}/approve",
        json=opening_approval_payload(draft),
        headers={'Authorization': f'Bearer {token}'},
    )
    assert approve.status_code == 200

    response = client.get(f"/chapters/{draft['chapter_id']}/history", headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    payload = response.json()
    assert payload['execution_context']['source'] == 'next_chapter_prep'
    assert payload['execution_context']['goal'] == context['goal']
