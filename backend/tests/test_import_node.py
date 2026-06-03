from sqlalchemy import select

from app.event.models import EventLog
from app.import_node.models import ImportBatch, ImportCandidateAsset
from app.world.models import World


def auth_headers(token: str) -> dict[str, str]:
    return {'Authorization': f'Bearer {token}'}


def register(client, email: str) -> str:
    return client.post('/auth/register', json={'email': email, 'password': 'strongpass123'}).json()['access_token']


def create_sample_world(client, token: str) -> dict:
    response = client.post('/worlds/from-template', headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def test_import_preview_classifies_material_and_reports_conflicts(client):
    token = register(client, 'import-preview@example.com')
    world = create_sample_world(client, token)

    response = client.post(
        f"/worlds/{world['id']}/imports/preview",
        headers=auth_headers(token),
        json={
            'source_type': 'markdown',
            'source_title': '旧设定.md',
            'content': '# 设定\n规则：青岚城所有密探必须隐藏真实姓名。\n\n角色：林砚：青岚城剑修，追查湿信。\n\n灵感：雨巷里有人递来一封湿透的信。',
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['asset_counts']['canon'] >= 1
    assert payload['asset_counts']['character'] >= 1
    assert payload['asset_counts']['inspiration'] >= 1
    assert {asset['asset_pool'] for asset in payload['assets']} == {'canon', 'character', 'inspiration'}
    assert any(conflict['category'] in {'canon_overlap', 'character_duplicate'} for conflict in payload['conflicts'])


def test_import_confirm_writes_candidates_and_audit_without_mutating_canon_or_world_version(client, db_session):
    token = register(client, 'import-confirm@example.com')
    world_payload = create_sample_world(client, token)
    original_world = db_session.get(World, world_payload['id'])
    original_canon = original_world.truth_canon
    original_version = original_world.world_version

    content = '设定：黑水城城墙下埋着旧王朝的骨印。\n角色：沈微霜：密探，擅长伪装。\n灵感：雨夜审讯从一盏坏灯开始。'
    preview = client.post(
        f"/worlds/{world_payload['id']}/imports/preview",
        headers=auth_headers(token),
        json={'source_type': 'txt', 'source_title': '灵感.txt', 'content': content},
    ).json()

    response = client.post(
        f"/worlds/{world_payload['id']}/imports/confirm",
        headers=auth_headers(token),
        json={
            'source_type': 'txt',
            'source_title': '灵感.txt',
            'content': content,
            'assets': preview['assets'],
            'conflicts': preview['conflicts'],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload['batch']['status'] == 'confirmed'
    assert payload['batch']['asset_counts']['canon'] >= 1
    assert len(payload['assets']) == len(preview['assets'])

    db_session.expire_all()
    world = db_session.get(World, world_payload['id'])
    assert world.truth_canon == original_canon
    assert world.world_version == original_version

    batch = db_session.get(ImportBatch, payload['batch']['id'])
    assert batch is not None
    candidates = list(db_session.scalars(select(ImportCandidateAsset).where(ImportCandidateAsset.batch_id == batch.id)))
    assert len(candidates) == len(preview['assets'])
    assert all(candidate.status == 'candidate' for candidate in candidates)

    event = db_session.scalar(select(EventLog).where(EventLog.world_id == world.id).where(EventLog.event_type == 'material_import_confirmed'))
    assert event is not None
    assert event.source_type == 'import_node'
    assert event.world_version_before == original_version
    assert event.world_version_after == original_version


def test_import_list_returns_recent_batches_with_candidates(client):
    token = register(client, 'import-list@example.com')
    world = create_sample_world(client, token)
    content = '灵感：城门口出现第二个月亮。'
    preview = client.post(
        f"/worlds/{world['id']}/imports/preview",
        headers=auth_headers(token),
        json={'source_type': 'pasted_text', 'source_title': '片段', 'content': content},
    ).json()
    client.post(
        f"/worlds/{world['id']}/imports/confirm",
        headers=auth_headers(token),
        json={'source_type': 'pasted_text', 'source_title': '片段', 'content': content, 'assets': preview['assets'], 'conflicts': preview['conflicts']},
    )

    response = client.get(f"/worlds/{world['id']}/imports", headers=auth_headers(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['world_id'] == world['id']
    assert payload['batches'][0]['source_title'] == '片段'
    assert payload['batches'][0]['assets'][0]['asset_pool'] == 'inspiration'


def test_non_owner_cannot_preview_or_confirm_import(client):
    owner_token = register(client, 'import-owner@example.com')
    other_token = register(client, 'import-other@example.com')
    world = create_sample_world(client, owner_token)

    preview = client.post(
        f"/worlds/{world['id']}/imports/preview",
        headers=auth_headers(other_token),
        json={'source_type': 'txt', 'source_title': 'x.txt', 'content': '灵感：越权导入。'},
    )
    confirm = client.post(
        f"/worlds/{world['id']}/imports/confirm",
        headers=auth_headers(other_token),
        json={'source_type': 'txt', 'source_title': 'x.txt', 'content': '灵感：越权导入。', 'assets': [], 'conflicts': []},
    )

    assert preview.status_code == 403
    assert confirm.status_code == 403
