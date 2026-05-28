# WorldSim-Writer MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first runnable WorldSim-Writer loop: login, create a sample world, generate a chapter draft with a real OpenAI-compatible API, approve it, and see world, character, foreshadow, and event state changes.

**Architecture:** Use a FastAPI monolith with PostgreSQL, SQLAlchemy, and Alembic for the backend, plus a React/Vite/Tailwind frontend. Keep backend code split by domain (`auth`, `world`, `character`, `foreshadow`, `narrative`, `event`, `llm`) while deploying as one app.

**Tech Stack:** Python 3.12 in conda env `worldsim`, FastAPI, SQLAlchemy, Alembic, psycopg, Pydantic Settings, pytest, httpx, React, Vite, TypeScript, Tailwind, Vitest, Testing Library.

---

## File Structure

### Backend

- Create: `backend/pyproject.toml` — Python package metadata, dependencies, and pytest configuration.
- Create: `backend/.env.example` — redacted local configuration template.
- Create: `backend/alembic.ini` — Alembic command configuration.
- Create: `backend/alembic/env.py` — Alembic metadata loading from SQLAlchemy models.
- Create: `backend/alembic/versions/0001_initial_schema.py` — initial database schema migration.
- Create: `backend/app/__init__.py` — backend package marker.
- Create: `backend/app/main.py` — FastAPI app, CORS, health endpoint, API router mounting.
- Create: `backend/app/core/config.py` — environment-driven settings.
- Create: `backend/app/core/database.py` — SQLAlchemy base, engine, and session dependency.
- Create: `backend/app/core/security.py` — password hashing and JWT helpers.
- Create: `backend/app/api/dependencies.py` — shared auth/database dependencies.
- Create: `backend/app/api/router.py` — top-level API router composition.
- Create: `backend/app/auth/models.py` — `User` SQLAlchemy model.
- Create: `backend/app/auth/schemas.py` — auth request/response schemas.
- Create: `backend/app/auth/service.py` — registration, login, and current-user lookup.
- Create: `backend/app/auth/router.py` — auth endpoints.
- Create: `backend/app/world/models.py` — `World` SQLAlchemy model.
- Create: `backend/app/world/schemas.py` — world creation and overview schemas.
- Create: `backend/app/world/templates.py` — built-in sample world payload.
- Create: `backend/app/world/service.py` — sample world creation and overview aggregation.
- Create: `backend/app/world/router.py` — world endpoints.
- Create: `backend/app/character/models.py` — `Character` and `CharacterRelation` models.
- Create: `backend/app/character/schemas.py` — character and relation response schemas.
- Create: `backend/app/foreshadow/models.py` — `Foreshadow` model.
- Create: `backend/app/foreshadow/schemas.py` — foreshadow response schema.
- Create: `backend/app/narrative/models.py` — `Chapter` and `ChapterDraft` models.
- Create: `backend/app/narrative/schemas.py` — draft, chapter, approval schemas.
- Create: `backend/app/narrative/service.py` — draft generation and approval transaction.
- Create: `backend/app/narrative/router.py` — narrative endpoints.
- Create: `backend/app/event/models.py` — `EventLog` model.
- Create: `backend/app/event/schemas.py` — event response schema.
- Create: `backend/app/llm/client.py` — OpenAI-compatible Chat Completions client.
- Create: `backend/app/llm/schemas.py` — structured LLM response schema.
- Create: `backend/tests/conftest.py` — test database setup and FastAPI client fixtures.
- Create: `backend/tests/test_auth.py` — auth behavior tests.
- Create: `backend/tests/test_world_template.py` — sample world and overview tests.
- Create: `backend/tests/test_llm_client.py` — model response parsing tests.
- Create: `backend/tests/test_narrative_approval.py` — generation and approval transaction tests.

### Frontend

- Create: `frontend/package.json` — scripts and dependencies.
- Create: `frontend/index.html` — Vite HTML entry.
- Create: `frontend/src/main.tsx` — React root rendering.
- Create: `frontend/src/App.tsx` — page routing by auth/world/studio state.
- Create: `frontend/src/api/client.ts` — authenticated fetch wrapper.
- Create: `frontend/src/api/types.ts` — frontend API types.
- Create: `frontend/src/auth/AuthPage.tsx` — login/register page.
- Create: `frontend/src/world/WorldPage.tsx` — world overview and sample-world creation.
- Create: `frontend/src/studio/StudioPage.tsx` — chapter goal input, draft display, approval flow.
- Create: `frontend/src/styles.css` — Tailwind entry and minimal layout styles.
- Create: `frontend/tests/App.test.tsx` — frontend flow tests with mocked API.

### Root docs

- Modify: `CLAUDE.md` — replace “no commands exist” with actual backend/frontend commands after scaffolding.
- Create or modify: `README.md` — local setup and manual acceptance instructions.

---

## Task 1: Backend scaffold and configuration

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/.env.example`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/database.py`
- Create: `backend/app/core/security.py`
- Create: `backend/app/api/router.py`
- Test: `backend/tests/test_health.py`

- [ ] **Step 1: Create the backend package and dependency manifest**

Write `backend/pyproject.toml`:

```toml
[project]
name = "worldsim-writer-backend"
version = "0.1.0"
description = "FastAPI backend for the WorldSim-Writer MVP loop"
requires-python = ">=3.12"
dependencies = [
  "alembic>=1.13.0",
  "email-validator>=2.1.0",
  "fastapi>=0.115.0",
  "httpx>=0.27.0",
  "passlib[bcrypt]>=1.7.4",
  "psycopg[binary]>=3.2.0",
  "pydantic-settings>=2.6.0",
  "python-jose[cryptography]>=3.3.0",
  "python-multipart>=0.0.9",
  "sqlalchemy>=2.0.0",
  "uvicorn[standard]>=0.30.0"
]

[project.optional-dependencies]
dev = [
  "pytest>=8.3.0",
  "pytest-cov>=5.0.0"
]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

- [ ] **Step 2: Create the backend environment template**

Write `backend/.env.example`:

```env
DATABASE_URL=postgresql+psycopg://worldsim:worldsim@localhost:5432/worldsim_writer
SECRET_KEY=change-this-local-secret
ACCESS_TOKEN_EXPIRE_MINUTES=1440
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=replace-with-your-key
LLM_MODEL=gpt-4o-mini
LLM_TIMEOUT_SECONDS=60
FRONTEND_ORIGIN=http://localhost:5173
```

- [ ] **Step 3: Create configuration loading**

Write `backend/app/core/config.py`:

```python
from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    database_url: str = Field(alias='DATABASE_URL')
    secret_key: str = Field(alias='SECRET_KEY')
    access_token_expire_minutes: int = Field(default=1440, alias='ACCESS_TOKEN_EXPIRE_MINUTES')
    llm_base_url: AnyHttpUrl = Field(alias='LLM_BASE_URL')
    llm_api_key: str = Field(alias='LLM_API_KEY')
    llm_model: str = Field(alias='LLM_MODEL')
    llm_timeout_seconds: int = Field(default=60, alias='LLM_TIMEOUT_SECONDS')
    frontend_origin: str = Field(default='http://localhost:5173', alias='FRONTEND_ORIGIN')


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 4: Create database session wiring**

Write `backend/app/core/database.py`:

```python
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
```

- [ ] **Step 5: Create security helpers**

Write `backend/app/core/security.py`:

```python
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

ALGORITHM = 'HS256'
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: str) -> str:
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {'sub': subject, 'exp': expires_at}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, get_settings().secret_key, algorithms=[ALGORITHM])
    except JWTError:
        return None
    subject = payload.get('sub')
    return subject if isinstance(subject, str) else None
```

- [ ] **Step 6: Create the FastAPI app and health endpoint**

Write `backend/app/api/router.py`:

```python
from fastapi import APIRouter

api_router = APIRouter()
```

Write `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title='WorldSim-Writer API')
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    app.include_router(api_router)
    return app


app = create_app()


@app.get('/health')
def health_check() -> dict[str, str]:
    return {'status': 'ok'}
```

Write `backend/app/__init__.py` as an empty file.

- [ ] **Step 7: Write the health test**

Write `backend/tests/test_health.py`:

```python
from fastapi.testclient import TestClient

from app.main import app


def test_health_check_returns_ok():
    client = TestClient(app)

    response = client.get('/health')

    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}
```

- [ ] **Step 8: Run the scaffold test**

Run:

```bash
conda activate worldsim && cd backend && pip install -e '.[dev]' && pytest tests/test_health.py -v
```

Expected: `test_health_check_returns_ok PASSED`.

- [ ] **Step 9: Commit the backend scaffold**

Run:

```bash
git add backend/pyproject.toml backend/.env.example backend/app backend/tests/test_health.py
git commit -m "Build FastAPI backend scaffold"
```

---

## Task 2: Database models and Alembic migration

**Files:**
- Create: `backend/app/auth/models.py`
- Create: `backend/app/world/models.py`
- Create: `backend/app/character/models.py`
- Create: `backend/app/foreshadow/models.py`
- Create: `backend/app/narrative/models.py`
- Create: `backend/app/event/models.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/0001_initial_schema.py`
- Test: `backend/tests/test_models.py`

- [ ] **Step 1: Define auth and world models**

Write `backend/app/auth/models.py`:

```python
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    worlds: Mapped[list['World']] = relationship(back_populates='owner')
```

Write `backend/app/world/models.py`:

```python
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class World(Base):
    __tablename__ = 'worlds'

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    title: Mapped[str] = mapped_column(String(200))
    genre_template: Mapped[str] = mapped_column(String(80))
    truth_canon: Mapped[str] = mapped_column(Text)
    truth_canon_version: Mapped[int] = mapped_column(Integer, default=1)
    world_version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(40), default='active')
    tone_profile: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    owner: Mapped['User'] = relationship(back_populates='worlds')
    characters: Mapped[list['Character']] = relationship(back_populates='world', cascade='all, delete-orphan')
    foreshadows: Mapped[list['Foreshadow']] = relationship(back_populates='world', cascade='all, delete-orphan')
    chapters: Mapped[list['Chapter']] = relationship(back_populates='world', cascade='all, delete-orphan')
    events: Mapped[list['EventLog']] = relationship(back_populates='world', cascade='all, delete-orphan')
```

- [ ] **Step 2: Define character and foreshadow models**

Write `backend/app/character/models.py`:

```python
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Character(Base):
    __tablename__ = 'characters'

    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[int] = mapped_column(ForeignKey('worlds.id', ondelete='CASCADE'), index=True)
    name: Mapped[str] = mapped_column(String(120))
    role_type: Mapped[str] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(60), default='active')
    public_profile: Mapped[dict] = mapped_column(JSONB, default=dict)
    hidden_traits: Mapped[dict] = mapped_column(JSONB, default=dict)
    destiny_flag: Mapped[str | None] = mapped_column(String(120), nullable=True)
    current_goals: Mapped[list[str]] = mapped_column(JSONB, default=list)

    world: Mapped['World'] = relationship(back_populates='characters')


class CharacterRelation(Base):
    __tablename__ = 'character_relations'

    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[int] = mapped_column(ForeignKey('worlds.id', ondelete='CASCADE'), index=True)
    source_character_id: Mapped[int] = mapped_column(ForeignKey('characters.id', ondelete='CASCADE'))
    target_character_id: Mapped[int] = mapped_column(ForeignKey('characters.id', ondelete='CASCADE'))
    relation_type: Mapped[str] = mapped_column(String(80))
    intensity: Mapped[int] = mapped_column(Integer, default=1)
    visibility: Mapped[str] = mapped_column(String(40), default='public')
```

Write `backend/app/foreshadow/models.py`:

```python
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Foreshadow(Base):
    __tablename__ = 'foreshadows'

    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[int] = mapped_column(ForeignKey('worlds.id', ondelete='CASCADE'), index=True)
    source_chapter_id: Mapped[int | None] = mapped_column(ForeignKey('chapters.id', ondelete='SET NULL'), nullable=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    foreshadow_type: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(40), default='planted')
    urgency_level: Mapped[int] = mapped_column(Integer, default=1)
    related_character_ids: Mapped[list[int]] = mapped_column(JSONB, default=list)
    expected_resolution_window: Mapped[str | None] = mapped_column(String(120), nullable=True)

    world: Mapped['World'] = relationship(back_populates='foreshadows')
```

- [ ] **Step 3: Define narrative and event models**

Write `backend/app/narrative/models.py`:

```python
from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Chapter(Base):
    __tablename__ = 'chapters'

    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[int] = mapped_column(ForeignKey('worlds.id', ondelete='CASCADE'), index=True)
    title: Mapped[str] = mapped_column(String(200))
    pov_character_id: Mapped[int | None] = mapped_column(ForeignKey('characters.id', ondelete='SET NULL'), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default='reviewing')
    draft_version: Mapped[int] = mapped_column(Integer, default=1)
    approved_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    base_world_version: Mapped[int] = mapped_column(Integer)
    approved_content: Mapped[str | None] = mapped_column(Text, nullable=True)

    world: Mapped['World'] = relationship(back_populates='chapters')
    drafts: Mapped[list['ChapterDraft']] = relationship(back_populates='chapter', cascade='all, delete-orphan')


class ChapterDraft(Base):
    __tablename__ = 'chapter_drafts'
    __table_args__ = (UniqueConstraint('chapter_id', 'draft_version', name='uq_chapter_draft_version'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey('chapters.id', ondelete='CASCADE'), index=True)
    draft_version: Mapped[int] = mapped_column(Integer, default=1)
    content: Mapped[str] = mapped_column(Text)
    context_summary: Mapped[str] = mapped_column(Text)
    review_hints: Mapped[list[str]] = mapped_column(JSONB, default=list)
    proposed_changes: Mapped[dict] = mapped_column(JSONB, default=dict)
    source_world_version: Mapped[int] = mapped_column(Integer)

    chapter: Mapped[Chapter] = relationship(back_populates='drafts')
```

Write `backend/app/event/models.py`:

```python
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EventLog(Base):
    __tablename__ = 'event_logs'

    id: Mapped[int] = mapped_column(primary_key=True)
    world_id: Mapped[int] = mapped_column(ForeignKey('worlds.id', ondelete='CASCADE'), index=True)
    event_type: Mapped[str] = mapped_column(String(80))
    source_type: Mapped[str] = mapped_column(String(80))
    commit_id: Mapped[str] = mapped_column(String(120), unique=True)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    world_version_before: Mapped[int] = mapped_column(Integer)
    world_version_after: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    world: Mapped['World'] = relationship(back_populates='events')
```

- [ ] **Step 4: Import all models for metadata registration**

Append to `backend/app/core/database.py`:

```python

def import_models() -> None:
    import app.auth.models  # noqa: F401
    import app.character.models  # noqa: F401
    import app.event.models  # noqa: F401
    import app.foreshadow.models  # noqa: F401
    import app.narrative.models  # noqa: F401
    import app.world.models  # noqa: F401
```

- [ ] **Step 5: Create Alembic configuration**

Write `backend/alembic.ini`:

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = postgresql+psycopg://worldsim:worldsim@localhost:5432/worldsim_writer

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

Write `backend/alembic/env.py`:

```python
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.core.database import Base, import_models

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

import_models()
target_metadata = Base.metadata
config.set_main_option('sqlalchemy.url', get_settings().database_url)


def run_migrations_offline() -> None:
    context.configure(url=get_settings().database_url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix='sqlalchemy.', poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 6: Create the initial migration**

Write `backend/alembic/versions/0001_initial_schema.py` with table definitions matching the models:

```python
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0001_initial_schema'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(length=320), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_table(
        'worlds',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('genre_template', sa.String(length=80), nullable=False),
        sa.Column('truth_canon', sa.Text(), nullable=False),
        sa.Column('truth_canon_version', sa.Integer(), nullable=False),
        sa.Column('world_version', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('tone_profile', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_worlds_owner_id', 'worlds', ['owner_id'])
    op.create_table(
        'characters',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('world_id', sa.Integer(), sa.ForeignKey('worlds.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('role_type', sa.String(length=60), nullable=False),
        sa.Column('status', sa.String(length=60), nullable=False),
        sa.Column('public_profile', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('hidden_traits', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('destiny_flag', sa.String(length=120), nullable=True),
        sa.Column('current_goals', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    )
    op.create_index('ix_characters_world_id', 'characters', ['world_id'])
    op.create_table(
        'character_relations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('world_id', sa.Integer(), sa.ForeignKey('worlds.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_character_id', sa.Integer(), sa.ForeignKey('characters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_character_id', sa.Integer(), sa.ForeignKey('characters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relation_type', sa.String(length=80), nullable=False),
        sa.Column('intensity', sa.Integer(), nullable=False),
        sa.Column('visibility', sa.String(length=40), nullable=False),
    )
    op.create_index('ix_character_relations_world_id', 'character_relations', ['world_id'])
    op.create_table(
        'chapters',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('world_id', sa.Integer(), sa.ForeignKey('worlds.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('pov_character_id', sa.Integer(), sa.ForeignKey('characters.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('draft_version', sa.Integer(), nullable=False),
        sa.Column('approved_version', sa.Integer(), nullable=True),
        sa.Column('base_world_version', sa.Integer(), nullable=False),
        sa.Column('approved_content', sa.Text(), nullable=True),
    )
    op.create_index('ix_chapters_world_id', 'chapters', ['world_id'])
    op.create_table(
        'foreshadows',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('world_id', sa.Integer(), sa.ForeignKey('worlds.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_chapter_id', sa.Integer(), sa.ForeignKey('chapters.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('foreshadow_type', sa.String(length=80), nullable=False),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('urgency_level', sa.Integer(), nullable=False),
        sa.Column('related_character_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('expected_resolution_window', sa.String(length=120), nullable=True),
    )
    op.create_index('ix_foreshadows_world_id', 'foreshadows', ['world_id'])
    op.create_table(
        'chapter_drafts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('chapter_id', sa.Integer(), sa.ForeignKey('chapters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('draft_version', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('context_summary', sa.Text(), nullable=False),
        sa.Column('review_hints', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('proposed_changes', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('source_world_version', sa.Integer(), nullable=False),
        sa.UniqueConstraint('chapter_id', 'draft_version', name='uq_chapter_draft_version'),
    )
    op.create_index('ix_chapter_drafts_chapter_id', 'chapter_drafts', ['chapter_id'])
    op.create_table(
        'event_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('world_id', sa.Integer(), sa.ForeignKey('worlds.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(length=80), nullable=False),
        sa.Column('source_type', sa.String(length=80), nullable=False),
        sa.Column('commit_id', sa.String(length=120), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('world_version_before', sa.Integer(), nullable=False),
        sa.Column('world_version_after', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_event_logs_world_id', 'event_logs', ['world_id'])
    op.create_index('ix_event_logs_commit_id', 'event_logs', ['commit_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_event_logs_commit_id', table_name='event_logs')
    op.drop_index('ix_event_logs_world_id', table_name='event_logs')
    op.drop_table('event_logs')
    op.drop_index('ix_chapter_drafts_chapter_id', table_name='chapter_drafts')
    op.drop_table('chapter_drafts')
    op.drop_index('ix_foreshadows_world_id', table_name='foreshadows')
    op.drop_table('foreshadows')
    op.drop_index('ix_chapters_world_id', table_name='chapters')
    op.drop_table('chapters')
    op.drop_index('ix_character_relations_world_id', table_name='character_relations')
    op.drop_table('character_relations')
    op.drop_index('ix_characters_world_id', table_name='characters')
    op.drop_table('characters')
    op.drop_index('ix_worlds_owner_id', table_name='worlds')
    op.drop_table('worlds')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
```

- [ ] **Step 7: Write a metadata registration test**

Write `backend/tests/test_models.py`:

```python
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
```

- [ ] **Step 8: Run model tests**

Run:

```bash
conda activate worldsim && cd backend && pytest tests/test_models.py -v
```

Expected: `test_all_mvp_tables_are_registered PASSED`.

- [ ] **Step 9: Commit the schema work**

Run:

```bash
git add backend/app backend/alembic.ini backend/alembic backend/tests/test_models.py
git commit -m "Add initial MVP database schema"
```

---

## Task 3: Authentication API

**Files:**
- Create: `backend/app/auth/schemas.py`
- Create: `backend/app/auth/service.py`
- Create: `backend/app/auth/router.py`
- Create: `backend/app/api/dependencies.py`
- Modify: `backend/app/api/router.py`
- Test: `backend/tests/conftest.py`
- Test: `backend/tests/test_auth.py`

- [ ] **Step 1: Write auth schemas**

Write `backend/app/auth/schemas.py`:

```python
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr

    model_config = {'from_attributes': True}


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    user: UserResponse
```

- [ ] **Step 2: Write auth service functions**

Write `backend/app/auth/service.py`:

```python
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.core.security import create_access_token, hash_password, verify_password


def register_user(db: Session, email: str, password: str) -> tuple[User, str]:
    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='EMAIL_ALREADY_REGISTERED')
    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, create_access_token(str(user.id))


def authenticate_user(db: Session, email: str, password: str) -> tuple[User, str]:
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='INVALID_CREDENTIALS')
    return user, create_access_token(str(user.id))


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)
```

- [ ] **Step 3: Write current-user dependency**

Write `backend/app/api/dependencies.py`:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.models import User
from app.auth.service import get_user_by_id
from app.core.database import get_db
from app.core.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


def require_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='UNAUTHORIZED')
    subject = decode_access_token(credentials.credentials)
    if subject is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='UNAUTHORIZED')
    user = get_user_by_id(db, int(subject))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='UNAUTHORIZED')
    return user
```

- [ ] **Step 4: Write auth router and mount it**

Write `backend/app/auth/router.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_user
from app.auth.models import User
from app.auth.schemas import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from app.auth.service import authenticate_user, register_user
from app.core.database import get_db

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/register', response_model=AuthResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user, token = register_user(db, payload.email, payload.password)
    return AuthResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post('/login', response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user, token = authenticate_user(db, payload.email, payload.password)
    return AuthResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post('/logout')
def logout() -> dict[str, bool]:
    return {'success': True}


@router.get('/me', response_model=UserResponse)
def me(current_user: User = Depends(require_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
```

Replace `backend/app/api/router.py` with:

```python
from fastapi import APIRouter

from app.auth.router import router as auth_router

api_router = APIRouter()
api_router.include_router(auth_router)
```

- [ ] **Step 5: Write isolated test fixtures**

Write `backend/tests/conftest.py`:

```python
import os
from collections.abc import Generator

os.environ.setdefault('DATABASE_URL', 'sqlite+pysqlite:///:memory:')
os.environ.setdefault('SECRET_KEY', 'test-secret')
os.environ.setdefault('LLM_BASE_URL', 'https://example.test/v1')
os.environ.setdefault('LLM_API_KEY', 'test-key')
os.environ.setdefault('LLM_MODEL', 'test-model')

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.database import Base, get_db, import_models
from app.main import app


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    import_models()
    engine = create_engine('sqlite+pysqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

- [ ] **Step 6: Write auth API tests**

Write `backend/tests/test_auth.py`:

```python
def test_register_login_and_me(client):
    register_response = client.post('/auth/register', json={'email': 'writer@example.com', 'password': 'strongpass123'})

    assert register_response.status_code == 200
    token = register_response.json()['access_token']
    assert register_response.json()['user']['email'] == 'writer@example.com'

    me_response = client.get('/auth/me', headers={'Authorization': f'Bearer {token}'})
    assert me_response.status_code == 200
    assert me_response.json()['email'] == 'writer@example.com'

    login_response = client.post('/auth/login', json={'email': 'writer@example.com', 'password': 'strongpass123'})
    assert login_response.status_code == 200
    assert login_response.json()['access_token']


def test_register_rejects_duplicate_email(client):
    client.post('/auth/register', json={'email': 'writer@example.com', 'password': 'strongpass123'})

    response = client.post('/auth/register', json={'email': 'writer@example.com', 'password': 'strongpass123'})

    assert response.status_code == 409
    assert response.json()['detail'] == 'EMAIL_ALREADY_REGISTERED'


def test_me_requires_token(client):
    response = client.get('/auth/me')

    assert response.status_code == 401
    assert response.json()['detail'] == 'UNAUTHORIZED'
```

- [ ] **Step 7: Run auth tests**

Run:

```bash
conda activate worldsim && cd backend && pytest tests/test_auth.py -v
```

Expected: all three auth tests pass.

- [ ] **Step 8: Commit auth API**

Run:

```bash
git add backend/app backend/tests/conftest.py backend/tests/test_auth.py
git commit -m "Add single-user authentication API"
```

---

## Task 4: Sample world creation and overview API

**Files:**
- Create: `backend/app/character/schemas.py`
- Create: `backend/app/event/schemas.py`
- Create: `backend/app/foreshadow/schemas.py`
- Create: `backend/app/world/schemas.py`
- Create: `backend/app/world/templates.py`
- Create: `backend/app/world/service.py`
- Create: `backend/app/world/router.py`
- Modify: `backend/app/api/router.py`
- Test: `backend/tests/test_world_template.py`

- [ ] **Step 1: Write response schemas**

Write `backend/app/character/schemas.py`:

```python
from pydantic import BaseModel


class CharacterResponse(BaseModel):
    id: int
    name: str
    role_type: str
    status: str
    public_profile: dict
    hidden_traits: dict
    destiny_flag: str | None
    current_goals: list[str]

    model_config = {'from_attributes': True}


class CharacterRelationResponse(BaseModel):
    id: int
    source_character_id: int
    target_character_id: int
    relation_type: str
    intensity: int
    visibility: str

    model_config = {'from_attributes': True}
```

Write `backend/app/foreshadow/schemas.py`:

```python
from pydantic import BaseModel


class ForeshadowResponse(BaseModel):
    id: int
    title: str
    description: str
    foreshadow_type: str
    status: str
    urgency_level: int
    related_character_ids: list[int]
    expected_resolution_window: str | None

    model_config = {'from_attributes': True}
```

Write `backend/app/event/schemas.py`:

```python
from datetime import datetime

from pydantic import BaseModel


class EventLogResponse(BaseModel):
    id: int
    event_type: str
    source_type: str
    commit_id: str
    payload: dict
    world_version_before: int
    world_version_after: int
    created_at: datetime

    model_config = {'from_attributes': True}
```

Write `backend/app/world/schemas.py`:

```python
from pydantic import BaseModel

from app.character.schemas import CharacterRelationResponse, CharacterResponse
from app.event.schemas import EventLogResponse
from app.foreshadow.schemas import ForeshadowResponse


class WorldResponse(BaseModel):
    id: int
    title: str
    genre_template: str
    truth_canon: str
    truth_canon_version: int
    world_version: int
    status: str
    tone_profile: dict

    model_config = {'from_attributes': True}


class WorldOverviewResponse(WorldResponse):
    characters: list[CharacterResponse]
    relations: list[CharacterRelationResponse]
    foreshadows: list[ForeshadowResponse]
    recent_events: list[EventLogResponse]
```

- [ ] **Step 2: Define the built-in sample template**

Write `backend/app/world/templates.py`:

```python
SAMPLE_WORLD = {
    'title': '青岚城风云',
    'genre_template': 'xianxia_intrigue',
    'truth_canon': '青岚城由城主府、云河剑宗与地下商盟共同影响。灵脉衰退正在改变各方力量平衡，主角必须查清城主府叛乱传闻的真相。',
    'tone_profile': {'style': '克制、悬疑、东方玄幻', 'pacing': '章节末保留明确推进'},
    'characters': [
        {
            'name': '林砚',
            'role_type': 'protagonist',
            'status': 'active',
            'public_profile': {'identity': '云河剑宗外门弟子', 'skill': '擅长阵纹推演'},
            'hidden_traits': {'fear': '害怕牵连师门'},
            'destiny_flag': '灵脉异动见证者',
            'current_goals': ['调查青岚城灵脉衰退'],
        },
        {
            'name': '沈微霜',
            'role_type': 'ally',
            'status': 'active',
            'public_profile': {'identity': '城主府书记官', 'skill': '熟悉卷宗与密道'},
            'hidden_traits': {'secret': '曾替叛乱嫌疑人销毁证据'},
            'destiny_flag': '关键证人',
            'current_goals': ['保住城主府档案'],
        },
    ],
    'relations': [
        {'source_index': 0, 'target_index': 1, 'relation_type': 'uneasy_alliance', 'intensity': 2, 'visibility': 'public'},
    ],
    'foreshadows': [
        {
            'title': '裂纹玉佩',
            'description': '林砚在废弃灵井旁拾到一枚带城主府纹章的裂纹玉佩。',
            'foreshadow_type': 'object_clue',
            'status': 'planted',
            'urgency_level': 3,
            'related_character_indexes': [0, 1],
            'expected_resolution_window': '第2-4章',
        }
    ],
}
```

- [ ] **Step 3: Write world service**

Write `backend/app/world/service.py`:

```python
from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.character.models import Character, CharacterRelation
from app.event.models import EventLog
from app.foreshadow.models import Foreshadow
from app.world.models import World
from app.world.templates import SAMPLE_WORLD


def create_sample_world(db: Session, user: User) -> World:
    world = World(
        owner_id=user.id,
        title=SAMPLE_WORLD['title'],
        genre_template=SAMPLE_WORLD['genre_template'],
        truth_canon=SAMPLE_WORLD['truth_canon'],
        truth_canon_version=1,
        world_version=1,
        status='active',
        tone_profile=SAMPLE_WORLD['tone_profile'],
    )
    db.add(world)
    db.flush()

    characters: list[Character] = []
    for item in SAMPLE_WORLD['characters']:
        character = Character(world_id=world.id, **item)
        db.add(character)
        characters.append(character)
    db.flush()

    for item in SAMPLE_WORLD['relations']:
        db.add(CharacterRelation(
            world_id=world.id,
            source_character_id=characters[item['source_index']].id,
            target_character_id=characters[item['target_index']].id,
            relation_type=item['relation_type'],
            intensity=item['intensity'],
            visibility=item['visibility'],
        ))

    for item in SAMPLE_WORLD['foreshadows']:
        db.add(Foreshadow(
            world_id=world.id,
            title=item['title'],
            description=item['description'],
            foreshadow_type=item['foreshadow_type'],
            status=item['status'],
            urgency_level=item['urgency_level'],
            related_character_ids=[characters[index].id for index in item['related_character_indexes']],
            expected_resolution_window=item['expected_resolution_window'],
        ))

    db.commit()
    db.refresh(world)
    return world


def list_user_worlds(db: Session, user: User) -> list[World]:
    return list(db.scalars(select(World).where(World.owner_id == user.id).order_by(World.id)))


def require_owned_world(db: Session, user: User, world_id: int) -> World:
    world = db.get(World, world_id)
    if world is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    if world.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='FORBIDDEN')
    return world


def get_world_overview(db: Session, user: User, world_id: int) -> dict:
    world = require_owned_world(db, user, world_id)
    characters = list(db.scalars(select(Character).where(Character.world_id == world.id).order_by(Character.id)))
    relations = list(db.scalars(select(CharacterRelation).where(CharacterRelation.world_id == world.id).order_by(CharacterRelation.id)))
    foreshadows = list(db.scalars(select(Foreshadow).where(Foreshadow.world_id == world.id).order_by(Foreshadow.id)))
    recent_events = list(db.scalars(select(EventLog).where(EventLog.world_id == world.id).order_by(desc(EventLog.id)).limit(10)))
    return {
        **world.__dict__,
        'characters': characters,
        'relations': relations,
        'foreshadows': foreshadows,
        'recent_events': recent_events,
    }
```

- [ ] **Step 4: Write world router and mount it**

Write `backend/app/world/router.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_user
from app.auth.models import User
from app.core.database import get_db
from app.world.schemas import WorldOverviewResponse, WorldResponse
from app.world.service import create_sample_world, get_world_overview, list_user_worlds, require_owned_world

router = APIRouter(prefix='/worlds', tags=['worlds'])


@router.post('/from-template', response_model=WorldResponse)
def create_from_template(current_user: User = Depends(require_user), db: Session = Depends(get_db)) -> WorldResponse:
    return WorldResponse.model_validate(create_sample_world(db, current_user))


@router.get('', response_model=list[WorldResponse])
def list_worlds(current_user: User = Depends(require_user), db: Session = Depends(get_db)) -> list[WorldResponse]:
    return [WorldResponse.model_validate(world) for world in list_user_worlds(db, current_user)]


@router.get('/{world_id}', response_model=WorldResponse)
def get_world(world_id: int, current_user: User = Depends(require_user), db: Session = Depends(get_db)) -> WorldResponse:
    return WorldResponse.model_validate(require_owned_world(db, current_user, world_id))


@router.get('/{world_id}/overview', response_model=WorldOverviewResponse)
def overview(world_id: int, current_user: User = Depends(require_user), db: Session = Depends(get_db)) -> WorldOverviewResponse:
    return WorldOverviewResponse.model_validate(get_world_overview(db, current_user, world_id))
```

Replace `backend/app/api/router.py` with:

```python
from fastapi import APIRouter

from app.auth.router import router as auth_router
from app.world.router import router as world_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(world_router)
```

- [ ] **Step 5: Write sample world tests**

Write `backend/tests/test_world_template.py`:

```python
def register(client):
    response = client.post('/auth/register', json={'email': 'writer@example.com', 'password': 'strongpass123'})
    return response.json()['access_token']


def test_create_sample_world_and_overview(client):
    token = register(client)

    create_response = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {token}'})

    assert create_response.status_code == 200
    world_id = create_response.json()['id']
    assert create_response.json()['world_version'] == 1

    overview_response = client.get(f'/worlds/{world_id}/overview', headers={'Authorization': f'Bearer {token}'})
    overview = overview_response.json()

    assert overview_response.status_code == 200
    assert overview['title'] == '青岚城风云'
    assert len(overview['characters']) == 2
    assert len(overview['relations']) == 1
    assert len(overview['foreshadows']) == 1
    assert overview['recent_events'] == []


def test_world_endpoints_require_login(client):
    response = client.post('/worlds/from-template')

    assert response.status_code == 401
    assert response.json()['detail'] == 'UNAUTHORIZED'
```

- [ ] **Step 6: Run world tests**

Run:

```bash
conda activate worldsim && cd backend && pytest tests/test_world_template.py -v
```

Expected: both world tests pass.

- [ ] **Step 7: Commit world API**

Run:

```bash
git add backend/app backend/tests/test_world_template.py
git commit -m "Add sample world overview API"
```

---

## Task 5: LLM client and response validation

**Files:**
- Create: `backend/app/llm/schemas.py`
- Create: `backend/app/llm/client.py`
- Test: `backend/tests/test_llm_client.py`

- [ ] **Step 1: Define structured generation schema**

Write `backend/app/llm/schemas.py`:

```python
import json

from pydantic import BaseModel, ValidationError


class ProposedCharacterChange(BaseModel):
    character_id: int
    status: str | None = None
    current_goals: list[str] | None = None


class ProposedForeshadowChange(BaseModel):
    foreshadow_id: int
    status: str
    description_note: str | None = None


class ChapterGeneration(BaseModel):
    title: str
    draft_content: str
    context_summary: str
    review_hints: list[str]
    proposed_character_changes: list[ProposedCharacterChange]
    proposed_foreshadow_changes: list[ProposedForeshadowChange]


def parse_chapter_generation(raw_text: str) -> ChapterGeneration:
    try:
        payload = json.loads(raw_text)
        return ChapterGeneration.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError('MODEL_RESPONSE_INVALID') from exc
```

- [ ] **Step 2: Implement OpenAI-compatible client**

Write `backend/app/llm/client.py`:

```python
import httpx

from app.core.config import Settings, get_settings
from app.llm.schemas import ChapterGeneration, parse_chapter_generation


class LLMClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def generate_chapter(self, messages: list[dict[str, str]]) -> ChapterGeneration:
        try:
            response = httpx.post(
                f'{self.settings.llm_base_url}/chat/completions',
                headers={'Authorization': f'Bearer {self.settings.llm_api_key}'},
                json={
                    'model': self.settings.llm_model,
                    'messages': messages,
                    'temperature': 0.7,
                    'response_format': {'type': 'json_object'},
                },
                timeout=self.settings.llm_timeout_seconds,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise TimeoutError('MODEL_TIMEOUT') from exc
        except httpx.HTTPError as exc:
            raise RuntimeError('MODEL_REQUEST_FAILED') from exc

        choices = response.json().get('choices', [])
        if not choices:
            raise ValueError('MODEL_RESPONSE_INVALID')
        content = choices[0].get('message', {}).get('content')
        if not isinstance(content, str):
            raise ValueError('MODEL_RESPONSE_INVALID')
        return parse_chapter_generation(content)
```

- [ ] **Step 3: Write parser tests**

Write `backend/tests/test_llm_client.py`:

```python
import json

import pytest

from app.llm.schemas import parse_chapter_generation


def test_parse_chapter_generation_accepts_valid_json():
    result = parse_chapter_generation(json.dumps({
        'title': '第一章 暗井回声',
        'draft_content': '林砚在灵井旁听见了第二个人的脚步声。',
        'context_summary': '林砚调查灵脉衰退，裂纹玉佩成为线索。',
        'review_hints': ['确认沈微霜动机是否一致'],
        'proposed_character_changes': [{'character_id': 1, 'current_goals': ['追查城主府叛乱']}],
        'proposed_foreshadow_changes': [{'foreshadow_id': 1, 'status': 'triggered', 'description_note': '玉佩线索被推进'}],
    }))

    assert result.title == '第一章 暗井回声'
    assert result.proposed_character_changes[0].character_id == 1
    assert result.proposed_foreshadow_changes[0].status == 'triggered'


def test_parse_chapter_generation_rejects_non_json():
    with pytest.raises(ValueError, match='MODEL_RESPONSE_INVALID'):
        parse_chapter_generation('not json')


def test_parse_chapter_generation_rejects_missing_fields():
    with pytest.raises(ValueError, match='MODEL_RESPONSE_INVALID'):
        parse_chapter_generation(json.dumps({'title': '缺字段'}))
```

- [ ] **Step 4: Run LLM parser tests**

Run:

```bash
conda activate worldsim && cd backend && pytest tests/test_llm_client.py -v
```

Expected: all three LLM parser tests pass.

- [ ] **Step 5: Commit LLM client**

Run:

```bash
git add backend/app/llm backend/tests/test_llm_client.py
git commit -m "Add structured LLM response validation"
```

---

## Task 6: Narrative draft creation and approval transaction

**Files:**
- Create: `backend/app/narrative/schemas.py`
- Create: `backend/app/narrative/service.py`
- Create: `backend/app/narrative/router.py`
- Modify: `backend/app/api/router.py`
- Test: `backend/tests/test_narrative_approval.py`

- [ ] **Step 1: Write narrative schemas**

Write `backend/app/narrative/schemas.py`:

```python
from pydantic import BaseModel, Field


class DraftRequest(BaseModel):
    chapter_goal: str = Field(min_length=3)


class DraftResponse(BaseModel):
    chapter_id: int
    draft_id: int
    title: str
    content: str
    context_summary: str
    review_hints: list[str]
    proposed_changes: dict
    source_world_version: int


class ChapterResponse(BaseModel):
    id: int
    world_id: int
    title: str
    status: str
    draft_version: int
    approved_version: int | None
    base_world_version: int
    approved_content: str | None

    model_config = {'from_attributes': True}
```

- [ ] **Step 2: Implement context assembly and draft creation**

Write the first part of `backend/app/narrative/service.py`:

```python
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.character.models import Character
from app.event.models import EventLog
from app.foreshadow.models import Foreshadow
from app.llm.client import LLMClient
from app.llm.schemas import ChapterGeneration
from app.narrative.models import Chapter, ChapterDraft
from app.world.service import require_owned_world


def build_generation_messages(world, characters: list[Character], foreshadows: list[Foreshadow], chapter_goal: str) -> list[dict[str, str]]:
    character_lines = '\n'.join(f'- {c.id}: {c.name}, status={c.status}, goals={c.current_goals}' for c in characters)
    foreshadow_lines = '\n'.join(f'- {f.id}: {f.title}, status={f.status}, urgency={f.urgency_level}' for f in foreshadows)
    return [
        {'role': 'system', 'content': '你是长篇小说创作系统的章节起草助手。必须只返回 JSON。'},
        {
            'role': 'user',
            'content': (
                f'世界设定：{world.truth_canon}\n'
                f'世界版本：{world.world_version}\n'
                f'角色：\n{character_lines}\n'
                f'伏笔：\n{foreshadow_lines}\n'
                f'本章目标：{chapter_goal}\n'
                '返回字段：title, draft_content, context_summary, review_hints, '
                'proposed_character_changes, proposed_foreshadow_changes。'
            ),
        },
    ]


def validate_generation_ids(generation: ChapterGeneration, characters: list[Character], foreshadows: list[Foreshadow]) -> None:
    character_ids = {character.id for character in characters}
    foreshadow_ids = {foreshadow.id for foreshadow in foreshadows}
    if any(change.character_id not in character_ids for change in generation.proposed_character_changes):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='MODEL_RESPONSE_INVALID')
    if any(change.foreshadow_id not in foreshadow_ids for change in generation.proposed_foreshadow_changes):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='MODEL_RESPONSE_INVALID')


def create_chapter_draft(db: Session, user: User, world_id: int, chapter_goal: str, llm_client: LLMClient | None = None) -> dict:
    world = require_owned_world(db, user, world_id)
    characters = list(db.scalars(select(Character).where(Character.world_id == world.id).order_by(Character.id)))
    foreshadows = list(db.scalars(select(Foreshadow).where(Foreshadow.world_id == world.id).order_by(Foreshadow.urgency_level.desc(), Foreshadow.id)))
    client = llm_client or LLMClient()
    try:
        generation = client.generate_chapter(build_generation_messages(world, characters, foreshadows, chapter_goal))
    except TimeoutError as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail='MODEL_TIMEOUT') from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='MODEL_RESPONSE_INVALID') from exc
    validate_generation_ids(generation, characters, foreshadows)

    chapter = Chapter(
        world_id=world.id,
        title=generation.title,
        pov_character_id=characters[0].id if characters else None,
        status='reviewing',
        draft_version=1,
        base_world_version=world.world_version,
    )
    db.add(chapter)
    db.flush()
    proposed_changes = {
        'characters': [change.model_dump(exclude_none=True) for change in generation.proposed_character_changes],
        'foreshadows': [change.model_dump(exclude_none=True) for change in generation.proposed_foreshadow_changes],
    }
    draft = ChapterDraft(
        chapter_id=chapter.id,
        draft_version=1,
        content=generation.draft_content,
        context_summary=generation.context_summary,
        review_hints=generation.review_hints,
        proposed_changes=proposed_changes,
        source_world_version=world.world_version,
    )
    db.add(draft)
    db.commit()
    db.refresh(chapter)
    db.refresh(draft)
    return {
        'chapter_id': chapter.id,
        'draft_id': draft.id,
        'title': chapter.title,
        'content': draft.content,
        'context_summary': draft.context_summary,
        'review_hints': draft.review_hints,
        'proposed_changes': draft.proposed_changes,
        'source_world_version': draft.source_world_version,
    }
```

- [ ] **Step 3: Implement approval transaction**

Append to `backend/app/narrative/service.py`:

```python

def approve_chapter(db: Session, user: User, chapter_id: int) -> Chapter:
    chapter = db.get(Chapter, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    world = require_owned_world(db, user, chapter.world_id)
    draft = db.scalar(
        select(ChapterDraft)
        .where(ChapterDraft.chapter_id == chapter.id)
        .where(ChapterDraft.draft_version == chapter.draft_version)
    )
    if draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    if draft.source_world_version != world.world_version:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='WORLD_VERSION_MISMATCH')

    version_before = world.world_version
    chapter.status = 'approved'
    chapter.approved_content = draft.content
    chapter.approved_version = draft.draft_version

    for change in draft.proposed_changes.get('characters', []):
        character = db.get(Character, change['character_id'])
        if character is None or character.world_id != world.id:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='MODEL_RESPONSE_INVALID')
        if 'status' in change:
            character.status = change['status']
        if 'current_goals' in change:
            character.current_goals = change['current_goals']

    for change in draft.proposed_changes.get('foreshadows', []):
        foreshadow = db.get(Foreshadow, change['foreshadow_id'])
        if foreshadow is None or foreshadow.world_id != world.id:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='MODEL_RESPONSE_INVALID')
        foreshadow.status = change['status']
        if change.get('description_note'):
            foreshadow.description = f"{foreshadow.description}\n审核备注：{change['description_note']}"

    world.world_version = version_before + 1
    db.add(EventLog(
        world_id=world.id,
        event_type='CHAPTER_APPROVED',
        source_type='chapter',
        commit_id=f'chapter-{chapter.id}-{uuid4().hex}',
        payload={
            'chapter_id': chapter.id,
            'chapter_title': chapter.title,
            'proposed_changes': draft.proposed_changes,
        },
        world_version_before=version_before,
        world_version_after=world.world_version,
    ))
    db.commit()
    db.refresh(chapter)
    return chapter
```

- [ ] **Step 4: Write narrative router and mount it**

Write `backend/app/narrative/router.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_user
from app.auth.models import User
from app.core.database import get_db
from app.narrative.schemas import ChapterResponse, DraftRequest, DraftResponse
from app.narrative.service import approve_chapter, create_chapter_draft

router = APIRouter(tags=['narrative'])


@router.post('/worlds/{world_id}/chapters/draft', response_model=DraftResponse)
def draft_chapter(
    world_id: int,
    payload: DraftRequest,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> DraftResponse:
    return DraftResponse.model_validate(create_chapter_draft(db, current_user, world_id, payload.chapter_goal))


@router.post('/chapters/{chapter_id}/approve', response_model=ChapterResponse)
def approve(
    chapter_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> ChapterResponse:
    return ChapterResponse.model_validate(approve_chapter(db, current_user, chapter_id))


@router.post('/chapters/{chapter_id}/reject', response_model=ChapterResponse)
def reject(
    chapter_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> ChapterResponse:
    chapter = approve_chapter(db, current_user, chapter_id)
    chapter.status = 'rejected'
    db.commit()
    db.refresh(chapter)
    return ChapterResponse.model_validate(chapter)
```

Replace `backend/app/api/router.py` with:

```python
from fastapi import APIRouter

from app.auth.router import router as auth_router
from app.narrative.router import router as narrative_router
from app.world.router import router as world_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(world_router)
api_router.include_router(narrative_router)
```

Before running tests, fix the reject endpoint to avoid approving on reject:

```python
from fastapi import HTTPException, status

from app.narrative.models import Chapter
from app.world.service import require_owned_world


@router.post('/chapters/{chapter_id}/reject', response_model=ChapterResponse)
def reject(
    chapter_id: int,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> ChapterResponse:
    chapter = db.get(Chapter, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='NOT_FOUND')
    require_owned_world(db, current_user, chapter.world_id)
    chapter.status = 'rejected'
    db.commit()
    db.refresh(chapter)
    return ChapterResponse.model_validate(chapter)
```

- [ ] **Step 5: Write narrative approval tests**

Write `backend/tests/test_narrative_approval.py`:

```python
from app.llm.schemas import ChapterGeneration, ProposedCharacterChange, ProposedForeshadowChange
from app.narrative import service as narrative_service


class FakeLLMClient:
    def generate_chapter(self, messages):
        return ChapterGeneration(
            title='第一章 暗井回声',
            draft_content='林砚在灵井旁听见了第二个人的脚步声。',
            context_summary='林砚调查灵脉衰退，裂纹玉佩成为线索。',
            review_hints=['确认沈微霜动机是否一致'],
            proposed_character_changes=[ProposedCharacterChange(character_id=1, current_goals=['追查城主府叛乱'])],
            proposed_foreshadow_changes=[ProposedForeshadowChange(foreshadow_id=1, status='triggered', description_note='玉佩线索被推进')],
        )


def register_and_create_world(client):
    token = client.post('/auth/register', json={'email': 'writer@example.com', 'password': 'strongpass123'}).json()['access_token']
    world = client.post('/worlds/from-template', headers={'Authorization': f'Bearer {token}'}).json()
    return token, world['id']


def test_create_draft_with_fake_llm(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())

    response = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert response.status_code == 200
    assert response.json()['title'] == '第一章 暗井回声'
    assert response.json()['source_world_version'] == 1
    assert response.json()['proposed_changes']['characters'][0]['current_goals'] == ['追查城主府叛乱']


def test_approve_chapter_updates_world_character_foreshadow_and_events(client, monkeypatch):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()

    approve_response = client.post(f"/chapters/{draft['chapter_id']}/approve", headers={'Authorization': f'Bearer {token}'})
    overview_response = client.get(f'/worlds/{world_id}/overview', headers={'Authorization': f'Bearer {token}'})
    overview = overview_response.json()

    assert approve_response.status_code == 200
    assert overview['world_version'] == 2
    assert overview['characters'][0]['current_goals'] == ['追查城主府叛乱']
    assert overview['foreshadows'][0]['status'] == 'triggered'
    assert overview['recent_events'][0]['event_type'] == 'CHAPTER_APPROVED'
    assert overview['recent_events'][0]['world_version_before'] == 1
    assert overview['recent_events'][0]['world_version_after'] == 2


def test_approve_rejects_world_version_mismatch(client, monkeypatch, db_session):
    token, world_id = register_and_create_world(client)
    monkeypatch.setattr(narrative_service, 'LLMClient', lambda: FakeLLMClient())
    draft = client.post(
        f'/worlds/{world_id}/chapters/draft',
        json={'chapter_goal': '推进玉佩线索'},
        headers={'Authorization': f'Bearer {token}'},
    ).json()
    world = db_session.get(__import__('app.world.models', fromlist=['World']).World, world_id)
    world.world_version = 2
    db_session.commit()

    response = client.post(f"/chapters/{draft['chapter_id']}/approve", headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 409
    assert response.json()['detail'] == 'WORLD_VERSION_MISMATCH'
```

- [ ] **Step 6: Run narrative tests**

Run:

```bash
conda activate worldsim && cd backend && pytest tests/test_narrative_approval.py -v
```

Expected: all three narrative tests pass.

- [ ] **Step 7: Commit narrative API**

Run:

```bash
git add backend/app backend/tests/test_narrative_approval.py
git commit -m "Add chapter draft and approval workflow"
```

---

## Task 7: Frontend scaffold and API client

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/types.ts`
- Create: `frontend/src/styles.css`

- [ ] **Step 1: Create frontend package manifest**

Write `frontend/package.json`:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "test": "vitest run"
  },
  "dependencies": {
    "@vitejs/plugin-react": "latest",
    "vite": "latest",
    "typescript": "latest",
    "react": "latest",
    "react-dom": "latest",
    "tailwindcss": "latest",
    "@tailwindcss/vite": "latest"
  },
  "devDependencies": {
    "@testing-library/react": "latest",
    "@testing-library/jest-dom": "latest",
    "@testing-library/user-event": "latest",
    "jsdom": "latest",
    "vitest": "latest"
  }
}
```

- [ ] **Step 2: Create Vite entry files**

Write `frontend/index.html`:

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>WorldSim-Writer</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Write `frontend/src/main.tsx`:

```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App';
import './styles.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

- [ ] **Step 3: Create API types**

Write `frontend/src/api/types.ts`:

```ts
export type User = { id: number; email: string };
export type AuthResponse = { access_token: string; token_type: string; user: User };

export type Character = {
  id: number;
  name: string;
  role_type: string;
  status: string;
  public_profile: Record<string, unknown>;
  hidden_traits: Record<string, unknown>;
  destiny_flag: string | null;
  current_goals: string[];
};

export type Foreshadow = {
  id: number;
  title: string;
  description: string;
  foreshadow_type: string;
  status: string;
  urgency_level: number;
  related_character_ids: number[];
  expected_resolution_window: string | null;
};

export type EventLog = {
  id: number;
  event_type: string;
  source_type: string;
  commit_id: string;
  payload: Record<string, unknown>;
  world_version_before: number;
  world_version_after: number;
  created_at: string;
};

export type WorldOverview = {
  id: number;
  title: string;
  genre_template: string;
  truth_canon: string;
  truth_canon_version: number;
  world_version: number;
  status: string;
  tone_profile: Record<string, unknown>;
  characters: Character[];
  relations: Array<Record<string, unknown>>;
  foreshadows: Foreshadow[];
  recent_events: EventLog[];
};

export type DraftResponse = {
  chapter_id: number;
  draft_id: number;
  title: string;
  content: string;
  context_summary: string;
  review_hints: string[];
  proposed_changes: Record<string, unknown>;
  source_world_version: number;
};
```

- [ ] **Step 4: Create authenticated API client**

Write `frontend/src/api/client.ts`:

```ts
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('worldsim_token');
  const headers = new Headers(options.headers);
  headers.set('Content-Type', 'application/json');
  if (token) headers.set('Authorization', `Bearer ${token}`);
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!response.ok) throw new Error(await response.text());
  return response.json() as Promise<T>;
}
```

- [ ] **Step 5: Create a shell App and styles**

Write `frontend/src/App.tsx`:

```tsx
export function App() {
  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <section className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="text-3xl font-bold">WorldSim-Writer</h1>
        <p className="mt-3 text-slate-300">长篇叙事世界创作台 MVP</p>
      </section>
    </main>
  );
}
```

Write `frontend/src/styles.css`:

```css
@import "tailwindcss";

body {
  margin: 0;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
```

- [ ] **Step 6: Install and build frontend**

Run:

```bash
cd frontend && npm install && npm run build
```

Expected: Vite production build succeeds and creates `frontend/dist`.

- [ ] **Step 7: Commit frontend scaffold**

Run:

```bash
git add frontend/package.json frontend/package-lock.json frontend/index.html frontend/src
git commit -m "Build React frontend scaffold"
```

---

## Task 8: Frontend auth, world page, and studio flow

**Files:**
- Create: `frontend/src/auth/AuthPage.tsx`
- Create: `frontend/src/world/WorldPage.tsx`
- Create: `frontend/src/studio/StudioPage.tsx`
- Modify: `frontend/src/App.tsx`
- Test: `frontend/tests/App.test.tsx`

- [ ] **Step 1: Build auth page**

Write `frontend/src/auth/AuthPage.tsx`:

```tsx
import { FormEvent, useState } from 'react';
import { apiRequest } from '../api/client';
import type { AuthResponse } from '../api/types';

type Props = { onAuth: (userEmail: string) => void };

export function AuthPage({ onAuth }: Props) {
  const [email, setEmail] = useState('writer@example.com');
  const [password, setPassword] = useState('strongpass123');
  const [error, setError] = useState('');

  async function submit(event: FormEvent, mode: 'login' | 'register') {
    event.preventDefault();
    setError('');
    try {
      const response = await apiRequest<AuthResponse>(`/auth/${mode}`, {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      localStorage.setItem('worldsim_token', response.access_token);
      onAuth(response.user.email);
    } catch (err) {
      setError(err instanceof Error ? err.message : '认证失败');
    }
  }

  return (
    <section className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
      <h1 className="text-3xl font-bold">WorldSim-Writer</h1>
      <p className="mt-2 text-slate-300">登录后创建世界并生成第一章草稿。</p>
      <form className="mt-8 space-y-4">
        <input className="w-full rounded bg-slate-800 px-4 py-3" value={email} onChange={(event) => setEmail(event.target.value)} aria-label="邮箱" />
        <input className="w-full rounded bg-slate-800 px-4 py-3" type="password" value={password} onChange={(event) => setPassword(event.target.value)} aria-label="密码" />
        {error && <p className="rounded bg-red-950 px-3 py-2 text-red-200">{error}</p>}
        <div className="flex gap-3">
          <button className="rounded bg-cyan-500 px-4 py-2 font-semibold text-slate-950" onClick={(event) => submit(event, 'login')}>登录</button>
          <button className="rounded border border-slate-600 px-4 py-2" onClick={(event) => submit(event, 'register')}>注册</button>
        </div>
      </form>
    </section>
  );
}
```

- [ ] **Step 2: Build world page**

Write `frontend/src/world/WorldPage.tsx`:

```tsx
import { useEffect, useState } from 'react';
import { apiRequest } from '../api/client';
import type { WorldOverview } from '../api/types';

type Props = { onEnterStudio: (world: WorldOverview) => void };

export function WorldPage({ onEnterStudio }: Props) {
  const [world, setWorld] = useState<WorldOverview | null>(null);
  const [loading, setLoading] = useState(true);

  async function loadWorld() {
    const worlds = await apiRequest<Array<{ id: number }>>('/worlds');
    if (worlds.length === 0) {
      setWorld(null);
    } else {
      setWorld(await apiRequest<WorldOverview>(`/worlds/${worlds[0].id}/overview`));
    }
    setLoading(false);
  }

  async function createWorld() {
    const created = await apiRequest<{ id: number }>('/worlds/from-template', { method: 'POST', body: '{}' });
    setWorld(await apiRequest<WorldOverview>(`/worlds/${created.id}/overview`));
  }

  useEffect(() => {
    loadWorld().catch(() => setLoading(false));
  }, []);

  if (loading) return <p className="p-6">加载世界中...</p>;

  if (!world) {
    return (
      <section className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="text-3xl font-bold">还没有世界</h1>
        <p className="mt-3 text-slate-300">创建内置示例世界，开始最小闭环。</p>
        <button className="mt-6 rounded bg-cyan-500 px-4 py-2 font-semibold text-slate-950" onClick={createWorld}>创建“青岚城风云”</button>
      </section>
    );
  }

  return (
    <section className="mx-auto max-w-6xl px-6 py-10">
      <div className="flex items-start justify-between gap-6">
        <div>
          <h1 className="text-3xl font-bold">{world.title}</h1>
          <p className="mt-2 text-slate-300">版本 {world.world_version} · {world.genre_template} · {world.status}</p>
        </div>
        <button className="rounded bg-cyan-500 px-4 py-2 font-semibold text-slate-950" onClick={() => onEnterStudio(world)}>进入创作台</button>
      </div>
      <div className="mt-8 grid gap-4 md:grid-cols-2">
        <article className="rounded bg-slate-900 p-4"><h2 className="font-semibold">真理库</h2><p className="mt-2 text-slate-300">{world.truth_canon}</p></article>
        <article className="rounded bg-slate-900 p-4"><h2 className="font-semibold">最近事件</h2>{world.recent_events.map((event) => <p key={event.id}>{event.event_type}: {event.world_version_before} → {event.world_version_after}</p>)}</article>
        <article className="rounded bg-slate-900 p-4"><h2 className="font-semibold">角色</h2>{world.characters.map((character) => <p key={character.id}>{character.name}: {character.current_goals.join('、')}</p>)}</article>
        <article className="rounded bg-slate-900 p-4"><h2 className="font-semibold">伏笔</h2>{world.foreshadows.map((item) => <p key={item.id}>{item.title}: {item.status}</p>)}</article>
      </div>
    </section>
  );
}
```

- [ ] **Step 3: Build studio page**

Write `frontend/src/studio/StudioPage.tsx`:

```tsx
import { useState } from 'react';
import { apiRequest } from '../api/client';
import type { DraftResponse, WorldOverview } from '../api/types';

type Props = { world: WorldOverview; onBack: () => void; onApproved: (world: WorldOverview) => void };

export function StudioPage({ world, onBack, onApproved }: Props) {
  const [goal, setGoal] = useState('推进裂纹玉佩线索，并让林砚发现城主府叛乱传闻的新证据。');
  const [draft, setDraft] = useState<DraftResponse | null>(null);
  const [working, setWorking] = useState(false);

  async function generateDraft() {
    setWorking(true);
    try {
      setDraft(await apiRequest<DraftResponse>(`/worlds/${world.id}/chapters/draft`, {
        method: 'POST',
        body: JSON.stringify({ chapter_goal: goal }),
      }));
    } finally {
      setWorking(false);
    }
  }

  async function approveDraft() {
    if (!draft) return;
    setWorking(true);
    try {
      await apiRequest(`/chapters/${draft.chapter_id}/approve`, { method: 'POST', body: '{}' });
      onApproved(await apiRequest<WorldOverview>(`/worlds/${world.id}/overview`));
    } finally {
      setWorking(false);
    }
  }

  return (
    <section className="mx-auto grid max-w-6xl gap-6 px-6 py-10 md:grid-cols-[280px_1fr]">
      <aside className="rounded bg-slate-900 p-4">
        <button className="mb-4 text-cyan-300" onClick={onBack}>返回世界页</button>
        <h2 className="font-semibold">当前上下文</h2>
        <p className="mt-2 text-sm text-slate-300">世界版本：{world.world_version}</p>
        <p className="mt-2 text-sm text-slate-300">POV：{world.characters[0]?.name ?? '未设置'}</p>
        <h3 className="mt-4 font-semibold">紧迫伏笔</h3>
        {world.foreshadows.map((item) => <p className="text-sm text-slate-300" key={item.id}>{item.title} · {item.status}</p>)}
      </aside>
      <main className="space-y-4">
        <h1 className="text-3xl font-bold">创作台</h1>
        <textarea className="h-28 w-full rounded bg-slate-800 p-3" value={goal} onChange={(event) => setGoal(event.target.value)} aria-label="章节目标" />
        <button className="rounded bg-cyan-500 px-4 py-2 font-semibold text-slate-950" disabled={working} onClick={generateDraft}>{working ? '处理中...' : '生成草稿'}</button>
        {draft && (
          <article className="space-y-4 rounded bg-slate-900 p-4">
            <h2 className="text-xl font-semibold">{draft.title}</h2>
            <p className="whitespace-pre-wrap text-slate-200">{draft.content}</p>
            <div><h3 className="font-semibold">上下文摘要</h3><p className="text-slate-300">{draft.context_summary}</p></div>
            <div><h3 className="font-semibold">审核提示</h3>{draft.review_hints.map((hint) => <p key={hint} className="text-slate-300">{hint}</p>)}</div>
            <pre className="overflow-auto rounded bg-slate-950 p-3 text-sm">{JSON.stringify(draft.proposed_changes, null, 2)}</pre>
            <button className="rounded bg-emerald-500 px-4 py-2 font-semibold text-slate-950" disabled={working} onClick={approveDraft}>通过并更新世界</button>
          </article>
        )}
      </main>
    </section>
  );
}
```

- [ ] **Step 4: Wire pages in App**

Replace `frontend/src/App.tsx` with:

```tsx
import { useState } from 'react';
import type { WorldOverview } from './api/types';
import { AuthPage } from './auth/AuthPage';
import { StudioPage } from './studio/StudioPage';
import { WorldPage } from './world/WorldPage';

export function App() {
  const [userEmail, setUserEmail] = useState(localStorage.getItem('worldsim_token') ? '已登录用户' : '');
  const [studioWorld, setStudioWorld] = useState<WorldOverview | null>(null);
  const [approvedWorld, setApprovedWorld] = useState<WorldOverview | null>(null);

  if (!userEmail) return <AuthPage onAuth={setUserEmail} />;

  if (studioWorld) {
    return (
      <main className="min-h-screen bg-slate-950 text-slate-100">
        <StudioPage
          world={studioWorld}
          onBack={() => setStudioWorld(null)}
          onApproved={(world) => {
            setApprovedWorld(world);
            setStudioWorld(null);
          }}
        />
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 px-6 py-3 text-sm text-slate-300">{userEmail}</header>
      {approvedWorld && <div className="bg-emerald-950 px-6 py-3 text-emerald-100">章节已通过，世界版本更新为 {approvedWorld.world_version}</div>}
      <WorldPage onEnterStudio={setStudioWorld} />
    </main>
  );
}
```

- [ ] **Step 5: Write frontend smoke test**

Write `frontend/tests/App.test.tsx`:

```tsx
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { App } from '../src/App';

describe('App', () => {
  it('shows the auth page when no token exists', () => {
    localStorage.clear();

    render(<App />);

    expect(screen.getByText('WorldSim-Writer')).toBeInTheDocument();
    expect(screen.getByText('登录')).toBeInTheDocument();
    expect(screen.getByText('注册')).toBeInTheDocument();
  });
});
```

- [ ] **Step 6: Run frontend tests and build**

Run:

```bash
cd frontend && npm run test && npm run build
```

Expected: Vitest passes and Vite production build succeeds.

- [ ] **Step 7: Commit frontend flow**

Run:

```bash
git add frontend/src frontend/tests
git commit -m "Add MVP frontend writing flow"
```

---

## Task 9: Local run documentation and manual end-to-end verification

**Files:**
- Modify: `CLAUDE.md`
- Create or modify: `README.md`

- [ ] **Step 1: Update repository commands in CLAUDE.md**

Replace the “Commands” section in `CLAUDE.md` with:

```markdown
## Commands

Run backend commands from `backend/` inside the project conda environment:

```bash
conda activate worldsim
pip install -e '.[dev]'
alembic upgrade head
uvicorn app.main:app --reload
pytest
pytest tests/test_narrative_approval.py -v
```

Run frontend commands from `frontend/`:

```bash
npm install
npm run dev
npm run build
npm run test
```

For local MVP acceptance, run the backend at `http://localhost:8000` and the frontend at `http://localhost:5173`.
```

- [ ] **Step 2: Write local setup README**

Write `README.md`:

```markdown
# WorldSim-Writer

WorldSim-Writer is a long-form narrative creation system. The MVP runs a small local loop: register or log in, create the built-in sample world, generate a chapter draft through an OpenAI-compatible Chat Completions API, approve the draft, and see world state updates.

## Local setup

Backend:

```bash
conda activate worldsim
cd backend
cp .env.example .env
pip install -e '.[dev]'
alembic upgrade head
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Set `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL` in `backend/.env` before generating a chapter draft.

## Verification

Run backend tests:

```bash
conda activate worldsim
cd backend
pytest
```

Run frontend tests:

```bash
cd frontend
npm run test
npm run build
```

Manual MVP check:

1. Open the frontend at `http://localhost:5173`.
2. Register or log in.
3. Create the built-in sample world.
4. Enter the studio.
5. Generate a chapter draft.
6. Approve the draft.
7. Confirm `world_version` changes from `1` to `2`.
8. Confirm a `CHAPTER_APPROVED` event appears.
9. Confirm at least one character goal changes.
10. Confirm the foreshadow status changes or the draft shows why no foreshadow changed.
```

- [ ] **Step 3: Run full automated checks**

Run:

```bash
conda activate worldsim && cd backend && pytest
```

Expected: all backend tests pass.

Run:

```bash
cd frontend && npm run test && npm run build
```

Expected: all frontend tests pass and the production build succeeds.

- [ ] **Step 4: Start backend and frontend for manual browser verification**

Terminal 1:

```bash
conda activate worldsim && cd backend && uvicorn app.main:app --reload
```

Terminal 2:

```bash
cd frontend && npm run dev
```

Expected: backend listens on `http://localhost:8000`; frontend listens on `http://localhost:5173`.

- [ ] **Step 5: Verify the browser loop**

In the browser:

1. Open `http://localhost:5173`.
2. Register with `writer@example.com` and `strongpass123`.
3. Click `创建“青岚城风云”`.
4. Confirm the world page shows version `1`, two characters, one foreshadow, and no recent events.
5. Click `进入创作台`.
6. Keep the default chapter goal or enter `让林砚追踪裂纹玉佩并发现城主府叛乱证据`.
7. Click `生成草稿`.
8. Confirm a chapter title, draft content, context summary, review hints, and proposed changes appear.
9. Click `通过并更新世界`.
10. Confirm the world page shows version `2`.
11. Confirm recent events include `CHAPTER_APPROVED`.
12. Confirm a character goal now mentions `追查城主府叛乱`.
13. Confirm `裂纹玉佩` status is `triggered`, or the draft review area explained why no foreshadow changed.

- [ ] **Step 6: Commit documentation**

Run:

```bash
git add CLAUDE.md README.md
git commit -m "Document local MVP workflow"
```

---

## Task 10: Final quality gate and push

**Files:**
- Review: all changed files

- [ ] **Step 1: Check git status and diff**

Run:

```bash
git status --short
git diff --stat HEAD
```

Expected: no untracked secrets, no `.env`, no `.superpowers`, no `node_modules`, no `frontend/dist`.

- [ ] **Step 2: Run final backend tests**

Run:

```bash
conda activate worldsim && cd backend && pytest -v
```

Expected: all backend tests pass.

- [ ] **Step 3: Run final frontend tests and build**

Run:

```bash
cd frontend && npm run test && npm run build
```

Expected: all frontend tests pass and Vite build succeeds.

- [ ] **Step 4: Run manual browser acceptance one more time**

Use the steps from Task 9 Step 5. Expected: login, sample-world creation, draft generation, approval, `world_version` increment, `CHAPTER_APPROVED`, character change, and foreshadow change are visible in the browser.

- [ ] **Step 5: Push only after user approval**

If the user asks to push the completed implementation, run:

```bash
git push origin main
```

Expected: GitHub `main` contains the MVP implementation and documentation.

---

## Self-Review

### Spec coverage

- Login/register: Task 3 backend, Task 8 frontend.
- Sample world creation: Task 4 backend, Task 8 frontend.
- Real OpenAI-compatible model call: Task 5 backend, Task 6 draft flow.
- Draft review display: Task 6 backend, Task 8 frontend.
- Approval transaction: Task 6 backend.
- World version update: Task 6 backend tests, Task 9 manual check.
- Character and foreshadow updates: Task 6 backend tests, Task 9 manual check.
- Event log: Task 6 backend tests, Task 9 manual check.
- Local conda Python 3.12 workflow: Task 1, Task 9.
- PostgreSQL schema: Task 2.
- Frontend pages: Task 8.

### Type consistency

- Backend uses `world_version`, `source_world_version`, and `base_world_version` consistently.
- LLM output uses `draft_content`, `context_summary`, `review_hints`, `proposed_character_changes`, and `proposed_foreshadow_changes` consistently.
- Frontend uses `access_token`, `WorldOverview`, and `DraftResponse` names matching backend response shapes.

### Known implementation correction

- In Task 6 Step 4, the first reject endpoint sketch is immediately replaced with the correct reject-only implementation before tests run. The final code must use the corrected version only.
