from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


engine = create_engine(get_settings().database_url, pool_pre_ping=True)
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
    import app.narrative.models  # noqa: F401
    import app.snapshot_export.models  # noqa: F401
    import app.world.models  # noqa: F401
