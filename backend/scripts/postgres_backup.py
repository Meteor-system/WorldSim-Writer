#!/usr/bin/env python
import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterator

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.migrations import ALEMBIC_INI, get_migration_status

EXIT_OK = 0
EXIT_CONFIG_INVALID = 20
EXIT_OUTPUT_UNSAFE = 21
EXIT_BACKUP_FAILED = 22
EXIT_BACKUP_PUBLISH_FAILED = 23
EXIT_BACKUP_FILE_UNSAFE = 24
EXIT_RESTORE_TARGET_UNSAFE = 25
EXIT_RESTORE_TARGET_UNAVAILABLE = 26
EXIT_RESTORE_TARGET_NOT_EMPTY = 27
EXIT_RESTORE_FAILED = 28
EXIT_RESTORE_STATUS_UNAVAILABLE = 29
EXIT_RESTORE_NOT_UP_TO_DATE = 30
EXIT_JOB_FAILED = 31

_LIBPQ_QUERY_ENV = {
    'channel_binding': 'PGCHANNELBINDING',
    'connect_timeout': 'PGCONNECT_TIMEOUT',
    'gssencmode': 'PGGSSENCMODE',
    'options': 'PGOPTIONS',
    'sslcert': 'PGSSLCERT',
    'sslcrl': 'PGSSLCRL',
    'sslkey': 'PGSSLKEY',
    'sslmode': 'PGSSLMODE',
    'sslrootcert': 'PGSSLROOTCERT',
    'target_session_attrs': 'PGTARGETSESSIONATTRS',
}
_CHILD_ENV_KEYS = {
    'COMSPEC',
    'HOME',
    'LANG',
    'LC_ALL',
    'LD_LIBRARY_PATH',
    'PATH',
    'PATHEXT',
    'SYSTEMROOT',
    'TEMP',
    'TMP',
    'TMPDIR',
    'USERPROFILE',
    'WINDIR',
}
_RESTORE_HAS_USER_OBJECTS_SQL = text(
    '''
    SELECT
        EXISTS (
            SELECT 1
            FROM pg_catalog.pg_namespace
            WHERE nspname NOT IN ('public', 'pg_catalog', 'information_schema')
              AND nspname NOT LIKE 'pg_toast%'
              AND nspname NOT LIKE 'pg_temp_%'
        )
        OR EXISTS (
            SELECT 1
            FROM pg_catalog.pg_class AS c
            JOIN pg_catalog.pg_namespace AS n ON n.oid = c.relnamespace
            WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
              AND n.nspname NOT LIKE 'pg_toast%'
              AND c.relkind IN ('r', 'p', 'v', 'm', 'S', 'f')
        )
        OR EXISTS (
            SELECT 1
            FROM pg_catalog.pg_proc AS p
            JOIN pg_catalog.pg_namespace AS n ON n.oid = p.pronamespace
            WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
              AND n.nspname NOT LIKE 'pg_toast%'
        )
        OR EXISTS (
            SELECT 1
            FROM pg_catalog.pg_type AS t
            JOIN pg_catalog.pg_namespace AS n ON n.oid = t.typnamespace
            WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
              AND n.nspname NOT LIKE 'pg_toast%'
        )
        OR EXISTS (SELECT 1 FROM pg_catalog.pg_extension WHERE extname <> 'plpgsql')
        OR EXISTS (SELECT 1 FROM pg_catalog.pg_language WHERE lanname NOT IN ('internal', 'c', 'sql', 'plpgsql'))
        OR EXISTS (SELECT 1 FROM pg_catalog.pg_event_trigger)
        OR EXISTS (SELECT 1 FROM pg_catalog.pg_foreign_data_wrapper)
        OR EXISTS (SELECT 1 FROM pg_catalog.pg_foreign_server)
        OR EXISTS (SELECT 1 FROM pg_catalog.pg_publication)
        OR EXISTS (SELECT 1 FROM pg_catalog.pg_largeobject_metadata)
        OR EXISTS (SELECT 1 FROM pg_catalog.pg_default_acl)
        OR EXISTS (
            SELECT 1
            FROM pg_catalog.pg_collation AS c
            JOIN pg_catalog.pg_namespace AS n ON n.oid = c.collnamespace
            WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
        )
        OR EXISTS (
            SELECT 1
            FROM pg_catalog.pg_conversion AS c
            JOIN pg_catalog.pg_namespace AS n ON n.oid = c.connamespace
            WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
        )
        OR EXISTS (
            SELECT 1
            FROM pg_catalog.pg_operator AS o
            JOIN pg_catalog.pg_namespace AS n ON n.oid = o.oprnamespace
            WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
        )
        OR EXISTS (
            SELECT 1
            FROM pg_catalog.pg_opclass AS o
            JOIN pg_catalog.pg_namespace AS n ON n.oid = o.opcnamespace
            WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
        )
        OR EXISTS (
            SELECT 1
            FROM pg_catalog.pg_opfamily AS o
            JOIN pg_catalog.pg_namespace AS n ON n.oid = o.opfnamespace
            WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
        )
        OR EXISTS (
            SELECT 1
            FROM pg_catalog.pg_ts_config AS t
            JOIN pg_catalog.pg_namespace AS n ON n.oid = t.cfgnamespace
            WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
        )
        OR EXISTS (
            SELECT 1
            FROM pg_catalog.pg_ts_dict AS t
            JOIN pg_catalog.pg_namespace AS n ON n.oid = t.dictnamespace
            WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
        )
        OR EXISTS (
            SELECT 1
            FROM pg_catalog.pg_ts_parser AS t
            JOIN pg_catalog.pg_namespace AS n ON n.oid = t.prsnamespace
            WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
        )
        OR EXISTS (
            SELECT 1
            FROM pg_catalog.pg_ts_template AS t
            JOIN pg_catalog.pg_namespace AS n ON n.oid = t.tmplnamespace
            WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
        )
        OR EXISTS (SELECT 1 FROM pg_catalog.pg_cast WHERE oid >= 16384)
        OR EXISTS (SELECT 1 FROM pg_catalog.pg_transform WHERE oid >= 16384)
        OR EXISTS (SELECT 1 FROM pg_catalog.pg_am WHERE oid >= 16384)
    '''
)


class _DiscardedOutput:
    def write(self, value: str) -> int:
        return len(value)

    def flush(self) -> None:
        return None


class _OperationError(Exception):
    def __init__(self, error: str, exit_code: int):
        super().__init__(error)
        self.error = error
        self.exit_code = exit_code


class _UsageError(Exception):
    pass


class _SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise _UsageError(message)


@dataclass(frozen=True)
class _PostgresTarget:
    url: URL
    database: str
    username: str
    password: str | None
    host: str | None
    port: int
    query_environment: tuple[tuple[str, str], ...]


_DISCARDED_OUTPUT = _DiscardedOutput()


def _failure(error: str, exit_code: int) -> tuple[int, dict[str, object]]:
    return exit_code, {'error': error, 'ok': False, 'status': 'failed'}


def _single_query_value(value: object) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, tuple) and len(value) == 1 and isinstance(value[0], str):
        return value[0]
    return None


def _parse_postgres_url(raw_url: str | None) -> _PostgresTarget:
    if not raw_url:
        raise _OperationError('POSTGRES_CONFIG_INVALID', EXIT_CONFIG_INVALID)
    try:
        url = make_url(raw_url)
    except (ArgumentError, TypeError, ValueError):
        raise _OperationError('POSTGRES_CONFIG_INVALID', EXIT_CONFIG_INVALID) from None
    if url.drivername != 'postgresql+psycopg' or not url.database or not url.username:
        raise _OperationError('POSTGRES_CONFIG_INVALID', EXIT_CONFIG_INVALID)

    query_environment: list[tuple[str, str]] = []
    for key, raw_value in url.query.items():
        environment_name = _LIBPQ_QUERY_ENV.get(key)
        value = _single_query_value(raw_value)
        if environment_name is None or value is None:
            raise _OperationError('POSTGRES_CONFIG_INVALID', EXIT_CONFIG_INVALID)
        query_environment.append((environment_name, value))

    return _PostgresTarget(
        url=url,
        database=url.database,
        username=url.username,
        password=url.password,
        host=url.host,
        port=url.port or 5432,
        query_environment=tuple(sorted(query_environment)),
    )


def _source_target() -> _PostgresTarget:
    raw_url = os.getenv('DATABASE_URL')
    if not raw_url:
        try:
            raw_url = get_settings().database_url
        except Exception:
            raise _OperationError('POSTGRES_CONFIG_INVALID', EXIT_CONFIG_INVALID) from None
    return _parse_postgres_url(raw_url)


def _restore_target(source: _PostgresTarget) -> _PostgresTarget:
    target = _parse_postgres_url(os.getenv('RESTORE_DATABASE_URL'))
    database = target.database.lower()
    is_test_database = database.startswith('test_') or database.endswith('_test') or '_test_' in database
    if (
        not is_test_database
        or database in {'postgres', 'template0', 'template1', 'worldsim_writer'}
        or database == source.database.lower()
    ):
        raise _OperationError('RESTORE_TARGET_UNSAFE', EXIT_RESTORE_TARGET_UNSAFE)
    return target


def _is_link_or_junction(path: Path) -> bool:
    try:
        return path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction())
    except OSError:
        return True


def _absolute_path(value: str | Path) -> Path:
    return Path(os.path.abspath(os.path.expanduser(str(value))))


def _ensure_safe_existing_parent(parent: Path, error: str, exit_code: int) -> None:
    if not parent.exists() or not parent.is_dir():
        raise _OperationError(error, exit_code)
    for component in (parent, *parent.parents):
        if _is_link_or_junction(component):
            raise _OperationError(error, exit_code)


def _safe_output_path(value: str | Path) -> Path:
    path = _absolute_path(value)
    if path.suffix.lower() != '.dump':
        raise _OperationError('BACKUP_OUTPUT_UNSAFE', EXIT_OUTPUT_UNSAFE)
    _ensure_safe_existing_parent(path.parent, 'BACKUP_OUTPUT_UNSAFE', EXIT_OUTPUT_UNSAFE)
    if os.path.lexists(path):
        raise _OperationError('BACKUP_OUTPUT_UNSAFE', EXIT_OUTPUT_UNSAFE)
    return path


def _safe_backup_file(value: str | Path) -> tuple[Path, os.stat_result]:
    path = _absolute_path(value)
    if path.suffix.lower() != '.dump':
        raise _OperationError('BACKUP_FILE_UNSAFE', EXIT_BACKUP_FILE_UNSAFE)
    _ensure_safe_existing_parent(path.parent, 'BACKUP_FILE_UNSAFE', EXIT_BACKUP_FILE_UNSAFE)
    try:
        path_stat = path.lstat()
    except OSError:
        raise _OperationError('BACKUP_FILE_UNSAFE', EXIT_BACKUP_FILE_UNSAFE) from None
    if _is_link_or_junction(path) or not stat.S_ISREG(path_stat.st_mode) or path_stat.st_size <= 0:
        raise _OperationError('BACKUP_FILE_UNSAFE', EXIT_BACKUP_FILE_UNSAFE)
    return path, path_stat


def _pgpass_escape(value: str) -> str:
    return value.replace('\\', '\\\\').replace(':', '\\:')


@contextmanager
def _connection_environment(target: _PostgresTarget, role: str) -> Iterator[dict[str, str]]:
    environment = {key: value for key, value in os.environ.items() if key.upper() in _CHILD_ENV_KEYS}
    if target.host:
        environment['PGHOST'] = target.host
    environment['PGPORT'] = str(target.port)
    environment['PGDATABASE'] = target.database
    environment['PGUSER'] = target.username
    environment['PGAPPNAME'] = f'worldsim-writer:{role}'
    for key, value in target.query_environment:
        environment[key] = value

    pgpass_path: Path | None = None
    try:
        descriptor, raw_path = tempfile.mkstemp(prefix='worldsim-pgpass-')
        pgpass_path = Path(raw_path)
        try:
            if hasattr(os, 'fchmod'):
                os.fchmod(descriptor, stat.S_IRUSR | stat.S_IWUSR)
            with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as handle:
                if target.password:
                    handle.write(
                        ':'.join(
                            [
                                _pgpass_escape(target.host or 'localhost'),
                                str(target.port),
                                _pgpass_escape(target.database),
                                _pgpass_escape(target.username),
                                _pgpass_escape(target.password),
                            ]
                        )
                        + '\n'
                    )
            os.chmod(pgpass_path, stat.S_IRUSR | stat.S_IWUSR)
        except BaseException:
            try:
                os.close(descriptor)
            except OSError:
                pass
            raise
        environment['PGPASSFILE'] = str(pgpass_path)
        yield environment
    finally:
        if pgpass_path is not None:
            try:
                pgpass_path.unlink(missing_ok=True)
            except OSError:
                pass


def _run_tool(
    arguments: list[str],
    environment: dict[str, str],
    timeout_seconds: int,
    *,
    stdin: BinaryIO | int | None = None,
    stdout: BinaryIO | int | None = None,
) -> int:
    result = subprocess.run(
        arguments,
        stdin=stdin,
        stdout=stdout,
        stderr=subprocess.DEVNULL,
        env=environment,
        timeout=timeout_seconds,
        check=False,
    )
    return result.returncode


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _publish_without_overwrite(temporary_path: Path, output_path: Path) -> None:
    os.link(temporary_path, output_path)


def run_backup(output: str | Path, pg_dump_bin: str = 'pg_dump', timeout_seconds: int = 3600) -> tuple[int, dict[str, object]]:
    try:
        source = _source_target()
        output_path = _safe_output_path(output)
    except _OperationError as exc:
        return _failure(exc.error, exc.exit_code)

    temporary_path: Path | None = None
    try:
        descriptor, raw_temporary_path = tempfile.mkstemp(
            prefix=f'.{output_path.name}.',
            suffix='.tmp',
            dir=output_path.parent,
        )
        temporary_path = Path(raw_temporary_path)
        try:
            with os.fdopen(descriptor, 'w+b') as output_handle:
                with _connection_environment(source, 'backup') as environment:
                    return_code = _run_tool(
                        [
                            pg_dump_bin,
                            '--format=custom',
                            '--compress=6',
                            '--no-owner',
                            '--no-privileges',
                            '--no-password',
                        ],
                        environment,
                        timeout_seconds,
                        stdin=subprocess.DEVNULL,
                        stdout=output_handle,
                    )
                output_handle.flush()
                os.fsync(output_handle.fileno())
        except (OSError, subprocess.SubprocessError):
            return _failure('BACKUP_COMMAND_FAILED', EXIT_BACKUP_FAILED)

        if return_code != 0 or temporary_path.stat().st_size <= 0:
            return _failure('BACKUP_COMMAND_FAILED', EXIT_BACKUP_FAILED)
        digest = _sha256(temporary_path)
        size_bytes = temporary_path.stat().st_size
        try:
            _publish_without_overwrite(temporary_path, output_path)
        except FileExistsError:
            return _failure('BACKUP_OUTPUT_UNSAFE', EXIT_OUTPUT_UNSAFE)
        except OSError:
            return _failure('BACKUP_PUBLISH_FAILED', EXIT_BACKUP_PUBLISH_FAILED)
        return EXIT_OK, {
            'ok': True,
            'path': str(output_path),
            'sha256': digest,
            'size_bytes': size_bytes,
            'status': 'backup_created',
        }
    except (OSError, subprocess.SubprocessError):
        return _failure('BACKUP_COMMAND_FAILED', EXIT_BACKUP_FAILED)
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass


def _restore_probe_engine(target: _PostgresTarget):
    return create_engine(target.url, poolclass=NullPool, pool_pre_ping=True, connect_args={'connect_timeout': 5})


def _restore_target_is_empty(target: _PostgresTarget) -> bool:
    engine = _restore_probe_engine(target)
    try:
        with engine.connect() as connection:
            return connection.scalar(_RESTORE_HAS_USER_OBJECTS_SQL) is False
    finally:
        engine.dispose()


def _restored_migration_status(target: _PostgresTarget) -> dict[str, object]:
    engine = _restore_probe_engine(target)
    try:
        return get_migration_status(engine=engine, alembic_ini=ALEMBIC_INI)
    finally:
        engine.dispose()


def run_verify_restore(
    backup_file: str | Path,
    pg_restore_bin: str = 'pg_restore',
    timeout_seconds: int = 3600,
) -> tuple[int, dict[str, object]]:
    try:
        source = _source_target()
        target = _restore_target(source)
        backup_path, expected_backup_stat = _safe_backup_file(backup_file)
    except _OperationError as exc:
        return _failure(exc.error, exc.exit_code)

    try:
        with redirect_stdout(_DISCARDED_OUTPUT), redirect_stderr(_DISCARDED_OUTPUT):
            target_is_empty = _restore_target_is_empty(target)
    except Exception:
        return _failure('RESTORE_TARGET_UNAVAILABLE', EXIT_RESTORE_TARGET_UNAVAILABLE)
    if not target_is_empty:
        return _failure('RESTORE_TARGET_NOT_EMPTY', EXIT_RESTORE_TARGET_NOT_EMPTY)

    flags = os.O_RDONLY
    if hasattr(os, 'O_BINARY'):
        flags |= os.O_BINARY
    if hasattr(os, 'O_NOFOLLOW'):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(backup_path, flags)
        opened_backup_stat = os.fstat(descriptor)
        if (
            opened_backup_stat.st_dev != expected_backup_stat.st_dev
            or opened_backup_stat.st_ino != expected_backup_stat.st_ino
            or not stat.S_ISREG(opened_backup_stat.st_mode)
            or opened_backup_stat.st_size <= 0
        ):
            os.close(descriptor)
            return _failure('BACKUP_FILE_UNSAFE', EXIT_BACKUP_FILE_UNSAFE)
        with os.fdopen(descriptor, 'rb', buffering=0) as backup_handle:
            if backup_handle.read(5) != b'PGDMP':
                return _failure('BACKUP_FILE_UNSAFE', EXIT_BACKUP_FILE_UNSAFE)
            backup_handle.seek(0)
            with _connection_environment(target, 'restore-verify') as environment:
                return_code = _run_tool(
                    [
                        pg_restore_bin,
                        '--exit-on-error',
                        '--single-transaction',
                        '--no-owner',
                        '--no-privileges',
                        '--no-password',
                        '--dbname',
                        target.database,
                    ],
                    environment,
                    timeout_seconds,
                    stdin=backup_handle,
                    stdout=subprocess.DEVNULL,
                )
    except (OSError, subprocess.SubprocessError):
        return _failure('RESTORE_COMMAND_FAILED', EXIT_RESTORE_FAILED)
    if return_code != 0:
        return _failure('RESTORE_COMMAND_FAILED', EXIT_RESTORE_FAILED)

    try:
        with redirect_stdout(_DISCARDED_OUTPUT), redirect_stderr(_DISCARDED_OUTPUT):
            migration_status = _restored_migration_status(target)
    except Exception:
        return _failure('RESTORE_STATUS_UNAVAILABLE', EXIT_RESTORE_STATUS_UNAVAILABLE)
    if migration_status.get('up_to_date') is True and migration_status.get('status') == 'up_to_date':
        return EXIT_OK, {'ok': True, 'status': 'restore_verified'}
    if migration_status.get('status') == 'behind':
        return _failure('RESTORE_NOT_UP_TO_DATE', EXIT_RESTORE_NOT_UP_TO_DATE)
    return _failure('RESTORE_STATUS_UNAVAILABLE', EXIT_RESTORE_STATUS_UNAVAILABLE)


def _positive_timeout(value: str) -> int:
    try:
        timeout = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError('timeout must be an integer') from None
    if timeout <= 0:
        raise argparse.ArgumentTypeError('timeout must be positive')
    return timeout


def _parser() -> argparse.ArgumentParser:
    parser = _SafeArgumentParser(description='Create PostgreSQL backups and verify restores in an isolated empty test database.')
    subparsers = parser.add_subparsers(dest='command', required=True)

    backup = subparsers.add_parser('backup', help='Create a custom-format PostgreSQL backup without overwriting files.')
    backup.add_argument('--output', required=True)
    backup.add_argument('--pg-dump-bin', default=os.getenv('PG_DUMP_BIN', 'pg_dump'))
    backup.add_argument('--timeout-seconds', type=_positive_timeout, default=3600)

    restore = subparsers.add_parser('verify-restore', help='Restore into an existing empty isolated test database and verify migration heads.')
    restore.add_argument('--backup-file', required=True)
    restore.add_argument('--pg-restore-bin', default=os.getenv('PG_RESTORE_BIN', 'pg_restore'))
    restore.add_argument('--timeout-seconds', type=_positive_timeout, default=3600)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
    except (_UsageError, argparse.ArgumentError):
        exit_code, payload = _failure('INVALID_INVOCATION', EXIT_CONFIG_INVALID)
    else:
        try:
            if args.command == 'backup':
                exit_code, payload = run_backup(args.output, args.pg_dump_bin, args.timeout_seconds)
            else:
                exit_code, payload = run_verify_restore(args.backup_file, args.pg_restore_bin, args.timeout_seconds)
        except Exception:
            exit_code, payload = _failure('POSTGRES_BACKUP_JOB_FAILED', EXIT_JOB_FAILED)

    print(json.dumps(payload, ensure_ascii=True, separators=(',', ':'), sort_keys=True))
    if exit_code != EXIT_OK:
        print(payload['error'], file=sys.stderr)
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
