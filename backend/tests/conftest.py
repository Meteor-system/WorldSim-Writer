import os
from collections.abc import Callable, Generator
from pathlib import Path

os.environ.setdefault('DATABASE_URL', 'sqlite+pysqlite:///:memory:')
os.environ.setdefault('SECRET_KEY', 'test-secret')
os.environ.setdefault('LLM_BASE_URL', 'https://example.test/v1')
os.environ.setdefault('LLM_API_KEY', 'test-key')
os.environ.setdefault('LLM_MODEL', 'test-model')

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.dialects.postgresql import JSONB

from app.character.models import Character
from app.core.config import get_settings
from app.core.database import Base, get_db, import_models
from app.main import app
from app.narrative.models import Chapter


def pytest_addoption(parser):
    parser.addoption(
        '--run-real-llm',
        action='store_true',
        default=False,
        help='explicitly select real LLM canary tests; environment cost opt-ins are still required',
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption('--run-real-llm'):
        return
    skip_real_llm = pytest.mark.skip(reason='real LLM canary requires explicit --run-real-llm')
    for item in items:
        if 'real_llm' in item.keywords:
            item.add_marker(skip_real_llm)


@pytest.fixture(autouse=True)
def block_unapproved_llm_network(request, monkeypatch):
    is_real_canary = 'real_llm' in request.node.keywords
    explicitly_selected = request.config.getoption('--run-real-llm')
    cost_opted_in = (
        os.getenv('RUN_REAL_LLM_CANARY') == '1'
        and os.getenv('LLM_CANARY_ACK_COST') == '1'
    )
    if is_real_canary and explicitly_selected and cost_opted_in:
        return

    def blocked_provider_call(*args, **kwargs):
        raise AssertionError(
            'External LLM calls are blocked by default; use --run-real-llm with both canary opt-ins.'
        )

    monkeypatch.setattr(httpx, 'post', blocked_provider_call)


@compiles(JSONB, 'sqlite')
def compile_jsonb_sqlite(_type, compiler, **kw):
    return 'JSON'


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def db_session(tmp_path: Path) -> Generator[Session, None, None]:
    import_models()
    database_path = tmp_path / 'worldsim-test.sqlite3'
    engine = create_engine(f'sqlite+pysqlite:///{database_path}', connect_args={'check_same_thread': False})
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


@pytest.fixture
def opening_approval_payload(db_session: Session) -> Callable[[dict], dict]:
    def build(draft: dict) -> dict:
        chapter = db_session.get(Chapter, int(draft['chapter_id']))
        assert chapter is not None
        assert chapter.pov_character_id is not None
        locked_character = db_session.get(Character, chapter.pov_character_id)
        assert locked_character is not None
        draft_version = int(draft.get('draft_version') or chapter.draft_version)
        return {
            'draft_version': draft_version,
            'opening_pov_confirmation': {
                'confirmed': True,
                'draft_version': draft_version,
                'locked_character_id': locked_character.id,
                'locked_character_name': locked_character.name,
            },
        }

    return build


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
