#!/usr/bin/env python
import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import TextIO

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alembic import command
from alembic.config import Config

from app.core.migrations import ALEMBIC_INI, get_migration_status

EXIT_OK = 0
EXIT_UPGRADE_FAILED = 10
EXIT_STATUS_UNAVAILABLE = 11
EXIT_NOT_UP_TO_DATE = 12
EXIT_JOB_FAILED = 13

_SAFE_STATUS_ERRORS = {
    'DATABASE_UNAVAILABLE',
    'MIGRATION_REPOSITORY_UNAVAILABLE',
}


class _DiscardedOutput:
    def write(self, value: str) -> int:
        return len(value)

    def flush(self) -> None:
        return None


_DISCARDED_OUTPUT = _DiscardedOutput()


def _alembic_config(alembic_ini: Path, output: TextIO) -> Config:
    config = Config(str(alembic_ini), output_buffer=output, stdout=output)
    config.set_main_option('script_location', str(alembic_ini.parent / 'alembic'))
    return config


def _failure(error: str, exit_code: int) -> tuple[int, dict[str, object]]:
    return exit_code, {'error': error, 'ok': False, 'status': 'failed'}


def run_migrations(alembic_ini: Path = ALEMBIC_INI) -> tuple[int, dict[str, object]]:
    output = _DISCARDED_OUTPUT
    with redirect_stdout(output), redirect_stderr(output):
        try:
            command.upgrade(_alembic_config(alembic_ini, output), 'head')
        except Exception:
            return _failure('MIGRATION_UPGRADE_FAILED', EXIT_UPGRADE_FAILED)

        try:
            migration_status = get_migration_status(alembic_ini=alembic_ini)
        except Exception:
            return _failure('MIGRATION_STATUS_UNAVAILABLE', EXIT_STATUS_UNAVAILABLE)

    if migration_status.get('up_to_date') is True and migration_status.get('status') == 'up_to_date':
        return EXIT_OK, {'ok': True, 'status': 'up_to_date'}
    if migration_status.get('status') == 'behind':
        return _failure('MIGRATION_NOT_UP_TO_DATE', EXIT_NOT_UP_TO_DATE)

    status_error = migration_status.get('error')
    if status_error not in _SAFE_STATUS_ERRORS:
        status_error = 'MIGRATION_STATUS_UNAVAILABLE'
    return _failure(status_error, EXIT_STATUS_UNAVAILABLE)


def main() -> int:
    try:
        exit_code, payload = run_migrations()
    except Exception:
        exit_code, payload = _failure('MIGRATION_JOB_FAILED', EXIT_JOB_FAILED)

    print(json.dumps(payload, ensure_ascii=True, separators=(',', ':'), sort_keys=True))
    if exit_code != EXIT_OK:
        print(payload['error'], file=sys.stderr)
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
