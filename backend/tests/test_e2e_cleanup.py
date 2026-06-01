import pytest
from sqlalchemy import select

from app.auth.models import User
from app.devtools.e2e_cleanup import cleanup_e2e_data
from app.snapshot_export.models import WorldSnapshot
from app.tags.models import ObjectTag, Tag
from app.world.models import World


def register(client, email):
    response = client.post('/auth/register', json={'email': email, 'password': 'strongpass123'})
    assert response.status_code == 200
    return response.json()['access_token']


def create_world(client, token):
    response = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    return response.json()


def test_cleanup_e2e_data_dry_run_counts_without_deleting(client, db_session):
    normal_token = register(client, 'cleanup-dry-normal@example.com')
    normal_world = create_world(client, normal_token)
    e2e_token = register(client, 'e2e-cleanup-dry@example.com')
    e2e_world = create_world(client, e2e_token)

    summary = cleanup_e2e_data(db_session, dry_run=True)

    assert summary['email_prefix'] == 'e2e-'
    assert summary['dry_run'] is True
    assert summary['users_deleted'] == 0
    assert summary['users_matched'] == 1
    assert summary['worlds_matched'] == 1
    assert db_session.scalar(select(User).where(User.email == 'e2e-cleanup-dry@example.com')) is not None
    assert db_session.get(World, e2e_world['id']) is not None
    assert db_session.scalar(select(User).where(User.email == 'cleanup-dry-normal@example.com')) is not None
    assert db_session.get(World, normal_world['id']) is not None


def test_cleanup_e2e_data_deletes_only_e2e_users_and_worlds(client, db_session):
    normal_token = register(client, 'cleanup-normal@example.com')
    normal_world = create_world(client, normal_token)
    e2e_token = register(client, 'e2e-cleanup@example.com')
    e2e_world = create_world(client, e2e_token)
    snapshot = client.post(f"/worlds/{e2e_world['id']}/snapshots", headers={'Authorization': f'Bearer {e2e_token}'}).json()
    tag = client.post(
        f"/worlds/{e2e_world['id']}/tags",
        json={'name': 'E2E Cleanup'},
        headers={'Authorization': f'Bearer {e2e_token}'},
    ).json()
    client.post(
        f"/worlds/{e2e_world['id']}/tags/{tag['id']}/objects",
        json={'object_type': 'world', 'object_id': e2e_world['id']},
        headers={'Authorization': f'Bearer {e2e_token}'},
    )

    summary = cleanup_e2e_data(db_session)

    assert summary['email_prefix'] == 'e2e-'
    assert summary['dry_run'] is False
    assert summary['users_matched'] == 1
    assert summary['users_deleted'] == 1
    assert summary['worlds_matched'] == 1
    assert summary['worlds_deleted'] == 1
    assert db_session.scalar(select(User).where(User.email == 'e2e-cleanup@example.com')) is None
    assert db_session.get(World, e2e_world['id']) is None
    assert db_session.get(WorldSnapshot, snapshot['id']) is None
    assert db_session.get(Tag, tag['id']) is None
    assert db_session.scalar(select(ObjectTag).where(ObjectTag.world_id == e2e_world['id'])) is None
    assert db_session.scalar(select(User).where(User.email == 'cleanup-normal@example.com')) is not None
    assert db_session.get(World, normal_world['id']) is not None


def test_cleanup_e2e_data_rejects_non_e2e_prefix(db_session):
    with pytest.raises(ValueError, match='e2e-'):
        cleanup_e2e_data(db_session, email_prefix='cleanup-')
