from sqlalchemy import select

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
