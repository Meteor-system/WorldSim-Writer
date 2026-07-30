from sqlalchemy import select

from app.character.models import Character, CharacterRelation
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
from app.world.models import World


class StoryBibleDraftLLMClient:
    def generate_outline(self, messages):
        return ChapterOutline(
            beats=[
                BeatCard(
                    beat_id='opening-1',
                    summary='林砚在雨巷接过沈微霜递来的湿信。',
                    pov_character='林砚',
                    location='青岚城雨巷',
                    emotional_arc='迟疑 -> 警觉',
                    key_dialogue_hints=['信上的名字不能让城主府看见。'],
                )
            ],
            core_conflict='林砚必须在巡夜人赶到前判断湿信是否指向玉佩。',
            pov_suggestion='林砚',
            pacing='雨巷密谈中逐步逼近巡夜压力。',
            role_skill_targets=['林砚', '沈微霜'],
            opening_contract=OpeningContract(
                background='青岚城雨夜不断，灵脉衰退引来城主府巡查。',
                protagonist_identity='林砚是替师门送药的外门弟子。',
                motivation='他必须查明湿信来源，保护师门和师妹。',
                personality_evidence_plan='让林砚先收拾被冲散的药瓶，再冒险留下读信。',
                conflict_goal='在巡夜人发现前确认湿信是否推进玉佩线索。',
                locked_pov='林砚限知第三人称。',
            ),
        )

    def generate_chapter(self, messages):
        content = '\n\n'.join([
            '雨水灌满青岚城的石缝，雨巷尽头的灵井仍冒着白雾。林砚停在檐下，听见城主府巡夜人的铜铃从远处逼近，湿冷的雾气把整条巷子压得喘不过气。',
            '他是替师门送药的外门弟子，师妹还在等药；可沈微霜递来的湿信写着失踪师兄的名字，他必须查明信从何而来，才不至于让师门再次替城主府的秘密付账。',
            '药瓶被雨水冲散时，林砚先蹲进泥水逐只捡回，再把发疼的手藏进袖里。他没有立刻拆信，只确认巷口没有第二双靴印，也不肯让师妹明日断药。',
            '沈微霜说信来自城主府库房，林砚只能看见她湿发下的神色，却猜不透她为何冒险送信；玉佩在掌心忽然发烫，信纸上的墨迹也像被井雾一点点唤醒。',
            '他必须在巡夜人发现前确认湿信是否推进玉佩线索，否则师门会被牵连，师兄的失踪也会被彻底抹去；他必须在雨停前做出选择。',
            '铜铃在巷口停住，林砚只能从信纸背面的血色水痕判断，送信的人也许已经被困在灵井下面；他把湿信贴近胸口，准备绕到井边寻找入口。',
        ])
        return ChapterGeneration(
            title='第一章 雨巷密谈',
            draft_content=content,
            context_summary='林砚与沈微霜交换线索。',
            review_hints=['确认第二段信息揭示是否过快'],
            proposed_character_changes=[
                ProposedCharacterChange(character_id=1, status='开始调查密信', current_goals=['追查湿信来源'])
            ],
            proposed_foreshadow_changes=[
                ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='湿信推进玉佩线索')
            ],
            opening_evidence=[
                OpeningEvidence(check='background', paragraph_index=0, quote='雨巷尽头的灵井仍冒着白雾'),
                OpeningEvidence(check='protagonist_identity', paragraph_index=1, quote='替师门送药的外门弟子'),
                OpeningEvidence(check='motivation', paragraph_index=1, quote='必须查明信从何而来'),
                OpeningEvidence(check='personality_evidence_plan', paragraph_index=2, quote='药瓶被雨水冲散时，林砚先蹲进泥水逐只捡回'),
                OpeningEvidence(check='conflict_goal', paragraph_index=4, quote='必须在巡夜人发现前确认湿信是否推进玉佩线索'),
                OpeningEvidence(check='locked_pov', paragraph_index=5, quote='林砚只能从信纸背面的血色水痕判断'),
            ],
        )


def register_user(client, email='story-bible@example.com'):
    return client.post('/auth/register', json={'email': email, 'password': 'strongpass123'}).json()['access_token']


def auth(token):
    return {'Authorization': f'Bearer {token}'}


def create_world(client, token):
    return client.post('/worlds/from-template', headers=auth(token)).json()


def first_character(db_session, world_id):
    return db_session.scalar(select(Character).where(Character.world_id == world_id).order_by(Character.id))


def second_character(db_session, world_id):
    return list(db_session.scalars(select(Character).where(Character.world_id == world_id).order_by(Character.id)))[1]


def first_relation(db_session, world_id):
    return db_session.scalar(select(CharacterRelation).where(CharacterRelation.world_id == world_id).order_by(CharacterRelation.id))


def manual_events(db_session, world_id):
    return list(
        db_session.scalars(
            select(EventLog)
            .where(EventLog.world_id == world_id)
            .where(EventLog.source_type == 'manual_edit')
            .order_by(EventLog.id)
        )
    )


def create_reviewing_draft(client, token, world_id, monkeypatch):
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: StoryBibleDraftLLMClient())
    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进雨巷密谈'},
        headers=auth(token),
    )
    assert response.status_code == 200
    return response.json()


def test_update_character_increments_world_version_refreshes_projection_and_writes_events(client, db_session):
    token = register_user(client)
    world_payload = create_world(client, token)
    world_id = world_payload['id']
    character = first_character(db_session, world_id)

    response = client.put(
        f'/characters/{character.id}',
        json={
            'status': '谨慎调查密信',
            'current_goals': ['验证沈微霜是否可信', '追查湿信来源'],
            'edit_reason': '同步 Story Bible 设定',
        },
        headers=auth(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['status'] == '谨慎调查密信'
    assert payload['current_goals'] == ['验证沈微霜是否可信', '追查湿信来源']

    db_session.expire_all()
    world = db_session.get(World, world_id)
    updated = db_session.get(Character, character.id)
    events = manual_events(db_session, world_id)

    assert world.world_version == 2
    assert updated.status == '谨慎调查密信'
    assert updated.current_goals == ['验证沈微霜是否可信', '追查湿信来源']
    projected = next(item for item in world.current_characters if item['id'] == character.id)
    assert projected['status'] == '谨慎调查密信'
    assert projected['current_goals'] == ['验证沈微霜是否可信', '追查湿信来源']
    assert [event.event_type for event in events] == ['character_change', 'world_version_increment']
    assert events[0].payload['action'] == 'updated'
    assert events[0].payload['edit_reason'] == '同步 Story Bible 设定'
    assert events[0].world_version_before == 1
    assert events[0].world_version_after == 2


def test_non_owner_cannot_update_character(client, db_session):
    owner_token = register_user(client, 'owner-story-bible@example.com')
    other_token = register_user(client, 'intruder-story-bible@example.com')
    world_payload = create_world(client, owner_token)
    character = first_character(db_session, world_payload['id'])

    response = client.put(
        f'/characters/{character.id}',
        json={'status': '非法修改'},
        headers=auth(other_token),
    )

    assert response.status_code == 403
    assert response.json()['detail'] == 'FORBIDDEN'


def test_missing_character_update_returns_not_found(client):
    token = register_user(client)

    response = client.put('/characters/999999', json={'status': '不存在'}, headers=auth(token))

    assert response.status_code == 404
    assert response.json()['detail'] == 'NOT_FOUND'


def test_create_relation_increments_world_version_refreshes_projection_and_writes_events(client, db_session):
    token = register_user(client)
    world_payload = create_world(client, token)
    world_id = world_payload['id']
    source = first_character(db_session, world_id)
    target = second_character(db_session, world_id)

    response = client.post(
        f'/worlds/{world_id}/relations',
        json={
            'source_character_id': source.id,
            'target_character_id': target.id,
            'relation_type': 'cautious_alliance',
            'intensity': 3,
            'visibility': 'private',
            'edit_reason': '补充试探关系',
        },
        headers=auth(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['relation_type'] == 'cautious_alliance'
    assert payload['intensity'] == 3
    assert payload['visibility'] == 'private'

    db_session.expire_all()
    world = db_session.get(World, world_id)
    events = manual_events(db_session, world_id)

    assert world.world_version == 2
    assert any(item['id'] == payload['id'] and item['relation_type'] == 'cautious_alliance' for item in world.current_relations)
    assert [event.event_type for event in events] == ['relation_change', 'world_version_increment']
    assert events[0].payload['action'] == 'created'
    assert events[0].payload['edit_reason'] == '补充试探关系'


def test_update_relation_increments_world_version_and_refreshes_projection(client, db_session):
    token = register_user(client)
    world_payload = create_world(client, token)
    world_id = world_payload['id']
    relation = first_relation(db_session, world_id)

    response = client.put(
        f'/relations/{relation.id}',
        json={'relation_type': 'trusted_ally', 'intensity': 4, 'visibility': 'public', 'edit_reason': '关系升温'},
        headers=auth(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['relation_type'] == 'trusted_ally'
    assert payload['intensity'] == 4

    db_session.expire_all()
    world = db_session.get(World, world_id)
    updated = db_session.get(CharacterRelation, relation.id)
    events = manual_events(db_session, world_id)

    assert world.world_version == 2
    assert updated.relation_type == 'trusted_ally'
    projected = next(item for item in world.current_relations if item['id'] == relation.id)
    assert projected['relation_type'] == 'trusted_ally'
    assert projected['intensity'] == 4
    assert [event.event_type for event in events] == ['relation_change', 'world_version_increment']
    assert events[0].payload['action'] == 'updated'


def test_relation_create_and_update_reject_invalid_or_cross_world_characters(client, db_session):
    token = register_user(client)
    first_world = create_world(client, token)
    second_world = create_world(client, token)
    source = first_character(db_session, first_world['id'])
    cross_world_character = first_character(db_session, second_world['id'])
    relation = first_relation(db_session, first_world['id'])

    self_response = client.post(
        f"/worlds/{first_world['id']}/relations",
        json={'source_character_id': source.id, 'target_character_id': source.id, 'relation_type': 'mirror'},
        headers=auth(token),
    )
    cross_create = client.post(
        f"/worlds/{first_world['id']}/relations",
        json={'source_character_id': source.id, 'target_character_id': cross_world_character.id, 'relation_type': 'impossible'},
        headers=auth(token),
    )
    cross_update = client.put(
        f'/relations/{relation.id}',
        json={'source_character_id': source.id, 'target_character_id': cross_world_character.id},
        headers=auth(token),
    )

    assert self_response.status_code == 400
    assert self_response.json()['detail'] == 'INVALID_SELF_RELATION'
    assert cross_create.status_code == 404
    assert cross_create.json()['detail'] == 'RELATED_CHARACTER_NOT_FOUND'
    assert cross_update.status_code == 404
    assert cross_update.json()['detail'] == 'RELATED_CHARACTER_NOT_FOUND'


def test_story_bible_edit_does_not_mutate_reviewing_draft_and_readiness_reports_version_mismatch(client, db_session, monkeypatch):
    token = register_user(client)
    world_payload = create_world(client, token)
    world_id = world_payload['id']
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)
    character = first_character(db_session, world_id)

    response = client.put(
        f'/characters/{character.id}',
        json={'status': '手动更新后的正式状态', 'current_goals': ['正式目标']},
        headers=auth(token),
    )
    assert response.status_code == 200

    db_session.expire_all()
    world = db_session.get(World, world_id)
    chapter = db_session.get(Chapter, draft['chapter_id'])
    stored_draft = db_session.scalar(select(ChapterDraft).where(ChapterDraft.id == draft['draft_id']))

    assert world.world_version == 2
    assert chapter.status == 'reviewing'
    assert chapter.draft_version == draft['draft_version']
    assert stored_draft.content == draft['content']
    assert stored_draft.source_world_version == 1

    readiness = client.get(f"/chapters/{draft['chapter_id']}/approval-readiness", headers=auth(token))
    preview = client.get(f"/chapters/{draft['chapter_id']}/approval-preview", headers=auth(token))

    assert readiness.status_code == 200
    readiness_payload = readiness.json()
    assert readiness_payload['world_version']['source_world_version'] == 1
    assert readiness_payload['world_version']['current_world_version'] == 2
    assert readiness_payload['world_version']['matches'] is False
    assert readiness_payload['status'] == 'blocked'
    assert readiness_payload['ready'] is False
    assert '世界版本已变化，请重新生成草稿后再批准。' in readiness_payload['blocking_reasons']
    assert isinstance(readiness_payload['warnings'], list)

    assert preview.status_code == 200
    preview_payload = preview.json()
    assert preview_payload['source_world_version'] == 1
    assert preview_payload['current_world_version'] == 2
    assert preview_payload['version_conflict'] is True


def test_approval_readiness_exposes_direct_ready_status(client, monkeypatch):
    token = register_user(client, 'readiness-direct@example.com')
    world_payload = create_world(client, token)
    draft = create_reviewing_draft(client, token, world_payload['id'], monkeypatch)

    response = client.get(f"/chapters/{draft['chapter_id']}/approval-readiness", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['ready'] is False
    assert payload['status'] in {'needs_review', 'blocked'}
    assert isinstance(payload['blocking_reasons'], list)
    assert isinstance(payload['warnings'], list)
