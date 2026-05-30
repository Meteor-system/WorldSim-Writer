from sqlalchemy import func, inspect, select

from app.event.models import EventLog
from app.llm.schemas import ChapterGeneration, ProposedCharacterChange, ProposedForeshadowChange
from app.narrative import service as narrative_service
from app.narrative.models import Chapter, ChapterDraft
from app.narrative.schemas import CreateChapterRequest, DraftRequest
from app.world.models import World


def sample_execution_context(goal='林砚带着湿信赴城主府外墙，并设置一次试探。'):
    return {
        'source': 'next_chapter_prep',
        'source_world_version': 2,
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

    def generate_chapter(self, messages):
        self.messages.append(messages)
        return ChapterGeneration(
            title='第二章 城主府外墙',
            draft_content='林砚抵达城主府外墙，借湿信试探沈微霜。',
            context_summary='本章执行城主府外墙试探。',
            review_hints=['确认沈微霜动机是否可信'],
            proposed_character_changes=[ProposedCharacterChange(character_id=1, current_goals=['试探沈微霜'])],
            proposed_foreshadow_changes=[
                ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='湿信线索继续推进')
            ],
        )


def register_and_create_world(client, email='execution-context@example.com'):
    token = client.post('/auth/register', json={'email': email, 'password': 'strongpass123'}).json()['access_token']
    world = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {token}'}).json()
    return token, world['id']


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


def test_write_chapter_copies_chapter_execution_context_to_draft(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'write-context@example.com')
    context = sample_execution_context()
    chapter = client.post(
        f'/worlds/{world_id}/chapters',
        json={'chapter_goal': context['goal'], 'title': '第二章 城主府外墙', 'execution_context': context},
        headers={'Authorization': f'Bearer {token}'},
    ).json()
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


def test_chapter_history_detail_exposes_execution_context(client, monkeypatch):
    token, world_id = register_and_create_world(client, 'history-context@example.com')
    context = sample_execution_context()
    llm = CapturingLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': context['goal'], 'execution_context': context},
        headers={'Authorization': f'Bearer {token}'},
    ).json()
    approve = client.post(f"/chapters/{draft['chapter_id']}/approve", headers={'Authorization': f'Bearer {token}'})
    assert approve.status_code == 200

    response = client.get(f"/chapters/{draft['chapter_id']}/history", headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    payload = response.json()
    assert payload['execution_context']['source'] == 'next_chapter_prep'
    assert payload['execution_context']['goal'] == context['goal']
