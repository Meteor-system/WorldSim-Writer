import os

os.environ.setdefault('DATABASE_URL', 'postgresql+psycopg://test:test@localhost:5432/test')
os.environ.setdefault('SECRET_KEY', 'test-secret-key')
os.environ.setdefault('LLM_BASE_URL', 'https://example.com/v1')
os.environ.setdefault('LLM_API_KEY', 'test-api-key')
os.environ.setdefault('LLM_MODEL', 'test-model')

from app.core.database import Base, import_models


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
