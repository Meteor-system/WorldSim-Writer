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


def test_world_owner_can_archive_and_restore_world(client, db_session):
    token = register(client, 'archive-owner@example.com')
    world = create_sample_world(client, token)

    archived = client.patch(
        f"/worlds/{world['id']}/status",
        json={'status': 'archived'},
        headers=auth_headers(token),
    )

    assert archived.status_code == 200
    assert archived.json()['status'] == 'archived'
    assert client.get(f"/worlds/{world['id']}", headers=auth_headers(token)).json()['status'] == 'archived'

    restored = client.patch(
        f"/worlds/{world['id']}/status",
        json={'status': 'active'},
        headers=auth_headers(token),
    )

    assert restored.status_code == 200
    assert restored.json()['status'] == 'active'
    assert db_session.get(World, world['id']) is not None


def test_world_status_update_records_archive_and_restore_events_without_incrementing_world_version(client, db_session):
    token = register(client, 'archive-events@example.com')
    world = create_sample_world(client, token)

    archived = client.patch(
        f"/worlds/{world['id']}/status",
        json={'status': 'archived'},
        headers=auth_headers(token),
    )
    restored = client.patch(
        f"/worlds/{world['id']}/status",
        json={'status': 'active'},
        headers=auth_headers(token),
    )

    assert archived.status_code == 200
    assert restored.status_code == 200
    assert archived.json()['world_version'] == world['world_version']
    assert restored.json()['world_version'] == world['world_version']

    events = list(
        db_session.scalars(
            select(EventLog)
            .where(EventLog.world_id == world['id'])
            .where(EventLog.event_type == 'world_status_changed')
            .order_by(EventLog.id)
        )
    )
    assert len(events) == 2
    assert [event.source_type for event in events] == ['world_status', 'world_status']
    assert [event.payload for event in events] == [
        {'previous_status': 'active', 'next_status': 'archived'},
        {'previous_status': 'archived', 'next_status': 'active'},
    ]
    assert [event.world_version_before for event in events] == [world['world_version'], world['world_version']]
    assert [event.world_version_after for event in events] == [world['world_version'], world['world_version']]


def test_world_status_update_does_not_record_event_for_unchanged_status(client, db_session):
    token = register(client, 'archive-unchanged@example.com')
    world = create_sample_world(client, token)

    response = client.patch(
        f"/worlds/{world['id']}/status",
        json={'status': 'active'},
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    events = list(
        db_session.scalars(
            select(EventLog)
            .where(EventLog.world_id == world['id'])
            .where(EventLog.event_type == 'world_status_changed')
        )
    )
    assert events == []


def test_world_status_update_rejects_invalid_status(client):
    token = register(client, 'archive-invalid@example.com')
    world = create_sample_world(client, token)

    response = client.patch(
        f"/worlds/{world['id']}/status",
        json={'status': 'deleted'},
        headers=auth_headers(token),
    )

    assert response.status_code == 422


def test_world_status_update_rejects_non_owner(client):
    owner_token = register(client, 'archive-real-owner@example.com')
    other_token = register(client, 'archive-other@example.com')
    world = create_sample_world(client, owner_token)

    response = client.patch(
        f"/worlds/{world['id']}/status",
        json={'status': 'archived'},
        headers=auth_headers(other_token),
    )

    assert response.status_code == 403
