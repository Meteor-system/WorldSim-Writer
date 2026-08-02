import pytest
from pydantic import ValidationError
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
from app.narrative.models import Chapter, ChapterDraft
from app.world.models import World


OPENING_CHECKS = [
    'background',
    'protagonist_identity',
    'motivation',
    'personality_evidence_plan',
    'conflict_goal',
    'locked_pov',
]


def auth(token):
    return {'Authorization': f'Bearer {token}'}


def register_and_create_world(client, email):
    token = client.post('/auth/register', json={'email': email, 'password': 'strongpass123'}).json()['access_token']
    world = client.post('/worlds/from-template', headers=auth(token)).json()
    return token, world['id']


def create_passing_opening_draft(client, db_session, monkeypatch, email):
    token, world_id = register_and_create_world(client, email)
    llm = OpeningQualityLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '建立林砚追查玉佩并保护师妹的开篇动机。'},
        headers=auth(token),
    )
    assert response.status_code == 200
    draft = response.json()
    assert draft['quality_report']['status'] == 'pass'
    chapter = db_session.get(Chapter, draft['chapter_id'])
    locked_character = db_session.get(narrative_service.Character, chapter.pov_character_id)
    assert locked_character is not None
    return token, world_id, draft, locked_character


def opening_pov_confirmation(current_draft_version, locked_character, **overrides):
    confirmation = {
        'confirmed': True,
        'draft_version': current_draft_version,
        'locked_character_id': locked_character.id,
        'locked_character_name': locked_character.name,
    }
    confirmation.update(overrides)
    return {
        'draft_version': current_draft_version,
        'opening_pov_confirmation': confirmation,
    }


def assert_approval_writes_are_unchanged(db_session, world_id, chapter_id, world_version, event_count):
    db_session.expire_all()
    assert db_session.get(Chapter, chapter_id).status == 'reviewing'
    assert db_session.get(World, world_id).world_version == world_version
    assert db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id)) == event_count


def opening_contract() -> OpeningContract:
    return OpeningContract(
        background='青岚城灵脉衰退，废弃灵井在雨夜发出异响。',
        protagonist_identity='林砚是为师门债务奔走的外门弟子。',
        motivation='他必须查清裂纹玉佩为何牵连师门，避免师妹被城主府带走。',
        personality_evidence_plan='让林砚先救下被雨水冲走的药箱，再隐瞒手伤继续追查。',
        conflict_goal='在城主府的巡夜人发现前，确认暗井中的玉佩是否属于失踪师兄。',
        locked_pov='林砚限知第三人称。',
    )


def opening_body() -> str:
    return '\n\n'.join(
        [
            '雨水压低了青岚城的屋檐，废弃灵井却在巷尾吐出温热白雾。林砚替师门送药归来，掌心的裂纹玉佩忽然发烫；城里人人都说灵脉衰退只是旱灾，他知道那是谎话。',
            '他是欠着师门药债的外门弟子，今夜原该回去照看师妹。可城主府的文书写明天亮前要带走她问话，林砚只能追查玉佩与失踪师兄的名字，哪怕这会把自己送进巡夜人的眼里。',
            '巷口的药箱被雨水冲翻，他先扑进泥水把药瓶一只只捡回，又把割裂的手藏进袖中。沈微霜问他为何不逃，林砚只说：师妹还在等药，这不是能算清的账。',
            '灵井底下传来铁链拖地声，玉佩映出师兄惯用的云纹。林砚没有告诉沈微霜自己看见了什么，只沿着井壁摸到一道新鲜的靴印，听见城主府巡夜人的铜铃越来越近。',
            '他必须在铜铃停在巷口前确认玉佩主人，否则师妹会被带走，师兄的失踪也会被埋进井里。林砚让沈微霜守住巷口，自己系紧绳索下井；他不确定她会不会出卖自己。',
            '林砚的靴底刚离开井沿，铜铃便在雨幕外停住。巡夜人喊出他的名字，他只能从井壁渗出的血色水痕判断，下面等着他的不是师兄，而是一场早已布好的局。',
        ]
    )


def opening_evidence(body: str) -> list[OpeningEvidence]:
    return [
        OpeningEvidence(check='background', paragraph_index=0, quote='废弃灵井却在巷尾吐出温热白雾'),
        OpeningEvidence(check='protagonist_identity', paragraph_index=1, quote='欠着师门药债的外门弟子'),
        OpeningEvidence(check='motivation', paragraph_index=1, quote='只能追查玉佩与失踪师兄的名字'),
        OpeningEvidence(check='personality_evidence_plan', paragraph_index=2, quote='先扑进泥水把药瓶一只只捡回'),
        OpeningEvidence(check='conflict_goal', paragraph_index=4, quote='必须在铜铃停在巷口前确认玉佩主人'),
        OpeningEvidence(check='locked_pov', paragraph_index=3, quote='林砚没有告诉沈微霜自己看见了什么'),
    ]


def second_character_opening_body() -> str:
    return '\n\n'.join(
        [
            '雨水压低了青岚城的屋檐，废弃灵井却在巷尾吐出温热白雾。沈微霜藏在檐影下，望见林砚掌心的裂纹玉佩发烫；城里人人都说灵脉衰退只是旱灾，她知道那是谎话。',
            '沈微霜是潜伏在青岚城的医师，今夜本该避开城主府的耳目。可她必须在巡夜人抵达前查清玉佩与失踪师兄的关系，才能弄明白林砚为何会被卷进暗井的秘密。',
            '巷口的药箱被雨水冲翻，沈微霜先扑进泥水把药瓶一只只捡回，又把手背的擦伤藏进袖中。林砚问她为何还不离开，她只说巡夜人快到了。',
            '灵井底下传来铁链拖地声，玉佩映出失踪师兄惯用的云纹。沈微霜没有告诉林砚自己看见了什么，只沿着井壁摸到一道新鲜的靴印，听见城主府巡夜人的铜铃越来越近。',
            '她必须在城主府巡夜人发现前确认暗井中的玉佩主人，否则线索会被埋进井里，林砚也会落入巡夜人的手中。沈微霜让林砚守住巷口，自己系紧绳索下井。',
            '沈微霜的靴底刚离开井沿，铜铃便在雨幕外停住。巡夜人喊出林砚的名字，沈微霜只能从井壁渗出的血色水痕判断，下面等着她的不是失踪师兄，而是一场早已布好的局。',
        ]
    )


def second_character_opening_evidence(body: str) -> list[OpeningEvidence]:
    return [
        OpeningEvidence(check='background', paragraph_index=0, quote='废弃灵井却在巷尾吐出温热白雾'),
        OpeningEvidence(check='protagonist_identity', paragraph_index=1, quote='沈微霜是潜伏在青岚城的医师'),
        OpeningEvidence(check='motivation', paragraph_index=1, quote='必须在巡夜人抵达前查清玉佩与失踪师兄的关系'),
        OpeningEvidence(check='personality_evidence_plan', paragraph_index=2, quote='沈微霜先扑进泥水把药瓶一只只捡回'),
        OpeningEvidence(check='conflict_goal', paragraph_index=4, quote='必须在城主府巡夜人发现前确认暗井中的玉佩主人'),
        OpeningEvidence(check='locked_pov', paragraph_index=3, quote='沈微霜没有告诉林砚自己看见了什么'),
    ]


def opening_beat_cards() -> list[dict]:
    return [
        BeatCard(
            beat_id='opening-1',
            summary='林砚在废弃灵井发现玉佩异动。',
            pov_character='林砚',
            location='青岚城后巷',
            emotional_arc='焦灼 -> 警觉',
            key_dialogue_hints=['师妹还在等药。'],
        ).model_dump()
    ]


class OpeningQualityLLMClient:
    def __init__(self, evidence=None):
        self.calls = []
        self._evidence = evidence

    def generate_outline(self, _messages):
        self.calls.append('outline')
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
            opening_contract=opening_contract(),
        )

    def generate_chapter(self, _messages):
        self.calls.append('writer')
        body = opening_body()
        return ChapterGeneration(
            title='第一章 雨井铜铃',
            draft_content=body,
            context_summary='林砚为保护师妹并追查失踪师兄，在雨夜下井。',
            review_hints=['批准前检查开篇质量契约。'],
            proposed_character_changes=[ProposedCharacterChange(character_id=1, current_goals=['查清裂纹玉佩的主人'])],
            proposed_foreshadow_changes=[
                ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='玉佩与暗井相连。')
            ],
            opening_evidence=self._evidence if self._evidence is not None else opening_evidence(body),
        )


class VerboseLockedLinYanOpeningLLM(OpeningQualityLLMClient):
    def generate_outline(self, messages):
        outline = super().generate_outline(messages)
        return outline.model_copy(
            update={
                'pov_suggestion': '林砚固定第三人称限知视角',
                'beats': [
                    outline.beats[0].model_copy(update={'pov_character': '林砚'})
                ],
                'opening_contract': opening_contract().model_copy(
                    update={
                        'locked_pov': '固定第三人称限知视角：全章仅跟随林砚的感知、判断与情绪，不直接进入沈微霜或其他角色的内心。'
                    }
                ),
            }
        )


class AlternatingLockedPovOpeningLLM(VerboseLockedLinYanOpeningLLM):
    def generate_outline(self, messages):
        outline = super().generate_outline(messages)
        return outline.model_copy(
            update={
                'opening_contract': outline.opening_contract.model_copy(
                    update={'locked_pov': '林砚与沈微霜交替使用第三人称限知视角。'}
                )
            }
        )


class OtherCharacterInteriorAccessOpeningLLM(VerboseLockedLinYanOpeningLLM):
    def __init__(self, locked_pov):
        super().__init__()
        self.locked_pov = locked_pov

    def generate_outline(self, messages):
        outline = super().generate_outline(messages)
        return outline.model_copy(
            update={
                'opening_contract': outline.opening_contract.model_copy(
                    update={'locked_pov': self.locked_pov}
                )
            }
        )


class ContractLockedSecondCharacterLLM:
    def __init__(self):
        self.calls = []
        self.writer_messages = []

    def generate_outline(self, _messages):
        self.calls.append('outline')
        return ChapterOutline(
            core_conflict='沈微霜必须在巡夜人抵达前确认玉佩主人的身份。',
            pov_suggestion=None,
            pacing='雨夜悬疑，逐段增加巡夜压力。',
            role_skill_targets=['林砚', '沈微霜'],
            beats=[
                BeatCard(
                    beat_id='opening-1',
                    summary='沈微霜在废弃灵井观察玉佩异动。',
                    pov_character=None,
                    location='青岚城后巷',
                    emotional_arc='焦灼 -> 警觉',
                    key_dialogue_hints=['巡夜人快到了。'],
                )
            ],
            opening_contract=OpeningContract(
                background='青岚城灵脉衰退，废弃灵井在雨夜发出异响。',
                protagonist_identity='沈微霜是潜伏在青岚城的医师。',
                motivation='她必须在巡夜人抵达前查清玉佩与失踪师兄的关系。',
                personality_evidence_plan='让沈微霜先救下药箱，再隐瞒自己的伤势。',
                conflict_goal='在城主府巡夜人发现前确认暗井中的玉佩主人。',
                locked_pov='沈微霜限知第三人称。',
            ),
        )

    def generate_chapter(self, messages):
        self.calls.append('writer')
        self.writer_messages.append(messages)
        body = second_character_opening_body()
        return ChapterGeneration(
            title='第一章 雨井铜铃',
            draft_content=body,
            context_summary='沈微霜在雨夜追查暗井玉佩。',
            review_hints=['批准前检查开篇质量契约。'],
            proposed_character_changes=[],
            proposed_foreshadow_changes=[],
            opening_evidence=second_character_opening_evidence(body),
        )


class ContractLockedSecondCharacterButLinYanBodyLLM(ContractLockedSecondCharacterLLM):
    def generate_chapter(self, messages):
        self.calls.append('writer')
        self.writer_messages.append(messages)
        body = opening_body()
        evidence = opening_evidence(body)
        evidence[-1] = OpeningEvidence(check='locked_pov', paragraph_index=2, quote='沈微霜问他为何不逃')
        return ChapterGeneration(
            title='第一章 雨井铜铃',
            draft_content=body,
            context_summary='沈微霜在雨夜追查暗井玉佩。',
            review_hints=['批准前检查开篇质量契约。'],
            proposed_character_changes=[],
            proposed_foreshadow_changes=[],
            opening_evidence=evidence,
        )


class WriterOnlyOpeningLLM:
    def __init__(self):
        self.calls = []

    def generate_chapter(self, _messages):
        self.calls.append('writer')
        return ChapterGeneration(
            title='不应生成的第一章',
            draft_content=opening_body(),
            context_summary='不应创建草稿。',
            review_hints=[],
            proposed_character_changes=[],
            proposed_foreshadow_changes=[],
        )


class MissingOpeningContractLLM:
    def __init__(self):
        self.calls = []

    def generate_outline(self, _messages):
        self.calls.append('outline')
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
            opening_contract=None,
        )

    def generate_chapter(self, _messages):
        self.calls.append('writer')
        return ChapterGeneration(
            title='不应生成的第一章',
            draft_content=opening_body(),
            context_summary='不应创建草稿。',
            review_hints=[],
            proposed_character_changes=[],
            proposed_foreshadow_changes=[],
        )


def test_draft_opening_chapter_runs_outline_before_writer_and_persists_passing_quality_report(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'opening-quality-pass@example.com')
    llm = OpeningQualityLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    before_events = db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id))

    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '建立林砚追查玉佩并保护师妹的开篇动机。'},
        headers=auth(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert llm.calls == ['outline', 'writer']
    assert len(payload['content'].split('\n\n')) >= 6
    assert payload['quality_report']['profile'] == 'opening_chapter'
    assert payload['quality_report']['status'] == 'pass'
    assert [check['check'] for check in payload['quality_report']['checks']] == OPENING_CHECKS
    assert all(check['status'] == 'pass' for check in payload['quality_report']['checks'])
    assert payload['outline_context']['opening_contract']['locked_pov'] == '林砚限知第三人称。'

    db_session.expire_all()
    draft = db_session.get(ChapterDraft, payload['draft_id'])
    world = db_session.get(World, world_id)
    assert draft.quality_report == payload['quality_report']
    assert draft.chapter.outline_context['opening_contract']['conflict_goal'] == opening_contract().conflict_goal
    assert world.world_version == 1
    assert db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id)) == before_events

def test_passing_opening_approval_requires_pov_confirmation_without_committing_state(client, db_session, monkeypatch):
    token, world_id, draft, _locked_character = create_passing_opening_draft(
        client, db_session, monkeypatch, 'opening-pov-confirmation-required@example.com'
    )
    before_world_version = db_session.get(World, world_id).world_version
    before_events = db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id))

    approval = client.post(
        f"/chapters/{draft['chapter_id']}/approve",
        headers=auth(token),
        json={'draft_version': draft['draft_version']},
    )

    assert approval.status_code == 409
    assert approval.json()['detail'] == 'OPENING_POV_CONFIRMATION_REQUIRED'
    assert_approval_writes_are_unchanged(
        db_session, world_id, draft['chapter_id'], before_world_version, before_events
    )


def test_passing_opening_approval_rejects_stale_pov_confirmation(client, db_session, monkeypatch):
    token, world_id, draft, locked_character = create_passing_opening_draft(
        client, db_session, monkeypatch, 'opening-pov-confirmation-stale@example.com'
    )
    chapter = db_session.get(Chapter, draft['chapter_id'])
    current_draft = db_session.get(ChapterDraft, draft['draft_id'])
    next_draft = narrative_service._create_draft_version(
        db_session,
        chapter,
        current_draft,
        current_draft.content,
        'manual_edit',
        '创建当前 v2 以验证旧确认失效',
    )
    next_draft.quality_report = {
        **current_draft.quality_report,
        'status': 'pass',
        'evaluated_draft_version': next_draft.draft_version,
        'current_draft_version': next_draft.draft_version,
    }
    db_session.commit()
    current_draft_version = next_draft.draft_version
    before_world_version = db_session.get(World, world_id).world_version
    before_events = db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id))

    approval = client.post(
        f"/chapters/{draft['chapter_id']}/approve",
        headers=auth(token),
        json=opening_pov_confirmation(current_draft_version, locked_character, draft_version=1),
    )

    assert approval.status_code == 409
    assert approval.json()['detail'] == 'OPENING_POV_CONFIRMATION_STALE'
    assert_approval_writes_are_unchanged(
        db_session, world_id, draft['chapter_id'], before_world_version, before_events
    )


@pytest.mark.parametrize(
    ('confirmation_override', 'label'),
    [
        ({'locked_character_id': 999999}, 'character-id'),
        ({'locked_character_name': '错误角色'}, 'character-name'),
    ],
)
def test_passing_opening_approval_rejects_confirmation_that_mismatches_locked_pov(
    client, db_session, monkeypatch, confirmation_override, label
):
    token, world_id, draft, locked_character = create_passing_opening_draft(
        client, db_session, monkeypatch, f'opening-pov-confirmation-mismatch-{label}@example.com'
    )
    before_world_version = db_session.get(World, world_id).world_version
    before_events = db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id))

    approval = client.post(
        f"/chapters/{draft['chapter_id']}/approve",
        headers=auth(token),
        json=opening_pov_confirmation(draft['draft_version'], locked_character, **confirmation_override),
    )

    assert approval.status_code == 409
    assert approval.json()['detail'] == 'OPENING_POV_CONFIRMATION_MISMATCH'
    assert_approval_writes_are_unchanged(
        db_session, world_id, draft['chapter_id'], before_world_version, before_events
    )


def test_passing_opening_approval_records_matching_locked_pov_attestation(client, db_session, monkeypatch):
    token, world_id, draft, locked_character = create_passing_opening_draft(
        client, db_session, monkeypatch, 'opening-pov-confirmation-approved@example.com'
    )

    preview_response = client.get(f"/chapters/{draft['chapter_id']}/approval-preview", headers=auth(token))

    assert preview_response.status_code == 200
    preview = preview_response.json()
    assert preview['chapter_id'] == draft['chapter_id']
    assert preview['draft_version'] == draft['draft_version']
    target = preview['opening_pov_confirmation_target']
    assert target['required'] is True
    assert target['locked_character_id'] == locked_character.id
    assert target['locked_character_name'] == locked_character.name

    approval = client.post(
        f"/chapters/{draft['chapter_id']}/approve",
        headers=auth(token),
        json={
            'draft_version': preview['draft_version'],
            'opening_pov_confirmation': {
                'confirmed': True,
                'draft_version': preview['draft_version'],
                'locked_character_id': target['locked_character_id'],
                'locked_character_name': target['locked_character_name'],
            },
        },
    )

    assert approval.status_code == 200
    assert approval.json()['status'] == 'approved'
    db_session.expire_all()
    event = db_session.scalar(
        select(EventLog).where(
            EventLog.world_id == world_id,
            EventLog.chapter_id == draft['chapter_id'],
            EventLog.event_type == 'chapter_approved',
        )
    )
    assert event is not None
    assert event.payload['approval_attestations']['locked_pov'] == {
        'confirmed': True,
        'confirmed_draft_version': preview['draft_version'],
        'locked_character_id': target['locked_character_id'],
        'locked_character_name': target['locked_character_name'],
        'pov_mode': 'third_person_limited',
    }


def test_verbose_locked_lin_yan_opening_contract_is_accepted_as_single_pov(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'opening-verbose-lin-yan-pov@example.com')
    locked_character = db_session.scalar(
        select(narrative_service.Character).where(
            narrative_service.Character.world_id == world_id,
            narrative_service.Character.name == '林砚',
        )
    )
    assert locked_character is not None
    llm = VerboseLockedLinYanOpeningLLM()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)

    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '建立林砚追查玉佩并保护师妹的开篇动机。'},
        headers=auth(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert llm.calls == ['outline', 'writer']
    assert payload['quality_report']['status'] == 'pass'
    assert payload['outline_context']['pov_suggestion'] == '林砚固定第三人称限知视角'
    assert payload['outline_context']['opening_contract']['locked_pov'] == (
        '固定第三人称限知视角：全章仅跟随林砚的感知、判断与情绪，不直接进入沈微霜或其他角色的内心。'
    )
    db_session.expire_all()
    assert db_session.get(Chapter, payload['chapter_id']).pov_character_id == locked_character.id


def test_opening_contract_rejects_alternating_pov_before_writer_and_draft_write(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'opening-alternating-pov@example.com')
    llm = AlternatingLockedPovOpeningLLM()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    before_chapters = db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id))
    before_drafts = db_session.scalar(select(func.count()).select_from(ChapterDraft).join(Chapter).where(Chapter.world_id == world_id))

    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '建立林砚追查玉佩并保护师妹的开篇动机。'},
        headers=auth(token),
    )

    assert response.status_code == 502
    assert response.json()['detail'] == 'MODEL_RESPONSE_INVALID'
    assert llm.calls == ['outline']
    db_session.expire_all()
    assert db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id)) == before_chapters
    assert db_session.scalar(select(func.count()).select_from(ChapterDraft).join(Chapter).where(Chapter.world_id == world_id)) == before_drafts


@pytest.mark.parametrize(
    'locked_pov',
    [
        '林砚第三人称限知。必要时进入沈微霜的内心。',
        '固定跟随林砚第三人称限知；后续从沈微霜感知补充信息。',
        '林砚第三人称限知，沈微霜偶有内心段落。',
    ],
)
def test_opening_contract_rejects_other_character_interior_access_before_writer_and_draft_write(
    client,
    db_session,
    monkeypatch,
    locked_pov,
):
    token, world_id = register_and_create_world(client, f'opening-implicit-multi-pov-{abs(hash(locked_pov))}@example.com')
    llm = OtherCharacterInteriorAccessOpeningLLM(locked_pov)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    before_chapters = db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id))
    before_drafts = db_session.scalar(select(func.count()).select_from(ChapterDraft).join(Chapter).where(Chapter.world_id == world_id))

    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '建立林砚追查玉佩并保护师妹的开篇动机。'},
        headers=auth(token),
    )

    assert response.status_code == 502
    assert response.json()['detail'] == 'MODEL_RESPONSE_INVALID'
    assert llm.calls == ['outline']
    db_session.expire_all()
    assert db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id)) == before_chapters
    assert db_session.scalar(select(func.count()).select_from(ChapterDraft).join(Chapter).where(Chapter.world_id == world_id)) == before_drafts


def test_locked_pov_character_does_not_fall_back_after_conflicting_recommendation(client, db_session):
    _, world_id = register_and_create_world(client, 'opening-conflicting-recommended-pov@example.com')
    characters = list(db_session.scalars(select(narrative_service.Character).where(narrative_service.Character.world_id == world_id)))
    lin_yan = next(character for character in characters if character.name == '林砚')

    locked_character = narrative_service._locked_pov_character(
        characters,
        {'recommended_pov': {'character_id': lin_yan.id, 'name': '沈微霜'}},
        {'pov_suggestion': '林砚'},
    )

    assert locked_character is None


def test_opening_contract_locked_second_character_controls_outline_direct_draft_and_write_pov(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'opening-contract-second-pov@example.com')
    characters = list(db_session.scalars(select(narrative_service.Character).where(narrative_service.Character.world_id == world_id).order_by(narrative_service.Character.id)))
    assert len(characters) >= 2
    locked_character = next(character for character in characters if character.name == '沈微霜')

    direct_llm = ContractLockedSecondCharacterLLM()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: direct_llm)
    direct_response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={
            'chapter_goal': '建立沈微霜追查玉佩的开篇动机。',
            'execution_context': {
                'source_world_version': 1,
                'next_chapter_number': 1,
                'goal': '建立沈微霜追查玉佩的开篇动机。',
                'recommended_pov': {},
            },
        },
        headers=auth(token),
    )

    assert direct_response.status_code == 200
    direct_payload = direct_response.json()
    assert direct_llm.calls == ['outline', 'writer']
    assert len(direct_payload['content']) >= 300
    assert len(direct_payload['content'].split('\n\n')) >= 6
    assert direct_payload['quality_report']['status'] == 'pass'
    assert all(check['status'] == 'pass' for check in direct_payload['quality_report']['checks'])
    assert '沈微霜限知第三人称。' in '\n'.join(message['content'] for message in direct_llm.writer_messages[0])
    db_session.expire_all()
    assert db_session.get(Chapter, direct_payload['chapter_id']).pov_character_id == locked_character.id

    abandon_response = client.post(f"/chapters/{direct_payload['chapter_id']}/abandon", headers=auth(token), json={})
    assert abandon_response.status_code == 200
    outline_llm = ContractLockedSecondCharacterLLM()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: outline_llm)
    session_response = client.post(
        f'/worlds/{world_id}/chapters',
        json={
            'chapter_goal': '建立沈微霜追查玉佩的开篇动机。',
            'execution_context': {
                'source_world_version': 1,
                'next_chapter_number': 1,
                'goal': '建立沈微霜追查玉佩的开篇动机。',
                'recommended_pov': {},
            },
        },
        headers=auth(token),
    )
    assert session_response.status_code == 200
    chapter_id = session_response.json()['id']

    outline_response = client.post(f'/chapters/{chapter_id}/outline', headers=auth(token), json={})

    assert outline_response.status_code == 200
    db_session.expire_all()
    assert db_session.get(Chapter, chapter_id).pov_character_id == locked_character.id

    write_response = client.post(f'/chapters/{chapter_id}/write', headers=auth(token), json={})

    assert write_response.status_code == 200
    written_payload = write_response.json()
    assert outline_llm.calls == ['outline', 'writer']
    assert len(written_payload['content']) >= 300
    assert len(written_payload['content'].split('\n\n')) >= 6
    assert written_payload['quality_report']['status'] == 'pass'
    assert all(check['status'] == 'pass' for check in written_payload['quality_report']['checks'])
    assert '沈微霜限知第三人称。' in '\n'.join(message['content'] for message in outline_llm.writer_messages[0])
    db_session.expire_all()
    assert db_session.get(Chapter, chapter_id).pov_character_id == locked_character.id


def test_opening_contract_locked_second_character_with_lin_yan_body_is_blocked_before_pov_confirmation(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'opening-contract-second-pov-mismatch@example.com')
    llm = ContractLockedSecondCharacterButLinYanBodyLLM()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    before_world_version = db_session.get(World, world_id).world_version
    before_events = db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id))
    before_character_statuses = {
        character.id: character.status
        for character in db_session.scalars(
            select(narrative_service.Character).where(narrative_service.Character.world_id == world_id)
        )
    }

    draft_response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '建立沈微霜追查玉佩的开篇动机。'},
        headers=auth(token),
    )

    assert draft_response.status_code == 200
    draft = draft_response.json()
    assert llm.calls == ['outline', 'writer']
    assert draft['quality_report']['status'] == 'fail'
    failed_checks = {
        check['check'] for check in draft['quality_report']['checks'] if check['status'] == 'fail'
    }
    assert 'protagonist_identity' in failed_checks

    readiness = client.get(f"/chapters/{draft['chapter_id']}/approval-readiness", headers=auth(token))
    approval = client.post(
        f"/chapters/{draft['chapter_id']}/approve",
        headers=auth(token),
        json={'draft_version': draft['draft_version']},
    )

    assert readiness.status_code == 200
    assert readiness.json()['status'] == 'blocked'
    assert next(
        check['status'] for check in readiness.json()['checks'] if check['key'] == 'opening_quality'
    ) == 'fail'
    assert approval.status_code == 409
    assert approval.json()['detail'] == 'OPENING_QUALITY_BLOCKED'
    db_session.expire_all()
    assert db_session.get(Chapter, draft['chapter_id']).status == 'reviewing'
    assert db_session.get(World, world_id).world_version == before_world_version
    assert db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id)) == before_events
    assert {
        character.id: character.status
        for character in db_session.scalars(
            select(narrative_service.Character).where(narrative_service.Character.world_id == world_id)
        )
    } == before_character_statuses


def test_client_chapter_number_cannot_bypass_opening_pipeline(client, monkeypatch):
    token, world_id = register_and_create_world(client, 'opening-context-authoritative@example.com')
    llm = OpeningQualityLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)

    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={
            'chapter_goal': '建立林砚追查玉佩并保护师妹的开篇动机。',
            'execution_context': {
                'source': 'manual',
                'source_world_version': 1,
                'next_chapter_number': 2,
                'goal': '客户端试图跳过开篇流程。',
            },
        },
        headers=auth(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert llm.calls == ['outline', 'writer']
    assert payload['execution_context']['next_chapter_number'] == 1
    assert payload['quality_report']['profile'] == 'opening_chapter'


@pytest.mark.parametrize('field', OPENING_CHECKS)
def test_opening_contract_rejects_blank_strings(field):
    payload = opening_contract().model_dump()
    payload[field] = ' \t '

    with pytest.raises(ValidationError):
        OpeningContract(**payload)


def test_first_chapter_direct_draft_fails_closed_when_client_has_no_callable_outline(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'opening-writer-only@example.com')
    llm = WriterOnlyOpeningLLM()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    before_world_version = db_session.get(World, world_id).world_version
    before_events = db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id))
    before_chapters = db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id))
    before_drafts = db_session.scalar(select(func.count()).select_from(ChapterDraft).join(Chapter).where(Chapter.world_id == world_id))

    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '建立林砚追查玉佩并保护师妹的开篇动机。'},
        headers=auth(token),
    )

    assert response.status_code == 502
    assert response.json()['detail'] == 'MODEL_RESPONSE_INVALID'
    assert llm.calls == []
    db_session.expire_all()
    assert db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id)) == before_chapters
    assert db_session.scalar(select(func.count()).select_from(ChapterDraft).join(Chapter).where(Chapter.world_id == world_id)) == before_drafts
    assert db_session.get(World, world_id).world_version == before_world_version
    assert db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id)) == before_events


def test_first_chapter_rejects_outline_without_opening_contract_before_writer(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'opening-contract-direct@example.com')
    llm = MissingOpeningContractLLM()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    before_world_version = db_session.get(World, world_id).world_version
    before_events = db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id))
    before_chapters = db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id))
    before_drafts = db_session.scalar(select(func.count()).select_from(ChapterDraft).join(Chapter).where(Chapter.world_id == world_id))

    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '建立林砚追查玉佩并保护师妹的开篇动机。'},
        headers=auth(token),
    )

    assert response.status_code == 502
    assert response.json()['detail'] == 'MODEL_RESPONSE_INVALID'
    assert llm.calls == ['outline']
    db_session.expire_all()
    assert db_session.scalar(select(func.count()).select_from(Chapter).where(Chapter.world_id == world_id)) == before_chapters
    assert db_session.scalar(select(func.count()).select_from(ChapterDraft).join(Chapter).where(Chapter.world_id == world_id)) == before_drafts
    assert db_session.get(World, world_id).world_version == before_world_version
    assert db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id)) == before_events


def test_explicit_first_chapter_outline_requires_opening_contract(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'opening-contract-outline@example.com')
    llm = MissingOpeningContractLLM()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    before_world_version = db_session.get(World, world_id).world_version
    before_events = db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id))

    session_response = client.post(
        f'/worlds/{world_id}/chapters',
        json={'chapter_goal': '建立林砚追查玉佩并保护师妹的开篇动机。'},
        headers=auth(token),
    )
    assert session_response.status_code == 200
    chapter_id = session_response.json()['id']

    response = client.post(f'/chapters/{chapter_id}/outline', headers=auth(token), json={})

    assert response.status_code == 502
    assert response.json()['detail'] == 'MODEL_RESPONSE_INVALID'
    assert llm.calls == ['outline']
    db_session.expire_all()
    chapter = db_session.get(Chapter, chapter_id)
    assert chapter.status == 'drafting'
    assert chapter.outline_beats == []
    assert chapter.outline_context == {}
    assert db_session.scalar(select(func.count()).select_from(ChapterDraft).where(ChapterDraft.chapter_id == chapter_id)) == 0
    assert db_session.get(World, world_id).world_version == before_world_version
    assert db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id)) == before_events


def test_write_first_chapter_without_opening_contract_rejects_before_writer_and_preserves_state(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'opening-write-contract-required@example.com')
    llm = OpeningQualityLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    before_world_version = db_session.get(World, world_id).world_version
    before_events = db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id))

    session_response = client.post(
        f'/worlds/{world_id}/chapters',
        json={'chapter_goal': '建立林砚追查玉佩并保护师妹的开篇动机。'},
        headers=auth(token),
    )
    assert session_response.status_code == 200
    chapter_id = session_response.json()['id']

    response = client.post(
        f'/chapters/{chapter_id}/write',
        json={'outline_beats': opening_beat_cards()},
        headers=auth(token),
    )

    assert response.status_code == 409
    assert response.json()['detail'] == 'OPENING_CONTRACT_REQUIRED'
    assert llm.calls == []
    db_session.expire_all()
    chapter = db_session.get(Chapter, chapter_id)
    assert chapter.status == 'drafting'
    assert db_session.scalar(select(func.count()).select_from(ChapterDraft).where(ChapterDraft.chapter_id == chapter_id)) == 0
    assert db_session.get(World, world_id).world_version == before_world_version
    assert db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id)) == before_events


def test_legacy_opening_context_without_contract_is_blocked_by_readiness_and_approval(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'opening-legacy-contractless@example.com')
    llm = OpeningQualityLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    draft_response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '建立林砚追查玉佩并保护师妹的开篇动机。'},
        headers=auth(token),
    )
    assert draft_response.status_code == 200
    draft = draft_response.json()
    chapter = db_session.get(Chapter, draft['chapter_id'])
    chapter.outline_context = {}
    draft_record = db_session.get(ChapterDraft, draft['draft_id'])
    draft_record.quality_report = {}
    db_session.commit()

    readiness = client.get(f"/chapters/{draft['chapter_id']}/approval-readiness", headers=auth(token))
    assert readiness.status_code == 200
    opening_quality = next(check for check in readiness.json()['checks'] if check['key'] == 'opening_quality')
    assert opening_quality['status'] == 'fail'
    assert readiness.json()['status'] == 'blocked'

    approval = client.post(f"/chapters/{draft['chapter_id']}/approve", headers=auth(token), json={})
    assert approval.status_code == 409
    assert approval.json()['detail'] == 'OPENING_QUALITY_RECHECK_REQUIRED'


def test_legacy_opening_quality_report_without_validation_version_requires_recheck(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'opening-quality-legacy-version@example.com')
    llm = OpeningQualityLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    draft_response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '建立林砚追查玉佩并保护师妹的开篇动机。'},
        headers=auth(token),
    )

    assert draft_response.status_code == 200
    draft = draft_response.json()
    assert draft['quality_report']['status'] == 'pass'

    draft_record = db_session.get(ChapterDraft, draft['draft_id'])
    legacy_quality_report = dict(draft_record.quality_report)
    legacy_quality_report.pop('validation_version', None)
    draft_record.quality_report = legacy_quality_report
    db_session.commit()

    before_world_version = db_session.get(World, world_id).world_version
    before_events = db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id))
    before_chapter_status = db_session.get(Chapter, draft['chapter_id']).status

    readiness = client.get(f"/chapters/{draft['chapter_id']}/approval-readiness", headers=auth(token))

    assert readiness.status_code == 200
    opening_quality = next(check for check in readiness.json()['checks'] if check['key'] == 'opening_quality')
    assert opening_quality['status'] == 'fail'
    assert readiness.json()['status'] == 'blocked'

    approval = client.post(f"/chapters/{draft['chapter_id']}/approve", headers=auth(token), json={})

    assert approval.status_code == 409
    assert approval.json()['detail'] == 'OPENING_QUALITY_RECHECK_REQUIRED'
    db_session.expire_all()
    assert db_session.get(Chapter, draft['chapter_id']).status == before_chapter_status == 'reviewing'
    assert db_session.get(World, world_id).world_version == before_world_version
    assert db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id)) == before_events


def test_stale_opening_quality_blocks_approval_and_readiness_marks_it_failed(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'opening-quality-stale@example.com')
    llm = OpeningQualityLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    draft_response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '建立林砚追查玉佩并保护师妹的开篇动机。'},
        headers=auth(token),
    )
    assert draft_response.status_code == 200
    draft = draft_response.json()
    assert draft['quality_report']['status'] == 'pass'

    edit_response = client.put(
        f"/chapters/{draft['chapter_id']}/draft",
        json={'content': f"{draft['content']}\n\n林砚在雨声中重新握紧玉佩。", 'change_summary': '形成未重新检查的第二版'},
        headers=auth(token),
    )
    assert edit_response.status_code == 200
    assert edit_response.json()['draft_version'] == 2
    before_world_version = db_session.get(World, world_id).world_version
    before_events = db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id))

    readiness = client.get(f"/chapters/{draft['chapter_id']}/approval-readiness", headers=auth(token))
    assert readiness.status_code == 200
    opening_quality = next(check for check in readiness.json()['checks'] if check['key'] == 'opening_quality')
    assert opening_quality['status'] == 'fail'
    assert readiness.json()['status'] == 'blocked'

    approval = client.post(f"/chapters/{draft['chapter_id']}/approve", headers=auth(token), json={})

    assert approval.status_code == 409
    assert approval.json()['detail'] == 'OPENING_QUALITY_RECHECK_REQUIRED'
    db_session.expire_all()
    chapter = db_session.get(Chapter, draft['chapter_id'])
    assert chapter.status == 'reviewing'
    assert chapter.draft_version == 2
    assert db_session.get(World, world_id).world_version == before_world_version
    assert db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id)) == before_events


def test_rewrite_second_opening_draft_rechecks_current_version_and_blocks_invalid_evidence(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'opening-quality-rewrite-v2@example.com')
    llm = OpeningQualityLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)
    draft_response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '建立林砚追查玉佩并保护师妹的开篇动机。'},
        headers=auth(token),
    )
    assert draft_response.status_code == 200
    draft = draft_response.json()

    edit_response = client.put(
        f"/chapters/{draft['chapter_id']}/draft",
        json={'content': f"{draft['content']}\n\n林砚在雨声中重新握紧玉佩。", 'change_summary': '先形成第二版再重写'},
        headers=auth(token),
    )
    assert edit_response.status_code == 200
    assert edit_response.json()['draft_version'] == 2

    invalid_evidence = opening_evidence(opening_body())[:-1]
    invalid_evidence[0] = OpeningEvidence(check='background', paragraph_index=0, quote='正文中不存在的背景引文')
    invalid_writer = OpeningQualityLLMClient(evidence=invalid_evidence)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: invalid_writer)
    rewrite = client.post(f"/chapters/{draft['chapter_id']}/write", headers=auth(token), json={})

    assert rewrite.status_code == 200
    rewritten = rewrite.json()
    assert invalid_writer.calls == ['writer']
    assert rewritten['draft_version'] == 2
    assert rewritten['quality_report']['evaluated_draft_version'] == 2
    assert rewritten['quality_report']['status'] == 'fail'
    before_world_version = db_session.get(World, world_id).world_version
    before_events = db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id))

    approval = client.post(f"/chapters/{draft['chapter_id']}/approve", headers=auth(token), json={})

    assert approval.status_code == 409
    assert approval.json()['detail'] == 'OPENING_QUALITY_BLOCKED'
    db_session.expire_all()
    assert db_session.get(World, world_id).world_version == before_world_version
    assert db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id)) == before_events


def test_opening_quality_failure_blocks_approval_without_committing_world_or_event_log(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'opening-quality-fail@example.com')
    invalid_evidence = opening_evidence(opening_body())[:-1]
    invalid_evidence[0] = OpeningEvidence(check='background', paragraph_index=0, quote='正文中不存在的背景引文')
    llm = OpeningQualityLLMClient(evidence=invalid_evidence)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)

    draft_response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '建立林砚追查玉佩并保护师妹的开篇动机。'},
        headers=auth(token),
    )
    assert draft_response.status_code == 200
    draft = draft_response.json()
    assert llm.calls == ['outline', 'writer']
    assert draft['quality_report']['profile'] == 'opening_chapter'
    assert draft['quality_report']['status'] == 'fail'
    assert {check['check'] for check in draft['quality_report']['checks']} == set(OPENING_CHECKS)
    assert any(check['status'] == 'fail' for check in draft['quality_report']['checks'])

    before_world_version = db_session.get(World, world_id).world_version
    before_events = db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id))
    approval = client.post(f"/chapters/{draft['chapter_id']}/approve", headers=auth(token), json={})

    assert approval.status_code == 409
    assert approval.json()['detail'] == 'OPENING_QUALITY_BLOCKED'
    db_session.expire_all()
    assert db_session.get(World, world_id).world_version == before_world_version
    assert db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id)) == before_events


# RED fixtures: every check points to the exact same otherwise-valid evidence location.
def repeated_opening_evidence() -> list[OpeningEvidence]:
    return [
        OpeningEvidence(check=check, paragraph_index=0, quote='林砚替师门送药归来')
        for check in OPENING_CHECKS
    ]


def test_opening_quality_evaluator_rejects_reused_evidence_across_checks():
    report = narrative_service._evaluate_opening_quality(
        opening_body(),
        repeated_opening_evidence(),
        opening_contract().model_dump(),
        draft_version=1,
        locked_pov_character_name='林砚',
    )

    assert report['status'] == 'fail'
    statuses = {check['check']: check['status'] for check in report['checks']}
    for check in OPENING_CHECKS[:-1]:
        assert statuses[check] == 'fail'


# Zero-cognition anchors are optional contract fields surfaced as advisories.
# The contract fixture above deliberately omits them, so it doubles as the
# backward-compatibility case for outlines stored before the fields existed.
def zero_cognition_contract(**overrides) -> OpeningContract:
    contract = opening_contract().model_dump()
    contract.update(
        inciting_incident='今晚城主府的文书送到，要求林砚天亮前交出玉佩。',
        prior_state='他原本只是每日替师门送药的外门弟子。',
        grounded_emotion='他害怕师妹被带走之后再也接不回来。',
    )
    contract.update(overrides)
    return OpeningContract(**contract)


def test_opening_advisories_report_missing_when_contract_omits_anchors():
    advisories = narrative_service._evaluate_opening_advisories(
        opening_body(),
        opening_contract().model_dump(),
    )

    assert [advisory['check'] for advisory in advisories] == list(narrative_service.OPENING_ADVISORY_CHECKS)
    assert {advisory['state'] for advisory in advisories} == {'missing'}
    assert all(advisory['blocking'] is False for advisory in advisories)


def test_opening_advisories_flag_weak_when_contract_declares_anchor_body_omits():
    body = '\n\n'.join(['一段与锚点信号无关的正文。'] * 6)

    advisories = narrative_service._evaluate_opening_advisories(
        body,
        zero_cognition_contract().model_dump(),
    )

    states = {advisory['check']: advisory['state'] for advisory in advisories}
    assert states == {check: 'weak' for check in narrative_service.OPENING_ADVISORY_CHECKS}
    assert all(advisory['blocking'] is False for advisory in advisories)


# The core invariant of this feature: advisories are informational only. A draft whose
# body lands none of the anchors must still pass, and the hard gate's check list must
# keep its exact six items and order.
def test_opening_advisories_never_affect_status_or_hard_gate_checks():
    report = narrative_service._evaluate_opening_quality(
        opening_body(),
        opening_evidence(opening_body()),
        zero_cognition_contract(
            inciting_incident='与正文毫无信号重叠的触发事件描述。',
            prior_state='与正文毫无信号重叠的起点状态描述。',
            grounded_emotion='与正文毫无信号重叠的情感锚点描述。',
        ).model_dump(),
        draft_version=1,
        locked_pov_character_name='林砚',
    )

    assert report['status'] == 'pass'
    assert [check['check'] for check in report['checks']] == list(OPENING_CHECKS)
    assert all(advisory['blocking'] is False for advisory in report['advisories'])


def test_opening_advisories_report_present_when_body_lands_every_anchor():
    advisories = narrative_service._evaluate_opening_advisories(
        opening_body() + '\n\n林砚一直担心师妹被带走，今天终于收到城主府的文书。',
        zero_cognition_contract().model_dump(),
    )

    assert {advisory['state'] for advisory in advisories} == {'present'}
    assert all(advisory['blocking'] is False for advisory in advisories)


def test_term_advisory_reports_missing_when_no_known_term_appears():
    advisory = narrative_service._evaluate_opening_term_advisory(opening_body(), {'不在正文里的名字'})

    assert advisory['check'] == narrative_service.OPENING_TERM_ADVISORY_CHECK
    assert advisory['state'] == 'missing'
    assert advisory['term_count'] == 0
    assert advisory['unglossed_terms'] == []
    assert advisory['blocking'] is False


def test_term_advisory_accepts_apposition_right_after_the_term():
    body = '\n\n'.join(['林砚是替师门送药的外门弟子，今夜必须赶回宗门。'] * 6)

    advisory = narrative_service._evaluate_opening_term_advisory(body, {'林砚'})

    assert advisory['state'] == 'present'
    assert advisory['unglossed_terms'] == []


# Guards the reason gloss detection is not a plain sentence-wide '是' search:
# '为何' and '不是' occur in ordinary prose, so a naive check would call every
# draft explained and the advisory would never fire.
def test_term_advisory_flags_term_whose_sentence_only_has_incidental_copula_characters():
    body = '\n\n'.join(['沈微霜问他为何不逃，这不是能算清的账。'] * 6)

    advisory = narrative_service._evaluate_opening_term_advisory(body, {'沈微霜'})

    assert advisory['state'] == 'weak'
    assert advisory['unglossed_terms'] == ['沈微霜']
    assert advisory['blocking'] is False


def test_term_advisory_prefers_longer_name_over_its_prefix():
    body = '\n\n'.join(['沈微霜是潜伏在青岚城的医师。'] * 6)

    advisory = narrative_service._evaluate_opening_term_advisory(body, {'沈微', '沈微霜'})

    # '沈微' only ever appears as a prefix of the glossed longer name, so neither is flagged.
    assert advisory['state'] == 'present'
    assert advisory['unglossed_terms'] == []


def test_term_advisory_caps_named_samples_but_keeps_full_list():
    body = '\n\n'.join(['铜铃、云纹、靴印、药箱与暗井接连出现，没有任何交代。'] * 6)
    terms = {'铜铃', '云纹', '靴印', '药箱', '暗井'}

    advisory = narrative_service._evaluate_opening_term_advisory(body, terms)

    assert advisory['state'] == 'weak'
    assert len(advisory['unglossed_terms']) == len(terms)
    assert f'等 {len(terms)} 个' in advisory['message']


def test_term_advisory_tolerates_absent_and_blank_term_input():
    for terms in (None, set(), {'', '   '}):
        advisory = narrative_service._evaluate_opening_term_advisory(opening_body(), terms)

        assert advisory['state'] == 'missing'
        assert advisory['blocking'] is False


def test_term_advisory_rides_along_quality_report_without_touching_the_hard_gate():
    report = narrative_service._evaluate_opening_quality(
        opening_body(),
        opening_evidence(opening_body()),
        opening_contract().model_dump(),
        draft_version=1,
        locked_pov_character_name='林砚',
        known_character_names={'林砚', '沈微霜'},
    )

    assert report['status'] == 'pass'
    assert [check['check'] for check in report['checks']] == list(OPENING_CHECKS)
    advisory_checks = [advisory['check'] for advisory in report['advisories']]
    assert advisory_checks == [
        *narrative_service.OPENING_ADVISORY_CHECKS,
        narrative_service.OPENING_TERM_ADVISORY_CHECK,
    ]
    assert all(advisory['blocking'] is False for advisory in report['advisories'])


# ----- 术语密度提示（jargon_density advisory）-----


@pytest.mark.parametrize('known_terms', [None, set()])
def test_term_advisory_reports_missing_without_a_term_list(known_terms):
    advisory = narrative_service._evaluate_opening_term_advisory(opening_body(), known_terms)

    assert advisory['state'] == 'missing'
    assert advisory['term_count'] == 0
    assert advisory['unglossed_terms'] == []
    assert advisory['blocking'] is False


# Guards the reason gloss detection is not a plain sentence-wide '是' search:
# '为何' and '不是' occur in almost every Chinese sentence.
def test_term_advisory_rejects_copula_not_adjacent_to_the_term():
    body = '\n\n'.join(['林砚问他为何不逃，可师妹还在等药。'] * 6)

    advisory = narrative_service._evaluate_opening_term_advisory(body, {'林砚'})

    assert advisory['state'] == 'weak'
    assert '林砚' in advisory['unglossed_terms']


def test_term_advisory_accepts_gloss_phrase_anywhere_in_the_sentence():
    body = '\n\n'.join(['林砚追查玉佩主人，也就是失踪的师兄。'] * 6)

    advisory = narrative_service._evaluate_opening_term_advisory(body, {'林砚'})

    assert advisory['state'] == 'present'
    assert advisory['unglossed_terms'] == []


def test_term_advisory_samples_first_three_unglossed_terms():
    body = '\n\n'.join(['林砚、沈微霜、师兄、师妹、巡夜人一起走在雨中。'] * 6)

    advisory = narrative_service._evaluate_opening_term_advisory(
        body, {'林砚', '沈微霜', '师兄', '师妹', '巡夜人'}
    )

    assert advisory['state'] == 'weak'
    assert advisory['term_count'] == 5
    assert len(advisory['unglossed_terms']) == 5
    # Message should sample only the first three, with "等 5 个" suffix
    assert advisory['message'].count('"') <= 6  # at most 3 terms quoted
    assert '等 5 个' in advisory['message']


def test_term_advisory_ignores_substring_when_longer_name_is_present():
    body = '\n\n'.join(['沈微霜在巷口停下，雨水顺着伞骨落进泥里。'] * 6)

    advisory = narrative_service._evaluate_opening_term_advisory(body, {'沈微', '沈微霜'})

    # '沈微' appears only as part of '沈微霜', so it should not be counted separately
    assert advisory['term_count'] == 1
    assert '沈微霜' in [t for t in advisory['unglossed_terms']]
    assert '沈微' not in [t for t in advisory['unglossed_terms']]


def test_full_opening_quality_report_includes_term_advisory():
    report = narrative_service._evaluate_opening_quality(
        opening_body(),
        opening_evidence(opening_body()),
        zero_cognition_contract().model_dump(),
        draft_version=1,
        locked_pov_character_name='林砚',
    )

    advisory_checks = [advisory['check'] for advisory in report['advisories']]
    assert advisory_checks == [
        *narrative_service.OPENING_ADVISORY_CHECKS,
        narrative_service.OPENING_TERM_ADVISORY_CHECK,
    ]
    # The hard gate keeps its exact six items, and the term hint never blocks.
    assert report['status'] == 'pass'
    assert [check['check'] for check in report['checks']] == OPENING_CHECKS
    assert all(advisory['blocking'] is False for advisory in report['advisories'])


def test_opening_advisories_never_affect_quality_status_or_checks():
    """The hard gate must stay byte-identical whether or not anchors are present."""
    without_anchors = narrative_service._evaluate_opening_quality(
        opening_body(),
        opening_evidence(opening_body()),
        opening_contract().model_dump(),
        draft_version=1,
        locked_pov_character_name='林砚',
    )
    with_anchors = narrative_service._evaluate_opening_quality(
        opening_body(),
        opening_evidence(opening_body()),
        zero_cognition_contract().model_dump(),
        draft_version=1,
        locked_pov_character_name='林砚',
    )

    assert without_anchors['status'] == with_anchors['status'] == 'pass'
    assert without_anchors['checks'] == with_anchors['checks']
    # Only the advisory payload differs; the gate's item set and order are untouched.
    assert [check['check'] for check in with_anchors['checks']] == OPENING_CHECKS
    assert without_anchors['advisories'] != with_anchors['advisories']


def test_reused_opening_evidence_blocks_approval_without_writing_canon(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client, 'opening-quality-reused-evidence@example.com')
    llm = OpeningQualityLLMClient(evidence=repeated_opening_evidence())
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm)

    draft_response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '建立林砚追查玉佩并保护师妹的开篇动机。'},
        headers=auth(token),
    )
    assert draft_response.status_code == 200
    draft = draft_response.json()
    chapter = db_session.get(Chapter, draft['chapter_id'])
    locked_character = db_session.get(narrative_service.Character, chapter.pov_character_id)
    assert locked_character is not None
    before_world_version = db_session.get(World, world_id).world_version
    before_events = db_session.scalar(select(func.count()).select_from(EventLog).where(EventLog.world_id == world_id))

    readiness = client.get(f"/chapters/{draft['chapter_id']}/approval-readiness", headers=auth(token))
    approval = client.post(
        f"/chapters/{draft['chapter_id']}/approve",
        headers=auth(token),
        json=opening_pov_confirmation(draft['draft_version'], locked_character),
    )

    observed = {
        'quality_status': draft['quality_report']['status'],
        'readiness_status': readiness.json()['status'],
        'opening_quality_status': next(
            check['status'] for check in readiness.json()['checks'] if check['key'] == 'opening_quality'
        ),
        'approval_status': approval.status_code,
        'approval_detail': approval.json().get('detail'),
    }
    assert observed == {
        'quality_status': 'fail',
        'readiness_status': 'blocked',
        'opening_quality_status': 'fail',
        'approval_status': 409,
        'approval_detail': 'OPENING_QUALITY_BLOCKED',
    }
    assert_approval_writes_are_unchanged(
        db_session, world_id, draft['chapter_id'], before_world_version, before_events
    )


def test_opening_quality_evaluator_rejects_quote_borrowing_contract_support_from_same_sentence():
    evidence = opening_evidence(opening_body())
    evidence[2] = OpeningEvidence(
        check='motivation',
        paragraph_index=1,
        quote='城主府的文书写明天亮前要带走她问话',
    )
    evidence[3] = OpeningEvidence(
        check='personality_evidence_plan',
        paragraph_index=2,
        quote='巷口的药箱被雨水冲翻',
    )

    report = narrative_service._evaluate_opening_quality(
        opening_body(),
        evidence,
        opening_contract().model_dump(),
        draft_version=1,
        locked_pov_character_name='林砚',
    )

    statuses = {check['check']: check['status'] for check in report['checks']}
    assert statuses['motivation'] == 'fail'
    assert statuses['personality_evidence_plan'] == 'fail'


def test_opening_quality_evaluator_rejects_overlapping_quote_spans_across_checks():
    evidence = opening_evidence(opening_body())
    evidence[1] = OpeningEvidence(
        check='protagonist_identity',
        paragraph_index=1,
        quote=(
            '他是欠着师门药债的外门弟子，今夜原该回去照看师妹。'
            '可城主府的文书写明天亮前要带走她问话，林砚只能追查玉佩与失踪师兄的名字'
        ),
    )

    report = narrative_service._evaluate_opening_quality(
        opening_body(),
        evidence,
        opening_contract().model_dump(),
        draft_version=1,
        locked_pov_character_name='林砚',
    )

    statuses = {check['check']: check['status'] for check in report['checks']}
    assert statuses['protagonist_identity'] == 'fail'
    assert statuses['motivation'] == 'fail'


def test_opening_quality_evaluator_rejects_entity_only_evidence_for_intent_slots():
    evidence = opening_evidence(opening_body())
    evidence[2] = OpeningEvidence(
        check='motivation',
        paragraph_index=0,
        quote='掌心的裂纹玉佩忽然发烫',
    )
    evidence[4] = OpeningEvidence(
        check='conflict_goal',
        paragraph_index=3,
        quote='玉佩映出师兄惯用的云纹',
    )

    report = narrative_service._evaluate_opening_quality(
        opening_body(),
        evidence,
        opening_contract().model_dump(),
        draft_version=1,
        locked_pov_character_name='林砚',
    )

    statuses = {check['check']: check['status'] for check in report['checks']}
    assert statuses['motivation'] == 'fail'
    assert statuses['conflict_goal'] == 'fail'


def test_opening_quality_evaluator_rejects_unique_evidence_mapped_to_wrong_contract_slots():
    wrong_slot_evidence = [
        OpeningEvidence(check='background', paragraph_index=1, quote='欠着师门药债的外门弟子'),
        OpeningEvidence(check='protagonist_identity', paragraph_index=1, quote='只能追查玉佩与失踪师兄的名字'),
        OpeningEvidence(check='motivation', paragraph_index=2, quote='先扑进泥水把药瓶一只只捡回'),
        OpeningEvidence(check='personality_evidence_plan', paragraph_index=4, quote='必须在铜铃停在巷口前确认玉佩主人'),
        OpeningEvidence(check='conflict_goal', paragraph_index=0, quote='废弃灵井却在巷尾吐出温热白雾'),
        OpeningEvidence(check='locked_pov', paragraph_index=5, quote='林砚的靴底刚离开井沿'),
    ]

    report = narrative_service._evaluate_opening_quality(
        opening_body(),
        wrong_slot_evidence,
        opening_contract().model_dump(),
        draft_version=1,
        locked_pov_character_name='林砚',
    )

    assert report['status'] == 'fail'
    statuses = {check['check']: check['status'] for check in report['checks']}
    for check in OPENING_CHECKS[:-1]:
        assert statuses[check] == 'fail'


def test_opening_quality_evaluator_rejects_locked_pov_evidence_with_only_external_action():
    evidence = opening_evidence(opening_body())
    evidence[5] = OpeningEvidence(
        check='locked_pov',
        paragraph_index=5,
        quote='林砚的靴底刚离开井沿',
    )

    report = narrative_service._evaluate_opening_quality(
        opening_body(),
        evidence,
        opening_contract().model_dump(),
        draft_version=1,
        locked_pov_character_name='林砚',
    )

    statuses = {check['check']: check['status'] for check in report['checks']}
    assert all(statuses[check] == 'pass' for check in OPENING_CHECKS[:-1])
    assert report['status'] == 'fail'
    assert statuses['locked_pov'] == 'fail'


def test_opening_quality_evaluator_rejects_non_overlapping_quotes_reused_from_same_sentence():
    paragraphs = opening_body().split('\n\n')
    paragraphs[1] = (
        '他是欠着师门药债的外门弟子，今夜原该回去照看师妹。'
        '林砚必须查清裂纹玉佩为何牵连师门，同时赶在城主府巡夜人发现前确认暗井中的玉佩属于失踪师兄。'
    )
    body = '\n\n'.join(paragraphs)
    evidence = opening_evidence(body)
    evidence[2] = OpeningEvidence(
        check='motivation',
        paragraph_index=1,
        quote='林砚必须查清裂纹玉佩为何牵连师门',
    )
    evidence[4] = OpeningEvidence(
        check='conflict_goal',
        paragraph_index=1,
        quote='赶在城主府巡夜人发现前确认暗井中的玉佩属于失踪师兄',
    )

    report = narrative_service._evaluate_opening_quality(
        body,
        evidence,
        opening_contract().model_dump(),
        draft_version=1,
        locked_pov_character_name='林砚',
    )

    checks = {check['check']: check for check in report['checks']}
    assert report['status'] == 'fail'
    assert checks['motivation']['status'] == 'fail'
    assert checks['conflict_goal']['status'] == 'fail'
    assert '同一句' in checks['motivation']['message']
    assert '不能跨检查复用' in checks['conflict_goal']['message']


def test_opening_quality_evaluator_rejects_locked_pov_subjectivity_owned_by_other_character():
    paragraphs = opening_body().split('\n\n')
    paragraphs[3] = (
        '灵井底下传来铁链拖地声，玉佩映出师兄惯用的云纹。'
        '林砚回头时，沈微霜以为他已经发现了秘密。'
        '随后林砚沿着井壁摸到一道新鲜的靴印，听见城主府巡夜人的铜铃越来越近。'
    )
    body = '\n\n'.join(paragraphs)
    evidence = opening_evidence(body)
    evidence[5] = OpeningEvidence(
        check='locked_pov',
        paragraph_index=3,
        quote='林砚回头时，沈微霜以为他已经发现了秘密',
    )

    report = narrative_service._evaluate_opening_quality(
        body,
        evidence,
        opening_contract().model_dump(),
        draft_version=1,
        locked_pov_character_name='林砚',
    )

    checks = {check['check']: check for check in report['checks']}
    assert len(paragraphs) == 6
    assert len(body) >= 300
    assert all(checks[check]['status'] == 'pass' for check in OPENING_CHECKS[:-1])
    assert report['status'] == 'fail'
    assert checks['locked_pov']['status'] == 'fail'
    assert '主观信号未明确归属于锁定角色' in checks['locked_pov']['message']


def test_opening_quality_evaluator_rejects_unpunctuated_other_character_subjectivity_for_locked_pov():
    paragraphs = opening_body().split('\n\n')
    quote = '林砚回头时沈微霜以为他已经发现了秘密'
    paragraphs[3] = (
        '灵井底下传来铁链拖地声，玉佩映出师兄惯用的云纹。'
        f'{quote}。'
        '随后林砚沿着井壁摸到一道新鲜的靴印，听见城主府巡夜人的铜铃越来越近。'
    )
    body = '\n\n'.join(paragraphs)
    evidence = opening_evidence(body)
    evidence[5] = OpeningEvidence(
        check='locked_pov',
        paragraph_index=3,
        quote=quote,
    )

    report = narrative_service._evaluate_opening_quality(
        body,
        evidence,
        opening_contract().model_dump(),
        draft_version=1,
        locked_pov_character_name='林砚',
    )

    checks = {check['check']: check for check in report['checks']}
    assert len(paragraphs) == 6
    assert len(body) >= 300
    assert quote in paragraphs[3]
    assert paragraphs[3].count(quote) == 1
    assert all(checks[check]['status'] == 'pass' for check in OPENING_CHECKS[:-1])
    assert report['status'] == 'fail'
    assert checks['locked_pov']['status'] == 'fail'
    assert '主观信号未明确归属于锁定角色' in checks['locked_pov']['message']


@pytest.mark.parametrize(
    'quote',
    [
        '林砚看见沈微霜以为他已经发现了秘密',
        '林砚觉得沈微霜知道暗井里藏着什么',
        '林砚意识到沈微霜害怕巡夜人发现她',
        '林砚觉得不安沈微霜后才意识到门已锁死',
    ],
)
def test_opening_quality_evaluator_rejects_unpunctuated_subjectivity_owned_by_known_other_character(quote):
    paragraphs = opening_body().split('\n\n')
    paragraphs[3] = (
        '灵井底下传来铁链拖地声，玉佩映出师兄惯用的云纹。'
        f'{quote}。'
        '随后林砚沿着井壁摸到一道新鲜的靴印，听见城主府巡夜人的铜铃越来越近。'
    )
    body = '\n\n'.join(paragraphs)
    evidence = opening_evidence(body)
    evidence[5] = OpeningEvidence(
        check='locked_pov',
        paragraph_index=3,
        quote=quote,
    )

    report = narrative_service._evaluate_opening_quality(
        body,
        evidence,
        opening_contract().model_dump(),
        draft_version=1,
        locked_pov_character_name='林砚',
        known_character_names={'林砚', '沈微霜'},
    )

    checks = {check['check']: check for check in report['checks']}
    assert len(paragraphs) == 6
    assert len(body) >= 300
    assert quote in paragraphs[3]
    assert paragraphs[3].count(quote) == 1
    assert all(checks[check]['status'] == 'pass' for check in OPENING_CHECKS[:-1])
    assert report['status'] == 'fail'
    assert checks['locked_pov']['status'] == 'fail'
    assert (
        '其他角色主观信号' in checks['locked_pov']['message']
        or '主观信号未唯一归属于锁定角色' in checks['locked_pov']['message']
    )


def test_opening_quality_evaluator_accepts_withholding_self_reference_when_character_names_overlap():
    report = narrative_service._evaluate_opening_quality(
        opening_body(),
        opening_evidence(opening_body()),
        opening_contract().model_dump(),
        draft_version=1,
        locked_pov_character_name='林砚',
        known_character_names={'林砚', '沈微', '沈微霜'},
    )

    checks = {check['check']: check for check in report['checks']}
    assert report['status'] == 'pass'
    assert checks['locked_pov']['status'] == 'pass'


def test_opening_quality_evaluator_rejects_subjectivity_owned_by_overlapping_longer_character_name():
    quote = '沈微霜以为铜铃已经停了'
    paragraphs = opening_body().split('\n\n')
    paragraphs[3] = (
        '灵井底下传来铁链拖地声，玉佩映出师兄惯用的云纹。'
        f'{quote}。'
        '随后林砚沿着井壁摸到一道新鲜的靴印，听见城主府巡夜人的铜铃越来越近。'
    )
    body = '\n\n'.join(paragraphs)
    evidence = opening_evidence(body)
    evidence[5] = OpeningEvidence(
        check='locked_pov',
        paragraph_index=3,
        quote=quote,
    )

    report = narrative_service._evaluate_opening_quality(
        body,
        evidence,
        opening_contract().model_dump(),
        draft_version=1,
        locked_pov_character_name='沈微',
        known_character_names={'沈微', '沈微霜'},
    )

    checks = {check['check']: check for check in report['checks']}
    assert all(checks[check]['status'] == 'pass' for check in OPENING_CHECKS[:-1])
    assert report['status'] == 'fail'
    assert checks['locked_pov']['status'] == 'fail'
    assert '显式包含锁定角色全名' in checks['locked_pov']['message']
