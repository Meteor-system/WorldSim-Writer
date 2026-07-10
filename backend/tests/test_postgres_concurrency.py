import os
import time
import uuid
from collections.abc import Iterator
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import contextmanager

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, event, func, select, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.orm import Session, sessionmaker

from app.auth.models import User
from app.core.database import Base, import_models
from app.event.models import EventLog
from app.narrative.models import Chapter, ChapterDraft
from app.narrative.service import _locked_world_query, approve_chapter, create_chapter_session
from app.world.models import World

LOCK_TIMEOUT_MS = 4000
STATEMENT_TIMEOUT_MS = 8000
IDLE_IN_TX_TIMEOUT_MS = 8000
THREAD_TIMEOUT_SECONDS = 10
WAIT_TIMEOUT_SECONDS = 5
POLL_INTERVAL_SECONDS = 0.05


def _postgres_test_url() -> str:
    if os.getenv('WORLDSIM_ALLOW_POSTGRES_TESTS') != '1':
        pytest.skip('set WORLDSIM_ALLOW_POSTGRES_TESTS=1 to run PostgreSQL concurrency tests')
    raw_url = os.getenv('WORLDSIM_TEST_POSTGRES_URL')
    if not raw_url:
        pytest.skip('set WORLDSIM_TEST_POSTGRES_URL to run PostgreSQL concurrency tests')
    try:
        url = make_url(raw_url)
    except ArgumentError:
        raise RuntimeError('WORLDSIM_TEST_POSTGRES_URL must be a valid SQLAlchemy URL') from None
    if url.drivername != 'postgresql+psycopg':
        raise RuntimeError('WORLDSIM_TEST_POSTGRES_URL must use the postgresql+psycopg driver')
    database = (url.database or '').lower()
    allowed = database.startswith('test_') or database.endswith('_test') or '_test_' in database
    if not database or not allowed or database in {'postgres', 'worldsim_writer'}:
        raise RuntimeError('WORLDSIM_TEST_POSTGRES_URL must point to an isolated test database')
    return raw_url


def _install_connect_settings(engine, schema_name: str) -> None:
    @event.listens_for(engine, 'connect')
    def _configure_connection(dbapi_connection, _connection_record):
        previous_autocommit = dbapi_connection.autocommit
        dbapi_connection.autocommit = True
        try:
            with dbapi_connection.cursor() as cursor:
                cursor.execute(f'SET search_path TO "{schema_name}", public')
                cursor.execute(f"SET lock_timeout = '{LOCK_TIMEOUT_MS}ms'")
                cursor.execute(f"SET statement_timeout = '{STATEMENT_TIMEOUT_MS}ms'")
                cursor.execute(f"SET idle_in_transaction_session_timeout = '{IDLE_IN_TX_TIMEOUT_MS}ms'")
                cursor.execute(f"SET application_name = '{schema_name}'")
        finally:
            dbapi_connection.autocommit = previous_autocommit


@contextmanager
def postgres_test_harness() -> Iterator[tuple[object, object, sessionmaker[Session], str]]:
    raw_url = _postgres_test_url()
    schema_name = f'test_pg_concurrency_{uuid.uuid4().hex}'
    admin_engine = create_engine(raw_url, future=True, pool_pre_ping=True)
    test_engine = None
    schema_created = False
    try:
        with admin_engine.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA "{schema_name}"'))
        schema_created = True
        import_models()
        test_engine = create_engine(raw_url, future=True, pool_pre_ping=True)
        _install_connect_settings(test_engine, schema_name)
        Base.metadata.create_all(test_engine)
        session_factory = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)
        yield admin_engine, test_engine, session_factory, schema_name
    finally:
        if test_engine is not None:
            test_engine.dispose()
        if schema_created:
            with admin_engine.begin() as conn:
                conn.execute(
                    text(
                        '''
                        SELECT pg_terminate_backend(pid)
                        FROM pg_stat_activity
                        WHERE application_name = :application_name
                          AND pid != pg_backend_pid()
                        '''
                    ),
                    {'application_name': schema_name},
                )
                conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
        admin_engine.dispose()


def _seed_user_and_world(db: Session) -> tuple[User, World]:
    user = User(email=f'user-{uuid.uuid4().hex}@example.test', password_hash='hash')
    db.add(user)
    db.flush()
    world = World(
        owner_id=user.id,
        title='Lock Test World',
        genre_template='fantasy',
        truth_canon='canon',
        truth_canon_version=1,
        world_version=1,
        status='active',
        tone_profile={},
        current_characters=[],
        current_foreshadows=[],
        current_relations=[],
        story_arc=[],
    )
    db.add(world)
    db.commit()
    db.refresh(user)
    db.refresh(world)
    return user, world


def _seed_reviewing_chapter(db: Session, world: World) -> Chapter:
    chapter = Chapter(
        world_id=world.id,
        title='Review Me',
        pov_character_id=None,
        status='reviewing',
        draft_version=1,
        approved_version=None,
        base_world_version=world.world_version,
        approved_content=None,
        chapter_goal='goal',
        outline_beats=[],
        outline_context={},
        critique_report={},
        character_arc_report={},
        execution_context={},
    )
    db.add(chapter)
    db.flush()
    db.add(
        ChapterDraft(
            chapter_id=chapter.id,
            draft_version=1,
            content='draft content',
            context_summary='summary',
            review_hints=[],
            proposed_changes={'characters': [], 'foreshadows': []},
            source_world_version=world.world_version,
            rejection_feedback=None,
            change_type='generated',
            change_summary=None,
            parent_draft_version=None,
            execution_context={},
        )
    )
    db.commit()
    db.refresh(chapter)
    return chapter


def _wait_for_lock_wait(admin_engine, blocked_pid: int, holder_pid: int) -> None:
    deadline = time.monotonic() + WAIT_TIMEOUT_SECONDS
    statement = text(
        '''
        SELECT wait_event_type, pg_blocking_pids(:pid) AS blocker_pids
        FROM pg_stat_activity
        WHERE pid = :pid
        '''
    )
    while time.monotonic() < deadline:
        with admin_engine.connect() as conn:
            row = conn.execute(statement, {'pid': blocked_pid}).one_or_none()
        if row is not None and row.wait_event_type == 'Lock' and holder_pid in row.blocker_pids:
            return
        time.sleep(POLL_INTERVAL_SECONDS)
    raise AssertionError('timed out waiting for blocked session to enter PostgreSQL lock wait')


def _backend_pid(db: Session) -> int:
    return int(db.execute(select(func.pg_backend_pid())).scalar_one())


def _active_chapter_count(db: Session, world_id: int) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(Chapter)
            .where(Chapter.world_id == world_id)
            .where(Chapter.status != 'approved')
        )
        or 0
    )


@pytest.mark.postgres
@pytest.mark.concurrency
def test_create_chapter_session_serializes_on_world_lock() -> None:
    with postgres_test_harness() as (admin_engine, _test_engine, session_factory, _schema_name):
        with session_factory() as seed_db:
            user, world = _seed_user_and_world(seed_db)
            user_id = user.id
            world_id = world.id

        blocked_pid_future: Future[int] = Future()

        def run_blocked_create() -> tuple[str, int, str]:
            db = session_factory()
            try:
                user = db.get(User, user_id)
                assert user is not None
                blocked_pid_future.set_result(_backend_pid(db))
                chapter = create_chapter_session(db, user, world_id, 'blocked goal')
                return ('ok', chapter.id, chapter.status)
            except HTTPException as exc:
                return ('http', exc.status_code, str(exc.detail))
            finally:
                db.rollback()
                db.close()

        with ThreadPoolExecutor(max_workers=1) as executor:
            session_a = session_factory()
            try:
                user_a = session_a.get(User, user_id)
                assert user_a is not None
                assert session_a.scalar(_locked_world_query(world_id)) is not None
                holder_pid = _backend_pid(session_a)
                blocked_future = executor.submit(run_blocked_create)
                blocked_pid = blocked_pid_future.result(timeout=THREAD_TIMEOUT_SECONDS)
                assert holder_pid != blocked_pid
                _wait_for_lock_wait(admin_engine, blocked_pid, holder_pid)
                assert not blocked_future.done()

                chapter_a = create_chapter_session(session_a, user_a, world_id, 'primary goal')
                assert chapter_a.status == 'drafting'
                blocked_result = blocked_future.result(timeout=THREAD_TIMEOUT_SECONDS)
            finally:
                session_a.rollback()
                session_a.close()

        assert blocked_result == ('http', 409, 'ACTIVE_CHAPTER_EXISTS')
        with session_factory() as verify_db:
            assert _active_chapter_count(verify_db, world_id) == 1
            chapters = list(verify_db.scalars(select(Chapter).where(Chapter.world_id == world_id).order_by(Chapter.id)))
            assert len(chapters) == 1
            assert chapters[0].status == 'drafting'


@pytest.mark.postgres
@pytest.mark.concurrency
def test_approve_chapter_serializes_on_world_lock() -> None:
    with postgres_test_harness() as (admin_engine, _test_engine, session_factory, _schema_name):
        with session_factory() as seed_db:
            user, world = _seed_user_and_world(seed_db)
            chapter = _seed_reviewing_chapter(seed_db, world)
            user_id = user.id
            world_id = world.id
            chapter_id = chapter.id

        blocked_pid_future: Future[int] = Future()

        def run_blocked_approve() -> tuple[str, int, str]:
            db = session_factory()
            try:
                user = db.get(User, user_id)
                assert user is not None
                blocked_pid_future.set_result(_backend_pid(db))
                approved = approve_chapter(db, user, chapter_id)
                return ('ok', approved.id, approved.status)
            except HTTPException as exc:
                return ('http', exc.status_code, str(exc.detail))
            finally:
                db.rollback()
                db.close()

        with ThreadPoolExecutor(max_workers=1) as executor:
            session_a = session_factory()
            try:
                user_a = session_a.get(User, user_id)
                assert user_a is not None
                assert session_a.scalar(_locked_world_query(world_id)) is not None
                holder_pid = _backend_pid(session_a)
                blocked_future = executor.submit(run_blocked_approve)
                blocked_pid = blocked_pid_future.result(timeout=THREAD_TIMEOUT_SECONDS)
                assert holder_pid != blocked_pid
                _wait_for_lock_wait(admin_engine, blocked_pid, holder_pid)
                assert not blocked_future.done()

                approved_a = approve_chapter(session_a, user_a, chapter_id)
                assert approved_a.status == 'approved'
                assert approved_a.approved_version == 1
                blocked_result = blocked_future.result(timeout=THREAD_TIMEOUT_SECONDS)
            finally:
                session_a.rollback()
                session_a.close()

        assert blocked_result == ('http', 409, 'ALREADY_APPROVED')
        with session_factory() as verify_db:
            world = verify_db.get(World, world_id)
            chapter = verify_db.get(Chapter, chapter_id)
            assert world is not None
            assert chapter is not None
            assert world.world_version == 2
            assert chapter.status == 'approved'
            assert chapter.approved_version == 1
            event_counts = dict(
                verify_db.execute(
                    select(EventLog.event_type, func.count())
                    .where(EventLog.chapter_id == chapter_id)
                    .group_by(EventLog.event_type)
                ).all()
            )
            assert event_counts.get('chapter_approved') == 1
            assert event_counts.get('world_version_increment') == 1


def test_postgres_concurrency_tests_require_explicit_enable_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv('WORLDSIM_ALLOW_POSTGRES_TESTS', raising=False)
    monkeypatch.delenv('WORLDSIM_TEST_POSTGRES_URL', raising=False)
    with pytest.raises(pytest.skip.Exception, match='WORLDSIM_ALLOW_POSTGRES_TESTS=1'):
        _postgres_test_url()


def test_postgres_concurrency_url_must_be_isolated_test_database(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('WORLDSIM_ALLOW_POSTGRES_TESTS', '1')
    unsafe_url = URL.create(
        'postgresql+psycopg',
        username='user',
        password='secret',
        host='localhost',
        database='worldsim_writer',
    )
    monkeypatch.setenv('WORLDSIM_TEST_POSTGRES_URL', unsafe_url.render_as_string(hide_password=False))
    with pytest.raises(RuntimeError, match='isolated test database') as exc_info:
        _postgres_test_url()
    assert 'secret' not in str(exc_info.value)
    assert 'postgresql' not in str(exc_info.value)
