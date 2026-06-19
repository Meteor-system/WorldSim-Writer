import os

import pytest

from app.core.config import Settings


DEV_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]


@pytest.mark.parametrize('origin', DEV_ORIGINS)
def test_options_preflight_allows_dev_origins(client, origin):
    response = client.options(
        '/auth/login',
        headers={
            'Origin': origin,
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'content-type',
        },
    )
    assert response.headers.get('access-control-allow-origin') == origin


def _make_settings(**overrides) -> Settings:
    base = {
        'DATABASE_URL': 'sqlite+pysqlite:///:memory:',
        'SECRET_KEY': 'test-secret',
        'LLM_BASE_URL': 'https://example.test/v1',
        'LLM_API_KEY': 'test-key',
        'LLM_MODEL': 'test-model',
    }
    base.update(overrides)
    return Settings(**base)


def test_cors_allow_origins_includes_dev_defaults_by_default():
    settings = _make_settings()
    for origin in DEV_ORIGINS:
        assert origin in settings.cors_allow_origins


def test_cors_allow_origins_prefers_frontend_origins_csv():
    settings = _make_settings(FRONTEND_ORIGINS='https://app.example.com, https://studio.example.com')
    assert 'https://app.example.com' in settings.cors_allow_origins
    assert 'https://studio.example.com' in settings.cors_allow_origins
    # dev defaults still appended
    assert 'http://127.0.0.1:5173' in settings.cors_allow_origins


def test_cors_allow_origins_falls_back_to_single_frontend_origin():
    settings = _make_settings(FRONTEND_ORIGIN='https://only.example.com')
    assert 'https://only.example.com' in settings.cors_allow_origins


def test_cors_allow_origins_is_deduplicated():
    settings = _make_settings(FRONTEND_ORIGINS='http://localhost:5173, http://localhost:5173')
    origins = settings.cors_allow_origins
    assert origins.count('http://localhost:5173') == 1
