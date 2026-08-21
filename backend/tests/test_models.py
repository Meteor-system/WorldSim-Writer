import os

import pytest
from pydantic import ValidationError
from sqlalchemy import inspect, select, text

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
from app.llm.usage import record_llm_usage
from app.llm_usage.models import LLMUsageAudit

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
        'llm_usage_audits',
    }.issubset(Base.metadata.tables.keys())


def test_llm_usage_audit_table_matches_model_contract(db_session):
    inspector = inspect(db_session.get_bind())
    columns = {
        column['name']: column
        for column in inspector.get_columns('llm_usage_audits')
    }

    assert set(columns) == {
        'id',
        'world_id',
        'chapter_id',
        'draft_id',
        'operation',
        'provider',
        'api_mode',
        'model',
        'is_mock',
        'status',
        'duration_ms',
        'attempt_count',
        'schema_fallback_used',
        'http_status',
        'input_message_count',
        'input_chars',
        'output_chars',
        'input_tokens',
        'output_tokens',
        'total_tokens',
        'error_code',
        'request_id',
        'provenance',
        'created_at',
    }
    assert {
        name
        for name, column in columns.items()
        if column['nullable']
    } == {
        'world_id',
        'chapter_id',
        'draft_id',
        'http_status',
        'input_tokens',
        'output_tokens',
        'total_tokens',
        'error_code',
        'request_id',
    }
    assert getattr(columns['operation']['type'], 'length', None) == 100
    assert getattr(columns['provider']['type'], 'length', None) == 100
    assert getattr(columns['api_mode']['type'], 'length', None) == 40
    assert getattr(columns['model']['type'], 'length', None) == 200
    assert getattr(columns['status']['type'], 'length', None) == 40
    assert getattr(columns['error_code']['type'], 'length', None) == 40
    assert getattr(columns['request_id']['type'], 'length', None) == 200
    assert inspector.get_pk_constraint('llm_usage_audits')['constrained_columns'] == ['id']

    foreign_keys = {
        foreign_key['constrained_columns'][0]: (
            foreign_key['referred_table'],
            foreign_key['referred_columns'],
            foreign_key.get('options', {}).get('ondelete'),
        )
        for foreign_key in inspector.get_foreign_keys('llm_usage_audits')
    }
    assert foreign_keys == {
        'world_id': ('worlds', ['id'], 'SET NULL'),
        'chapter_id': ('chapters', ['id'], 'SET NULL'),
        'draft_id': ('chapter_drafts', ['id'], 'SET NULL'),
    }
    assert {
        index['name']
        for index in inspector.get_indexes('llm_usage_audits')
    } == {
        'ix_llm_usage_audits_world_id',
        'ix_llm_usage_audits_chapter_id',
        'ix_llm_usage_audits_draft_id',
        'ix_llm_usage_audits_operation',
        'ix_llm_usage_audits_status',
        'ix_llm_usage_audits_created_at',
    }


def test_record_llm_usage_persists_sanitized_audit_record(db_session):
    recorded = record_llm_usage(
        db_session,
        operation='chapter_generation',
        provider='openai-compatible',
        api_mode='responses',
        model='writer-test-model',
        is_mock=True,
        status='success',
        duration_ms=-12,
        attempt_count=0,
        schema_fallback_used=True,
        http_status=200,
        input_message_count=-1,
        input_chars=-20,
        output_chars=88,
        input_tokens=12,
        output_tokens=-3,
        total_tokens=12,
        error_code='UNSAFE_PROVIDER_MESSAGE',
        request_id='req-test-001',
        provenance={
            'endpoint': '/responses',
            'response_id': 'resp-001',
            'schema_name': 'chapter_generation',
            'prompt': 'must not be persisted',
            'authorization': 'must not be persisted',
        },
    )

    assert recorded is True
    db_session.commit()

    audit = db_session.scalar(select(LLMUsageAudit))
    assert audit is not None
    assert audit.operation == 'chapter_generation'
    assert audit.provider == 'openai-compatible'
    assert audit.api_mode == 'responses'
    assert audit.model == 'writer-test-model'
    assert audit.is_mock is True
    assert audit.status == 'success'
    assert audit.duration_ms == 0
    assert audit.attempt_count == 1
    assert audit.schema_fallback_used is True
    assert audit.http_status == 200
    assert audit.input_message_count == 0
    assert audit.input_chars == 0
    assert audit.output_chars == 88
    assert audit.input_tokens == 12
    assert audit.output_tokens is None
    assert audit.total_tokens == 12
    assert audit.error_code is None
    assert audit.request_id == 'req-test-001'
    assert audit.provenance == {
        'endpoint': '/responses',
        'response_id': 'resp-001',
        'schema_name': 'chapter_generation',
    }
    assert audit.created_at is not None


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
