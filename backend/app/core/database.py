from collections.abc import Generator
from typing import Any, Literal

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import Settings, get_settings

DatabaseRole = Literal['api', 'alembic']


class Base(DeclarativeBase):
    pass


def database_application_name(settings: Settings, role: DatabaseRole) -> str:
    return f'{settings.db_application_name}:{role}'


def database_connect_args(settings: Settings, role: DatabaseRole = 'api') -> dict[str, Any]:
    if make_url(settings.database_url).get_backend_name() != 'postgresql':
        return {}
    return {
        'connect_timeout': settings.db_connect_timeout_seconds,
        'application_name': database_application_name(settings, role),
    }


def database_engine_options(settings: Settings) -> dict[str, Any]:
    options: dict[str, Any] = {'pool_pre_ping': True}
    connect_args = database_connect_args(settings)
    if not connect_args:
        return options
    options.update(
        {
            'connect_args': connect_args,
            'pool_size': settings.db_pool_size,
            'max_overflow': settings.db_max_overflow,
            'pool_timeout': settings.db_pool_timeout_seconds,
            'pool_recycle': settings.db_pool_recycle_seconds,
        }
    )
    return options


def create_database_engine(settings: Settings | None = None) -> Engine:
    current_settings = settings or get_settings()
    return create_engine(current_settings.database_url, **database_engine_options(current_settings))


engine = create_database_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def import_models() -> None:
    import app.auth.models  # noqa: F401
    import app.character.models  # noqa: F401
    import app.event.models  # noqa: F401
    import app.foreshadow.models  # noqa: F401
    import app.import_node.models  # noqa: F401
    import app.narrative.models  # noqa: F401
    import app.snapshot_export.models  # noqa: F401
    import app.tags.models  # noqa: F401
    import app.world.models  # noqa: F401
