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


OPENING_CONTENT = '\n\n'.join(
    [
        '雨水压低了青岚城的屋檐，废弃灵井在巷尾吐出温热白雾。林砚替师门送药归来，掌心玉佩忽然发烫；城里人人都说灵脉衰退只是旱灾，他知道那是谎话。',
        '他是欠着师门药债的外门弟子，今夜原该回去照看师妹。可城主府的文书写明天亮前要带走她问话，林砚只能追查玉佩与失踪师兄的名字。',
        '巷口的药箱被雨水冲翻，他先扑进泥水把药瓶一只只捡回，又把割裂的手藏进袖中。沈微霜问他为何不逃，林砚只说师妹还在等药。',
        '灵井底下传来铁链拖地声，玉佩映出师兄惯用的云纹。林砚没有告诉沈微霜自己看见了什么，只沿着井壁摸到一道新鲜的靴印。',
        '他必须在铜铃停在巷口前确认玉佩主人，否则师妹会被带走，师兄的失踪也会被埋进井里。林砚让沈微霜守住巷口，自己系紧绳索下井。',
        '林砚的靴底刚离开井沿，铜铃便在雨幕外停住。巡夜人喊出他的名字，他只能从井壁渗出的血色水痕判断，下面等着他的不是师兄，而是一场早已布好的局。',
    ]
)


class NarrativeControlLLMClient:
    def generate_outline(self, _messages):
        return ChapterOutline(
            core_conflict='林砚必须在巡夜人抵达前确认玉佩主人的身份。',
            pov_suggestion='林砚',
            pacing='雨夜悬疑，逐段增加巡夜压力。',
            role_skill_targets=['林砚', '沈微霜'],
            beats=[
                BeatCard(
                    beat_id='opening-1',
                    summary='林砚在废弃灵井发现玉佩异动。',
                    pov_character='林砚',
                    location='青岚城后巷',
                    emotional_arc='焦灼 -> 警觉',
                    key_dialogue_hints=['师妹还在等药。'],
                )
            ],
            opening_contract=OpeningContract(
                background='青岚城灵脉衰退，废弃灵井在雨夜发出异响。',
                protagonist_identity='林砚是为师门债务奔走的外门弟子。',
                motivation='他必须查清玉佩为何牵连师门，避免师妹被城主府带走。',
                personality_evidence_plan='让林砚先救下药箱，再隐瞒手伤继续追查。',
                conflict_goal='在城主府巡夜人发现前，确认暗井中的玉佩是否属于失踪师兄。',
                locked_pov='林砚限知第三人称。',
            ),
        )

    def generate_chapter(self, _messages):
        return ChapterGeneration(
            title='第一章 雨巷密谈',
            draft_content=OPENING_CONTENT,
            context_summary='林砚与沈微霜在雨巷交换湿信线索。',
            review_hints=['确认沈微霜的动机是否可信'],
            proposed_character_changes=[
                ProposedCharacterChange(character_id=1, status='开始调查密信', current_goals=['追查湿信来源'])
            ],
            proposed_foreshadow_changes=[
                ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='湿信推进玉佩线索')
            ],
            opening_evidence=[
                OpeningEvidence(check='background', paragraph_index=0, quote='废弃灵井在巷尾吐出温热白雾'),
                OpeningEvidence(check='protagonist_identity', paragraph_index=1, quote='欠着师门药债的外门弟子'),
                OpeningEvidence(check='motivation', paragraph_index=1, quote='只能追查玉佩与失踪师兄的名字'),
                OpeningEvidence(check='personality_evidence_plan', paragraph_index=2, quote='先扑进泥水把药瓶一只只捡回'),
                OpeningEvidence(check='conflict_goal', paragraph_index=4, quote='必须在铜铃停在巷口前确认玉佩主人'),
                OpeningEvidence(check='locked_pov', paragraph_index=3, quote='林砚没有告诉沈微霜自己看见了什么'),
            ],
        )


def register_and_create_world(client, email='ncc@example.com'):
    token = client.post('/auth/register', json={'email': email, 'password': 'strongpass123'}).json()['access_token']
    world = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {token}'}).json()
    return token, world['id']


def create_draft(client, token, world_id, monkeypatch):
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: NarrativeControlLLMClient())
    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进雨巷密谈'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == 200
    return response.json()


def approve_draft(client, token, draft, opening_approval_payload):
    response = client.post(
        f"/chapters/{draft['chapter_id']}/approve",
        json=opening_approval_payload(draft),
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == 200
    return response.json()


def approve_chapter(client, token, world_id, monkeypatch, opening_approval_payload):
    draft = create_draft(client, token, world_id, monkeypatch)
    return approve_draft(client, token, draft, opening_approval_payload)


def create_approved_chapter(db_session, world_id, title):
    chapter = Chapter(
        world_id=world_id,
        title=title,
        status='approved',
        draft_version=1,
        approved_version=1,
        base_world_version=1,
        approved_content='正文',
    )
    db_session.add(chapter)
    db_session.commit()
    db_session.refresh(chapter)
    return chapter.id


def test_chapter_history_returns_only_approved_chapters(client, monkeypatch, opening_approval_payload):
    token, world_id = register_and_create_world(client)
    approved = approve_chapter(client, token, world_id, monkeypatch, opening_approval_payload)
    create_draft(client, token, world_id, monkeypatch)

    response = client.get(f'/worlds/{world_id}/chapters/history', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    payload = response.json()
    assert payload['world_id'] == world_id
    assert [chapter['id'] for chapter in payload['chapters']] == [approved['id']]
    assert payload['chapters'][0]['status'] == 'approved'


def test_chapter_history_item_includes_excerpt_and_event_counts(client, monkeypatch, opening_approval_payload):
    token, world_id = register_and_create_world(client)
    approved = approve_chapter(client, token, world_id, monkeypatch, opening_approval_payload)

    response = client.get(f'/worlds/{world_id}/chapters/history', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    item = response.json()['chapters'][0]
    assert item['id'] == approved['id']
    assert item['approved_version'] == 1
    assert item['base_world_version'] == 1
    assert item['world_version_after'] == 2
    assert item['approved_excerpt'].startswith('雨水压低了青岚城的屋檐')
    assert item['event_count'] == 4
    assert item['character_change_count'] == 1
    assert item['foreshadow_change_count'] == 1


def test_chapter_history_detail_returns_approved_content_and_event_changes(client, monkeypatch, opening_approval_payload):
    token, world_id = register_and_create_world(client)
    approved = approve_chapter(client, token, world_id, monkeypatch, opening_approval_payload)

    response = client.get(f"/chapters/{approved['id']}/history", headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    payload = response.json()
    assert payload['id'] == approved['id']
    assert payload['world_id'] == world_id
    assert payload['approved_content'].startswith('雨水压低了青岚城的屋檐')
    assert payload['approved_version'] == 1
    assert payload['base_world_version'] == 1
    assert payload['world_version_before'] == 1
    assert payload['world_version_after'] == 2
    assert payload['character_changes'][0]['event_type'] == 'character_change'
    assert payload['character_changes'][0]['object_type'] == 'character'
    assert payload['character_changes'][0]['before']['status'] == 'active'
    assert payload['character_changes'][0]['after']['status'] == '开始调查密信'
    assert payload['foreshadow_changes'][0]['event_type'] == 'foreshadow_change'
    assert payload['foreshadow_changes'][0]['object_type'] == 'foreshadow'
    assert payload['foreshadow_changes'][0]['after']['status'] == 'advanced'
    assert any(event['event_type'] == 'chapter_approved' for event in payload['events'])


def test_unapproved_chapter_history_detail_returns_conflict(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_draft(client, token, world_id, monkeypatch)

    response = client.get(f"/chapters/{draft['chapter_id']}/history", headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 409
    assert response.json()['detail'] == 'CHAPTER_NOT_APPROVED'


def test_next_chapter_prep_uses_high_priority_character_arc_progression_hint(client, db_session, monkeypatch, opening_approval_payload):
    token, world_id = register_and_create_world(client)
    approved = approve_chapter(client, token, world_id, monkeypatch, opening_approval_payload)
    chapter = db_session.get(Chapter, approved['id'])
    chapter.character_arc_report = {
        'summary': '林砚从被动等待转向主动追查。',
        'draft_version': 1,
        'current_draft_version': 1,
        'is_stale': False,
        'character_arcs': [
            {
                'character_id': 1,
                'name': '林砚',
                'role_type': 'protagonist',
                'current_status': '开始调查密信',
                'current_goals': ['追查湿信来源'],
                'presence_level': 'major',
                'arc_stage': 'choice',
                'chapter_function': '承担调查者功能。',
                'observed_shift': '开始主动追问。',
                'proposed_state_change': None,
                'continuity_risk': 'medium',
                'risk_reason': '下一章需要补足试探过程。',
                'suggested_revision': None,
                'next_chapter_setup': '前往城主府外墙。',
            }
        ],
        'relationship_notes': [],
        'progression_hints': [
            {
                'hint_type': 'character',
                'priority': 'high',
                'title': '试探沈微霜是否可信',
                'rationale': '上一章已经建立湿信线索。',
                'suggested_next_beat': '林砚带着湿信赴城主府外墙，并设置一次试探。',
                'related_character_ids': [1],
                'related_foreshadow_ids': [1],
                'can_seed_next_chapter_goal': True,
            }
        ],
        'created_at': '2026-05-29T00:00:00Z',
    }
    db_session.commit()

    response = client.get(f'/worlds/{world_id}/next-chapter-prep', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    payload = response.json()
    assert payload['world_id'] == world_id
    assert payload['world_version'] == 2
    assert payload['next_chapter_number'] == 2
    assert payload['suggested_goal'] == '林砚带着湿信赴城主府外墙，并设置一次试探。'
    assert payload['recommended_pov_character_id'] == 1
    assert payload['recommended_pov_character_name'] == '林砚'
    assert 'character_arc_progression_hint' in payload['source_signals']
    assert payload['priority_characters'][0]['character_id'] == 1
    assert payload['priority_foreshadows'][0]['foreshadow_id'] == 1
    assert payload['progression_hints'][0]['title'] == '试探沈微霜是否可信'
    assert payload['continuity_warnings'][0]['category'] == 'character_arc'


def test_next_chapter_prep_falls_back_to_next_story_arc_summary(client, db_session, monkeypatch, opening_approval_payload):
    token, world_id = register_and_create_world(client)
    approve_chapter(client, token, world_id, monkeypatch, opening_approval_payload)
    world = db_session.get(World, world_id)
    world.story_arc = [
        {'chapter_number': 2, 'summary': '林砚潜入城主府外墙，发现密道入口。', 'pov_suggestion': '林砚'}
    ]
    db_session.commit()

    response = client.get(f'/worlds/{world_id}/next-chapter-prep', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    payload = response.json()
    assert payload['suggested_goal'] == '林砚潜入城主府外墙，发现密道入口。'
    assert payload['recommended_pov_character_name'] == '林砚'
    assert 'story_arc' in payload['source_signals']


def test_next_chapter_prep_falls_back_to_highest_urgency_foreshadow(client, db_session, monkeypatch, opening_approval_payload):
    token, world_id = register_and_create_world(client)
    approve_chapter(client, token, world_id, monkeypatch, opening_approval_payload)
    world = db_session.get(World, world_id)
    world.story_arc = []
    db_session.commit()

    response = client.get(f'/worlds/{world_id}/next-chapter-prep', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    payload = response.json()
    assert payload['suggested_goal'].startswith('推进伏笔《')
    assert 'urgent_foreshadow' in payload['source_signals']
    assert payload['priority_foreshadows'][0]['urgency_level'] >= 1


def test_next_chapter_prep_prioritizes_stale_ledger_foreshadows(client, db_session, monkeypatch, opening_approval_payload):
    token, world_id = register_and_create_world(client)
    approve_chapter(client, token, world_id, monkeypatch, opening_approval_payload)
    world = db_session.get(World, world_id)
    world.story_arc = []
    db_session.commit()
    from app.foreshadow.models import Foreshadow
    stale = db_session.get(Foreshadow, 1)
    assert stale is not None
    stale.status = 'planted'
    stale.urgency_level = 5
    stale.source_chapter_id = create_approved_chapter(db_session, world_id, '伏笔源章节')
    db_session.commit()
    for index in range(6):
        create_approved_chapter(db_session, world_id, f'后续章节 {index}')

    response = client.get(f'/worlds/{world_id}/next-chapter-prep', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    payload = response.json()
    assert payload['priority_foreshadows'][0]['foreshadow_id'] == stale.id
    assert payload['priority_foreshadows'][0]['urgency_level'] == 5
    assert '已埋设 6 章未推进' in payload['priority_foreshadows'][0]['reason']
    assert payload['suggested_goal'].startswith('推进伏笔《')
    assert 'urgent_foreshadow' in payload['source_signals']


def test_next_chapter_prep_does_not_mutate_world_version_or_write_events(client, db_session, monkeypatch, opening_approval_payload):
    token, world_id = register_and_create_world(client)
    approve_chapter(client, token, world_id, monkeypatch, opening_approval_payload)
    db_session.expire_all()
    world_before = db_session.get(World, world_id)
    version_before = world_before.world_version
    event_count_before = db_session.scalar(select(func.count()).select_from(EventLog))

    response = client.get(f'/worlds/{world_id}/next-chapter-prep', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 200
    db_session.expire_all()
    world_after = db_session.get(World, world_id)
    event_count_after = db_session.scalar(select(func.count()).select_from(EventLog))
    assert world_after.world_version == version_before
    assert event_count_after == event_count_before


def test_narrative_control_center_rejects_non_owner_access(client, monkeypatch, opening_approval_payload):
    owner_token, world_id = register_and_create_world(client, 'owner-ncc@example.com')
    approved = approve_chapter(client, owner_token, world_id, monkeypatch, opening_approval_payload)
    other_token = client.post('/auth/register', json={'email': 'other-ncc@example.com', 'password': 'strongpass123'}).json()['access_token']

    history_response = client.get(f'/worlds/{world_id}/chapters/history', headers={'Authorization': f'Bearer {other_token}'})
    detail_response = client.get(f"/chapters/{approved['id']}/history", headers={'Authorization': f'Bearer {other_token}'})
    prep_response = client.get(f'/worlds/{world_id}/next-chapter-prep', headers={'Authorization': f'Bearer {other_token}'})

    assert history_response.status_code == 403
    assert history_response.json()['detail'] == 'FORBIDDEN'
    assert detail_response.status_code == 403
    assert detail_response.json()['detail'] == 'FORBIDDEN'
    assert prep_response.status_code == 403
    assert prep_response.json()['detail'] == 'FORBIDDEN'
