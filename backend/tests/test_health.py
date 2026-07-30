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


@pytest.mark.parametrize(
    ('configured_origin', 'alias_origin'),
    [
        ('http://localhost:5173', 'http://127.0.0.1:5173'),
        ('http://127.0.0.1:5179', 'http://localhost:5179'),
    ],
)
def test_cors_preflight_allows_loopback_frontend_origin_without_allowing_unknown_origins(
    monkeypatch, configured_origin, alias_origin
):
    monkeypatch.setenv('FRONTEND_ORIGIN', configured_origin)
    client = TestClient(create_app())
    preflight_headers = {
        'Origin': configured_origin,
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'authorization,content-type',
    }

    configured_origin_response = client.options('/worlds', headers=preflight_headers)
    alias_origin_response = client.options(
        '/worlds', headers={**preflight_headers, 'Origin': alias_origin}
    )
    unknown_origin_response = client.options(
        '/worlds',
        headers={**preflight_headers, 'Origin': 'https://unknown.example'},
    )

    assert configured_origin_response.status_code == 200
    assert configured_origin_response.headers['Access-Control-Allow-Origin'] == configured_origin
    assert alias_origin_response.status_code == 200
    assert alias_origin_response.headers['Access-Control-Allow-Origin'] == alias_origin
    assert unknown_origin_response.status_code == 400
    assert 'Access-Control-Allow-Origin' not in unknown_origin_response.headers


def test_create_app_ignores_invalid_frontend_origin_port(monkeypatch):
    monkeypatch.setenv('FRONTEND_ORIGIN', 'http://localhost:not-a-port')

    client = TestClient(create_app())

    response = client.get('/live')

    assert response.status_code == 200


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


@pytest.mark.parametrize('timeout', [1, 300])
def test_settings_accepts_llm_timeout_boundaries(timeout):
    settings = Settings(
        DATABASE_URL='postgresql+psycopg://test:test@localhost:5432/test',
        SECRET_KEY='test-secret-key',
        LLM_BASE_URL='https://example.com/v1',
        LLM_API_KEY='test-api-key',
        LLM_MODEL='test-model',
        LLM_TIMEOUT_SECONDS=timeout,
    )

    assert settings.llm_timeout_seconds == timeout


@pytest.mark.parametrize('timeout', [1, 300, 167])
def test_settings_accepts_llm_read_timeout_boundaries_and_known_generation_duration(timeout):
    settings = Settings(
        DATABASE_URL='postgresql+psycopg://test:test@localhost:5432/test',
        SECRET_KEY='test-secret-key',
        LLM_BASE_URL='https://example.com/v1',
        LLM_API_KEY='test-api-key',
        LLM_MODEL='test-model',
        LLM_READ_TIMEOUT_SECONDS=timeout,
    )

    assert settings.llm_read_timeout_seconds == timeout


@pytest.mark.parametrize('timeout', [0, 1801])
def test_settings_rejects_out_of_range_llm_read_timeout(timeout):
    with pytest.raises(ValidationError):
        Settings(
            DATABASE_URL='postgresql+psycopg://test:test@localhost:5432/test',
            SECRET_KEY='test-secret-key',
            LLM_BASE_URL='https://example.com/v1',
            LLM_API_KEY='test-api-key',
            LLM_MODEL='test-model',
            LLM_READ_TIMEOUT_SECONDS=timeout,
        )


def test_settings_loads_required_fields_from_bom_aware_dotenv(tmp_path, monkeypatch):
    for name in ['DATABASE_URL', 'SECRET_KEY', 'LLM_BASE_URL', 'LLM_API_KEY', 'LLM_MODEL']:
        monkeypatch.delenv(name, raising=False)

    env_file = tmp_path / '.env'
    env_file.write_text(
        '\n'.join(
            [
                'DATABASE_URL=postgresql+psycopg://test:test@localhost:5432/test',
                'SECRET_KEY=test-secret-key',
                'LLM_BASE_URL=https://example.com/v1',
                'LLM_API_KEY=test-api-key',
                'LLM_MODEL=test-model',
            ]
        ),
        encoding='utf-8-sig',
    )

    settings = Settings(_env_file=env_file)

    assert settings.database_url == 'postgresql+psycopg://test:test@localhost:5432/test'
    assert settings.secret_key == 'test-secret-key'
    assert settings.llm_model == 'test-model'


@pytest.mark.parametrize('timeout', [0, 301])
def test_settings_rejects_out_of_range_llm_timeout(timeout):
    with pytest.raises(ValidationError):
        Settings(
            DATABASE_URL='postgresql+psycopg://test:test@localhost:5432/test',
            SECRET_KEY='test-secret-key',
            LLM_BASE_URL='https://example.com/v1',
            LLM_API_KEY='test-api-key',
            LLM_MODEL='test-model',
            LLM_TIMEOUT_SECONDS=timeout,
        )


def test_settings_rejects_invalid_llm_api_mode():
    with pytest.raises(ValidationError):
        Settings(
            DATABASE_URL='postgresql+psycopg://test:test@localhost:5432/test',
            SECRET_KEY='test-secret-key',
            LLM_BASE_URL='https://example.com/v1',
            LLM_API_KEY='test-api-key',
            LLM_MODEL='test-model',
            LLM_API_MODE='unsupported',
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


def test_settings_defaults_documented_api_runtime_fields():
    settings = Settings(
        DATABASE_URL='postgresql+psycopg://test:test@localhost:5432/test',
        SECRET_KEY='test-secret-key',
        LLM_BASE_URL='https://example.com/v1',
        LLM_API_KEY='test-api-key',
        LLM_MODEL='test-model',
    )

    assert settings.llm_api_mode == 'responses'
    assert settings.api_host == '127.0.0.1'
    assert settings.api_port == '8000'
    assert settings.api_workers == '1'
    assert settings.api_backlog == '2048'
    assert settings.api_limit_concurrency == '100'
    assert settings.api_timeout_keep_alive_seconds == '5'
    assert settings.api_timeout_graceful_shutdown_seconds == '30'
    assert settings.api_proxy_headers == 'false'
    assert settings.api_forwarded_allow_ips == '127.0.0.1'


def test_settings_accepts_documented_api_runtime_fields():
    settings = Settings(
        DATABASE_URL='postgresql+psycopg://test:test@localhost:5432/test',
        SECRET_KEY='test-secret-key',
        LLM_BASE_URL='https://example.com/v1',
        LLM_API_KEY='test-api-key',
        LLM_MODEL='test-model',
        LLM_API_MODE='chat_completions',
        API_HOST='0.0.0.0',
        API_PORT='9000',
        API_WORKERS='4',
        API_BACKLOG='4096',
        API_LIMIT_CONCURRENCY='250',
        API_TIMEOUT_KEEP_ALIVE_SECONDS='10',
        API_TIMEOUT_GRACEFUL_SHUTDOWN_SECONDS='60',
        API_PROXY_HEADERS='true',
        API_FORWARDED_ALLOW_IPS='10.0.0.0/8',
    )

    assert settings.llm_api_mode == 'chat_completions'
    assert settings.api_host == '0.0.0.0'
    assert settings.api_port == '9000'
    assert settings.api_workers == '4'
    assert settings.api_backlog == '4096'
    assert settings.api_limit_concurrency == '250'
    assert settings.api_timeout_keep_alive_seconds == '10'
    assert settings.api_timeout_graceful_shutdown_seconds == '60'
    assert settings.api_proxy_headers == 'true'
    assert settings.api_forwarded_allow_ips == '10.0.0.0/8'


def test_settings_loads_api_runtime_fields_from_shared_dotenv(tmp_path, monkeypatch):
    environment_names = [
        'DATABASE_URL',
        'SECRET_KEY',
        'LLM_BASE_URL',
        'LLM_API_KEY',
        'LLM_MODEL',
        'LLM_API_MODE',
        'API_HOST',
        'API_PORT',
        'API_WORKERS',
        'API_BACKLOG',
        'API_LIMIT_CONCURRENCY',
        'API_TIMEOUT_KEEP_ALIVE_SECONDS',
        'API_TIMEOUT_GRACEFUL_SHUTDOWN_SECONDS',
        'API_PROXY_HEADERS',
        'API_FORWARDED_ALLOW_IPS',
    ]
    for name in environment_names:
        monkeypatch.delenv(name, raising=False)

    env_file = tmp_path / '.env'
    env_file.write_text(
        '\n'.join(
            [
                'DATABASE_URL=postgresql+psycopg://test:test@localhost:5432/test',
                'SECRET_KEY=test-secret-key',
                'LLM_BASE_URL=https://example.com/v1',
                'LLM_API_KEY=test-api-key',
                'LLM_MODEL=test-model',
                'LLM_API_MODE=chat_completions',
                'API_HOST=0.0.0.0',
                'API_PORT=9000',
                'API_WORKERS=4',
                'API_BACKLOG=4096',
                'API_LIMIT_CONCURRENCY=250',
                'API_TIMEOUT_KEEP_ALIVE_SECONDS=10',
                'API_TIMEOUT_GRACEFUL_SHUTDOWN_SECONDS=60',
                'API_PROXY_HEADERS=true',
                'API_FORWARDED_ALLOW_IPS=10.1.2.3/8',
            ]
        ),
        encoding='utf-8',
    )

    settings = Settings(_env_file=env_file)

    assert settings.llm_api_mode == 'chat_completions'
    assert settings.api_host == '0.0.0.0'
    assert settings.api_port == '9000'
    assert settings.api_workers == '4'
    assert settings.api_backlog == '4096'
    assert settings.api_limit_concurrency == '250'
    assert settings.api_timeout_keep_alive_seconds == '10'
    assert settings.api_timeout_graceful_shutdown_seconds == '60'
    assert settings.api_proxy_headers == 'true'
    assert settings.api_forwarded_allow_ips == '10.1.2.3/8'


def test_settings_rejects_unknown_api_runtime_field_in_shared_dotenv(tmp_path, monkeypatch):
    for name in ['DATABASE_URL', 'SECRET_KEY', 'LLM_BASE_URL', 'LLM_API_KEY', 'LLM_MODEL', 'API_WOKERS']:
        monkeypatch.delenv(name, raising=False)

    env_file = tmp_path / '.env'
    env_file.write_text(
        '\n'.join(
            [
                'DATABASE_URL=postgresql+psycopg://test:test@localhost:5432/test',
                'SECRET_KEY=test-secret-key',
                'LLM_BASE_URL=https://example.com/v1',
                'LLM_API_KEY=test-api-key',
                'LLM_MODEL=test-model',
                'API_WOKERS=4',
            ]
        ),
        encoding='utf-8',
    )

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=env_file)

    assert exc_info.value.errors()[0]['loc'] == ('api_wokers',)
    assert exc_info.value.errors()[0]['type'] == 'extra_forbidden'
