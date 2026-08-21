from copy import deepcopy

from sqlalchemy import select

from app.character.models import Character
from app.event.models import EventLog
from app.foreshadow.models import Foreshadow, ForeshadowEvent
from app.llm.schemas import BeatCard, ChapterGeneration, ChapterOutline, OpeningContract, OpeningEvidence, ProposedCharacterChange, ProposedForeshadowChange
from app.narrative import service as narrative_service
from app.narrative.models import Chapter, ChapterDraft
from app.narrative.schemas import ApproveRequest
from app.world.models import World


def opening_body() -> str:
    return '\n\n'.join([
        '林砚在灵井旁听见了第二个人的脚步声。雨水压低了青岚城的屋檐，废弃灵井却在巷尾吐出温热白雾；城里人人都说灵脉衰退只是旱灾，他知道那是谎话。',
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


class DraftVersioningLLMClient:
    def __init__(self):
        self.revision_calls = 0
        self.paragraph_calls = 0
        self.outline_messages = []
        self.generation_messages = []
        self.revision_messages = []
        self.paragraph_messages = []

    def generate_outline(self, messages):
        # Keep planning traffic separate from writer traffic so call-order tests
        # can distinguish the first-chapter outline from generation/revision calls.
        self.outline_messages.append(messages)
        return opening_outline()

    def generate_chapter(self, messages):
        self.generation_messages.append(messages)
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

    def revise_paragraph(self, messages):
        self.paragraph_calls += 1
        self.paragraph_messages = messages
        return type(
            'ParagraphRevisionResult',
            (),
            {
                'paragraph': '第二段：沈微霜没有立刻交出湿信，而是先问林砚是否愿意承担真相的代价。',
                'revision_note': '增强第二段的悬念与人物试探。',
            },
        )()

    def revise_chapter(self, messages):
        self.revision_calls += 1
        self.revision_messages = messages
        generation = self.generate_chapter(messages)
        generation.title = '第一章 雨巷密谈（修订版）'
        generation.context_summary = '根据审稿意见强化林砚的试探过程。'
        generation.review_hints = ['确认修订后 Critic 高风险是否解除']
        generation.proposed_character_changes = [
            ProposedCharacterChange(character_id=1, status='谨慎试探沈微霜', current_goals=['验证湿信来源'])
        ]
        generation.proposed_foreshadow_changes = [
            ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='修订版继续推进玉佩线索')
        ]
        return generation


def register_and_create_world(client):
    token = client.post('/auth/register', json={'email': 'draft-versioning@example.com', 'password': 'strongpass123'}).json()[
        'access_token'
    ]
    world = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {token}'}).json()
    return token, world['id']


def create_reviewing_draft(client, token, world_id, monkeypatch, llm_client=None):
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: llm_client or DraftVersioningLLMClient())
    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进雨巷密谈'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == 200
    return response.json()


def get_drafts_for_chapter(db_session, chapter_id):
    return list(
        db_session.scalars(
            select(ChapterDraft).where(ChapterDraft.chapter_id == chapter_id).order_by(ChapterDraft.draft_version)
        )
    )


def opening_outline() -> ChapterOutline:
    return ChapterOutline(
        beats=[
            BeatCard(
                beat_id='opening-1',
                summary='林砚在雨夜灵井追查裂纹玉佩。',
                pov_character='林砚',
                location='青岚城灵井',
                emotional_arc='焦灼 -> 警觉',
                key_dialogue_hints=['师妹还在等药。'],
            )
        ],
        core_conflict='林砚必须在巡夜人抵达前确认玉佩主人的身份。',
        pov_suggestion='林砚',
        pacing='雨夜悬疑，逐段增加巡夜压力。',
        role_skill_targets=['林砚'],
        opening_contract=OpeningContract(
            background='青岚城灵脉衰退，废弃灵井在雨夜发出异响。',
            protagonist_identity='林砚是为师门债务奔走的外门弟子。',
            motivation='他必须查清裂纹玉佩为何牵连师门，避免师妹被城主府带走。',
            personality_evidence_plan='让林砚先救下被雨水冲走的药箱，再隐瞒手伤继续追查。',
            conflict_goal='在巡夜人发现前确认暗井中的玉佩是否属于失踪师兄。',
            locked_pov='林砚限知第三人称。',
        ),
    )


def test_manual_edit_creates_new_draft_version_without_mutating_world(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)
    original_content = draft['content']
    edited_content = '第一段：林砚停在雨巷口，掌心的玉佩微微发烫。\n\n第二段：沈微霜递来一封湿透的信。\n\n第三段：远处城主府钟声响起。'

    response = client.put(
        f"/chapters/{draft['chapter_id']}/draft",
        json={'content': edited_content, 'change_summary': '强化第一段玉佩反应'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['draft_version'] == 2
    assert payload['content'] == edited_content
    assert payload['change_type'] == 'manual_edit'
    assert payload['change_summary'] == '强化第一段玉佩反应'
    assert payload['parent_draft_version'] == 1

    db_session.expire_all()
    chapter = db_session.get(Chapter, draft['chapter_id'])
    world = db_session.get(World, world_id)
    drafts = get_drafts_for_chapter(db_session, draft['chapter_id'])

    assert chapter.draft_version == 2
    assert world.world_version == 1
    assert [item.draft_version for item in drafts] == [1, 2]
    assert drafts[0].content == original_content
    assert drafts[1].content == edited_content


def test_active_session_restores_complete_draft_version_history_without_mutating_world(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)
    headers = {'Authorization': f'Bearer {token}'}
    before_event_count = db_session.query(EventLog).filter_by(world_id=world_id).count()

    edited_content = '第一段：林砚停在雨巷口，玉佩发烫。\n\n第二段：沈微霜递来湿信。\n\n第三段：钟声响起。'
    edit_response = client.put(
        f"/chapters/{draft['chapter_id']}/draft",
        json={'content': edited_content, 'change_summary': '形成第二版'},
        headers=headers,
    )
    assert edit_response.status_code == 200
    stash_response = client.post(
        f"/chapters/{draft['chapter_id']}/draft/stash",
        json={'note': '形成第三版快照'},
        headers=headers,
    )
    assert stash_response.status_code == 200

    response = client.get(f'/worlds/{world_id}/chapters/active', headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload['chapter']['id'] == draft['chapter_id']
    assert payload['chapter']['draft_version'] == 3
    assert payload['draft']['draft_version'] == 3
    assert payload['draft']['content'] == edited_content
    assert payload['draft_versions'] == [1, 2, 3]

    db_session.expire_all()
    world = db_session.get(World, world_id)
    chapter = db_session.get(Chapter, draft['chapter_id'])
    assert world.world_version == 1
    assert chapter.status == 'reviewing'
    assert chapter.approved_version is None
    assert db_session.query(EventLog).filter_by(world_id=world_id).count() == before_event_count


def test_stash_creates_snapshot_version_with_same_content(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)

    response = client.post(
        f"/chapters/{draft['chapter_id']}/draft/stash",
        json={'note': '开始人工改稿前暂存'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['draft_version'] == 2
    assert payload['content'] == draft['content']
    assert payload['change_type'] == 'stash'
    assert payload['change_summary'] == '开始人工改稿前暂存'
    assert payload['parent_draft_version'] == 1

    db_session.expire_all()
    chapter = db_session.get(Chapter, draft['chapter_id'])
    world = db_session.get(World, world_id)
    drafts = get_drafts_for_chapter(db_session, draft['chapter_id'])

    assert chapter.draft_version == 2
    assert world.world_version == 1
    assert [item.content for item in drafts] == [draft['content'], draft['content']]


def test_paragraph_rewrite_only_changes_target_paragraph_and_versions_draft(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    fake_client = DraftVersioningLLMClient()
    draft = create_reviewing_draft(client, token, world_id, monkeypatch, fake_client)

    response = client.post(
        f"/chapters/{draft['chapter_id']}/draft/paragraph",
        json={'paragraph_index': 1, 'mode': 'rewrite', 'instruction': '增强悬念和人物试探'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    payload = response.json()
    expected_paragraphs = draft['content'].split('\n\n')
    expected_paragraphs[1] = '第二段：沈微霜没有立刻交出湿信，而是先问林砚是否愿意承担真相的代价。'
    expected_content = '\n\n'.join(expected_paragraphs)
    assert payload['draft_version'] == 2
    assert payload['content'] == expected_content
    assert payload['change_type'] == 'paragraph_rewrite'
    assert payload['parent_draft_version'] == 1
    assert '增强第二段的悬念与人物试探' in payload['change_summary']
    system_prompt = fake_client.paragraph_messages[0]['content']
    assert '有效 JSON' in system_prompt
    assert '"paragraph"' in system_prompt
    assert '"revision_note"' in system_prompt

    db_session.expire_all()
    chapter = db_session.get(Chapter, draft['chapter_id'])
    world = db_session.get(World, world_id)
    drafts = get_drafts_for_chapter(db_session, draft['chapter_id'])

    assert chapter.draft_version == 2
    assert world.world_version == 1
    assert drafts[0].content == draft['content']
    assert drafts[1].content == expected_content


def test_paragraph_selection_text_rewrites_only_selected_span(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    fake_client = DraftVersioningLLMClient()
    draft = create_reviewing_draft(client, token, world_id, monkeypatch, fake_client)

    original_paragraphs = draft['content'].split('\n\n')
    target = original_paragraphs[1]
    selection = target[:10]

    response = client.post(
        f"/chapters/{draft['chapter_id']}/draft/paragraph",
        json={
            'paragraph_index': 1,
            'mode': 'polish',
            'instruction': '让这个片段更克制',
            'selection_text': selection,
        },
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    payload = response.json()
    updated_paragraphs = payload['content'].split('\n\n')
    # Only target paragraph changed; others identical
    assert updated_paragraphs[0] == original_paragraphs[0]
    assert updated_paragraphs[2] == original_paragraphs[2]
    assert updated_paragraphs[1] != target
    # The untouched suffix of the paragraph must remain
    assert updated_paragraphs[1].endswith(target[10:])
    assert '选中片段' in payload['change_summary']
    # The mock revision span should be embedded
    assert '第二段：沈微霜没有立刻交出湿信' in updated_paragraphs[1]
    assert '选中的片段' in fake_client.paragraph_messages[1]['content']
    assert selection in fake_client.paragraph_messages[1]['content']


def test_paragraph_selection_text_not_found_returns_400(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    fake_client = DraftVersioningLLMClient()
    draft = create_reviewing_draft(client, token, world_id, monkeypatch, fake_client)

    response = client.post(
        f"/chapters/{draft['chapter_id']}/draft/paragraph",
        json={
            'paragraph_index': 0,
            'mode': 'polish',
            'instruction': '测试',
            'selection_text': '这段文字根本不存在',
        },
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 400
    assert response.json()['detail'] == 'SELECTION_TEXT_NOT_FOUND'
    db_session.expire_all()
    chapter = db_session.get(Chapter, draft['chapter_id'])
    assert chapter.draft_version == 1


def test_mock_paragraph_rewrite_api_versions_and_preserves_non_target_paragraphs(client, db_session, monkeypatch):
    monkeypatch.setenv('LLM_MOCK', 'true')
    narrative_service.get_settings.cache_clear()
    token, world_id = register_and_create_world(client)
    source_world_version = db_session.get(World, world_id).world_version
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进当前冲突'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert draft.status_code == 200
    draft_payload = draft.json()
    original_paragraphs = draft_payload['content'].split('\n\n')
    target_index = len(original_paragraphs) // 2
    current_paragraph = original_paragraphs[target_index]
    instruction = '提高这一段的紧张感，同时保留已有信息。'

    response = client.post(
        f"/chapters/{draft_payload['chapter_id']}/draft/paragraph",
        json={'paragraph_index': target_index, 'mode': 'rewrite', 'instruction': instruction},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    payload = response.json()
    revised_paragraphs = payload['content'].split('\n\n')
    assert payload['draft_version'] == draft_payload['draft_version'] + 1
    assert payload['parent_draft_version'] == draft_payload['draft_version']
    assert payload['change_type'] == 'paragraph_rewrite'
    assert revised_paragraphs[:target_index] == original_paragraphs[:target_index]
    assert revised_paragraphs[target_index + 1:] == original_paragraphs[target_index + 1:]
    assert revised_paragraphs[target_index] != current_paragraph
    assert current_paragraph in revised_paragraphs[target_index]
    assert instruction in revised_paragraphs[target_index]

    db_session.expire_all()
    assert db_session.get(World, world_id).world_version == source_world_version


def test_archived_world_rejects_draft_lifecycle_mutations(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)
    edited_content = '第一段：林砚停在雨巷口，玉佩微微发烫。\n\n第二段：沈微霜递来一封湿透的信。'

    archive_response = client.patch(f'/worlds/{world_id}/status', headers={'Authorization': f'Bearer {token}'}, json={'status': 'archived'})
    assert archive_response.status_code == 200

    edit_response = client.put(
        f"/chapters/{draft['chapter_id']}/draft",
        json={'content': edited_content, 'change_summary': '归档后不应编辑'},
        headers={'Authorization': f'Bearer {token}'},
    )
    stash_response = client.post(
        f"/chapters/{draft['chapter_id']}/draft/stash",
        json={'note': '归档后不应暂存'},
        headers={'Authorization': f'Bearer {token}'},
    )
    paragraph_response = client.post(
        f"/chapters/{draft['chapter_id']}/draft/paragraph",
        json={'paragraph_index': 1, 'mode': 'rewrite', 'instruction': '归档后不应改写'},
        headers={'Authorization': f'Bearer {token}'},
    )
    revise_response = client.post(
        f"/chapters/{draft['chapter_id']}/draft/revise",
        json={'instruction': '归档后不应修订'},
        headers={'Authorization': f'Bearer {token}'},
    )

    for response in (edit_response, stash_response, paragraph_response, revise_response):
        assert response.status_code == 409
        assert response.json()['detail'] == 'WORLD_ARCHIVED'

    db_session.expire_all()
    world = db_session.get(World, world_id)
    chapter = db_session.get(Chapter, draft['chapter_id'])
    drafts = get_drafts_for_chapter(db_session, draft['chapter_id'])
    assert world.world_version == 1
    assert chapter.draft_version == 1
    assert [item.draft_version for item in drafts] == [1]
    assert drafts[0].content == draft['content']


def test_draft_lifecycle_rejects_extra_body_fields_without_side_effects(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)
    fake_client = DraftVersioningLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: fake_client)

    chapter = db_session.get(Chapter, draft['chapter_id'])
    world = db_session.get(World, world_id)
    drafts = get_drafts_for_chapter(db_session, draft['chapter_id'])
    before_chapter_status = chapter.status
    before_chapter_draft_version = chapter.draft_version
    before_world_version = world.world_version
    before_event_count = db_session.query(EventLog).filter_by(world_id=world_id).count()
    before_draft_versions = [item.draft_version for item in drafts]
    before_draft_contents = [item.content for item in drafts]

    cases = [
        (
            client.post,
            f"/chapters/{draft['chapter_id']}/reject",
            {'feedback': '此处反馈应被额外字段拦截。', 'raw_text': 'reject raw payload'},
        ),
        (
            client.put,
            f"/chapters/{draft['chapter_id']}/draft",
            {
                'content': '第一段：这份手动改稿不应被保存，因为请求包含额外字段。',
                'change_summary': '额外字段拒绝',
                'raw_text': 'edit raw payload',
            },
        ),
        (
            client.post,
            f"/chapters/{draft['chapter_id']}/draft/stash",
            {'note': '此暂存不应创建版本。', 'raw_text': 'stash raw payload'},
        ),
        (
            client.post,
            f"/chapters/{draft['chapter_id']}/draft/revise",
            {'instruction': '这次修订不应调用模型。', 'raw_text': 'revise raw payload'},
        ),
        (
            client.post,
            f"/chapters/{draft['chapter_id']}/draft/paragraph",
            {
                'paragraph_index': 1,
                'mode': 'rewrite',
                'instruction': '这次段落改写不应调用模型。',
                'raw_text': 'paragraph raw payload',
            },
        ),
    ]

    for method, url, payload in cases:
        response = method(url, json=payload, headers={'Authorization': f'Bearer {token}'})

        assert response.status_code == 422
        assert any(
            error['type'] == 'extra_forbidden' and error['loc'] == ['body', 'raw_text']
            for error in response.json()['detail']
        )

        db_session.expire_all()
        chapter = db_session.get(Chapter, draft['chapter_id'])
        world = db_session.get(World, world_id)
        drafts = get_drafts_for_chapter(db_session, draft['chapter_id'])

        assert chapter.status == before_chapter_status
        assert chapter.draft_version == before_chapter_draft_version
        assert world.world_version == before_world_version
        assert [item.draft_version for item in drafts] == before_draft_versions
        assert [item.content for item in drafts] == before_draft_contents
        assert db_session.query(EventLog).filter_by(world_id=world_id).count() == before_event_count
        assert fake_client.revision_calls == 0
        assert fake_client.paragraph_calls == 0


def test_abandon_releases_active_session_preserves_draft_history_and_blocks_chapter_writes(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)
    headers = {'Authorization': f'Bearer {token}'}

    edited_content = '第一段：林砚停在雨巷口，掌心的玉佩微微发烫。\n\n第二段：沈微霜递来一封湿透的信。\n\n第三段：远处城主府钟声响起。'
    edit_response = client.put(
        f"/chapters/{draft['chapter_id']}/draft",
        json={'content': edited_content, 'change_summary': '强化第一段玉佩反应'},
        headers=headers,
    )
    assert edit_response.status_code == 200

    before_world = db_session.get(World, world_id)
    before_character = db_session.get(Character, 1)
    before_foreshadow = db_session.get(Foreshadow, 1)
    before_event_count = db_session.query(EventLog).filter_by(world_id=world_id).count()
    before_foreshadow_event_count = db_session.query(ForeshadowEvent).count()
    before_world_projection = {
        'world_version': before_world.world_version,
        'truth_canon': before_world.truth_canon,
        'truth_canon_version': before_world.truth_canon_version,
        'current_characters': deepcopy(before_world.current_characters),
        'current_foreshadows': deepcopy(before_world.current_foreshadows),
        'current_relations': deepcopy(before_world.current_relations),
    }
    before_character_state = (before_character.status, deepcopy(before_character.current_goals))
    before_foreshadow_state = (before_foreshadow.status, before_foreshadow.description)

    active_before = client.get(f'/worlds/{world_id}/chapters/active', headers=headers)
    assert active_before.status_code == 200
    assert active_before.json()['chapter']['id'] == draft['chapter_id']
    assert active_before.json()['draft_versions'] == [1, 2]

    first_abandon = client.post(f"/chapters/{draft['chapter_id']}/abandon", headers=headers, json={})
    second_abandon = client.post(f"/chapters/{draft['chapter_id']}/abandon", headers=headers, json={})

    for response in (first_abandon, second_abandon):
        assert response.status_code == 200
        payload = response.json()
        assert payload['id'] == draft['chapter_id']
        assert payload['status'] == 'abandoned'
        assert payload['draft_version'] == 2
        assert payload['approved_version'] is None
        assert payload['approved_content'] is None

    read_v1 = client.get(f"/chapters/{draft['chapter_id']}/drafts/1", headers=headers)
    read_v2 = client.get(f"/chapters/{draft['chapter_id']}/drafts/2", headers=headers)
    diff_response = client.get(f"/chapters/{draft['chapter_id']}/drafts/diff?from=1&to=2", headers=headers)

    assert read_v1.status_code == 200
    assert read_v1.json()['content'] == draft['content']
    assert read_v1.json()['draft_version'] == 1
    assert read_v2.status_code == 200
    assert read_v2.json()['content'] == edited_content
    assert read_v2.json()['draft_version'] == 2
    assert diff_response.status_code == 200
    assert diff_response.json()['from_content'] == draft['content']
    assert diff_response.json()['to_content'] == edited_content
    assert {'type': 'removed', 'text': draft['content'].split('\n\n')[0]} in diff_response.json()['diff_lines']
    assert {'type': 'added', 'text': edited_content.split('\n\n')[0]} in diff_response.json()['diff_lines']

    blocked_responses = [
        client.get(f"/chapters/{draft['chapter_id']}/approval-preview", headers=headers),
        client.get(f"/chapters/{draft['chapter_id']}/approval-readiness", headers=headers),
        client.post(
            f"/chapters/{draft['chapter_id']}/approval-consistency",
            json={'draft_version': 2},
            headers=headers,
        ),
        client.post(
            f"/chapters/{draft['chapter_id']}/approve",
            headers=headers,
            json={},
        ),
        client.post(
            f"/chapters/{draft['chapter_id']}/reject",
            json={'feedback': '废弃后不应驳回'},
            headers=headers,
        ),
        client.put(
            f"/chapters/{draft['chapter_id']}/draft",
            json={'content': edited_content + '\n\n尾声：这次编辑不应保存。', 'change_summary': '废弃后编辑'},
            headers=headers,
        ),
        client.post(
            f"/chapters/{draft['chapter_id']}/draft/stash",
            json={'note': '废弃后暂存'},
            headers=headers,
        ),
        client.post(
            f"/chapters/{draft['chapter_id']}/draft/revise",
            json={'instruction': '废弃后不应继续修订'},
            headers=headers,
        ),
        client.post(
            f"/chapters/{draft['chapter_id']}/draft/paragraph",
            json={'paragraph_index': 1, 'mode': 'rewrite', 'instruction': '废弃后不应段落改写'},
            headers=headers,
        ),
    ]
    for response in blocked_responses:
        assert response.status_code == 409
        assert response.json()['detail'] == 'CHAPTER_ABANDONED'

    active_after = client.get(f'/worlds/{world_id}/chapters/active', headers=headers)
    assert active_after.status_code == 200
    assert active_after.json() == {'chapter': None, 'draft': None, 'draft_versions': [], 'recent_approval': None}

    new_draft_response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '废弃旧章后创建新章'},
        headers=headers,
    )
    assert new_draft_response.status_code == 200
    assert new_draft_response.json()['chapter_id'] != draft['chapter_id']

    db_session.expire_all()
    world = db_session.get(World, world_id)
    chapter = db_session.get(Chapter, draft['chapter_id'])
    drafts = get_drafts_for_chapter(db_session, draft['chapter_id'])
    new_chapter = db_session.get(Chapter, new_draft_response.json()['chapter_id'])
    character = db_session.get(Character, 1)
    foreshadow = db_session.get(Foreshadow, 1)

    assert chapter.status == 'abandoned'
    assert chapter.draft_version == 2
    assert chapter.approved_version is None
    assert chapter.approved_content is None
    assert [item.draft_version for item in drafts] == [1, 2]
    assert [item.content for item in drafts] == [draft['content'], edited_content]
    assert world.world_version == before_world_projection['world_version']
    assert world.truth_canon == before_world_projection['truth_canon']
    assert world.truth_canon_version == before_world_projection['truth_canon_version']
    assert world.current_characters == before_world_projection['current_characters']
    assert world.current_foreshadows == before_world_projection['current_foreshadows']
    assert world.current_relations == before_world_projection['current_relations']
    assert (character.status, character.current_goals) == before_character_state
    assert (foreshadow.status, foreshadow.description) == before_foreshadow_state
    assert db_session.query(EventLog).filter_by(world_id=world_id).count() == before_event_count
    assert db_session.query(ForeshadowEvent).count() == before_foreshadow_event_count
    assert db_session.query(EventLog).filter_by(world_id=world_id, event_type='chapter_approved').count() == 0
    assert db_session.query(EventLog).filter_by(world_id=world_id, event_type='foreshadow_advanced').count() == 0
    assert db_session.query(EventLog).filter_by(world_id=world_id, event_type='foreshadow_resolved').count() == 0
    assert db_session.query(EventLog).filter_by(world_id=world_id, event_type='foreshadow_expired').count() == 0
    assert new_chapter is not None
    assert new_chapter.status == 'reviewing'
def test_draft_diff_endpoint_returns_line_changes_between_versions(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)
    edited_content = '第一段：林砚停在雨巷口，掌心的玉佩微微发烫。\n\n第二段：沈微霜递来一封湿透的信。\n\n第三段：远处城主府钟声响起。'
    edit_response = client.put(
        f"/chapters/{draft['chapter_id']}/draft",
        json={'content': edited_content, 'change_summary': '强化第一段玉佩反应'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert edit_response.status_code == 200

    response = client.get(
        f"/chapters/{draft['chapter_id']}/drafts/diff?from=1&to=2",
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['chapter_id'] == draft['chapter_id']
    assert payload['from_version'] == 1
    assert payload['to_version'] == 2
    assert payload['from_content'] == draft['content']
    assert payload['to_content'] == edited_content
    assert {'type': 'removed', 'text': draft['content'].split('\n\n')[0]} in payload['diff_lines']
    assert {'type': 'added', 'text': edited_content.split('\n\n')[0]} in payload['diff_lines']


def test_approval_preview_describes_world_state_changes_before_commit(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)

    response = client.get(
        f"/chapters/{draft['chapter_id']}/approval-preview",
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['chapter_id'] == draft['chapter_id']
    assert payload['draft_version'] == 1
    assert payload['source_world_version'] == 1
    assert payload['current_world_version'] == 1
    assert payload['will_increment_world_version'] is True
    assert payload['world_version_before'] == 1
    assert payload['world_version_after'] == 2
    assert payload['version_conflict'] is False
    assert payload['warnings'] == []

    character_change = payload['character_changes'][0]
    assert character_change['character_id'] == 1
    assert character_change['name']
    assert character_change['after']['status'] == '开始调查密信'
    assert character_change['after']['current_goals'] == ['追查湿信来源']

    foreshadow_change = payload['foreshadow_changes'][0]
    assert foreshadow_change['foreshadow_id'] == 1
    assert foreshadow_change['title']
    assert foreshadow_change['before']['status'] == 'planted'
    assert foreshadow_change['after']['status'] == 'advanced'
    assert '湿信推进玉佩线索' in foreshadow_change['after']['description']


def test_full_draft_revision_creates_new_version_from_review_context_without_mutating_world(client, db_session, monkeypatch):
    token, world_id = register_and_create_world(client)
    fake_client = DraftVersioningLLMClient()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: fake_client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: fake_client)
    chapter = db_session.get(Chapter, draft['chapter_id'])
    chapter.critique_report = {
        'chapter_id': chapter.id,
        'draft_version': 1,
        'current_draft_version': 1,
        'is_stale': False,
        'overall_score': 71,
        'summary': '人物信任转折过快。',
        'dimensions': {},
        'issues': [
            {
                'severity': 'high',
                'dimension': 'character_consistency',
                'message': '林砚突然信任沈微霜。',
                'paragraph_index': 0,
                'suggested_action': '补足试探。',
            }
        ],
        'suggestions': ['增加试探动作。'],
        'created_at': '2026-05-30T00:00:00Z',
    }
    chapter.character_arc_report = {
        'chapter_id': chapter.id,
        'draft_version': 1,
        'current_draft_version': 1,
        'is_stale': False,
        'summary': '角色弧线需要补足选择铺垫。',
        'character_arcs': [
            {
                'character_id': 1,
                'name': '林砚',
                'continuity_risk': 'high',
                'risk_reason': '选择缺少铺垫。',
                'suggested_revision': '加入试探沈微霜。',
            }
        ],
        'relationship_notes': [],
        'progression_hints': [],
        'created_at': '2026-05-30T00:00:00Z',
    }
    db_session.commit()

    response = client.post(
        f"/chapters/{draft['chapter_id']}/draft/revise",
        json={'instruction': '保留雨巷会面，但补足林砚试探沈微霜的过程。'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['draft_version'] == 2
    assert payload['parent_draft_version'] == 1
    assert payload['change_type'] == 'revision'
    assert payload['change_summary'] == '保留雨巷会面，但补足林砚试探沈微霜的过程。'
    assert payload['title'] == '第一章 雨巷密谈（修订版）'
    assert payload['proposed_changes']['characters'][0]['status'] == '谨慎试探沈微霜'

    db_session.expire_all()
    world = db_session.get(World, world_id)
    chapter = db_session.get(Chapter, draft['chapter_id'])
    drafts = get_drafts_for_chapter(db_session, draft['chapter_id'])
    event_types = [event.event_type for event in db_session.query(EventLog).filter_by(world_id=world_id).order_by(EventLog.id)]

    assert world.world_version == 1
    assert chapter.draft_version == 2
    assert chapter.status == 'reviewing'
    assert [item.draft_version for item in drafts] == [1, 2]
    assert drafts[0].content == draft['content']
    assert drafts[1].change_type == 'revision'
    assert event_types == ['WORLD_CREATED']

    joined_messages = '\n'.join(message['content'] for message in fake_client.revision_messages)
    assert '保留雨巷会面，但补足林砚试探沈微霜的过程。' in joined_messages
    assert '人物信任转折过快。' in joined_messages
    assert '角色弧线需要补足选择铺垫。' in joined_messages
    assert '存在建议复核项，请确认后再批准。' in joined_messages
    assert '本章执行上下文' in joined_messages


def test_full_revision_of_opening_chapter_requires_fresh_opening_evidence(client, db_session, monkeypatch):
    class OpeningRevisionLLM(DraftVersioningLLMClient):
        def generate_outline(self, messages):
            return opening_outline()

        def generate_chapter(self, messages):
            from test_narrative_approval import opening_body

            generation = super().generate_chapter(messages)
            generation.draft_content = opening_body()
            generation.opening_evidence = [
                OpeningEvidence(check='background', paragraph_index=0, quote='废弃灵井却在巷尾吐出温热白雾'),
                OpeningEvidence(check='protagonist_identity', paragraph_index=1, quote='欠着师门药债的外门弟子'),
                OpeningEvidence(check='motivation', paragraph_index=1, quote='只能追查玉佩与失踪师兄的名字'),
                OpeningEvidence(check='personality_evidence_plan', paragraph_index=2, quote='先扑进泥水把药瓶一只只捡回'),
                OpeningEvidence(check='conflict_goal', paragraph_index=4, quote='必须在铜铃停在巷口前确认玉佩主人'),
                OpeningEvidence(check='locked_pov', paragraph_index=3, quote='林砚没有告诉沈微霜自己看见了什么'),
            ]
            return generation

        def revise_chapter(self, messages):
            self.revision_calls += 1
            self.revision_messages = messages
            generation = self.generate_chapter(messages)
            generation.title = '第一章 暗井回声（修订版）'
            return generation

    token, world_id = register_and_create_world(client)
    fake_client = OpeningRevisionLLM()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: fake_client)
    draft = create_reviewing_draft(
        client,
        token,
        world_id,
        monkeypatch,
        fake_client,
    )

    response = client.post(
        f"/chapters/{draft['chapter_id']}/draft/revise",
        json={'instruction': '在不改变开篇承诺的前提下润色全文。'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['draft_version'] == 2
    assert payload['quality_report']['profile'] == 'opening_chapter'
    assert payload['quality_report']['status'] == 'pass'
    assert payload['quality_report']['evaluated_draft_version'] == 2
    joined_messages = '\n'.join(message['content'] for message in fake_client.revision_messages)
    assert 'opening_evidence' in joined_messages


def test_full_revision_of_opening_chapter_without_evidence_cannot_reuse_old_pass(client, monkeypatch):
    class MissingOpeningEvidenceRevisionLLM(DraftVersioningLLMClient):
        def generate_outline(self, messages):
            return opening_outline()

        def generate_chapter(self, messages):
            from test_narrative_approval import opening_body

            generation = super().generate_chapter(messages)
            generation.draft_content = opening_body()
            generation.opening_evidence = [
                OpeningEvidence(check='background', paragraph_index=0, quote='废弃灵井却在巷尾吐出温热白雾'),
                OpeningEvidence(check='protagonist_identity', paragraph_index=1, quote='欠着师门药债的外门弟子'),
                OpeningEvidence(check='motivation', paragraph_index=1, quote='只能追查玉佩与失踪师兄的名字'),
                OpeningEvidence(check='personality_evidence_plan', paragraph_index=2, quote='先扑进泥水把药瓶一只只捡回'),
                OpeningEvidence(check='conflict_goal', paragraph_index=4, quote='必须在铜铃停在巷口前确认玉佩主人'),
                OpeningEvidence(check='locked_pov', paragraph_index=3, quote='林砚没有告诉沈微霜自己看见了什么'),
            ]
            return generation

        def revise_chapter(self, messages):
            self.revision_calls += 1
            self.revision_messages = messages
            generation = self.generate_chapter(messages)
            generation.opening_evidence = []
            return generation

    token, world_id = register_and_create_world(client)
    fake_client = MissingOpeningEvidenceRevisionLLM()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: fake_client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch, fake_client)

    response = client.post(
        f"/chapters/{draft['chapter_id']}/draft/revise",
        json={'instruction': '重写全文，但不要改变开篇信息。'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['draft_version'] == 2
    assert payload['quality_report']['profile'] == 'opening_chapter'
    assert payload['quality_report']['status'] == 'fail'
    assert payload['quality_report']['evaluated_draft_version'] == 2


def test_get_exact_draft_version_returns_requested_version(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)
    edited_content = (
        '第一段：林砚停在雨巷口，掌心的玉佩微微发烫。\n\n'
        '第二段：沈微霜递来一封湿透的信。\n\n'
        '第三段：远处城主府钟声响起。'
    )
    client.put(
        f"/chapters/{draft['chapter_id']}/draft",
        json={'content': edited_content, 'change_summary': '强化第一段玉佩反应'},
        headers={'Authorization': f'Bearer {token}'},
    )

    first = client.get(f"/chapters/{draft['chapter_id']}/drafts/1", headers={'Authorization': f'Bearer {token}'})
    second = client.get(f"/chapters/{draft['chapter_id']}/drafts/2", headers={'Authorization': f'Bearer {token}'})
    missing = client.get(f"/chapters/{draft['chapter_id']}/drafts/99", headers={'Authorization': f'Bearer {token}'})

    assert first.status_code == 200
    assert first.json()['draft_version'] == 1
    assert first.json()['content'] == draft['content']
    assert second.status_code == 200
    assert second.json()['draft_version'] == 2
    assert second.json()['content'] == edited_content
    assert missing.status_code == 404


def test_late_revision_cannot_create_draft_after_chapter_is_approved(client, db_session, monkeypatch, opening_approval_payload):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)
    user = db_session.get(World, world_id).owner

    class ApprovingRevisionLLM(DraftVersioningLLMClient):
        def revise_chapter(self, messages):
            generation = super().revise_chapter(messages)
            approved = narrative_service.approve_chapter(
                db_session,
                user,
                draft['chapter_id'],
                ApproveRequest.model_validate(opening_approval_payload(draft)),
            )
            assert approved.status == 'approved'
            return generation

    before_events = db_session.query(EventLog).filter_by(world_id=world_id).count()
    try:
        narrative_service.revise_chapter_draft(
            db_session,
            user,
            draft['chapter_id'],
            '批准完成后不应接受迟到修订。',
            llm_client=ApprovingRevisionLLM(),
        )
    except Exception as error:
        assert getattr(error, 'status_code', None) == 409
        assert getattr(error, 'detail', None) == 'ALREADY_APPROVED'
    else:
        raise AssertionError('expected ALREADY_APPROVED')

    db_session.expire_all()
    chapter = db_session.get(Chapter, draft['chapter_id'])
    assert chapter.status == 'approved'
    assert chapter.draft_version == draft['draft_version'] == 1
    assert chapter.approved_version == draft['draft_version']
    assert chapter.approved_content == draft['content']
    assert [item.draft_version for item in get_drafts_for_chapter(db_session, draft['chapter_id'])] == [1]
    assert db_session.get(World, world_id).world_version == 2
    assert db_session.query(EventLog).filter_by(world_id=world_id).count() > before_events
    assert db_session.query(EventLog).filter_by(world_id=world_id, event_type='chapter_approved').count() == 1


def test_late_paragraph_revision_cannot_create_draft_after_chapter_is_approved(client, db_session, monkeypatch, opening_approval_payload):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)
    user = db_session.get(World, world_id).owner

    class ApprovingParagraphLLM(DraftVersioningLLMClient):
        def revise_paragraph(self, messages):
            revision = super().revise_paragraph(messages)
            approved = narrative_service.approve_chapter(
                db_session,
                user,
                draft['chapter_id'],
                ApproveRequest.model_validate(opening_approval_payload(draft)),
            )
            assert approved.status == 'approved'
            return revision

    try:
        narrative_service.revise_chapter_paragraph(
            db_session,
            user,
            draft['chapter_id'],
            1,
            'rewrite',
            '增强人物试探。',
            llm_client=ApprovingParagraphLLM(),
        )
    except Exception as error:
        assert getattr(error, 'status_code', None) == 409
        assert getattr(error, 'detail', None) == 'ALREADY_APPROVED'
    else:
        raise AssertionError('expected ALREADY_APPROVED')

    db_session.expire_all()
    chapter = db_session.get(Chapter, draft['chapter_id'])
    assert chapter.status == 'approved'
    assert chapter.draft_version == draft['draft_version'] == 1
    assert chapter.approved_version == draft['draft_version']
    assert chapter.approved_content == draft['content']
    assert [item.draft_version for item in get_drafts_for_chapter(db_session, draft['chapter_id'])] == [1]
    assert db_session.get(World, world_id).world_version == 2
    assert db_session.query(EventLog).filter_by(world_id=world_id, event_type='chapter_approved').count() == 1


def test_revision_rejects_approved_chapter(client, monkeypatch, opening_approval_payload):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)
    approve = client.post(
        f"/chapters/{draft['chapter_id']}/approve",
        json=opening_approval_payload(draft),
        headers={'Authorization': f'Bearer {token}'},
    )
    assert approve.status_code == 200

    response = client.post(
        f"/chapters/{draft['chapter_id']}/draft/revise",
        json={'instruction': '批准后不允许再修订。'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 409
    assert response.json()['detail'] == 'ALREADY_APPROVED'


def test_revision_rejects_model_changes_for_unknown_ids(client, monkeypatch):
    class InvalidRevisionLLM(DraftVersioningLLMClient):
        def revise_chapter(self, messages):
            return ChapterGeneration(
                title='错误修订版',
                draft_content='错误修订正文。',
                context_summary='包含不存在角色。',
                review_hints=[],
                proposed_character_changes=[ProposedCharacterChange(character_id=999, status='不存在')],
                proposed_foreshadow_changes=[],
            )

    token, world_id = register_and_create_world(client)
    invalid_client = InvalidRevisionLLM()
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: invalid_client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: invalid_client)

    response = client.post(
        f"/chapters/{draft['chapter_id']}/draft/revise",
        json={'instruction': '触发非法角色 ID。'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 502
    assert response.json()['detail'] == 'MODEL_RESPONSE_INVALID'
