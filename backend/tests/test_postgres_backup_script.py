import importlib.util
import json
import os
import stat
import subprocess
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


SCRIPT_PATH = Path(__file__).resolve().parents[1] / 'scripts' / 'postgres_backup.py'
SOURCE_URL = 'postgresql+psycopg://source-user:source-password@db.internal:5432/worldsim_source'
RESTORE_URL = 'postgresql+psycopg://restore-user:restore-password@db.internal:5432/worldsim_restore_test'


def load_postgres_backup_module():
    spec = importlib.util.spec_from_file_location('postgres_backup_script', SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def set_database_urls(monkeypatch, source=SOURCE_URL, restore=RESTORE_URL):
    monkeypatch.setenv('DATABASE_URL', source)
    if restore is None:
        monkeypatch.delenv('RESTORE_DATABASE_URL', raising=False)
    else:
        monkeypatch.setenv('RESTORE_DATABASE_URL', restore)


def write_dump(path: Path, content: bytes = b'PGDMP-test-archive') -> Path:
    path.write_bytes(content)
    return path


def test_parse_postgres_url_maps_safe_libpq_query_options():
    module = load_postgres_backup_module()

    target = module._parse_postgres_url(
        'postgresql+psycopg://user:password@db.internal:5544/worldsim?sslmode=require&connect_timeout=7'
    )

    assert target.database == 'worldsim'
    assert target.username == 'user'
    assert target.password == 'password'
    assert target.host == 'db.internal'
    assert target.port == 5544
    assert target.query_environment == (('PGCONNECT_TIMEOUT', '7'), ('PGSSLMODE', 'require'))


@pytest.mark.parametrize(
    'raw_url',
    [
        None,
        'not-a-url',
        'sqlite+pysqlite:///:memory:',
        'postgresql://user:password@db.internal/worldsim',
        'postgresql+psycopg://db.internal/worldsim',
        'postgresql+psycopg://user:password@db.internal/',
        'postgresql+psycopg://user:password@db.internal/worldsim?unknown=value',
    ],
)
def test_parse_postgres_url_rejects_invalid_or_unsupported_configuration(raw_url):
    module = load_postgres_backup_module()

    with pytest.raises(module._OperationError) as exc_info:
        module._parse_postgres_url(raw_url)

    assert exc_info.value.error == 'POSTGRES_CONFIG_INVALID'
    assert exc_info.value.exit_code == module.EXIT_CONFIG_INVALID
    assert 'password' not in str(exc_info.value)


@pytest.mark.parametrize(
    'restore_url',
    [
        None,
        'postgresql+psycopg://user:secret@db.internal/postgres',
        'postgresql+psycopg://user:secret@db.internal/template1',
        'postgresql+psycopg://user:secret@db.internal/worldsim_writer',
        'postgresql+psycopg://user:secret@db.internal/restore_candidate',
        SOURCE_URL,
    ],
)
def test_restore_target_requires_explicit_distinct_isolated_test_database(monkeypatch, restore_url):
    module = load_postgres_backup_module()
    set_database_urls(monkeypatch, restore=restore_url)
    source = module._source_target()

    with pytest.raises(module._OperationError) as exc_info:
        module._restore_target(source)

    assert exc_info.value.exit_code in {module.EXIT_CONFIG_INVALID, module.EXIT_RESTORE_TARGET_UNSAFE}
    assert 'secret' not in str(exc_info.value)
    assert 'postgresql' not in str(exc_info.value)


@pytest.mark.parametrize('database', ['test_restore', 'restore_test', 'restore_test_candidate'])
def test_restore_target_accepts_isolated_test_database_names(monkeypatch, database):
    module = load_postgres_backup_module()
    set_database_urls(
        monkeypatch,
        restore=f'postgresql+psycopg://restore-user:restore-password@db.internal:5432/{database}',
    )

    target = module._restore_target(module._source_target())

    assert target.database == database


def test_connection_environment_uses_short_lived_pgpass_and_excludes_application_secrets(monkeypatch, tmp_path):
    module = load_postgres_backup_module()
    monkeypatch.setenv('SECRET_KEY', 'application-secret')
    monkeypatch.setenv('LLM_API_KEY', 'llm-secret')
    monkeypatch.setenv('PGPASSWORD', 'inherited-pg-secret')
    monkeypatch.setenv('DATABASE_URL', SOURCE_URL)
    monkeypatch.setattr(module.tempfile, 'tempdir', str(tmp_path))
    target = module._source_target()

    with module._connection_environment(target, 'backup') as environment:
        pgpass_path = Path(environment['PGPASSFILE'])
        pgpass_content = pgpass_path.read_text(encoding='utf-8')
        mode = stat.S_IMODE(pgpass_path.stat().st_mode)
        assert pgpass_content == 'db.internal:5432:worldsim_source:source-user:source-password\n'
        assert environment['PGDATABASE'] == 'worldsim_source'
        assert environment['PGUSER'] == 'source-user'
        assert environment['PGAPPNAME'] == 'worldsim-writer:backup'
        assert 'PGPASSWORD' not in environment
        assert 'DATABASE_URL' not in environment
        assert 'RESTORE_DATABASE_URL' not in environment
        assert 'SECRET_KEY' not in environment
        assert 'LLM_API_KEY' not in environment
        if os.name != 'nt':
            assert mode == 0o600

    assert not pgpass_path.exists()
    assert os.environ['PGPASSWORD'] == 'inherited-pg-secret'


def test_connection_environment_escapes_pgpass_fields(monkeypatch, tmp_path):
    module = load_postgres_backup_module()
    monkeypatch.setattr(module.tempfile, 'tempdir', str(tmp_path))
    target = module._parse_postgres_url(
        'postgresql+psycopg://user%3Aname:pass%3Aword%5Ctail@db.internal:5432/test_escape'
    )

    with module._connection_environment(target, 'backup') as environment:
        content = Path(environment['PGPASSFILE']).read_text(encoding='utf-8')

    assert content == 'db.internal:5432:test_escape:user\\:name:pass\\:word\\\\tail\n'


def test_connection_environment_uses_empty_pgpass_when_password_is_absent(monkeypatch, tmp_path):
    module = load_postgres_backup_module()
    monkeypatch.setattr(module.tempfile, 'tempdir', str(tmp_path))
    target = module._parse_postgres_url('postgresql+psycopg://user@db.internal:5432/test_no_password')

    with module._connection_environment(target, 'backup') as environment:
        pgpass_path = Path(environment['PGPASSFILE'])
        assert pgpass_path.read_bytes() == b''

    assert not pgpass_path.exists()


def test_backup_creates_custom_dump_atomically_without_credentials_in_argv_or_child_environment(monkeypatch, tmp_path):
    module = load_postgres_backup_module()
    set_database_urls(monkeypatch)
    monkeypatch.setenv('SECRET_KEY', 'application-secret')
    output_path = tmp_path / 'worldsim.dump'
    captured = {}

    def run_tool(arguments, environment, timeout_seconds, *, stdin=None, stdout=None):
        captured['arguments'] = arguments
        captured['environment'] = dict(environment)
        captured['pgpass_exists_during_run'] = Path(environment['PGPASSFILE']).exists()
        captured['timeout_seconds'] = timeout_seconds
        stdout.write(b'PGDMP-realistic-custom-archive')
        return 0

    monkeypatch.setattr(module, '_run_tool', run_tool)

    exit_code, payload = module.run_backup(output_path, pg_dump_bin='pg_dump-safe', timeout_seconds=90)

    assert exit_code == module.EXIT_OK
    assert payload['status'] == 'backup_created'
    assert payload['path'] == str(output_path)
    assert payload['size_bytes'] == output_path.stat().st_size
    assert len(payload['sha256']) == 64
    assert output_path.read_bytes() == b'PGDMP-realistic-custom-archive'
    assert captured['arguments'] == [
        'pg_dump-safe',
        '--format=custom',
        '--compress=6',
        '--no-owner',
        '--no-privileges',
        '--no-password',
    ]
    assert captured['pgpass_exists_during_run'] is True
    assert captured['timeout_seconds'] == 90
    assert 'source-password' not in repr(captured['arguments'])
    assert SOURCE_URL not in repr(captured['arguments'])
    assert 'DATABASE_URL' not in captured['environment']
    assert 'SECRET_KEY' not in captured['environment']
    assert not Path(captured['environment']['PGPASSFILE']).exists()
    assert list(tmp_path.glob('*.tmp')) == []


def test_backup_failure_cleans_partial_file_and_never_publishes(monkeypatch, tmp_path):
    module = load_postgres_backup_module()
    set_database_urls(monkeypatch)
    output_path = tmp_path / 'worldsim.dump'

    def fail_dump(arguments, environment, timeout_seconds, *, stdin=None, stdout=None):
        stdout.write(b'partial-secret-source-password')
        return 1

    monkeypatch.setattr(module, '_run_tool', fail_dump)

    exit_code, payload = module.run_backup(output_path)

    assert exit_code == module.EXIT_BACKUP_FAILED
    assert payload['error'] == 'BACKUP_COMMAND_FAILED'
    assert not output_path.exists()
    assert list(tmp_path.iterdir()) == []


def test_backup_rejects_zero_byte_dump(monkeypatch, tmp_path):
    module = load_postgres_backup_module()
    set_database_urls(monkeypatch)
    output_path = tmp_path / 'worldsim.dump'
    monkeypatch.setattr(module, '_run_tool', lambda *args, **kwargs: 0)

    exit_code, payload = module.run_backup(output_path)

    assert exit_code == module.EXIT_BACKUP_FAILED
    assert payload['error'] == 'BACKUP_COMMAND_FAILED'
    assert not output_path.exists()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    'error',
    [
        subprocess.TimeoutExpired('pg_dump', 90),
        subprocess.SubprocessError('pg_dump failed'),
    ],
)
def test_backup_maps_subprocess_exceptions_to_stable_failure(monkeypatch, tmp_path, error):
    module = load_postgres_backup_module()
    set_database_urls(monkeypatch)
    output_path = tmp_path / 'worldsim.dump'
    monkeypatch.setattr(module, '_run_tool', lambda *args, **kwargs: (_ for _ in ()).throw(error))

    exit_code, payload = module.run_backup(output_path)

    assert exit_code == module.EXIT_BACKUP_FAILED
    assert payload['error'] == 'BACKUP_COMMAND_FAILED'
    assert not output_path.exists()
    assert list(tmp_path.iterdir()) == []


def test_backup_refuses_existing_output_without_running_pg_dump(monkeypatch, tmp_path):
    module = load_postgres_backup_module()
    set_database_urls(monkeypatch)
    output_path = tmp_path / 'worldsim.dump'
    output_path.write_bytes(b'preserve-me')
    monkeypatch.setattr(
        module,
        '_run_tool',
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('pg_dump must not run')),
    )

    exit_code, payload = module.run_backup(output_path)

    assert exit_code == module.EXIT_OUTPUT_UNSAFE
    assert payload['error'] == 'BACKUP_OUTPUT_UNSAFE'
    assert output_path.read_bytes() == b'preserve-me'


def test_backup_publish_race_does_not_overwrite_competing_file(monkeypatch, tmp_path):
    module = load_postgres_backup_module()
    set_database_urls(monkeypatch)
    output_path = tmp_path / 'worldsim.dump'

    def racing_dump(arguments, environment, timeout_seconds, *, stdin=None, stdout=None):
        stdout.write(b'new-backup')
        output_path.write_bytes(b'competing-backup')
        return 0

    monkeypatch.setattr(module, '_run_tool', racing_dump)

    exit_code, payload = module.run_backup(output_path)

    assert exit_code == module.EXIT_OUTPUT_UNSAFE
    assert payload['error'] == 'BACKUP_OUTPUT_UNSAFE'
    assert output_path.read_bytes() == b'competing-backup'
    assert list(tmp_path.glob('*.tmp')) == []


def test_backup_publish_failure_cleans_temporary_file(monkeypatch, tmp_path):
    module = load_postgres_backup_module()
    set_database_urls(monkeypatch)
    output_path = tmp_path / 'worldsim.dump'

    def successful_dump(arguments, environment, timeout_seconds, *, stdin=None, stdout=None):
        stdout.write(b'PGDMP-valid-backup')
        return 0

    monkeypatch.setattr(module, '_run_tool', successful_dump)
    monkeypatch.setattr(module, '_publish_without_overwrite', lambda *args: (_ for _ in ()).throw(OSError('disk full')))

    exit_code, payload = module.run_backup(output_path)

    assert exit_code == module.EXIT_BACKUP_PUBLISH_FAILED
    assert payload['error'] == 'BACKUP_PUBLISH_FAILED'
    assert not output_path.exists()
    assert list(tmp_path.iterdir()) == []


def test_backup_rejects_symlink_output(monkeypatch, tmp_path):
    module = load_postgres_backup_module()
    set_database_urls(monkeypatch)
    target = tmp_path / 'target.dump'
    link = tmp_path / 'backup.dump'
    target.write_bytes(b'preserve-me')
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip('symlinks unavailable in this environment')

    exit_code, payload = module.run_backup(link)

    assert exit_code == module.EXIT_OUTPUT_UNSAFE
    assert payload['error'] == 'BACKUP_OUTPUT_UNSAFE'
    assert target.read_bytes() == b'preserve-me'


def test_verify_restore_rejects_nonempty_target_before_tool_execution(monkeypatch, tmp_path):
    module = load_postgres_backup_module()
    set_database_urls(monkeypatch)
    backup_path = write_dump(tmp_path / 'worldsim.dump')
    monkeypatch.setattr(module, '_restore_target_is_empty', lambda target: False)
    monkeypatch.setattr(
        module,
        '_run_tool',
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('pg_restore must not run')),
    )

    exit_code, payload = module.run_verify_restore(backup_path)

    assert exit_code == module.EXIT_RESTORE_TARGET_NOT_EMPTY
    assert payload['error'] == 'RESTORE_TARGET_NOT_EMPTY'


def test_verify_restore_reports_unavailable_target_without_leaking_details(monkeypatch, tmp_path, capsys):
    module = load_postgres_backup_module()
    set_database_urls(monkeypatch)
    backup_path = write_dump(tmp_path / 'worldsim.dump')
    secret = 'postgresql://restore-user:restore-password@private-host/test_restore'
    monkeypatch.setattr(module, '_restore_target_is_empty', lambda target: (_ for _ in ()).throw(RuntimeError(secret)))

    exit_code = module.main(['verify-restore', '--backup-file', str(backup_path)])
    output = capsys.readouterr()

    assert exit_code == module.EXIT_RESTORE_TARGET_UNAVAILABLE
    assert json.loads(output.out)['error'] == 'RESTORE_TARGET_UNAVAILABLE'
    assert output.err == 'RESTORE_TARGET_UNAVAILABLE\n'
    assert secret not in output.out
    assert secret not in output.err
    assert 'restore-password' not in output.out
    assert 'restore-password' not in output.err


def test_verify_restore_streams_backup_then_checks_migration_heads(monkeypatch, tmp_path):
    module = load_postgres_backup_module()
    set_database_urls(monkeypatch)
    backup_bytes = b'PGDMP-round-trip-archive'
    backup_path = write_dump(tmp_path / 'worldsim.dump', backup_bytes)
    events = []
    captured = {}
    monkeypatch.setattr(module, '_restore_target_is_empty', lambda target: events.append('empty') or True)

    def run_restore(arguments, environment, timeout_seconds, *, stdin=None, stdout=None):
        events.append('restore')
        captured['arguments'] = arguments
        captured['environment'] = dict(environment)
        captured['file_offset'] = os.lseek(stdin.fileno(), 0, os.SEEK_CUR)
        captured['backup'] = stdin.read()
        captured['pgpass_exists_during_run'] = Path(environment['PGPASSFILE']).exists()
        return 0

    def migration_status(target):
        events.append('migration_status')
        return {
            'current': '0013_add_import_node',
            'head': '0013_add_import_node',
            'up_to_date': True,
            'status': 'up_to_date',
        }

    monkeypatch.setattr(module, '_run_tool', run_restore)
    monkeypatch.setattr(module, '_restored_migration_status', migration_status)

    exit_code, payload = module.run_verify_restore(backup_path, pg_restore_bin='pg_restore-safe', timeout_seconds=120)

    assert exit_code == module.EXIT_OK
    assert payload == {'ok': True, 'status': 'restore_verified'}
    assert events == ['empty', 'restore', 'migration_status']
    assert captured['backup'] == backup_bytes
    assert captured['file_offset'] == 0
    assert captured['arguments'] == [
        'pg_restore-safe',
        '--exit-on-error',
        '--single-transaction',
        '--no-owner',
        '--no-privileges',
        '--no-password',
        '--dbname',
        'worldsim_restore_test',
    ]
    assert captured['pgpass_exists_during_run'] is True
    assert 'restore-password' not in repr(captured['arguments'])
    assert RESTORE_URL not in repr(captured['arguments'])
    assert 'DATABASE_URL' not in captured['environment']
    assert 'RESTORE_DATABASE_URL' not in captured['environment']
    assert not Path(captured['environment']['PGPASSFILE']).exists()


def test_verify_restore_fails_when_pg_restore_fails(monkeypatch, tmp_path):
    module = load_postgres_backup_module()
    set_database_urls(monkeypatch)
    backup_path = write_dump(tmp_path / 'worldsim.dump')
    monkeypatch.setattr(module, '_restore_target_is_empty', lambda target: True)
    monkeypatch.setattr(module, '_run_tool', lambda *args, **kwargs: 1)
    monkeypatch.setattr(
        module,
        '_restored_migration_status',
        lambda target: (_ for _ in ()).throw(AssertionError('migration check must not run')),
    )

    exit_code, payload = module.run_verify_restore(backup_path)

    assert exit_code == module.EXIT_RESTORE_FAILED
    assert payload['error'] == 'RESTORE_COMMAND_FAILED'


@pytest.mark.parametrize(
    'error',
    [
        subprocess.TimeoutExpired('pg_restore', 120),
        subprocess.SubprocessError('pg_restore failed'),
    ],
)
def test_verify_restore_maps_subprocess_exceptions_to_stable_failure(monkeypatch, tmp_path, error):
    module = load_postgres_backup_module()
    set_database_urls(monkeypatch)
    backup_path = write_dump(tmp_path / 'worldsim.dump')
    monkeypatch.setattr(module, '_restore_target_is_empty', lambda target: True)
    monkeypatch.setattr(module, '_run_tool', lambda *args, **kwargs: (_ for _ in ()).throw(error))
    monkeypatch.setattr(
        module,
        '_restored_migration_status',
        lambda target: (_ for _ in ()).throw(AssertionError('migration check must not run')),
    )

    exit_code, payload = module.run_verify_restore(backup_path)

    assert exit_code == module.EXIT_RESTORE_FAILED
    assert payload['error'] == 'RESTORE_COMMAND_FAILED'


def test_verify_restore_fails_when_restored_database_is_behind(monkeypatch, tmp_path):
    module = load_postgres_backup_module()
    set_database_urls(monkeypatch)
    backup_path = write_dump(tmp_path / 'worldsim.dump')
    monkeypatch.setattr(module, '_restore_target_is_empty', lambda target: True)
    monkeypatch.setattr(module, '_run_tool', lambda *args, **kwargs: 0)
    monkeypatch.setattr(
        module,
        '_restored_migration_status',
        lambda target: {
            'current': '0012_add_tags',
            'head': '0013_add_import_node',
            'up_to_date': False,
            'status': 'behind',
        },
    )

    exit_code, payload = module.run_verify_restore(backup_path)

    assert exit_code == module.EXIT_RESTORE_NOT_UP_TO_DATE
    assert payload['error'] == 'RESTORE_NOT_UP_TO_DATE'


def test_verify_restore_fails_when_restored_migration_status_is_unknown(monkeypatch, tmp_path):
    module = load_postgres_backup_module()
    set_database_urls(monkeypatch)
    backup_path = write_dump(tmp_path / 'worldsim.dump')
    monkeypatch.setattr(module, '_restore_target_is_empty', lambda target: True)
    monkeypatch.setattr(module, '_run_tool', lambda *args, **kwargs: 0)
    monkeypatch.setattr(
        module,
        '_restored_migration_status',
        lambda target: {
            'current': None,
            'head': '0013_add_import_node',
            'up_to_date': False,
            'status': 'unknown',
            'error': 'postgresql://user:secret@private-host/test_restore',
        },
    )

    exit_code, payload = module.run_verify_restore(backup_path)

    assert exit_code == module.EXIT_RESTORE_STATUS_UNAVAILABLE
    assert payload['error'] == 'RESTORE_STATUS_UNAVAILABLE'
    assert 'secret' not in json.dumps(payload)


def test_verify_restore_rejects_backup_file_replaced_after_validation(monkeypatch, tmp_path):
    module = load_postgres_backup_module()
    set_database_urls(monkeypatch)
    backup_path = write_dump(tmp_path / 'worldsim.dump')
    original_safe_backup_file = module._safe_backup_file

    def replace_after_validation(value):
        path, path_stat = original_safe_backup_file(value)
        replacement = tmp_path / 'replacement.dump'
        replacement.write_bytes(b'PGDMP-replacement')
        path.unlink()
        replacement.rename(path)
        return path, path_stat

    monkeypatch.setattr(module, '_safe_backup_file', replace_after_validation)
    monkeypatch.setattr(module, '_restore_target_is_empty', lambda target: True)
    monkeypatch.setattr(
        module,
        '_run_tool',
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('pg_restore must not run')),
    )

    exit_code, payload = module.run_verify_restore(backup_path)

    assert exit_code == module.EXIT_BACKUP_FILE_UNSAFE
    assert payload['error'] == 'BACKUP_FILE_UNSAFE'


def test_verify_restore_rejects_symlink_backup_file(monkeypatch, tmp_path):
    module = load_postgres_backup_module()
    set_database_urls(monkeypatch)
    target = write_dump(tmp_path / 'target.dump')
    link = tmp_path / 'backup.dump'
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip('symlinks unavailable in this environment')

    exit_code, payload = module.run_verify_restore(link)

    assert exit_code == module.EXIT_BACKUP_FILE_UNSAFE
    assert payload['error'] == 'BACKUP_FILE_UNSAFE'


def test_verify_restore_rejects_non_custom_archive_before_running_pg_restore(monkeypatch, tmp_path):
    module = load_postgres_backup_module()
    set_database_urls(monkeypatch)
    backup_path = write_dump(tmp_path / 'worldsim.dump', b'not-a-custom-archive')
    monkeypatch.setattr(module, '_restore_target_is_empty', lambda target: True)
    monkeypatch.setattr(
        module,
        '_run_tool',
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError('pg_restore must not run')),
    )

    exit_code, payload = module.run_verify_restore(backup_path)

    assert exit_code == module.EXIT_BACKUP_FILE_UNSAFE
    assert payload['error'] == 'BACKUP_FILE_UNSAFE'


def test_main_uses_stable_failure_output_without_leaking_unexpected_exception(monkeypatch, tmp_path, capsys):
    module = load_postgres_backup_module()
    secret = 'postgresql://user:password@private-host/worldsim'
    monkeypatch.setattr(module, 'run_backup', lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError(secret)))

    exit_code = module.main(['backup', '--output', str(tmp_path / 'worldsim.dump')])
    output = capsys.readouterr()

    assert exit_code == module.EXIT_JOB_FAILED
    assert json.loads(output.out) == {
        'error': 'POSTGRES_BACKUP_JOB_FAILED',
        'ok': False,
        'status': 'failed',
    }
    assert output.err == 'POSTGRES_BACKUP_JOB_FAILED\n'
    assert secret not in output.out
    assert secret not in output.err


def test_main_rejects_invalid_invocation_without_argparse_usage_noise(capsys):
    module = load_postgres_backup_module()

    exit_code = module.main(['backup'])
    output = capsys.readouterr()

    assert exit_code == module.EXIT_CONFIG_INVALID
    assert json.loads(output.out)['error'] == 'INVALID_INVOCATION'
    assert output.err == 'INVALID_INVOCATION\n'
    assert 'usage:' not in output.out
    assert 'usage:' not in output.err


@pytest.mark.postgres
def test_restore_target_empty_check_rejects_custom_schema_on_real_postgres(monkeypatch):
    if os.getenv('WORLDSIM_ALLOW_POSTGRES_TESTS') != '1':
        pytest.skip('set WORLDSIM_ALLOW_POSTGRES_TESTS=1 to run PostgreSQL restore target tests')
    raw_url = os.getenv('WORLDSIM_BACKUP_RESTORE_TEST_URL')
    if not raw_url:
        pytest.skip('set WORLDSIM_BACKUP_RESTORE_TEST_URL to run PostgreSQL restore target tests')
    url = make_url(raw_url)
    database = (url.database or '').lower()
    is_test_database = database.startswith('test_') or database.endswith('_test') or '_test_' in database
    if url.drivername != 'postgresql+psycopg' or not is_test_database or database in {'postgres', 'worldsim_writer'}:
        raise RuntimeError('WORLDSIM_BACKUP_RESTORE_TEST_URL must point to an isolated PostgreSQL test database')

    module = load_postgres_backup_module()
    target = module._parse_postgres_url(raw_url)
    engine = create_engine(raw_url)
    schema_name = f'test_restore_schema_{uuid.uuid4().hex}'
    try:
        assert module._restore_target_is_empty(target) is True
        with engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema_name}"'))
        assert module._restore_target_is_empty(target) is False
    finally:
        with engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
        engine.dispose()

    assert module._restore_target_is_empty(target) is True


def test_main_does_not_swallow_keyboard_interrupt(monkeypatch, tmp_path, capsys):
    module = load_postgres_backup_module()
    monkeypatch.setattr(module, 'run_backup', lambda *args, **kwargs: (_ for _ in ()).throw(KeyboardInterrupt))

    with pytest.raises(KeyboardInterrupt):
        module.main(['backup', '--output', str(tmp_path / 'worldsim.dump')])

    output = capsys.readouterr()
    assert output.out == ''
    assert output.err == ''
