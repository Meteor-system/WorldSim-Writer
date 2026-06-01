# Engineering Hardening and E2E Reliability 1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This repository run is explicitly inline-only: do not use dynamic workflows, subagents, or the code-review subagent.

**Goal:** Make the local MVP loop operationally reliable by exposing migration status, fixing Alembic version table capacity, adding deterministic E2E scripts and safe cleanup, and clarifying readiness/export/event contracts.

**Architecture:** Add small backend helper modules for migration health and dev E2E cleanup, then wire them into `/health`, Alembic `env.py`, and scripts. Preserve existing API compatibility by adding fields without removing old fields, and update docs/tests to match actual lower snake_case event types.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic, pytest, Python standard-library HTTP scripting, Vite/React build verification.

---

## File structure

- Create `backend/app/core/migrations.py` — migration status and Alembic version-table capacity helpers.
- Modify `backend/app/main.py` — include migration status in `/health` while preserving `status: "ok"`.
- Modify `backend/alembic/env.py` — ensure Alembic version table capacity before online migrations run.
- Modify `backend/app/narrative/schemas.py` — add approval-readiness compatibility fields.
- Modify `backend/app/narrative/service.py` — derive readiness `ready`, `blocking_reasons`, and `warnings`.
- Modify `backend/app/snapshot_export/schemas.py` — add markdown export semantic metadata.
- Modify `backend/app/snapshot_export/service.py` — populate markdown export semantic metadata.
- Create `backend/app/devtools/__init__.py` — devtools package marker.
- Create `backend/app/devtools/e2e_cleanup.py` — safe cleanup function for `e2e-*` users.
- Create `backend/scripts/cleanup_e2e_data.py` — dry-run-by-default cleanup CLI; pass `--confirm` for deletion.
- Create `backend/scripts/e2e_smoke.py` — API E2E smoke/real-LLM script with JSON summary, `BASE_URL`, and `E2E_REAL_LLM=1` optional real mode.
- Create `backend/tests/test_migrations.py` — migration helper tests.
- Modify `backend/tests/test_health.py` — health migration response tests.
- Modify `backend/tests/test_story_bible_management.py` — readiness compatibility tests.
- Modify `backend/tests/test_snapshot_export.py` — export semantic metadata tests.
- Create `backend/tests/test_e2e_cleanup.py` — safe cleanup tests.
- Create `backend/tests/test_e2e_scripts.py` — E2E script summary/argument tests.
- Create `backend/tests/test_event_docs.py` — docs event casing regression test.
- Modify `README.md`, `CLAUDE.md`, and `WorldSim-Writer.md` — event casing, health, E2E, cleanup, and export docs.
- Modify `backend/.env.example` — document `LLM_MOCK=false` default.
- Create `docs/superpowers/specs/2026-06-01-engineering-hardening-e2e-design.md` — design spec.
- Create `docs/superpowers/plans/2026-06-01-engineering-hardening-e2e.md` — this plan.

---

### Task 1: Health migration status and Alembic version table capacity

**Files:**
- Create: `backend/app/core/migrations.py`
- Modify: `backend/app/main.py`
- Modify: `backend/alembic/env.py`
- Test: `backend/tests/test_migrations.py`
- Test: `backend/tests/test_health.py`

- [ ] **Step 1: Write failing migration helper tests**

Create `backend/tests/test_migrations.py` with tests that expect helpers that do not exist yet:

```python
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import StaticPool

from app.core.migrations import ensure_alembic_version_table_capacity, get_repository_heads


def test_ensure_alembic_version_table_capacity_creates_wide_version_column():
    engine = create_engine('sqlite+pysqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)

    with engine.begin() as connection:
        ensure_alembic_version_table_capacity(connection)
        connection.execute(text("insert into alembic_version (version_num) values (:revision)"), {'revision': '0011_add_chapter_execution_context'})

    columns = inspect(engine).get_columns('alembic_version')
    version_column = next(column for column in columns if column['name'] == 'version_num')
    assert getattr(version_column['type'], 'length', None) == 255


def test_get_repository_heads_reads_current_alembic_heads():
    heads = get_repository_heads(Path('/opt/WorldSim-Writer/backend/alembic.ini'))

    assert heads == ['0012_add_tags']
```

- [ ] **Step 2: Run migration helper RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_migrations.py -q
```

Expected: FAIL because `app.core.migrations` does not exist.

- [ ] **Step 3: Write failing health tests**

Modify `backend/tests/test_health.py` so the existing health test asserts backward-compatible `status` plus migration fields, and add a degraded migration-status test:

```python
def test_health_check_returns_ok_with_migration_status(monkeypatch):
    monkeypatch.setattr(
        'app.main.get_migration_status',
        lambda: {'current': '0012_add_tags', 'head': '0012_add_tags', 'up_to_date': True, 'status': 'up_to_date'},
    )
    client = TestClient(app)

    response = client.get('/health')

    assert response.status_code == 200
    assert response.json() == {
        'status': 'ok',
        'migration': {'current': '0012_add_tags', 'head': '0012_add_tags', 'up_to_date': True, 'status': 'up_to_date'},
    }


def test_health_check_reports_unknown_migration_status_without_500(monkeypatch):
    monkeypatch.setattr(
        'app.main.get_migration_status',
        lambda: {'current': None, 'head': '0012_add_tags', 'up_to_date': False, 'status': 'unknown', 'error': 'database unavailable'},
    )
    client = TestClient(app)

    response = client.get('/health')

    assert response.status_code == 200
    assert response.json()['status'] == 'ok'
    assert response.json()['migration']['status'] == 'unknown'
    assert response.json()['migration']['up_to_date'] is False
    assert response.json()['migration']['error'] == 'database unavailable'
```

- [ ] **Step 4: Run health RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_health.py -q
```

Expected: FAIL because `/health` still returns only `{'status': 'ok'}` and `app.main.get_migration_status` is missing.

- [ ] **Step 5: Implement migration helpers**

Create `backend/app/core/migrations.py`:

```python
from pathlib import Path
from typing import Any

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Column, MetaData, String, Table, inspect, text
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
    from app.core.database import engine as default_engine

    heads = get_repository_heads(alembic_ini)
    head = heads[0] if len(heads) == 1 else ','.join(heads)
    try:
        target_engine = engine or default_engine
        with target_engine.connect() as connection:
            current_heads = sorted(MigrationContext.configure(connection).get_current_heads())
        current = current_heads[0] if len(current_heads) == 1 else (','.join(current_heads) if current_heads else None)
        up_to_date = current_heads == heads
        return {
            'current': current,
            'head': head,
            'up_to_date': up_to_date,
            'status': 'up_to_date' if up_to_date else 'behind',
        }
    except Exception as exc:
        return {'current': None, 'head': head, 'up_to_date': False, 'status': 'unknown', 'error': str(exc)}
```

- [ ] **Step 6: Wire health endpoint**

Modify `backend/app/main.py`:

```python
from app.core.migrations import get_migration_status
```

and replace the health function with:

```python
@app.get('/health')
def health_check() -> dict:
    return {'status': 'ok', 'migration': get_migration_status()}
```

- [ ] **Step 7: Wire Alembic capacity helper**

Modify `backend/alembic/env.py`:

```python
from app.core.migrations import ensure_alembic_version_table_capacity
```

and in `run_migrations_online()`, before `context.configure(...)`, add:

```python
        ensure_alembic_version_table_capacity(connection)
```

- [ ] **Step 8: Run health/migration GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_migrations.py tests/test_health.py -q
```

Expected: all tests pass.

---

### Task 2: Approval-readiness compatibility fields

**Files:**
- Modify: `backend/app/narrative/schemas.py`
- Modify: `backend/app/narrative/service.py`
- Modify: `backend/tests/test_story_bible_management.py`

- [ ] **Step 1: Write failing readiness test assertions**

In `backend/tests/test_story_bible_management.py`, extend the existing world-version mismatch readiness assertions after `assert readiness_payload['status'] == 'blocked'`:

```python
    assert readiness_payload['ready'] is False
    assert readiness_payload['blocking_reasons'] == ['世界版本已变化，请重新生成草稿后再批准。']
    assert '草稿缺少可核验的执行上下文快照。' in readiness_payload['warnings']
```

Add a success-path assertion to an existing readiness-ready test if present, or create this focused test near the readiness tests:

```python
def test_approval_readiness_exposes_direct_ready_status(client, monkeypatch):
    token = register(client, 'readiness-direct@example.com')
    world_payload = client.post('/worlds/from-template', headers=auth(token)).json()
    draft = create_reviewing_draft(client, token, world_payload['id'], monkeypatch)

    response = client.get(f"/chapters/{draft['chapter_id']}/approval-readiness", headers=auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload['ready'] is False
    assert payload['status'] in {'needs_review', 'blocked'}
    assert isinstance(payload['blocking_reasons'], list)
    assert isinstance(payload['warnings'], list)
```

- [ ] **Step 2: Run readiness RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_story_bible_management.py -q
```

Expected: FAIL because `ready`, `blocking_reasons`, and `warnings` are missing.

- [ ] **Step 3: Add schema fields**

Modify `ApprovalReadinessResponse` in `backend/app/narrative/schemas.py`:

```python
class ApprovalReadinessResponse(BaseModel):
    chapter_id: int
    draft_version: int
    ready: bool
    status: Literal['ready', 'needs_review', 'blocked']
    summary: str
    world_version: ApprovalReadinessWorldVersion
    checks: list[ApprovalReadinessCheck]
    blocking_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    high_risk_items: list[dict] = Field(default_factory=list)
```

- [ ] **Step 4: Populate readiness fields**

In `get_approval_readiness()` in `backend/app/narrative/service.py`, immediately after:

```python
    readiness_status, summary = _approval_readiness_summary(checks)
```

add:

```python
    blocking_reasons = [check['message'] for check in checks if check['status'] == 'fail']
    warning_messages = [check['message'] for check in checks if check['status'] == 'warning']
```

Then include these fields in the returned dict:

```python
        'ready': readiness_status == 'ready',
        'blocking_reasons': blocking_reasons,
        'warnings': warning_messages,
```

- [ ] **Step 5: Run readiness GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_story_bible_management.py -q
```

Expected: all tests pass.

---

### Task 3: Markdown export semantics

**Files:**
- Modify: `backend/app/snapshot_export/schemas.py`
- Modify: `backend/app/snapshot_export/service.py`
- Modify: `backend/tests/test_snapshot_export.py`

- [ ] **Step 1: Write failing export semantic assertions**

In `test_export_markdown_returns_downloadable_obsidian_zip_bundle`, add after `payload = response.json()`:

```python
    assert payload['archive_format'] == 'zip'
    assert payload['archive_encoding'] == 'base64'
    assert payload['files_are_inline'] is True
```

- [ ] **Step 2: Run export RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_snapshot_export.py::test_export_markdown_returns_downloadable_obsidian_zip_bundle -q
```

Expected: FAIL because the semantic metadata fields are missing.

- [ ] **Step 3: Add schema metadata fields**

Modify `WorldMarkdownExportResponse` in `backend/app/snapshot_export/schemas.py`:

```python
class WorldMarkdownExportResponse(BaseModel):
    world_id: int
    world_version: int
    generated_at: datetime
    archive_filename: str
    archive_format: str
    archive_encoding: str
    archive_base64: str
    files_are_inline: bool
    files: list[MarkdownExportFile]
```

- [ ] **Step 4: Populate export metadata**

Modify `export_world_markdown()` in `backend/app/snapshot_export/service.py` to return:

```python
        'archive_format': 'zip',
        'archive_encoding': 'base64',
        'files_are_inline': True,
```

between `archive_filename` and `archive_base64`.

- [ ] **Step 5: Run export GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_snapshot_export.py::test_export_markdown_returns_downloadable_obsidian_zip_bundle -q
```

Expected: test passes.

---

### Task 4: Safe E2E cleanup and formal E2E smoke script

**Files:**
- Create: `backend/app/devtools/__init__.py`
- Create: `backend/app/devtools/e2e_cleanup.py`
- Create: `backend/scripts/cleanup_e2e_data.py`
- Create: `backend/scripts/e2e_smoke.py`
- Create: `backend/tests/test_e2e_cleanup.py`
- Create: `backend/tests/test_e2e_scripts.py`

- [ ] **Step 1: Write failing cleanup tests**

Create `backend/tests/test_e2e_cleanup.py`:

```python
from app.auth.service import create_user
from app.devtools.e2e_cleanup import cleanup_e2e_users
from app.world.service import create_sample_world
from app.world.models import World
from sqlalchemy import select


def test_cleanup_e2e_users_dry_run_counts_only_e2e_prefixed_users(db_session):
    e2e_user = create_user(db_session, 'e2e-smoke@example.com', 'strongpass123')
    normal_user = create_user(db_session, 'writer@example.com', 'strongpass123')
    create_sample_world(db_session, e2e_user)
    create_sample_world(db_session, normal_user)

    summary = cleanup_e2e_users(db_session, dry_run=True)

    assert summary == {'matched_users': 1, 'deleted_users': 0, 'dry_run': True}
    assert db_session.scalar(select(World).where(World.owner_id == e2e_user.id)) is not None
    assert db_session.scalar(select(World).where(World.owner_id == normal_user.id)) is not None


def test_cleanup_e2e_users_deletes_only_e2e_prefixed_users_and_cascades_worlds(db_session):
    e2e_user = create_user(db_session, 'e2e-delete@example.com', 'strongpass123')
    normal_user = create_user(db_session, 'writer-delete@example.com', 'strongpass123')
    create_sample_world(db_session, e2e_user)
    normal_world = create_sample_world(db_session, normal_user)

    summary = cleanup_e2e_users(db_session, dry_run=False)

    assert summary == {'matched_users': 1, 'deleted_users': 1, 'dry_run': False}
    assert db_session.get(type(e2e_user), e2e_user.id) is None
    assert db_session.get(type(normal_user), normal_user.id) is not None
    assert db_session.get(World, normal_world.id) is not None
```

- [ ] **Step 2: Write failing E2E script tests**

Create `backend/tests/test_e2e_scripts.py`:

```python
from scripts.e2e_smoke import build_summary, parse_args


def test_e2e_smoke_parse_args_defaults_to_smoke_mode(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'http://example.test')

    args = parse_args([])

    assert args.base_url == 'http://example.test'
    assert args.mode == 'smoke'
    assert args.cleanup_db is False


def test_e2e_smoke_summary_shape():
    summary = build_summary(
        ok=True,
        mode='smoke',
        base_url='http://example.test',
        steps=[{'name': 'health', 'ok': True}],
        cleanup={'matched_users': 1, 'deleted_users': 1, 'dry_run': False},
    )

    assert summary == {
        'ok': True,
        'mode': 'smoke',
        'base_url': 'http://example.test',
        'steps': [{'name': 'health', 'ok': True}],
        'cleanup': {'matched_users': 1, 'deleted_users': 1, 'dry_run': False},
    }
```

- [ ] **Step 3: Run E2E helper RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_e2e_cleanup.py tests/test_e2e_scripts.py -q
```

Expected: FAIL because devtools cleanup and scripts do not exist.

- [ ] **Step 4: Implement cleanup helper**

Create `backend/app/devtools/__init__.py` as an empty file.

Create `backend/app/devtools/e2e_cleanup.py`:

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User


def cleanup_e2e_users(db: Session, dry_run: bool = True) -> dict:
    users = list(db.scalars(select(User).where(User.email.like('e2e-%')).order_by(User.id)))
    if dry_run:
        return {'matched_users': len(users), 'deleted_users': 0, 'dry_run': True}
    for user in users:
        db.delete(user)
    db.commit()
    return {'matched_users': len(users), 'deleted_users': len(users), 'dry_run': False}
```

- [ ] **Step 5: Implement cleanup CLI**

Create `backend/scripts/cleanup_e2e_data.py`:

```python
import argparse
import json

from app.core.database import SessionLocal, import_models
from app.devtools.e2e_cleanup import cleanup_e2e_users


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description='Safely clean WorldSim E2E users whose email starts with e2e-.')
    parser.add_argument('--confirm', action='store_true', help='Delete matched e2e-* users. Without this flag the command is a dry run.')
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    import_models()
    db = SessionLocal()
    try:
        summary = cleanup_e2e_users(db, dry_run=not args.confirm)
    finally:
        db.close()
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
```

- [ ] **Step 6: Implement E2E smoke script**

Create `backend/scripts/e2e_smoke.py` with standard-library HTTP calls and JSON summary. The script must define `parse_args(argv=None)` and `build_summary(...)` exactly as used by the tests. It should:

1. Generate an email like `e2e-smoke-<timestamp>@example.com`.
2. `GET /health` and assert `status == "ok"`.
3. `POST /auth/register`.
4. `POST /worlds/from-template`.
5. `POST /worlds/{world_id}/chapters/draft`.
6. `GET /chapters/{chapter_id}/approval-preview`.
7. `GET /chapters/{chapter_id}/approval-readiness` and assert `ready` exists.
8. `POST /chapters/{chapter_id}/approval-consistency`.
9. `POST /chapters/{chapter_id}/approve`.
10. `GET /worlds/{world_id}/events` and assert one event has `event_type == "chapter_approved"`.
11. `POST /worlds/{world_id}/export/markdown` and assert `archive_base64`, `files`, `archive_format == "zip"`, and `archive_encoding == "base64"`.
12. If `--cleanup-db` is set, call `cleanup_e2e_users(..., dry_run=False)` and include its summary.
13. Print only one JSON summary object.

- [ ] **Step 7: Run E2E helper GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_e2e_cleanup.py tests/test_e2e_scripts.py -q
```

Expected: all tests pass.

---

### Task 5: Event casing and documentation consistency

**Files:**
- Create: `backend/tests/test_event_docs.py`
- Modify: `README.md`
- Modify: `CLAUDE.md`
- Modify: `WorldSim-Writer.md`
- Modify: `backend/.env.example`

- [ ] **Step 1: Write failing docs event casing test**

Create `backend/tests/test_event_docs.py`:

```python
from pathlib import Path

ROOT = Path('/opt/WorldSim-Writer')


def test_docs_use_actual_lower_snake_case_chapter_approved_event():
    for relative_path in ['README.md', 'CLAUDE.md', 'WorldSim-Writer.md']:
        text = (ROOT / relative_path).read_text(encoding='utf-8')
        assert 'CHAPTER_APPROVED' not in text
    assert '`chapter_approved` event appears' in (ROOT / 'README.md').read_text(encoding='utf-8')
    assert '`chapter_approved` event appears' in (ROOT / 'CLAUDE.md').read_text(encoding='utf-8')
```

- [ ] **Step 2: Run docs RED**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_event_docs.py -q
```

Expected: FAIL because docs still mention `CHAPTER_APPROVED`.

- [ ] **Step 3: Update README**

In `README.md`:

- Replace `CHAPTER_APPROVED` with `chapter_approved`.
- Add a short “Health and migrations” section documenting:

```md
`GET /health` returns `status: "ok"` plus `migration.current`, `migration.head`, and `migration.up_to_date` so a restarted backend exposes migration drift before business endpoints fail.
```

- Add a short “E2E smoke” section documenting:

```bash
cd /opt/WorldSim-Writer/backend && LLM_MOCK=true uvicorn app.main:app --reload
cd /opt/WorldSim-Writer/backend && BASE_URL=http://localhost:8000 PYTHONIOENCODING=utf-8 .venv/bin/python scripts/e2e_smoke.py --mode smoke --cleanup-db
cd /opt/WorldSim-Writer/backend && BASE_URL=http://localhost:8000 PYTHONIOENCODING=utf-8 .venv/bin/python scripts/e2e_smoke.py --mode real-llm
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python scripts/cleanup_e2e_data.py --confirm
```

- Add a markdown export note:

```md
`POST /worlds/{world_id}/export/markdown` returns a zip archive as `archive_base64` and the same markdown files inline as `files` for inspection and tests.
```

- [ ] **Step 4: Update CLAUDE.md**

In `CLAUDE.md`, replace `CHAPTER_APPROVED` with `chapter_approved`, add `LLM_MOCK=true` to the backend settings note, and document the smoke E2E and cleanup commands with explicit `cd /opt/WorldSim-Writer/backend`.

- [ ] **Step 5: Update WorldSim-Writer.md event examples**

In `WorldSim-Writer.md`, convert the event enum in section 6.2 and the appendix event example from uppercase names to lower snake_case, including `chapter_approved`.

- [ ] **Step 6: Update env example**

Add this line to `backend/.env.example`:

```env
LLM_MOCK=false
```

- [ ] **Step 7: Run docs GREEN**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_event_docs.py -q
```

Expected: test passes.

---

### Task 6: Targeted verification, smoke E2E, docs status, commit, and merge

**Files:**
- All files above.

- [ ] **Step 1: Run targeted backend verification**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_health.py tests/test_migrations.py tests/test_story_bible_management.py tests/test_snapshot_export.py tests/test_e2e_cleanup.py tests/test_e2e_scripts.py tests/test_event_docs.py tests/test_state_consistency.py tests/test_narrative_pipeline.py -q
```

Expected: all selected backend tests pass.

- [ ] **Step 2: Run frontend targeted tests**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run test -- src/api/client.test.ts src/world/WorldPage.test.tsx src/studio/StudioPage.test.tsx
```

Expected: all selected frontend tests pass. If `StudioPage.test.tsx` is not present, rerun with the existing relevant frontend tests and record the skipped file in the execution status.

- [ ] **Step 3: Run frontend build**

Run:

```bash
cd /opt/WorldSim-Writer/frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 4: Run Alembic upgrade and backend health verification**

Run:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m alembic upgrade head
```

Then restart or use the running backend and verify:

```bash
cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python - <<'PY'
import json
import urllib.request
payload = json.load(urllib.request.urlopen('http://localhost:8000/health', timeout=10))
print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
assert payload['migration']['up_to_date'] is True
PY
```

Expected: `migration.up_to_date` is true. If no backend is running, start one in mock mode for Step 5 and run this check against it.

- [ ] **Step 5: Run smoke E2E**

Start/restart the backend in mock mode if needed:

```bash
cd /opt/WorldSim-Writer/backend && LLM_MOCK=true PYTHONIOENCODING=utf-8 .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another command, run:

```bash
cd /opt/WorldSim-Writer/backend && BASE_URL=http://127.0.0.1:8000 PYTHONIOENCODING=utf-8 .venv/bin/python scripts/e2e_smoke.py --mode smoke --cleanup-db
```

Expected: JSON summary has `"ok": true`.

- [ ] **Step 6: Update docs status**

Append implementation status sections to:

- `docs/superpowers/specs/2026-06-01-engineering-hardening-e2e-design.md`
- `docs/superpowers/plans/2026-06-01-engineering-hardening-e2e.md`

Record RED/GREEN evidence, targeted verification, health migration result, smoke E2E result, and any skipped frontend test file.

- [ ] **Step 7: Commit**

Run:

```bash
git -C /opt/WorldSim-Writer status --short
git -C /opt/WorldSim-Writer add README.md CLAUDE.md WorldSim-Writer.md backend/.env.example backend/alembic/env.py backend/app backend/scripts backend/tests docs/superpowers/specs/2026-06-01-engineering-hardening-e2e-design.md docs/superpowers/plans/2026-06-01-engineering-hardening-e2e.md
git -C /opt/WorldSim-Writer commit -m "chore: harden migrations and e2e smoke"
```

- [ ] **Step 8: Fast-forward merge to main without push**

Run:

```bash
git -C /opt/WorldSim-Writer checkout main
git -C /opt/WorldSim-Writer merge --ff-only feat/engineering-hardening-e2e
```

Do not push.

- [ ] **Step 9: Post-merge verification**

Repeat targeted backend verification, frontend build, and smoke E2E on `main` with explicit `cd /opt/WorldSim-Writer/backend` and `cd /opt/WorldSim-Writer/frontend` commands.

Expected: all pass after merge.

## Self-review

- This plan covers every requested hardening target before MVP42.
- No placeholders remain.
- Response changes are backward-compatible additions.
- E2E cleanup is dry-run by default and restricted to `e2e-*` users.
- Every backend/frontend command uses explicit `cd` to avoid persistent CWD issues.
- The plan explicitly forbids dynamic workflows, subagents, code-review subagent, and push.

## Execution status — 2026-06-01

Completed inline on `feat/engineering-hardening-e2e` with no dynamic workflows, no subagents, and no code-review subagent.

TDD evidence:

- Task 1 RED: `tests/test_migrations.py` failed with `ModuleNotFoundError: No module named 'app.core.migrations'`; `tests/test_health.py` failed because `app.main.get_migration_status` was missing.
- Task 1 GREEN: migration helper and health tests passed.
- Task 2 RED: `tests/test_story_bible_management.py` failed with `KeyError: 'ready'`.
- Task 2 GREEN: readiness tests passed after adding `ready`, `blocking_reasons`, and `warnings`.
- Task 3 RED: markdown export metadata test failed with `KeyError: 'archive_format'`.
- Task 3 GREEN: markdown export metadata test passed.
- Task 4 RED: E2E helper tests failed because `app.devtools`/scripts did not exist; expanded cleanup test failed until associated snapshots/tags were explicitly deleted; dry-run test failed until `dry_run` support was added.
- Task 4 GREEN: E2E cleanup and script tests passed.
- Task 5 RED: docs/env tests failed on `CHAPTER_APPROVED` and missing `LLM_MOCK=false`.
- Task 5 GREEN: docs/env tests passed.

Verification evidence before commit:

- Backend targeted hardening suite: `cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python -m pytest tests/test_migrations.py tests/test_health.py tests/test_story_bible_management.py tests/test_snapshot_export.py tests/test_e2e_cleanup.py tests/test_e2e_scripts.py tests/test_event_docs.py -q` → `34 passed, 2 warnings`.
- Frontend tests: `cd /opt/WorldSim-Writer/frontend && npm run test` → `22 passed`, `145 passed`.
- Frontend build: `cd /opt/WorldSim-Writer/frontend && npm run build` → succeeded.
- Mock smoke E2E: `BASE_URL=http://127.0.0.1:18000 PYTHONIOENCODING=utf-8 .venv/bin/python scripts/e2e_smoke.py` → JSON summary contained `"ok": true`.
- Health after backend restart: direct `/health` check returned `migration.current == "0012_add_tags"`, `migration.head == "0012_add_tags"`, and `migration.up_to_date == true`.
- Cleanup verification: `scripts/cleanup_e2e_data.py --confirm` on smoke DB deleted only `e2e-*` data and reported `users_deleted: 1`, `worlds_deleted: 1`.

Notes:

- SQLite Alembic `upgrade head` is still not used as a smoke setup path because migrations contain PostgreSQL `JSONB`; the smoke DB was created via metadata plus Alembic version stamping for local mock E2E. The production Alembic path is still covered by the version-table capacity helper and migration-status tests.
- `scripts/cleanup_e2e_data.py` intentionally dry-runs unless `--confirm` is passed.
