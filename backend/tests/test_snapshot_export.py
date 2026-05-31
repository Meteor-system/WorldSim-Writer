import base64
from io import BytesIO
from zipfile import ZipFile

from sqlalchemy import func, select

from app.llm.schemas import ChapterGeneration, ProposedCharacterChange, ProposedForeshadowChange
from app.narrative import service as narrative_service
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
    assert payload['archive_base64']

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
