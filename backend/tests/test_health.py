import json
import os
import re
from pathlib import Path
from traceback import FrameSummary

os.environ.setdefault('DATABASE_URL', 'postgresql+psycopg://test:test@localhost:5432/test')
os.environ.setdefault('SECRET_KEY', 'test-secret-key')
os.environ.setdefault('LLM_BASE_URL', 'https://example.com/v1')
os.environ.setdefault('LLM_API_KEY', 'test-api-key')
os.environ.setdefault('LLM_MODEL', 'test-model')

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import _exception_location, app, create_app, request_logger


def _migration_status(*, status: str = 'up_to_date') -> dict:
    up_to_date = status == 'up_to_date'
    return {
        'current': '0013_add_import_node' if status != 'unknown' else None,
        'head': '0013_add_import_node',
        'up_to_date': up_to_date,
        'status': status,
    }


def test_health_check_returns_ok_with_migration_status(monkeypatch):
    monkeypatch.setattr('app.main.get_migration_status', _migration_status)
    client = TestClient(app)

    response = client.get('/health')

    assert response.status_code == 200
    assert response.json() == {
        'status': 'ok',
        'migration': _migration_status(),
        'llm': {'mock': False},
    }


def test_health_check_redacts_unknown_migration_error(monkeypatch):
    secret_error = 'database unavailable at postgresql://user:password@private-host/worldsim'
    monkeypatch.setattr(
        'app.main.get_migration_status',
        lambda: {**_migration_status(status='unknown'), 'error': secret_error},
    )
    client = TestClient(app)

    response = client.get('/health')

    assert response.status_code == 200
    assert response.json()['status'] == 'ok'
    assert response.json()['migration'] == {
        **_migration_status(status='unknown'),
        'error': 'MIGRATION_STATUS_UNAVAILABLE',
    }
    assert secret_error not in response.text


def test_liveness_does_not_check_database(monkeypatch):
    monkeypatch.setattr('app.main.get_migration_status', lambda: pytest.fail('liveness accessed the database'))
    client = TestClient(app)

    response = client.get('/live')

    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_readiness_returns_ready_when_database_and_migration_are_current(monkeypatch):
    monkeypatch.setattr('app.main.get_migration_status', _migration_status)
    client = TestClient(app)

    response = client.get('/ready')

    assert response.status_code == 200
    assert response.json() == {
        'status': 'ready',
        'checks': {'database': 'ok', 'migration': _migration_status()},
    }


def test_readiness_returns_503_when_migration_is_behind(monkeypatch):
    monkeypatch.setattr('app.main.get_migration_status', lambda: _migration_status(status='behind'))
    client = TestClient(app)

    response = client.get('/ready')

    assert response.status_code == 503
    assert response.json() == {
        'status': 'not_ready',
        'checks': {'database': 'ok', 'migration': _migration_status(status='behind')},
        'error': 'MIGRATION_NOT_UP_TO_DATE',
    }


def test_readiness_returns_503_without_leaking_database_error(monkeypatch):
    secret_error = 'connection failed for postgresql://user:password@private-host/worldsim'
    monkeypatch.setattr(
        'app.main.get_migration_status',
        lambda: {**_migration_status(status='unknown'), 'error': 'DATABASE_UNAVAILABLE', 'detail': secret_error},
    )
    client = TestClient(app)

    response = client.get('/ready')

    assert response.status_code == 503
    assert response.json() == {
        'status': 'not_ready',
        'checks': {
            'database': 'unavailable',
            'migration': {
                **_migration_status(status='unknown'),
                'error': 'DATABASE_UNAVAILABLE',
            },
        },
        'error': 'DATABASE_UNAVAILABLE',
    }
    assert secret_error not in response.text


def test_readiness_distinguishes_unavailable_migration_repository(monkeypatch):
    monkeypatch.setattr(
        'app.main.get_migration_status',
        lambda: {
            **_migration_status(status='unknown'),
            'head': None,
            'error': 'MIGRATION_REPOSITORY_UNAVAILABLE',
        },
    )
    client = TestClient(app)

    response = client.get('/ready')

    assert response.status_code == 503
    assert response.json()['checks']['database'] == 'unknown'
    assert response.json()['checks']['migration']['error'] == 'MIGRATION_REPOSITORY_UNAVAILABLE'
    assert response.json()['error'] == 'MIGRATION_REPOSITORY_UNAVAILABLE'


def test_request_id_is_propagated_or_replaced_when_invalid():
    client = TestClient(app)

    accepted = client.get('/live', headers={'X-Request-ID': 'edge-request_123'})
    replaced = client.get('/live', headers={'X-Request-ID': 'invalid request id'})

    assert accepted.headers['X-Request-ID'] == 'edge-request_123'
    assert re.fullmatch(r'[0-9a-f]{32}', replaced.headers['X-Request-ID'])
    assert replaced.headers['X-Request-ID'] != 'invalid request id'


def test_structured_request_log_excludes_headers_query_and_body(caplog):
    client = TestClient(app)
    request_logger.addHandler(caplog.handler)
    try:
        response = client.post(
            '/missing?prompt=secret-query',
            headers={'Authorization': 'Bearer secret-token', 'X-Request-ID': 'safe-request-id'},
            json={'content': 'secret-draft-body'},
        )
    finally:
        request_logger.removeHandler(caplog.handler)

    payload = next(
        payload
        for record in caplog.records
        if (payload := json.loads(record.getMessage())).get('request_id') == 'safe-request-id'
    )
    serialized = json.dumps(payload)
    assert response.status_code == 404
    assert response.headers['X-Request-ID'] == 'safe-request-id'
    assert payload == {
        'duration_ms': payload['duration_ms'],
        'event': 'request.completed',
        'level': 'warning',
        'method': 'POST',
        'request_id': 'safe-request-id',
        'route': '<unmatched>',
        'status_code': 404,
        'timestamp': payload['timestamp'],
    }
    assert isinstance(payload['duration_ms'], float)
    assert payload['duration_ms'] >= 0
    assert 'secret-query' not in serialized
    assert 'secret-token' not in serialized
    assert 'secret-draft-body' not in serialized


def test_exception_location_uses_redacted_external_fallback(monkeypatch):
    monkeypatch.setattr(
        'app.main.extract_tb',
        lambda _traceback: [FrameSummary('/private/provider/client.py', 77, 'send_secret_request')],
    )

    location = _exception_location(RuntimeError('secret provider failure'))

    assert location == {
        'exception_file': '<external>/client.py',
        'exception_line': 77,
        'exception_function': 'send_secret_request',
    }
    assert '/private/provider' not in json.dumps(location)
    assert 'secret provider failure' not in json.dumps(location)


def test_unhandled_exception_response_and_log_do_not_expose_exception_message(caplog):
    test_app = create_app()

    @test_app.get('/explode')
    def explode() -> None:
        raise RuntimeError('secret exception details')

    request_logger.addHandler(caplog.handler)
    try:
        client = TestClient(test_app, raise_server_exceptions=False)
        response = client.get('/explode', headers={'X-Request-ID': 'failure-request-id'})
    finally:
        request_logger.removeHandler(caplog.handler)

    payload = next(
        payload
        for record in caplog.records
        if (payload := json.loads(record.getMessage())).get('request_id') == 'failure-request-id'
    )
    assert response.status_code == 500
    assert response.headers['X-Request-ID'] == 'failure-request-id'
    assert response.json() == {'detail': 'INTERNAL_SERVER_ERROR', 'request_id': 'failure-request-id'}
    assert payload['event'] == 'request.failed'
    assert payload['exception_type'] == 'RuntimeError'
    assert payload['exception_file'] == 'tests/test_health.py'
    assert payload['exception_function'] == 'explode'
    assert payload['exception_line'] > 0
    assert payload['route'] == '/explode'
    assert 'secret exception details' not in response.text
    assert 'secret exception details' not in json.dumps(payload)
    assert str(Path(__file__).resolve().parent) not in json.dumps(payload)


def test_settings_rejects_example_secret_key():
    with pytest.raises(ValidationError, match='SECRET_KEY must be changed'):
        Settings(
            DATABASE_URL='postgresql+psycopg://test:test@localhost:5432/test',
            SECRET_KEY='change-this-local-secret',
            LLM_BASE_URL='https://example.com/v1',
            LLM_API_KEY='test-api-key',
            LLM_MODEL='test-model',
        )


def test_settings_normalizes_log_level():
    settings = Settings(
        DATABASE_URL='postgresql+psycopg://test:test@localhost:5432/test',
        SECRET_KEY='test-secret-key',
        LLM_BASE_URL='https://example.com/v1',
        LLM_API_KEY='test-api-key',
        LLM_MODEL='test-model',
        LOG_LEVEL='warning',
    )

    assert settings.log_level == 'WARNING'
