from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import StaticPool

from app.core.migrations import ensure_alembic_version_table_capacity, get_repository_heads


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
    heads = get_repository_heads(Path('/opt/WorldSim-Writer/backend/alembic.ini'))

    assert heads == ['0013_add_import_node']


def test_alembic_upgrade_from_0012_to_0013_creates_import_tables(tmp_path, monkeypatch):
    target_db = tmp_path / 'target.db'
    env_db = tmp_path / 'env-should-not-be-used.db'
    target_url = f'sqlite+pysqlite:///{target_db}'
    monkeypatch.setenv('DATABASE_URL', f'sqlite+pysqlite:///{env_db}')

    config = Config('/opt/WorldSim-Writer/backend/alembic.ini')
    config.set_main_option('script_location', '/opt/WorldSim-Writer/backend/alembic')
    config.set_main_option('sqlalchemy.url', target_url)

    engine = create_engine(target_url)
    with engine.begin() as connection:
        ensure_alembic_version_table_capacity(connection)
        connection.execute(text('create table worlds (id integer primary key)'))
        connection.execute(text("insert into alembic_version (version_num) values ('0012_add_tags')"))

    command.upgrade(config, 'head')

    inspector = inspect(engine)
    assert inspector.has_table('import_batches')
    assert inspector.has_table('import_candidate_assets')
    with engine.connect() as connection:
        version = connection.scalar(text('select version_num from alembic_version'))
    assert version == '0013_add_import_node'
    assert not env_db.exists()
