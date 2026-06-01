import os

os.environ.setdefault('DATABASE_URL', 'postgresql+psycopg://test:test@localhost:5432/test')
os.environ.setdefault('SECRET_KEY', 'test-secret-key')
os.environ.setdefault('LLM_BASE_URL', 'https://example.com/v1')
os.environ.setdefault('LLM_API_KEY', 'test-api-key')
os.environ.setdefault('LLM_MODEL', 'test-model')

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import app


def test_health_check_returns_ok_with_migration_status(monkeypatch):
    monkeypatch.setattr(
        'app.main.get_migration_status',
        lambda: {'current': '0012_add_tags', 'head': '0012_add_tags', 'up_to_date': True, 'status': 'up_to_date'},
    )
    client = TestClient(app)

    response = client.get('/health')

    assert response.status_code == 200
    assert response.json() == {
        'status': 'ok',
        'migration': {'current': '0012_add_tags', 'head': '0012_add_tags', 'up_to_date': True, 'status': 'up_to_date'},
        'llm': {'mock': False},
    }


def test_health_check_reports_unknown_migration_status_without_500(monkeypatch):
    monkeypatch.setattr(
        'app.main.get_migration_status',
        lambda: {
            'current': None,
            'head': '0012_add_tags',
            'up_to_date': False,
            'status': 'unknown',
            'error': 'database unavailable',
        },
    )
    client = TestClient(app)

    response = client.get('/health')

    assert response.status_code == 200
    assert response.json()['status'] == 'ok'
    assert response.json()['migration']['status'] == 'unknown'
    assert response.json()['migration']['up_to_date'] is False
    assert response.json()['migration']['error'] == 'database unavailable'


def test_settings_rejects_example_secret_key():
    with pytest.raises(ValidationError, match='SECRET_KEY must be changed'):
        Settings(
            DATABASE_URL='postgresql+psycopg://test:test@localhost:5432/test',
            SECRET_KEY='change-this-local-secret',
            LLM_BASE_URL='https://example.com/v1',
            LLM_API_KEY='test-api-key',
            LLM_MODEL='test-model',
        )
