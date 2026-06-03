from pathlib import Path

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
