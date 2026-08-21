from sqlalchemy import select

from app.event.models import EventLog
from app.world.models import World


def auth_headers(token: str) -> dict[str, str]:
    return {'Authorization': f'Bearer {token}'}


def register(client, email: str) -> str:
    return client.post('/auth/register', json={'email': email, 'password': 'strongpass123'}).json()['access_token']


def create_sample_world(client, token: str) -> dict:
    response = client.post('/worlds/from-template', headers=auth_headers(token))
    assert response.status_code == 200
    return response.json()


def test_overview_includes_truth_layers_and_unfrozen_layers_can_be_updated(client, db_session):
    token = register(client, 'truth-layers@example.com')
    world = create_sample_world(client, token)

    overview = client.get(f"/worlds/{world['id']}/overview", headers=auth_headers(token))
    assert overview.status_code == 200
    assert 'truth_layers' in overview.json()

    updated = client.patch(
        f"/worlds/{world['id']}/truth-layers",
        json={
            'truth_layers': [
                {
                    'id': 'layer-1',
                    'title': '表层公开史',
                    'content': '青岚城的公开记录只写到城主府。',
                    'reveal_at_chapter': 0,
                    'frozen': False,
                },
                {
                    'id': 'layer-2',
                    'title': '深层禁忌',
                    'content': '湿信来自旧朝档案。',
                    'reveal_at_chapter': 4,
                    'frozen': True,
                },
            ],
            'edit_reason': '补全真相层',
        },
        headers=auth_headers(token),
    )
    assert updated.status_code == 200
    payload = updated.json()
    assert payload['world_version'] == world['world_version'] + 1
    assert payload['truth_layers'][0]['title'] == '表层公开史'
    assert payload['truth_layers'][1]['frozen'] is True

    frozen_edit = client.patch(
        f"/worlds/{world['id']}/truth-layers",
        json={
            'truth_layers': [
                {
                    'id': 'layer-1',
                    'title': '表层公开史',
                    'content': '青岚城的公开记录只写到城主府。',
                    'reveal_at_chapter': 0,
                    'frozen': False,
                },
                {
                    'id': 'layer-2',
                    'title': '深层禁忌',
                    'content': '试图改写冻结层',
                    'reveal_at_chapter': 4,
                    'frozen': True,
                },
            ],
        },
        headers=auth_headers(token),
    )
    assert frozen_edit.status_code == 409
    assert frozen_edit.json()['detail'] == 'FROZEN_TRUTH_LAYER_LOCKED'

    stored = db_session.get(World, world['id'])
    assert stored is not None
    assert stored.truth_layers[1]['content'] == '湿信来自旧朝档案。'

    events = list(
        db_session.scalars(
            select(EventLog)
            .where(EventLog.world_id == world['id'])
            .where(EventLog.event_type == 'truth_layer_change')
        )
    )
    assert len(events) == 1
