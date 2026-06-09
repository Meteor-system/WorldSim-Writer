import base64
from io import BytesIO
from zipfile import ZipFile

from sqlalchemy import func, select

from app.llm.schemas import ChapterGeneration, ProposedCharacterChange, ProposedForeshadowChange
from app.narrative import service as narrative_service
from app.event.models import EventLog
from app.snapshot_export.models import WorldSnapshot
from app.world.models import World


class SnapshotExportLLMClient:
    def generate_chapter(self, messages):
        return ChapterGeneration(
            title='第一章 档案门廊',
            draft_content='林砚推开档案门廊，玉佩在掌心发亮。',
            context_summary='林砚发现门廊中的玉佩线索。',
            review_hints=['确认玉佩线索是否进入伏笔台账'],
            proposed_character_changes=[
                ProposedCharacterChange(character_id=1, status='追查档案门廊', current_goals=['确认玉佩来源'])
            ],
            proposed_foreshadow_changes=[
                ProposedForeshadowChange(foreshadow_id=1, status='advanced', description_note='玉佩线索推进')
            ],
        )


def create_draft(client, token, world_id, monkeypatch):
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: SnapshotExportLLMClient())
    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进档案门廊线索'},
        headers={'Authorization': f'Bearer {token}'},
    )
    assert response.status_code == 200
    return response.json()


def approve_chapter(client, token, world_id, monkeypatch):
    draft = create_draft(client, token, world_id, monkeypatch)
    response = client.post(f"/chapters/{draft['chapter_id']}/approve", headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    return response.json()


def register_and_create_world(client, email='snapshot@example.com'):
    token = client.post('/auth/register', json={'email': email, 'password': 'strongpass123'}).json()['access_token']
    world = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {token}'}).json()
    return token, world['id']


def auth_headers(token: str) -> dict[str, str]:
    return {'Authorization': f'Bearer {token}'}


def test_create_snapshot_freezes_current_world_version_without_mutating_world(client, db_session):
    token, world_id = register_and_create_world(client)
    world_before = db_session.get(World, world_id)
    version_before = world_before.world_version

    response = client.post(
        f'/worlds/{world_id}/snapshots',
        json={'label': 'Before chapter 2', 'note': 'Checkpoint before the next reveal'},
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['id']
    assert payload['world_id'] == world_id
    assert payload['world_version'] == version_before
    assert payload['label'] == 'Before chapter 2'
    assert payload['note'] == 'Checkpoint before the next reveal'
    assert payload['created_at']

    db_session.expire_all()
    world_after = db_session.get(World, world_id)
    assert world_after.world_version == version_before

    from app.snapshot_export.models import WorldSnapshot

    snapshot = db_session.get(WorldSnapshot, payload['id'])
    assert snapshot is not None
    assert snapshot.world_id == world_id
    assert snapshot.world_version == version_before
    assert snapshot.payload['world']['world_version'] == version_before
    assert snapshot.payload['characters'] == world_before.current_characters
    assert snapshot.payload['relations'] == world_before.current_relations
    assert snapshot.payload['foreshadows'] == world_before.current_foreshadows
    assert 'approved_chapters' in snapshot.payload
    assert 'events' in snapshot.payload


def test_archived_world_rejects_snapshot_creation_but_allows_archive_reads(client, db_session):
    token, world_id = register_and_create_world(client, 'snapshot-archived@example.com')
    existing_snapshot = client.post(
        f'/worlds/{world_id}/snapshots',
        json={'label': 'Before archive'},
        headers=auth_headers(token),
    ).json()
    archive_response = client.patch(
        f'/worlds/{world_id}/status',
        json={'status': 'archived'},
        headers=auth_headers(token),
    )
    assert archive_response.status_code == 200
    snapshot_count_before = db_session.scalar(
        select(func.count()).select_from(WorldSnapshot).where(WorldSnapshot.world_id == world_id)
    )

    create_response = client.post(
        f'/worlds/{world_id}/snapshots',
        json={'label': 'After archive'},
        headers=auth_headers(token),
    )
    list_response = client.get(f'/worlds/{world_id}/snapshots', headers=auth_headers(token))
    detail_response = client.get(f"/snapshots/{existing_snapshot['id']}", headers=auth_headers(token))
    export_response = client.post(f'/worlds/{world_id}/export/markdown', headers=auth_headers(token))

    assert create_response.status_code == 409
    assert create_response.json()['detail'] == 'WORLD_ARCHIVED'
    assert list_response.status_code == 200
    assert detail_response.status_code == 200
    assert export_response.status_code == 200
    assert list_response.json()['snapshots'][0]['id'] == existing_snapshot['id']
    assert export_response.json()['archive_format'] == 'zip'

    db_session.expire_all()
    snapshot_count_after = db_session.scalar(
        select(func.count()).select_from(WorldSnapshot).where(WorldSnapshot.world_id == world_id)
    )
    assert snapshot_count_after == snapshot_count_before


def test_list_snapshots_returns_only_owned_world_snapshots(client):
    owner_token, world_id = register_and_create_world(client, 'snapshot-owner@example.com')
    other_token, other_world_id = register_and_create_world(client, 'snapshot-other@example.com')

    first = client.post(
        f'/worlds/{world_id}/snapshots',
        json={'label': 'Owner snapshot 1'},
        headers=auth_headers(owner_token),
    ).json()
    second = client.post(
        f'/worlds/{world_id}/snapshots',
        json={'label': 'Owner snapshot 2'},
        headers=auth_headers(owner_token),
    ).json()
    client.post(
        f'/worlds/{other_world_id}/snapshots',
        json={'label': 'Other snapshot'},
        headers=auth_headers(other_token),
    )

    response = client.get(f'/worlds/{world_id}/snapshots', headers=auth_headers(owner_token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['world_id'] == world_id
    assert [snapshot['id'] for snapshot in payload['snapshots']] == [second['id'], first['id']]
    assert [snapshot['label'] for snapshot in payload['snapshots']] == ['Owner snapshot 2', 'Owner snapshot 1']


def test_snapshot_detail_returns_frozen_payload(client, db_session):
    token, world_id = register_and_create_world(client, 'snapshot-frozen@example.com')
    world_before = db_session.get(World, world_id)
    original_character_name = world_before.current_characters[0]['name']

    created = client.post(f'/worlds/{world_id}/snapshots', headers=auth_headers(token)).json()

    world_before.current_characters = [world_before.current_characters[0] | {'name': 'Changed after snapshot'}]
    world_before.world_version += 1
    db_session.commit()

    response = client.get(f"/snapshots/{created['id']}", headers=auth_headers(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['id'] == created['id']
    assert payload['world_version'] == created['world_version']
    assert payload['payload']['world']['world_version'] == created['world_version']
    assert payload['payload']['characters'][0]['name'] == original_character_name


def test_snapshot_detail_rejects_non_owner(client):
    owner_token, world_id = register_and_create_world(client, 'snapshot-detail-owner@example.com')
    other_token = client.post(
        '/auth/register', json={'email': 'snapshot-detail-other@example.com', 'password': 'strongpass123'}
    ).json()['access_token']
    created = client.post(f'/worlds/{world_id}/snapshots', headers=auth_headers(owner_token)).json()

    response = client.get(f"/snapshots/{created['id']}", headers=auth_headers(other_token))

    assert response.status_code == 403
    assert response.json()['detail'] == 'FORBIDDEN'


def test_compare_snapshots_returns_grouped_world_archive_diff(client, db_session):
    token, world_id = register_and_create_world(client, 'snapshot-compare@example.com')
    base = client.post(
        f'/worlds/{world_id}/snapshots',
        json={'label': 'Before reveal'},
        headers=auth_headers(token),
    ).json()

    world = db_session.get(World, world_id)
    first_character = world.current_characters[0]
    world.title = '青岚城：雨巷之后'
    world.world_version += 1
    world.current_characters = [first_character | {'status': '追查档案门廊'}, *world.current_characters[1:]]
    world.current_foreshadows = world.current_foreshadows + [
        {
            'id': 999,
            'source_chapter_id': None,
            'title': '雨巷铜铃',
            'description': '铜铃会在真相逼近时震动。',
            'foreshadow_type': 'item',
            'status': 'planted',
            'urgency_level': 3,
            'related_character_ids': [first_character['id']],
            'expected_resolution_window': '第4章',
        }
    ]
    db_session.add(
        EventLog(
            world_id=world_id,
            chapter_id=None,
            event_type='manual_note',
            source_type='test',
            commit_id='snapshot-compare-event',
            payload={'summary': '雨巷后新增档案线索'},
            world_version_before=base['world_version'],
            world_version_after=world.world_version,
        )
    )
    db_session.commit()

    target = client.post(
        f'/worlds/{world_id}/snapshots',
        json={'label': 'After reveal'},
        headers=auth_headers(token),
    ).json()

    response = client.get(f"/snapshots/{base['id']}/compare/{target['id']}", headers=auth_headers(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['world_id'] == world_id
    assert payload['base_snapshot']['id'] == base['id']
    assert payload['target_snapshot']['id'] == target['id']
    assert payload['summary']['total_changes'] >= 4
    assert payload['summary']['object_type_counts']['world'] == 1
    assert payload['summary']['object_type_counts']['character'] == 1
    assert payload['summary']['object_type_counts']['foreshadow'] == 1
    assert payload['summary']['object_type_counts']['event'] == 1

    world_change = next(change for change in payload['changes']['world'] if change['object_type'] == 'world')
    assert world_change['change_type'] == 'changed'
    assert set(world_change['fields_changed']) >= {'title', 'world_version'}
    assert world_change['before']['title'] != world_change['after']['title']

    character_change = next(change for change in payload['changes']['characters'] if change['object_id'] == first_character['id'])
    assert character_change['change_type'] == 'changed'
    assert character_change['fields_changed'] == ['status']
    assert character_change['title'] == first_character['name']

    foreshadow_change = next(change for change in payload['changes']['foreshadows'] if change['object_id'] == 999)
    assert foreshadow_change['change_type'] == 'added'
    assert foreshadow_change['title'] == '雨巷铜铃'


def test_compare_identical_snapshot_returns_zero_changes(client):
    token, world_id = register_and_create_world(client, 'snapshot-compare-identical@example.com')
    snapshot = client.post(f'/worlds/{world_id}/snapshots', headers=auth_headers(token)).json()

    response = client.get(f"/snapshots/{snapshot['id']}/compare/{snapshot['id']}", headers=auth_headers(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['summary']['total_changes'] == 0
    assert payload['summary']['object_type_counts'] == {}
    assert all(changes == [] for changes in payload['changes'].values())


def test_compare_snapshots_rejects_cross_world_targets(client):
    owner_token, world_id = register_and_create_world(client, 'snapshot-compare-owner@example.com')
    other_token, other_world_id = register_and_create_world(client, 'snapshot-compare-other@example.com')
    owner_snapshot = client.post(f'/worlds/{world_id}/snapshots', headers=auth_headers(owner_token)).json()
    other_snapshot = client.post(f'/worlds/{other_world_id}/snapshots', headers=auth_headers(other_token)).json()

    response = client.get(
        f"/snapshots/{owner_snapshot['id']}/compare/{other_snapshot['id']}",
        headers=auth_headers(owner_token),
    )

    assert response.status_code == 403
    assert response.json()['detail'] == 'FORBIDDEN'


def test_export_markdown_returns_world_archive_files(client, monkeypatch):
    token, world_id = register_and_create_world(client, 'markdown-export@example.com')
    approved = approve_chapter(client, token, world_id, monkeypatch)

    response = client.post(f'/worlds/{world_id}/export/markdown', headers=auth_headers(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['world_id'] == world_id
    assert payload['world_version'] == 2
    assert payload['generated_at']
    paths = [file['path'] for file in payload['files']]
    assert 'World.md' in paths
    assert 'Relations.md' in paths
    assert 'Timeline.md' in paths
    assert any(path.startswith('Characters/') for path in paths)
    assert any(path.startswith('Foreshadows/') for path in paths)
    assert any(path.startswith('Chapters/') for path in paths)
    chapter_file = next(file for file in payload['files'] if file['path'].startswith('Chapters/'))
    assert approved['approved_content'] in chapter_file['content']


def test_export_markdown_returns_downloadable_obsidian_zip_bundle(client, monkeypatch):
    token, world_id = register_and_create_world(client, 'markdown-zip@example.com')
    approved = approve_chapter(client, token, world_id, monkeypatch)

    response = client.post(f'/worlds/{world_id}/export/markdown', headers=auth_headers(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['archive_filename'].endswith('-v2-markdown.zip')
    assert payload['archive_format'] == 'zip'
    assert payload['archive_encoding'] == 'base64'
    assert payload['archive_base64']
    assert payload['files_are_inline'] is True

    files_by_path = {file['path']: file['content'] for file in payload['files']}
    assert 'World.md' in files_by_path
    assert 'Relations.md' in files_by_path
    assert 'Timeline.md' in files_by_path
    assert 'Timeline/Events.md' not in files_by_path
    assert 'Chapters/Chapter-001.md' in files_by_path
    assert approved['approved_content'] in files_by_path['Chapters/Chapter-001.md']
    assert 'World Version: 2' in files_by_path['World.md']
    assert 'Truth Canon Version:' in files_by_path['World.md']
    assert '[[Timeline]]' in files_by_path['World.md']

    archive_bytes = base64.b64decode(payload['archive_base64'])
    with ZipFile(BytesIO(archive_bytes)) as archive:
        archived_paths = set(archive.namelist())
        assert archived_paths == set(files_by_path)
        assert archive.read('Chapters/Chapter-001.md').decode('utf-8') == files_by_path['Chapters/Chapter-001.md']


def test_export_markdown_enriches_existing_files_with_obsidian_metadata(client, monkeypatch):
    token, world_id = register_and_create_world(client, 'markdown-metadata@example.com')
    approved = approve_chapter(client, token, world_id, monkeypatch)

    response = client.post(f'/worlds/{world_id}/export/markdown', headers=auth_headers(token))

    assert response.status_code == 200
    files_by_path = {file['path']: file['content'] for file in response.json()['files']}

    world_markdown = files_by_path['World.md']
    assert world_markdown.startswith('---\n')
    assert 'worldsim_type: world_index' in world_markdown
    assert f'world_id: {world_id}' in world_markdown
    assert 'tags:\n  - worldsim/world' in world_markdown
    assert '## Vault Navigation' in world_markdown
    assert '[[Indexes/Characters]]' in world_markdown
    assert '[[Indexes/Foreshadows]]' in world_markdown
    assert '[[Indexes/Chapters]]' in world_markdown

    chapter_markdown = files_by_path['Chapters/Chapter-001.md']
    assert chapter_markdown.startswith('---\n')
    assert 'worldsim_type: chapter' in chapter_markdown
    assert f"chapter_id: {approved['id']}" in chapter_markdown
    assert 'chapter_number: 1' in chapter_markdown
    assert 'tags:\n  - worldsim/chapter' in chapter_markdown
    assert '[[World]]' in chapter_markdown
    assert approved['approved_content'] in chapter_markdown


def test_export_markdown_adds_obsidian_readme_and_index_files(client, monkeypatch):
    token, world_id = register_and_create_world(client, 'markdown-indexes@example.com')
    approve_chapter(client, token, world_id, monkeypatch)

    response = client.post(f'/worlds/{world_id}/export/markdown', headers=auth_headers(token))

    assert response.status_code == 200
    files_by_path = {file['path']: file['content'] for file in response.json()['files']}
    assert 'World.md' in files_by_path
    assert 'Relations.md' in files_by_path
    assert 'Timeline.md' in files_by_path
    assert 'Chapters/Chapter-001.md' in files_by_path
    assert 'README.md' in files_by_path
    assert 'Indexes/Characters.md' in files_by_path
    assert 'Indexes/Foreshadows.md' in files_by_path
    assert 'Indexes/Chapters.md' in files_by_path
    assert 'Indexes/Timeline.md' in files_by_path

    readme = files_by_path['README.md']
    assert readme.startswith('---\n')
    assert 'worldsim_type: vault_readme' in readme
    assert 'Open [[World]] first.' in readme
    assert 'The original API contract is preserved' in readme

    character_index = files_by_path['Indexes/Characters.md']
    assert character_index.startswith('---\n')
    assert 'worldsim_type: character_index' in character_index
    assert '| Character | Role | Status | Goals |' in character_index
    assert '[[Characters/' in character_index

    timeline_index = files_by_path['Indexes/Timeline.md']
    assert timeline_index.startswith('---\n')
    assert 'worldsim_type: timeline_index' in timeline_index
    assert '[[Timeline]]' in timeline_index


def test_export_markdown_adds_story_bible_and_event_notes_with_wikilinks(client, monkeypatch):
    token, world_id = register_and_create_world(client, 'markdown-story-events@example.com')
    approved = approve_chapter(client, token, world_id, monkeypatch)

    response = client.post(f'/worlds/{world_id}/export/markdown', headers=auth_headers(token))

    assert response.status_code == 200
    files_by_path = {file['path']: file['content'] for file in response.json()['files']}
    assert 'Story Bible.md' in files_by_path
    assert 'Events/Event-001.md' in files_by_path
    assert 'Indexes/Events.md' in files_by_path

    assert '[[Story Bible]]' in files_by_path['README.md']
    assert '[[Story Bible]]' in files_by_path['World.md']
    assert '[[Indexes/Events]]' in files_by_path['World.md']
    assert '[[Events/Event-001]]' in files_by_path['Timeline.md']
    assert '[[Chapters/Chapter-001]]' in files_by_path['Timeline.md']
    assert '[[Events/Event-001]]' in files_by_path['Indexes/Timeline.md']
    assert '[[Events/Event-001]]' in files_by_path['Indexes/Events.md']

    story_bible = files_by_path['Story Bible.md']
    assert story_bible.startswith('---\n')
    assert 'worldsim_type: story_bible' in story_bible
    assert '## Truth Canon' in story_bible
    assert '## Story Arc' in story_bible
    assert '[[World]]' in story_bible

    event_note = files_by_path['Events/Event-001.md']
    event_notes = [content for path, content in files_by_path.items() if path.startswith('Events/')]
    assert event_note.startswith('---\n')
    assert 'worldsim_type: event' in event_note
    assert 'event_id:' in event_note
    assert 'Event ID:' not in event_note
    assert '[[World]]' in event_note
    assert any('[[Chapters/Chapter-001]]' in content for content in event_notes)
    assert all(f"chapter_id: {approved['id']}" not in content for content in event_notes)
    assert all('character_id' not in content for content in event_notes)
    assert all('foreshadow_id' not in content for content in event_notes)


def test_export_markdown_sanitizes_and_deduplicates_markdown_paths(client, db_session):
    token, world_id = register_and_create_world(client, 'markdown-sanitize@example.com')
    world = db_session.get(World, world_id)
    world.title = '青岚/城?'
    world.current_characters = [
        {
            'id': 101,
            'name': '林/砚?',
            'role_type': 'protagonist',
            'status': 'active',
            'public_profile': {'origin': '雨巷'},
            'hidden_traits': {'secret': '玉佩'},
            'destiny_flag': None,
            'current_goals': ['追查湿信'],
        },
        {
            'id': 102,
            'name': '林:砚',
            'role_type': 'ally',
            'status': 'active',
            'public_profile': {},
            'hidden_traits': {},
            'destiny_flag': None,
            'current_goals': [],
        },
    ]
    world.current_relations = [
        {
            'id': 201,
            'source_character_id': 101,
            'target_character_id': 102,
            'relation_type': 'mirror',
            'intensity': 3,
            'visibility': 'private',
        }
    ]
    world.current_foreshadows = [
        {
            'id': 301,
            'source_chapter_id': None,
            'title': '../裂纹/玉佩?',
            'description': '玉佩裂纹扩散。',
            'foreshadow_type': 'item',
            'status': 'advanced',
            'urgency_level': 5,
            'related_character_ids': [101],
            'expected_resolution_window': '第3章',
        },
        {
            'id': 302,
            'source_chapter_id': None,
            'title': '..:裂纹:玉佩',
            'description': '重复标题用于测试去重。',
            'foreshadow_type': 'item',
            'status': 'planted',
            'urgency_level': 4,
            'related_character_ids': [102],
            'expected_resolution_window': None,
        },
    ]
    db_session.commit()

    response = client.post(f'/worlds/{world_id}/export/markdown', headers=auth_headers(token))

    assert response.status_code == 200
    payload = response.json()
    paths = [file['path'] for file in payload['files']]
    assert payload['archive_filename'] == 'WorldSim-青岚-城-v1-markdown.zip'
    assert 'Characters/林-砚.md' in paths
    assert 'Characters/林-砚-2.md' in paths
    assert 'Foreshadows/裂纹-玉佩.md' in paths
    assert 'Foreshadows/裂纹-玉佩-2.md' in paths
    assert all('/../' not in f'/{path}' for path in paths)
    assert all('?' not in path and ':' not in path for path in paths)

    relations = next(file for file in payload['files'] if file['path'] == 'Relations.md')['content']
    assert '林/砚?' in relations
    assert '林:砚' in relations

    foreshadow = next(file for file in payload['files'] if file['path'] == 'Foreshadows/裂纹-玉佩.md')['content']
    assert '林/砚?' in foreshadow
    assert '[[Characters/林-砚]]' in foreshadow


def test_export_markdown_does_not_mutate_world_or_create_snapshot(client, db_session):
    token, world_id = register_and_create_world(client, 'markdown-export-readonly@example.com')
    world_before = db_session.get(World, world_id)
    version_before = world_before.world_version
    snapshot_count_before = db_session.scalar(select(func.count()).select_from(WorldSnapshot))

    response = client.post(f'/worlds/{world_id}/export/markdown', headers=auth_headers(token))

    assert response.status_code == 200
    db_session.expire_all()
    world_after = db_session.get(World, world_id)
    snapshot_count_after = db_session.scalar(select(func.count()).select_from(WorldSnapshot))
    assert world_after.world_version == version_before
    assert snapshot_count_after == snapshot_count_before


def test_snapshot_export_routes_require_authentication(client):
    token, world_id = register_and_create_world(client, 'snapshot-auth@example.com')
    created = client.post(f'/worlds/{world_id}/snapshots', headers=auth_headers(token)).json()

    responses = [
        client.post(f'/worlds/{world_id}/snapshots'),
        client.get(f'/worlds/{world_id}/snapshots'),
        client.get(f"/snapshots/{created['id']}"),
        client.get(f"/snapshots/{created['id']}/compare/{created['id']}"),
        client.post(f'/worlds/{world_id}/export/markdown'),
    ]

    assert all(response.status_code == 401 for response in responses)


def test_snapshot_export_routes_reject_non_owner(client):
    owner_token, world_id = register_and_create_world(client, 'snapshot-owner-auth@example.com')
    other_token = client.post(
        '/auth/register', json={'email': 'snapshot-other-auth@example.com', 'password': 'strongpass123'}
    ).json()['access_token']
    created = client.post(f'/worlds/{world_id}/snapshots', headers=auth_headers(owner_token)).json()

    responses = [
        client.post(f'/worlds/{world_id}/snapshots', headers=auth_headers(other_token)),
        client.get(f'/worlds/{world_id}/snapshots', headers=auth_headers(other_token)),
        client.get(f"/snapshots/{created['id']}", headers=auth_headers(other_token)),
        client.get(f"/snapshots/{created['id']}/compare/{created['id']}", headers=auth_headers(other_token)),
        client.post(f'/worlds/{world_id}/export/markdown', headers=auth_headers(other_token)),
    ]

    assert all(response.status_code == 403 for response in responses)
    assert all(response.json()['detail'] == 'FORBIDDEN' for response in responses)


def test_rejected_drafts_do_not_appear_in_snapshot_or_markdown_export(client, monkeypatch):
    token, world_id = register_and_create_world(client, 'snapshot-rejected@example.com')
    draft = create_draft(client, token, world_id, monkeypatch)
    rejected = client.post(
        f"/chapters/{draft['chapter_id']}/reject",
        json={'feedback': 'Not canon'},
        headers=auth_headers(token),
    )
    assert rejected.status_code == 200

    snapshot = client.post(f'/worlds/{world_id}/snapshots', headers=auth_headers(token)).json()
    detail = client.get(f"/snapshots/{snapshot['id']}", headers=auth_headers(token)).json()
    export = client.post(f'/worlds/{world_id}/export/markdown', headers=auth_headers(token)).json()

    assert detail['payload']['approved_chapters'] == []
    assert not any(file['path'].startswith('Chapters/') for file in export['files'])
    assert all('林砚推开档案门廊' not in file['content'] for file in export['files'])
