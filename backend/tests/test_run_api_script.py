import importlib.util
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / 'scripts' / 'run_api.py'
API_ENV_NAMES = {
    'API_HOST',
    'API_PORT',
    'API_WORKERS',
    'API_BACKLOG',
    'API_LIMIT_CONCURRENCY',
    'API_TIMEOUT_KEEP_ALIVE_SECONDS',
    'API_TIMEOUT_GRACEFUL_SHUTDOWN_SECONDS',
    'API_PROXY_HEADERS',
    'API_FORWARDED_ALLOW_IPS',
}


def load_run_api_module():
    spec = importlib.util.spec_from_file_location('run_api_script', SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


def clear_api_environment(monkeypatch):
    for name in API_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)


def api_settings(**overrides):
    values = {
        'api_host': '127.0.0.1',
        'api_port': '8000',
        'api_workers': '1',
        'api_backlog': '2048',
        'api_limit_concurrency': '100',
        'api_timeout_keep_alive_seconds': '5',
        'api_timeout_graceful_shutdown_seconds': '30',
        'api_proxy_headers': 'false',
        'api_forwarded_allow_ips': '127.0.0.1',
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def application_module():
    return SimpleNamespace(app=lambda scope, receive, send: None)


def test_run_api_defaults_are_explicit_and_safe(monkeypatch):
    module = load_run_api_module()
    clear_api_environment(monkeypatch)

    config = module.load_config()

    assert config == module.ApiConfig(
        host='127.0.0.1',
        port=8000,
        workers=1,
        backlog=2048,
        limit_concurrency=100,
        timeout_keep_alive_seconds=5,
        timeout_graceful_shutdown_seconds=30,
        proxy_headers=False,
        forwarded_allow_ips='127.0.0.1',
    )
    assert module.build_uvicorn_args(config) == [
        sys.executable,
        '-m',
        'uvicorn',
        'app.main:app',
        '--host',
        '127.0.0.1',
        '--port',
        '8000',
        '--workers',
        '1',
        '--limit-concurrency',
        '100',
        '--backlog',
        '2048',
        '--timeout-keep-alive',
        '5',
        '--timeout-graceful-shutdown',
        '30',
        '--log-level',
        'info',
        '--no-access-log',
        '--no-server-header',
        '--no-date-header',
        '--no-use-colors',
        '--no-proxy-headers',
        '--forwarded-allow-ips',
        '127.0.0.1',
    ]


def test_run_api_builds_multi_worker_proxy_configuration(monkeypatch):
    module = load_run_api_module()
    clear_api_environment(monkeypatch)
    monkeypatch.setenv('API_HOST', '0.0.0.0')
    monkeypatch.setenv('API_PORT', '9000')
    monkeypatch.setenv('API_WORKERS', '4')
    monkeypatch.setenv('API_BACKLOG', '4096')
    monkeypatch.setenv('API_LIMIT_CONCURRENCY', '250')
    monkeypatch.setenv('API_TIMEOUT_KEEP_ALIVE_SECONDS', '10')
    monkeypatch.setenv('API_TIMEOUT_GRACEFUL_SHUTDOWN_SECONDS', '60')
    monkeypatch.setenv('API_PROXY_HEADERS', 'true')
    monkeypatch.setenv(
        'API_FORWARDED_ALLOW_IPS',
        '127.0.0.1, 10.1.2.3/8, ::1, 2001:db8::/32,127.0.0.1',
    )

    config = module.load_config()
    arguments = module.build_uvicorn_args(config)

    assert config.forwarded_allow_ips == '127.0.0.1,10.0.0.0/8,::1,2001:db8::/32'
    assert '--proxy-headers' in arguments
    assert '--no-proxy-headers' not in arguments
    assert arguments[arguments.index('--workers') + 1] == '4'
    assert arguments[arguments.index('--limit-concurrency') + 1] == '250'
    assert '--reload' not in arguments
    assert '--factory' not in arguments


@pytest.mark.parametrize('raw_value', ['true', 'TRUE', '1', 'yes', 'on'])
def test_run_api_accepts_enabled_boolean_values(monkeypatch, raw_value):
    module = load_run_api_module()
    clear_api_environment(monkeypatch)
    monkeypatch.setenv('API_PROXY_HEADERS', raw_value)

    assert module.load_config().proxy_headers is True


@pytest.mark.parametrize('raw_value', ['false', 'FALSE', '0', 'no', 'off'])
def test_run_api_accepts_disabled_boolean_values(monkeypatch, raw_value):
    module = load_run_api_module()
    clear_api_environment(monkeypatch)
    monkeypatch.setenv('API_PROXY_HEADERS', raw_value)

    assert module.load_config().proxy_headers is False


@pytest.mark.parametrize('raw_value', ['', 'enabled', '2', 'none'])
def test_run_api_rejects_invalid_boolean_values(monkeypatch, raw_value):
    module = load_run_api_module()
    clear_api_environment(monkeypatch)
    monkeypatch.setenv('API_PROXY_HEADERS', raw_value)

    with pytest.raises(module._OperationError) as exc_info:
        module.load_config()

    assert exc_info.value.error == 'API_CONFIG_INVALID'


@pytest.mark.parametrize(
    ('name', 'raw_value'),
    [
        ('API_PORT', '0'),
        ('API_PORT', '65536'),
        ('API_WORKERS', '0'),
        ('API_WORKERS', '33'),
        ('API_BACKLOG', '0'),
        ('API_BACKLOG', '65536'),
        ('API_LIMIT_CONCURRENCY', '0'),
        ('API_LIMIT_CONCURRENCY', '10001'),
        ('API_TIMEOUT_KEEP_ALIVE_SECONDS', '0'),
        ('API_TIMEOUT_KEEP_ALIVE_SECONDS', '121'),
        ('API_TIMEOUT_GRACEFUL_SHUTDOWN_SECONDS', '0'),
        ('API_TIMEOUT_GRACEFUL_SHUTDOWN_SECONDS', '301'),
        ('API_WORKERS', '-1'),
        ('API_WORKERS', '1.5'),
        ('API_WORKERS', '1_0'),
    ],
)
def test_run_api_rejects_out_of_range_or_non_decimal_numbers(monkeypatch, name, raw_value):
    module = load_run_api_module()
    clear_api_environment(monkeypatch)
    monkeypatch.setenv(name, raw_value)

    with pytest.raises(module._OperationError) as exc_info:
        module.load_config()

    assert exc_info.value.error == 'API_CONFIG_INVALID'


@pytest.mark.parametrize('raw_value', ['localhost', 'example.com', '[::1]', 'fe80::1%eth0', '224.0.0.1'])
def test_run_api_rejects_non_ip_or_unsafe_bind_hosts(monkeypatch, raw_value):
    module = load_run_api_module()
    clear_api_environment(monkeypatch)
    monkeypatch.setenv('API_HOST', raw_value)

    with pytest.raises(module._OperationError) as exc_info:
        module.load_config()

    assert exc_info.value.error == 'API_CONFIG_INVALID'


@pytest.mark.parametrize(
    'raw_value',
    [
        '',
        '*',
        '0.0.0.0/0',
        '::/0',
        '0.0.0.0',
        '::',
        'localhost',
        'example.com',
        'https://proxy.example.com',
        'http://user:password@proxy.example.com',
        '/tmp/uvicorn.sock',
        'unix:///tmp/uvicorn.sock',
        '127.0.0.1,',
        ',127.0.0.1',
        '127.0.0.1,,10.0.0.0/8',
        '10.0.0.0/33',
        '2001:db8::/129',
        'fe80::1%eth0',
        '224.0.0.0/4',
    ],
)
def test_run_api_rejects_ambiguous_or_wildcard_proxy_trust(monkeypatch, raw_value):
    module = load_run_api_module()
    clear_api_environment(monkeypatch)
    monkeypatch.setenv('API_FORWARDED_ALLOW_IPS', raw_value)

    with pytest.raises(module._OperationError) as exc_info:
        module.load_config()

    assert exc_info.value.error == 'API_CONFIG_INVALID'


def test_run_api_rejects_unsafe_proxy_trust_even_when_proxy_headers_are_disabled(monkeypatch):
    module = load_run_api_module()
    clear_api_environment(monkeypatch)
    monkeypatch.setenv('API_PROXY_HEADERS', 'false')
    monkeypatch.setenv('API_FORWARDED_ALLOW_IPS', '*')

    with pytest.raises(module._OperationError) as exc_info:
        module.load_config()

    assert exc_info.value.error == 'API_CONFIG_INVALID'


def test_run_api_removes_uvicorn_override_environment_without_removing_application_secrets():
    module = load_run_api_module()
    secret = 'postgresql+psycopg://user:password@private-host/worldsim'
    environment = {
        'DATABASE_URL': secret,
        'LLM_API_KEY': 'private-api-key',
        'UVICORN_RELOAD': 'true',
        'uvicorn_host': '0.0.0.0',
        'WEB_CONCURRENCY': '99',
        'FORWARDED_ALLOW_IPS': '*',
        'OTHER': 'kept',
    }

    child_environment = module.build_child_environment(environment)

    assert child_environment == {
        'DATABASE_URL': secret,
        'LLM_API_KEY': 'private-api-key',
        'OTHER': 'kept',
    }
    assert environment['UVICORN_RELOAD'] == 'true'


def test_run_api_builds_config_from_settings_and_launches_once(monkeypatch):
    module = load_run_api_module()
    clear_api_environment(monkeypatch)
    settings = api_settings(
        api_host='0.0.0.0',
        api_port='9001',
        api_workers='2',
        api_proxy_headers='true',
        api_forwarded_allow_ips='10.1.2.3/8',
    )
    monkeypatch.setattr(module, 'get_settings', lambda: settings)
    monkeypatch.setattr(module.importlib, 'import_module', lambda name: application_module())
    captured = {}

    def launch_api(config):
        captured['config'] = config

    monkeypatch.setattr(module, 'launch_api', launch_api)

    exit_code = module.run_api()

    expected_config = module.load_config(module._api_environment_from_settings(settings))
    assert exit_code == module.EXIT_OK
    assert expected_config.forwarded_allow_ips == '10.0.0.0/8'
    assert captured == {'config': expected_config}


def test_run_api_posix_executes_uvicorn_from_backend_directory_with_sanitized_environment(monkeypatch):
    module = load_run_api_module()
    config = module.load_config({})
    environment = {
        'DATABASE_URL': 'sqlite+pysqlite:///:memory:',
        'UVICORN_RELOAD': 'true',
        'WEB_CONCURRENCY': '99',
        'FORWARDED_ALLOW_IPS': '*',
        'OTHER': 'kept',
    }
    original_directory = Path.cwd()
    captured = {}

    def execve(executable, arguments, child_environment):
        captured['executable'] = executable
        captured['arguments'] = arguments
        captured['environment'] = child_environment
        captured['directory'] = Path.cwd()

    monkeypatch.setattr(module.os, 'execve', execve)

    module.launch_api(config, environment, platform='posix')

    assert captured['executable'] == sys.executable
    assert captured['arguments'] == module.build_uvicorn_args(config)
    assert captured['directory'] == SCRIPT_PATH.parents[1]
    assert captured['environment'] == {
        'DATABASE_URL': 'sqlite+pysqlite:///:memory:',
        'OTHER': 'kept',
    }
    assert Path.cwd() == original_directory


def test_run_api_windows_runs_uvicorn_in_current_process_with_sanitized_environment(monkeypatch):
    module = load_run_api_module()
    config = module.load_config({'API_WORKERS': '2'})
    environment = {
        'DATABASE_URL': 'sqlite+pysqlite:///:memory:',
        'UVICORN_RELOAD': 'true',
        'WEB_CONCURRENCY': '99',
        'FORWARDED_ALLOW_IPS': '*',
        'OTHER': 'kept',
    }
    original_directory = Path.cwd()
    original_environment = os.environ.copy()
    captured = {}

    def uvicorn_main(*, args, prog_name, standalone_mode):
        captured['args'] = args
        captured['prog_name'] = prog_name
        captured['standalone_mode'] = standalone_mode
        captured['environment'] = os.environ.copy()
        captured['directory'] = Path.cwd()

    monkeypatch.setattr(module.uvicorn, 'main', uvicorn_main)

    module.launch_api(config, environment, platform='nt')

    assert captured['args'] == module._build_uvicorn_cli_args(config)
    assert captured['prog_name'] == 'python -m uvicorn'
    assert captured['standalone_mode'] is False
    assert captured['directory'] == SCRIPT_PATH.parents[1]
    assert captured['environment'] == {
        'DATABASE_URL': 'sqlite+pysqlite:///:memory:',
        'OTHER': 'kept',
    }
    assert Path.cwd() == original_directory
    assert os.environ == original_environment


def test_run_api_configuration_failure_is_stable_and_redacted(monkeypatch, capsys):
    module = load_run_api_module()
    clear_api_environment(monkeypatch)
    secret = 'postgresql://user:password@private-host/worldsim'
    monkeypatch.setattr(module, 'get_settings', lambda: api_settings(api_port=secret))

    exit_code = module.main()
    output = capsys.readouterr()

    assert exit_code == module.EXIT_CONFIG_INVALID
    assert json.loads(output.out) == {'error': 'API_CONFIG_INVALID', 'ok': False, 'status': 'failed'}
    assert output.err == 'API_CONFIG_INVALID\n'
    assert secret not in output.out
    assert secret not in output.err


def test_run_api_import_failure_is_stable_and_redacted(monkeypatch, capsys):
    module = load_run_api_module()
    clear_api_environment(monkeypatch)
    secret = 'postgresql://user:password@private-host/worldsim'
    monkeypatch.setattr(module, 'get_settings', lambda: api_settings())

    def import_failure(name):
        print(secret)
        print(secret, file=sys.stderr)
        raise RuntimeError(secret)

    monkeypatch.setattr(module.importlib, 'import_module', import_failure)

    exit_code = module.main()
    output = capsys.readouterr()

    assert exit_code == module.EXIT_APPLICATION_CONFIG_INVALID
    assert json.loads(output.out) == {
        'error': 'API_APPLICATION_CONFIG_INVALID',
        'ok': False,
        'status': 'failed',
    }
    assert output.err == 'API_APPLICATION_CONFIG_INVALID\n'
    assert secret not in output.out
    assert secret not in output.err


def test_run_api_application_configuration_failure_is_stable_and_redacted(monkeypatch, capsys):
    module = load_run_api_module()
    clear_api_environment(monkeypatch)
    secret = 'postgresql://user:password@private-host/worldsim'

    def invalid_settings():
        print(secret)
        print(secret, file=sys.stderr)
        raise RuntimeError(secret)

    monkeypatch.setattr(module, 'get_settings', invalid_settings)

    exit_code = module.main()
    output = capsys.readouterr()

    assert exit_code == module.EXIT_APPLICATION_CONFIG_INVALID
    assert json.loads(output.out) == {
        'error': 'API_APPLICATION_CONFIG_INVALID',
        'ok': False,
        'status': 'failed',
    }
    assert output.err == 'API_APPLICATION_CONFIG_INVALID\n'
    assert secret not in output.out
    assert secret not in output.err


@pytest.mark.parametrize('platform', ['posix', 'nt'])
def test_run_api_platform_start_failures_are_stable(monkeypatch, platform):
    module = load_run_api_module()
    config = module.load_config({})
    secret = 'postgresql://user:password@private-host/worldsim'
    if platform == 'posix':
        monkeypatch.setattr(module.os, 'execve', lambda *args: (_ for _ in ()).throw(OSError(secret)))
    else:
        monkeypatch.setattr(module.uvicorn, 'main', lambda **kwargs: (_ for _ in ()).throw(RuntimeError(secret)))

    with pytest.raises(module._OperationError) as exc_info:
        module.launch_api(config, {}, platform=platform)

    assert exc_info.value.error == 'API_START_FAILED'
    assert exc_info.value.exit_code == module.EXIT_START_FAILED


def test_run_api_windows_maps_uvicorn_system_exit_failure(monkeypatch):
    module = load_run_api_module()
    config = module.load_config({})
    monkeypatch.setattr(module.uvicorn, 'main', lambda **kwargs: (_ for _ in ()).throw(SystemExit(3)))

    with pytest.raises(module._OperationError) as exc_info:
        module.launch_api(config, {}, platform='nt')

    assert exc_info.value.error == 'API_START_FAILED'
    assert exc_info.value.exit_code == module.EXIT_START_FAILED


def test_run_api_windows_allows_uvicorn_clean_system_exit(monkeypatch):
    module = load_run_api_module()
    config = module.load_config({})
    monkeypatch.setattr(module.uvicorn, 'main', lambda **kwargs: (_ for _ in ()).throw(SystemExit(0)))

    module.launch_api(config, {}, platform='nt')


def test_run_api_start_failure_is_stable_and_redacted(monkeypatch, capsys):
    module = load_run_api_module()
    clear_api_environment(monkeypatch)
    secret = 'postgresql://user:password@private-host/worldsim'
    monkeypatch.setattr(module, 'get_settings', lambda: api_settings())
    monkeypatch.setattr(module.importlib, 'import_module', lambda name: application_module())
    monkeypatch.setattr(
        module,
        'launch_api',
        lambda config: (_ for _ in ()).throw(module._OperationError('API_START_FAILED', module.EXIT_START_FAILED)),
    )

    exit_code = module.main()
    output = capsys.readouterr()

    assert exit_code == module.EXIT_START_FAILED
    assert json.loads(output.out) == {'error': 'API_START_FAILED', 'ok': False, 'status': 'failed'}
    assert output.err == 'API_START_FAILED\n'
    assert secret not in output.out
    assert secret not in output.err


def test_run_api_unexpected_runner_failure_is_stable_and_redacted(monkeypatch, capsys):
    module = load_run_api_module()
    secret = 'postgresql://user:password@private-host/worldsim'
    monkeypatch.setattr(module, 'run_api', lambda: (_ for _ in ()).throw(RuntimeError(secret)))

    exit_code = module.main()
    output = capsys.readouterr()

    assert exit_code == module.EXIT_RUNNER_FAILED
    assert json.loads(output.out) == {'error': 'API_RUNNER_FAILED', 'ok': False, 'status': 'failed'}
    assert output.err == 'API_RUNNER_FAILED\n'
    assert secret not in output.out
    assert secret not in output.err


@pytest.mark.parametrize('platform', ['posix', 'nt'])
def test_run_api_platform_launch_does_not_swallow_keyboard_interrupt(monkeypatch, platform):
    module = load_run_api_module()
    config = module.load_config({})
    if platform == 'posix':
        monkeypatch.setattr(module.os, 'execve', lambda *args: (_ for _ in ()).throw(KeyboardInterrupt))
    else:
        monkeypatch.setattr(module.uvicorn, 'main', lambda **kwargs: (_ for _ in ()).throw(KeyboardInterrupt))

    with pytest.raises(KeyboardInterrupt):
        module.launch_api(config, {}, platform=platform)


@pytest.mark.parametrize('stage', ['preflight', 'launch'])
def test_run_api_does_not_swallow_keyboard_interrupt(monkeypatch, capsys, stage):
    module = load_run_api_module()
    clear_api_environment(monkeypatch)
    if stage == 'preflight':
        monkeypatch.setattr(module, 'get_settings', lambda: (_ for _ in ()).throw(KeyboardInterrupt))
    else:
        monkeypatch.setattr(module, 'get_settings', lambda: api_settings())
        monkeypatch.setattr(module.importlib, 'import_module', lambda name: application_module())
        monkeypatch.setattr(module, 'launch_api', lambda config: (_ for _ in ()).throw(KeyboardInterrupt))

    with pytest.raises(KeyboardInterrupt):
        module.main()

    output = capsys.readouterr()
    assert output.out == ''
    assert output.err == ''
