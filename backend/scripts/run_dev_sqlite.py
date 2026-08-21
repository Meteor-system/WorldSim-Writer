"""Dev-only launcher: run the API on SQLite without local PostgreSQL.

Usage:
    python scripts/run_dev_sqlite.py

This registers the same JSONB -> JSON compiler used by the test suite, creates
all tables directly (no Alembic), and starts uvicorn on 127.0.0.1:8000.
Set DATABASE_URL / API_PORT / LLM_MOCK env vars to override.
"""
import os
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_BACKEND_ROOT))

# Do this before importing any app model modules.
os.environ.setdefault('DATABASE_URL', 'sqlite+pysqlite:///./dev_workbench.db')
os.environ.setdefault('LLM_MOCK', 'true')

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.ext.compiler import compiles  # noqa: E402
from sqlalchemy.dialects.postgresql import JSONB  # noqa: E402


@compiles(JSONB, 'sqlite')
def _compile_jsonb_sqlite(_type, _compiler, **_kw):
    return 'JSON'


def main() -> int:
    from app.core.database import Base, import_models

    import_models()
    database_url = os.environ.get('DATABASE_URL', '')
    engine = create_engine(
        database_url,
        connect_args={'check_same_thread': False} if database_url.startswith('sqlite') else {},
    )
    Base.metadata.create_all(engine)
    engine.dispose()
    print(f'[run_dev_sqlite] tables ready on {database_url.split("@")[-1] if "@" in database_url else database_url}')

    import uvicorn

    host = os.environ.get('API_HOST', '127.0.0.1')
    port = int(os.environ.get('API_PORT', '8000'))
    print(f'[run_dev_sqlite] starting API on http://{host}:{port}')
    uvicorn.run(
        'app.main:app',
        host=host,
        port=port,
        log_level='info',
        access_log=False,
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
