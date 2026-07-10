import importlib.util
import json
import sys
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / 'scripts' / 'run_migrations.py'


def load_run_migrations_module():
    spec = importlib.util.spec_from_file_location('run_migrations_script', SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_run_migrations_script_upgrades_head_and_verifies_status(monkeypatch, capsys):
    module = load_run_migrations_module()
    captured = {}
    secret = 'postgresql://user:password@private-host/worldsim'

    def upgrade(config, revision):
        captured['config_file_name'] = config.config_file_name
        captured['script_location'] = config.get_main_option('script_location')
        captured['revision'] = revision
        print(secret)
        print(secret, file=sys.stderr)
        config.print_stdout(secret)

    monkeypatch.setattr(module.command, 'upgrade', upgrade)
    monkeypatch.setattr(
        module,
        'get_migration_status',
        lambda *, alembic_ini: {
            'current': '0013_add_import_node',
            'head': '0013_add_import_node',
            'up_to_date': True,
            'status': 'up_to_date',
        },
    )

    exit_code = module.main()
    output = capsys.readouterr()

    assert exit_code == module.EXIT_OK
    assert json.loads(output.out) == {'ok': True, 'status': 'up_to_date'}
    assert output.err == ''
    assert secret not in output.out
    assert captured == {
        'config_file_name': str(module.ALEMBIC_INI),
        'script_location': str(module.ALEMBIC_INI.parent / 'alembic'),
        'revision': 'head',
    }


def test_run_migrations_script_fails_when_upgrade_fails_without_leaking_details(monkeypatch, capsys):
    module = load_run_migrations_module()
    secret = 'postgresql://user:password@private-host/worldsim'

    def upgrade(config, revision):
        print(secret)
        print(secret, file=sys.stderr)
        config.print_stdout(secret)
        raise RuntimeError(secret)

    def unexpected_status_check(**kwargs):
        raise AssertionError('status check must not run after an upgrade failure')

    monkeypatch.setattr(module.command, 'upgrade', upgrade)
    monkeypatch.setattr(module, 'get_migration_status', unexpected_status_check)

    exit_code = module.main()
    output = capsys.readouterr()

    assert exit_code == module.EXIT_UPGRADE_FAILED
    assert json.loads(output.out) == {
        'error': 'MIGRATION_UPGRADE_FAILED',
        'ok': False,
        'status': 'failed',
    }
    assert output.err == 'MIGRATION_UPGRADE_FAILED\n'
    assert secret not in output.out
    assert secret not in output.err


def test_run_migrations_script_fails_when_postcheck_is_unavailable_without_leaking_details(monkeypatch, capsys):
    module = load_run_migrations_module()
    secret = 'postgresql://user:password@private-host/worldsim'

    monkeypatch.setattr(module.command, 'upgrade', lambda config, revision: None)
    monkeypatch.setattr(module, 'get_migration_status', lambda **kwargs: (_ for _ in ()).throw(RuntimeError(secret)))

    exit_code = module.main()
    output = capsys.readouterr()

    assert exit_code == module.EXIT_STATUS_UNAVAILABLE
    assert json.loads(output.out) == {
        'error': 'MIGRATION_STATUS_UNAVAILABLE',
        'ok': False,
        'status': 'failed',
    }
    assert output.err == 'MIGRATION_STATUS_UNAVAILABLE\n'
    assert secret not in output.out
    assert secret not in output.err


def test_run_migrations_script_fails_when_database_remains_behind(monkeypatch, capsys):
    module = load_run_migrations_module()

    monkeypatch.setattr(module.command, 'upgrade', lambda config, revision: None)
    monkeypatch.setattr(
        module,
        'get_migration_status',
        lambda *, alembic_ini: {
            'current': '0012_previous',
            'head': '0013_add_import_node',
            'up_to_date': False,
            'status': 'behind',
        },
    )

    exit_code = module.main()
    output = capsys.readouterr()

    assert exit_code == module.EXIT_NOT_UP_TO_DATE
    assert json.loads(output.out) == {
        'error': 'MIGRATION_NOT_UP_TO_DATE',
        'ok': False,
        'status': 'failed',
    }
    assert output.err == 'MIGRATION_NOT_UP_TO_DATE\n'


def test_run_migrations_script_preserves_safe_status_error(monkeypatch, capsys):
    module = load_run_migrations_module()

    monkeypatch.setattr(module.command, 'upgrade', lambda config, revision: None)
    monkeypatch.setattr(
        module,
        'get_migration_status',
        lambda *, alembic_ini: {
            'current': None,
            'head': '0013_add_import_node',
            'up_to_date': False,
            'status': 'unknown',
            'error': 'DATABASE_UNAVAILABLE',
        },
    )

    exit_code = module.main()
    output = capsys.readouterr()

    assert exit_code == module.EXIT_STATUS_UNAVAILABLE
    assert json.loads(output.out)['error'] == 'DATABASE_UNAVAILABLE'
    assert output.err == 'DATABASE_UNAVAILABLE\n'


def test_run_migrations_script_replaces_untrusted_status_error(monkeypatch, capsys):
    module = load_run_migrations_module()
    secret = 'postgresql://user:password@private-host/worldsim'

    monkeypatch.setattr(module.command, 'upgrade', lambda config, revision: None)
    monkeypatch.setattr(
        module,
        'get_migration_status',
        lambda *, alembic_ini: {
            'current': secret,
            'head': secret,
            'up_to_date': False,
            'status': 'unknown',
            'error': secret,
        },
    )

    exit_code = module.main()
    output = capsys.readouterr()

    assert exit_code == module.EXIT_STATUS_UNAVAILABLE
    assert json.loads(output.out)['error'] == 'MIGRATION_STATUS_UNAVAILABLE'
    assert output.err == 'MIGRATION_STATUS_UNAVAILABLE\n'
    assert secret not in output.out
    assert secret not in output.err


def test_run_migrations_script_does_not_swallow_keyboard_interrupt(monkeypatch, capsys):
    module = load_run_migrations_module()

    def interrupt(config, revision):
        raise KeyboardInterrupt

    monkeypatch.setattr(module.command, 'upgrade', interrupt)

    with pytest.raises(KeyboardInterrupt):
        module.main()

    output = capsys.readouterr()
    assert output.out == ''
    assert output.err == ''


def test_run_migrations_script_redacts_unexpected_job_failure(monkeypatch, capsys):
    module = load_run_migrations_module()
    secret = 'postgresql://user:password@private-host/worldsim'

    monkeypatch.setattr(module, 'run_migrations', lambda: (_ for _ in ()).throw(RuntimeError(secret)))

    exit_code = module.main()
    output = capsys.readouterr()

    assert exit_code == module.EXIT_JOB_FAILED
    assert json.loads(output.out) == {
        'error': 'MIGRATION_JOB_FAILED',
        'ok': False,
        'status': 'failed',
    }
    assert output.err == 'MIGRATION_JOB_FAILED\n'
    assert secret not in output.out
    assert secret not in output.err
