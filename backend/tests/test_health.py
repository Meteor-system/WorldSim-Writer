import os

os.environ.setdefault('DATABASE_URL', 'postgresql+psycopg://test:test@localhost:5432/test')
os.environ.setdefault('SECRET_KEY', 'test-secret-key')
os.environ.setdefault('LLM_BASE_URL', 'https://example.com/v1')
os.environ.setdefault('LLM_API_KEY', 'test-api-key')
os.environ.setdefault('LLM_MODEL', 'test-model')

from fastapi.testclient import TestClient

from app.main import app


def test_health_check_returns_ok():
    client = TestClient(app)

    response = client.get('/health')

    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}
