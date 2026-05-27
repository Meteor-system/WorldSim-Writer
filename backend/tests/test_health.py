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


def test_health_check_returns_ok():
    client = TestClient(app)

    response = client.get('/health')

    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_settings_rejects_example_secret_key():
    with pytest.raises(ValidationError, match='SECRET_KEY must be changed'):
        Settings(
            DATABASE_URL='postgresql+psycopg://test:test@localhost:5432/test',
            SECRET_KEY='change-this-local-secret',
            LLM_BASE_URL='https://example.com/v1',
            LLM_API_KEY='test-api-key',
            LLM_MODEL='test-model',
        )
