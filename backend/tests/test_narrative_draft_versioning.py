from sqlalchemy import select

from app.event.models import EventLog
from app.llm.schemas import ChapterGeneration, ProposedCharacterChange, ProposedForeshadowChange
from app.narrative import service as narrative_service
from app.narrative.models import Chapter, ChapterDraft
from app.world.models import World


class DraftVersioningLLMClient:
    def generate_chapter(self, messages):
        return ChapterGeneration(
            title='第一章 雨巷密谈',
            draft_content='第一段：林砚停在雨巷口。\n\n第二段：沈微霜递来一封湿透的信。\n\n第三段：远处城主府钟声响起。',
            context_summary='林砚与沈微霜在雨巷交换线索。',
            review_hints=['确认第二段的信息揭示是否过快'],
            proposed_character_changes=[
                ProposedCharacterChange(character_id=1, status='开始调查密信', current_goals=['追查湿信来源'])
            ],
            proposed_foreshadow_changes=[
                ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='湿信推进玉佩线索')
            ],
        )

    def revise_paragraph(self, messages):
        return type(
            'ParagraphRevisionResult',
            (),
            {
                'paragraph': '第二段：沈微霜没有立刻交出湿信，而是先问林砚是否愿意承担真相的代价。',
                'revision_note': '增强第二段的悬念与人物试探。',
            },
        )()

    def revise_chapter(self, messages):
        self.revision_messages = messages
        joined = '\n'.join(message['content'] for message in messages)
        return ChapterGeneration(
            title='第一章 雨巷密谈（修订版）',
            draft_content=f'修订版正文：{joined[:24]}',
            context_summary='根据审稿意见强化林砚的试探过程。',
            review_hints=['确认修订后 Critic 高风险是否解除'],
            proposed_character_changes=[
                ProposedCharacterChange(character_id=1, status='谨慎试探沈微霜', current_goals=['验证湿信来源'])
            ],
            proposed_foreshadow_changes=[
                ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='修订版继续推进玉佩线索')
            ],
        )


def register_and_create_world(client):
    token = client.post('/auth/register', json={'email': 'draft-versioning@example.com', 'password': 'strongpass123'}).json()[
        'access_token'
    ]
    world = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {token}'}).json()
    return token, world['id']


def create_reviewing_draft(client, token, world_id, monkeypatch):
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: DraftVersioningLLMClient())
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
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)

    response = client.post(
        f"/chapters/{draft['chapter_id']}/draft/paragraph",
        json={'paragraph_index': 1, 'mode': 'rewrite', 'instruction': '增强悬念和人物试探'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    payload = response.json()
    expected_content = (
        '第一段：林砚停在雨巷口。\n\n'
        '第二段：沈微霜没有立刻交出湿信，而是先问林砚是否愿意承担真相的代价。\n\n'
        '第三段：远处城主府钟声响起。'
    )
    assert payload['draft_version'] == 2
    assert payload['content'] == expected_content
    assert payload['change_type'] == 'paragraph_rewrite'
    assert payload['parent_draft_version'] == 1
    assert '增强第二段的悬念与人物试探' in payload['change_summary']

    db_session.expire_all()
    chapter = db_session.get(Chapter, draft['chapter_id'])
    world = db_session.get(World, world_id)
    drafts = get_drafts_for_chapter(db_session, draft['chapter_id'])

    assert chapter.draft_version == 2
    assert world.world_version == 1
    assert drafts[0].content == draft['content']
    assert drafts[1].content == expected_content


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
    assert {'type': 'removed', 'text': '第一段：林砚停在雨巷口。'} in payload['diff_lines']
    assert {'type': 'added', 'text': '第一段：林砚停在雨巷口，掌心的玉佩微微发烫。'} in payload['diff_lines']


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


def test_revision_rejects_approved_chapter(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    draft = create_reviewing_draft(client, token, world_id, monkeypatch)
    approve = client.post(f"/chapters/{draft['chapter_id']}/approve", headers={'Authorization': f'Bearer {token}'})
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
