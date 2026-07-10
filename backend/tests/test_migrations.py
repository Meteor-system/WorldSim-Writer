import runpy
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

from alembic import context
import sqlalchemy
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import StaticPool

from app.core.migrations import ensure_alembic_version_table_capacity, get_migration_status, get_repository_heads


def test_ensure_alembic_version_table_capacity_creates_wide_version_column():
    engine = create_engine('sqlite+pysqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)

    with engine.begin() as connection:
        ensure_alembic_version_table_capacity(connection)
        connection.execute(
            text('insert into alembic_version (version_num) values (:revision)'),
            {'revision': '0011_add_chapter_execution_context'},
        )

    columns = inspect(engine).get_columns('alembic_version')
    version_column = next(column for column in columns if column['name'] == 'version_num')
    assert getattr(version_column['type'], 'length', None) == 255


def test_get_repository_heads_reads_current_alembic_heads():
    heads = get_repository_heads(Path(__file__).resolve().parents[1] / 'alembic.ini')

    assert heads == ['0013_add_import_node']


def test_get_migration_status_redacts_database_connection_error():
    class UnavailableEngine:
        def connect(self):
            raise RuntimeError('postgresql://user:password@private-host/worldsim')

    status = get_migration_status(engine=UnavailableEngine())

    assert status == {
        'current': None,
        'head': '0013_add_import_node',
        'up_to_date': False,
        'status': 'unknown',
        'error': 'DATABASE_UNAVAILABLE',
    }


def test_get_migration_status_handles_unavailable_repository(tmp_path):
    status = get_migration_status(engine=create_engine('sqlite+pysqlite:///:memory:'), alembic_ini=tmp_path / 'missing.ini')

    assert status == {
        'current': None,
        'head': None,
        'up_to_date': False,
        'status': 'unknown',
        'error': 'MIGRATION_REPOSITORY_UNAVAILABLE',
    }


def test_alembic_online_migrations_commit_version_table_preparation_before_revisions(monkeypatch):
    import app.core.config as config_module
    import app.core.database as database_module
    import app.core.migrations as migrations_module

    events = []

    class FakeConfig:
        config_file_name = None
        config_ini_section = 'alembic'

        def set_main_option(self, key, value):
            events.append(('set_main_option', key, value))

        def get_section(self, section, default):
            return default

    class FakeConnection:
        def __enter__(self):
            events.append('connect')
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            events.append('disconnect')

        def commit(self):
            events.append('commit')

    class FakeConnectable:
        def connect(self):
            return FakeConnection()

    @contextmanager
    def migration_transaction():
        events.append('begin_migration_transaction')
        yield
        events.append('end_migration_transaction')

    monkeypatch.setattr(context, 'config', FakeConfig(), raising=False)
    monkeypatch.setattr(context, 'is_offline_mode', lambda: False)
    monkeypatch.setattr(context, 'configure', lambda **kwargs: events.append('configure'))
    monkeypatch.setattr(context, 'begin_transaction', migration_transaction)
    monkeypatch.setattr(context, 'run_migrations', lambda: events.append('run_migrations'))
    monkeypatch.setattr(sqlalchemy, 'engine_from_config', lambda *args, **kwargs: FakeConnectable())
    monkeypatch.setattr(config_module, 'get_settings', lambda: SimpleNamespace(database_url='postgresql+psycopg://test'))
    monkeypatch.setattr(database_module, 'database_connect_args', lambda settings, role: {})
    monkeypatch.setattr(database_module, 'import_models', lambda: events.append('import_models'))
    monkeypatch.setattr(migrations_module, 'ensure_alembic_version_table_capacity', lambda connection: events.append('ensure_capacity'))

    runpy.run_path(str(Path(__file__).resolve().parents[1] / 'alembic' / 'env.py'))

    assert events.index('ensure_capacity') < events.index('commit')
    assert events.index('commit') < events.index('configure')
    assert events.index('configure') < events.index('begin_migration_transaction')
    assert events.index('begin_migration_transaction') < events.index('run_migrations')
    assert events.count('commit') == 1
