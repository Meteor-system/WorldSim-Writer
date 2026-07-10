import os

import pytest
from pydantic import ValidationError
from sqlalchemy import text

os.environ.setdefault('DATABASE_URL', 'postgresql+psycopg://test:test@localhost:5432/test')
os.environ.setdefault('SECRET_KEY', 'test-secret-key')
os.environ.setdefault('LLM_BASE_URL', 'https://example.com/v1')
os.environ.setdefault('LLM_API_KEY', 'test-api-key')
os.environ.setdefault('LLM_MODEL', 'test-model')

from app.core.config import Settings
from app.core.database import (
    Base,
    create_database_engine,
    database_application_name,
    database_connect_args,
    database_engine_options,
    import_models,
)

DATABASE_SETTING_ENV_VARS = (
    'DB_CONNECT_TIMEOUT_SECONDS',
    'DB_APPLICATION_NAME',
    'DB_POOL_SIZE',
    'DB_MAX_OVERFLOW',
    'DB_POOL_TIMEOUT_SECONDS',
    'DB_POOL_RECYCLE_SECONDS',
)


def make_settings(monkeypatch, **overrides) -> Settings:
    for env_var in DATABASE_SETTING_ENV_VARS:
        monkeypatch.delenv(env_var, raising=False)
    values = {
        'DATABASE_URL': 'postgresql+psycopg://test:test@localhost:5432/test',
        'SECRET_KEY': 'test-secret-key',
        'LLM_BASE_URL': 'https://example.com/v1',
        'LLM_API_KEY': 'test-api-key',
        'LLM_MODEL': 'test-model',
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_all_mvp_tables_are_registered():
    import_models()

    assert {
        'users',
        'worlds',
        'characters',
        'character_relations',
        'foreshadows',
        'chapters',
        'chapter_drafts',
        'event_logs',
    }.issubset(Base.metadata.tables.keys())


def test_postgresql_database_options_use_production_defaults(monkeypatch):
    settings = make_settings(monkeypatch)

    assert database_connect_args(settings) == {
        'connect_timeout': 5,
        'application_name': 'worldsim-writer:api',
    }
    assert database_connect_args(settings, role='alembic') == {
        'connect_timeout': 5,
        'application_name': 'worldsim-writer:alembic',
    }
    assert database_engine_options(settings) == {
        'pool_pre_ping': True,
        'connect_args': {
            'connect_timeout': 5,
            'application_name': 'worldsim-writer:api',
        },
        'pool_size': 5,
        'max_overflow': 5,
        'pool_timeout': 5,
        'pool_recycle': 1800,
    }


def test_postgresql_database_options_use_configured_values(monkeypatch):
    settings = make_settings(
        monkeypatch,
        DB_CONNECT_TIMEOUT_SECONDS=9,
        DB_APPLICATION_NAME='writer-prod.1',
        DB_POOL_SIZE=7,
        DB_MAX_OVERFLOW=3,
        DB_POOL_TIMEOUT_SECONDS=11,
        DB_POOL_RECYCLE_SECONDS=900,
    )

    assert database_engine_options(settings) == {
        'pool_pre_ping': True,
        'connect_args': {
            'connect_timeout': 9,
            'application_name': 'writer-prod.1:api',
        },
        'pool_size': 7,
        'max_overflow': 3,
        'pool_timeout': 11,
        'pool_recycle': 900,
    }


def test_sqlite_database_options_omit_postgresql_arguments(monkeypatch):
    settings = make_settings(monkeypatch, DATABASE_URL='sqlite+pysqlite:///:memory:')

    assert database_connect_args(settings) == {}
    assert database_engine_options(settings) == {'pool_pre_ping': True}

    engine = create_database_engine(settings)
    try:
        with engine.connect() as connection:
            assert connection.execute(text('select 1')).scalar_one() == 1
    finally:
        engine.dispose()


def test_database_application_name_fits_postgresql_limit(monkeypatch):
    settings = make_settings(monkeypatch, DB_APPLICATION_NAME='a' * 55)

    application_name = database_application_name(settings, role='alembic')

    assert len(application_name.encode('ascii')) == 63


@pytest.mark.parametrize(
    ('field', 'invalid_value'),
    [
        ('DB_CONNECT_TIMEOUT_SECONDS', 0),
        ('DB_CONNECT_TIMEOUT_SECONDS', 61),
        ('DB_APPLICATION_NAME', ''),
        ('DB_APPLICATION_NAME', 'writer prod'),
        ('DB_APPLICATION_NAME', 'a' * 56),
        ('DB_POOL_SIZE', 0),
        ('DB_POOL_SIZE', 51),
        ('DB_MAX_OVERFLOW', -1),
        ('DB_MAX_OVERFLOW', 51),
        ('DB_POOL_TIMEOUT_SECONDS', 0),
        ('DB_POOL_TIMEOUT_SECONDS', 121),
        ('DB_POOL_RECYCLE_SECONDS', 29),
        ('DB_POOL_RECYCLE_SECONDS', 86401),
    ],
)
def test_database_settings_reject_invalid_values(monkeypatch, field, invalid_value):
    with pytest.raises(ValidationError):
        make_settings(monkeypatch, **{field: invalid_value})
