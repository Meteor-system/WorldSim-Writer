from pathlib import Path
from typing import Any

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Column, MetaData, String, Table, text
from sqlalchemy.engine import Connection, Engine

BACKEND_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = BACKEND_ROOT / 'alembic.ini'


def _alembic_config(alembic_ini: Path = ALEMBIC_INI) -> Config:
    config = Config(str(alembic_ini))
    config.set_main_option('script_location', str(alembic_ini.parent / 'alembic'))
    return config


def get_repository_heads(alembic_ini: Path = ALEMBIC_INI) -> list[str]:
    script = ScriptDirectory.from_config(_alembic_config(alembic_ini))
    return sorted(script.get_heads())


def ensure_alembic_version_table_capacity(connection: Connection) -> None:
    metadata = MetaData()
    version_table = Table('alembic_version', metadata, Column('version_num', String(255), primary_key=True))
    version_table.create(connection, checkfirst=True)

    dialect = connection.dialect.name
    if dialect == 'postgresql':
        connection.execute(text('ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(255)'))
    elif dialect in {'mysql', 'mariadb'}:
        connection.execute(text('ALTER TABLE alembic_version MODIFY version_num VARCHAR(255) NOT NULL'))


def get_migration_status(engine: Engine | None = None, alembic_ini: Path = ALEMBIC_INI) -> dict[str, Any]:
    try:
        heads = get_repository_heads(alembic_ini)
        head = heads[0] if len(heads) == 1 else ','.join(heads)
    except Exception:
        return {
            'current': None,
            'head': None,
            'up_to_date': False,
            'status': 'unknown',
            'error': 'MIGRATION_REPOSITORY_UNAVAILABLE',
        }

    try:
        if engine is None:
            from app.core.database import engine as default_engine

            engine = default_engine
        with engine.connect() as connection:
            current_heads = sorted(MigrationContext.configure(connection).get_current_heads())
        current = current_heads[0] if len(current_heads) == 1 else (','.join(current_heads) if current_heads else None)
        up_to_date = current_heads == heads
        return {
            'current': current,
            'head': head,
            'up_to_date': up_to_date,
            'status': 'up_to_date' if up_to_date else 'behind',
        }
    except Exception:
        return {
            'current': None,
            'head': head,
            'up_to_date': False,
            'status': 'unknown',
            'error': 'DATABASE_UNAVAILABLE',
        }
