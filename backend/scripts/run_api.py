#!/usr/bin/env python
import importlib
import ipaddress
import json
import os
import sys
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Mapping

import uvicorn

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_BACKEND_ROOT))

from app.core.config import get_settings

EXIT_OK = 0
EXIT_CONFIG_INVALID = 40
EXIT_APPLICATION_CONFIG_INVALID = 41
EXIT_START_FAILED = 42
EXIT_RUNNER_FAILED = 43

_TRUE_VALUES = frozenset({'1', 'true', 'yes', 'on'})
_FALSE_VALUES = frozenset({'0', 'false', 'no', 'off'})
_UVICORN_ENV_NAMES = frozenset({'FORWARDED_ALLOW_IPS', 'WEB_CONCURRENCY'})
_API_SETTING_FIELDS = {
    'API_HOST': 'api_host',
    'API_PORT': 'api_port',
    'API_WORKERS': 'api_workers',
    'API_BACKLOG': 'api_backlog',
    'API_LIMIT_CONCURRENCY': 'api_limit_concurrency',
    'API_TIMEOUT_KEEP_ALIVE_SECONDS': 'api_timeout_keep_alive_seconds',
    'API_TIMEOUT_GRACEFUL_SHUTDOWN_SECONDS': 'api_timeout_graceful_shutdown_seconds',
    'API_PROXY_HEADERS': 'api_proxy_headers',
    'API_FORWARDED_ALLOW_IPS': 'api_forwarded_allow_ips',
}


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


@dataclass(frozen=True)
class ApiConfig:
    host: str
    port: int
    workers: int
    backlog: int
    limit_concurrency: int
    timeout_keep_alive_seconds: int
    timeout_graceful_shutdown_seconds: int
    proxy_headers: bool
    forwarded_allow_ips: str


_DISCARDED_OUTPUT = _DiscardedOutput()


def _configuration_error() -> _OperationError:
    return _OperationError('API_CONFIG_INVALID', EXIT_CONFIG_INVALID)


def _environment_value(environment: Mapping[str, str], name: str, default: str) -> str:
    value = environment.get(name, default)
    if not isinstance(value, str):
        raise _configuration_error()
    return value


def _parse_integer(environment: Mapping[str, str], name: str, default: int, minimum: int, maximum: int) -> int:
    raw_value = _environment_value(environment, name, str(default)).strip()
    if not raw_value or not raw_value.isascii() or not raw_value.isdecimal():
        raise _configuration_error()
    value = int(raw_value)
    if value < minimum or value > maximum:
        raise _configuration_error()
    return value


def _parse_boolean(environment: Mapping[str, str], name: str, default: bool) -> bool:
    raw_value = _environment_value(environment, name, str(default)).strip().lower()
    if raw_value in _TRUE_VALUES:
        return True
    if raw_value in _FALSE_VALUES:
        return False
    raise _configuration_error()


def _parse_bind_host(environment: Mapping[str, str]) -> str:
    raw_value = _environment_value(environment, 'API_HOST', '127.0.0.1').strip()
    if not raw_value or '%' in raw_value:
        raise _configuration_error()
    try:
        address = ipaddress.ip_address(raw_value)
    except ValueError:
        raise _configuration_error() from None
    if address.is_multicast:
        raise _configuration_error()
    return str(address)


def _parse_forwarded_allow_ips(environment: Mapping[str, str]) -> str:
    raw_value = _environment_value(environment, 'API_FORWARDED_ALLOW_IPS', '127.0.0.1')
    if not raw_value or len(raw_value) > 2048:
        raise _configuration_error()

    raw_entries = raw_value.split(',')
    if len(raw_entries) > 32:
        raise _configuration_error()

    normalized_entries: list[str] = []
    for raw_entry in raw_entries:
        entry = raw_entry.strip()
        if not entry or entry == '*' or '%' in entry:
            raise _configuration_error()
        try:
            if '/' in entry:
                network = ipaddress.ip_network(entry, strict=False)
                if network.prefixlen == 0 or network.network_address.is_unspecified or network.network_address.is_multicast:
                    raise _configuration_error()
                normalized_entry = str(network)
            else:
                address = ipaddress.ip_address(entry)
                if address.is_unspecified or address.is_multicast:
                    raise _configuration_error()
                normalized_entry = str(address)
        except ValueError:
            raise _configuration_error() from None
        if normalized_entry not in normalized_entries:
            normalized_entries.append(normalized_entry)

    return ','.join(normalized_entries)


def load_config(environment: Mapping[str, str] | None = None) -> ApiConfig:
    source = os.environ if environment is None else environment
    return ApiConfig(
        host=_parse_bind_host(source),
        port=_parse_integer(source, 'API_PORT', 8000, 1, 65535),
        workers=_parse_integer(source, 'API_WORKERS', 1, 1, 32),
        backlog=_parse_integer(source, 'API_BACKLOG', 2048, 1, 65535),
        limit_concurrency=_parse_integer(source, 'API_LIMIT_CONCURRENCY', 100, 1, 10000),
        timeout_keep_alive_seconds=_parse_integer(source, 'API_TIMEOUT_KEEP_ALIVE_SECONDS', 5, 1, 120),
        timeout_graceful_shutdown_seconds=_parse_integer(
            source,
            'API_TIMEOUT_GRACEFUL_SHUTDOWN_SECONDS',
            30,
            1,
            300,
        ),
        proxy_headers=_parse_boolean(source, 'API_PROXY_HEADERS', False),
        forwarded_allow_ips=_parse_forwarded_allow_ips(source),
    )


def _build_uvicorn_cli_args(config: ApiConfig) -> list[str]:
    proxy_option = '--proxy-headers' if config.proxy_headers else '--no-proxy-headers'
    return [
        'app.main:app',
        '--host',
        config.host,
        '--port',
        str(config.port),
        '--workers',
        str(config.workers),
        '--limit-concurrency',
        str(config.limit_concurrency),
        '--backlog',
        str(config.backlog),
        '--timeout-keep-alive',
        str(config.timeout_keep_alive_seconds),
        '--timeout-graceful-shutdown',
        str(config.timeout_graceful_shutdown_seconds),
        '--log-level',
        'info',
        '--no-access-log',
        '--no-server-header',
        '--no-date-header',
        '--no-use-colors',
        proxy_option,
        '--forwarded-allow-ips',
        config.forwarded_allow_ips,
    ]


def build_uvicorn_args(config: ApiConfig) -> list[str]:
    return [sys.executable, '-m', 'uvicorn', *_build_uvicorn_cli_args(config)]


def build_child_environment(environment: Mapping[str, str] | None = None) -> dict[str, str]:
    source = os.environ if environment is None else environment
    return {
        name: value
        for name, value in source.items()
        if name.upper() not in _UVICORN_ENV_NAMES and not name.upper().startswith('UVICORN_')
    }


@contextmanager
def _backend_working_directory() -> Iterator[None]:
    previous_directory = Path.cwd()
    os.chdir(_BACKEND_ROOT)
    try:
        yield
    finally:
        os.chdir(previous_directory)


@contextmanager
def _replaced_environment(environment: Mapping[str, str]) -> Iterator[None]:
    previous_environment = os.environ.copy()
    os.environ.clear()
    os.environ.update(environment)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(previous_environment)


def _load_application_settings():
    try:
        with _backend_working_directory(), redirect_stdout(_DISCARDED_OUTPUT), redirect_stderr(_DISCARDED_OUTPUT):
            return get_settings()
    except Exception:
        raise _OperationError('API_APPLICATION_CONFIG_INVALID', EXIT_APPLICATION_CONFIG_INVALID) from None


def _api_environment_from_settings(settings: object) -> dict[str, str]:
    try:
        environment = {name: getattr(settings, field) for name, field in _API_SETTING_FIELDS.items()}
    except AttributeError:
        raise _OperationError('API_APPLICATION_CONFIG_INVALID', EXIT_APPLICATION_CONFIG_INVALID) from None
    if not all(isinstance(value, str) for value in environment.values()):
        raise _OperationError('API_APPLICATION_CONFIG_INVALID', EXIT_APPLICATION_CONFIG_INVALID)
    return environment


def _preflight_application_import() -> None:
    try:
        with _backend_working_directory(), redirect_stdout(_DISCARDED_OUTPUT), redirect_stderr(_DISCARDED_OUTPUT):
            application_module = importlib.import_module('app.main')
            if not callable(getattr(application_module, 'app', None)):
                raise TypeError
    except Exception:
        raise _OperationError('API_APPLICATION_CONFIG_INVALID', EXIT_APPLICATION_CONFIG_INVALID) from None


def _launch_api_windows(config: ApiConfig, environment: Mapping[str, str]) -> None:
    try:
        with _backend_working_directory(), _replaced_environment(environment):
            uvicorn.main(
                args=_build_uvicorn_cli_args(config),
                prog_name='python -m uvicorn',
                standalone_mode=False,
            )
    except SystemExit as exc:
        if exc.code in {None, EXIT_OK}:
            return
        raise _OperationError('API_START_FAILED', EXIT_START_FAILED) from None
    except Exception:
        raise _OperationError('API_START_FAILED', EXIT_START_FAILED) from None


def _launch_api_posix(arguments: list[str], environment: Mapping[str, str]) -> None:
    try:
        with _backend_working_directory():
            os.execve(sys.executable, arguments, dict(environment))
    except OSError:
        raise _OperationError('API_START_FAILED', EXIT_START_FAILED) from None


def launch_api(
    config: ApiConfig,
    environment: Mapping[str, str] | None = None,
    *,
    platform: str | None = None,
) -> None:
    child_environment = build_child_environment(environment)
    current_platform = os.name if platform is None else platform
    if current_platform == 'nt':
        _launch_api_windows(config, child_environment)
        return
    _launch_api_posix(build_uvicorn_args(config), child_environment)


def run_api() -> int:
    settings = _load_application_settings()
    config = load_config(_api_environment_from_settings(settings))
    _preflight_application_import()
    launch_api(config)
    return EXIT_OK


def _failure(error: str) -> dict[str, object]:
    return {'error': error, 'ok': False, 'status': 'failed'}


def main() -> int:
    try:
        return run_api()
    except _OperationError as exc:
        exit_code = exc.exit_code
        payload = _failure(exc.error)
    except Exception:
        exit_code = EXIT_RUNNER_FAILED
        payload = _failure('API_RUNNER_FAILED')

    print(json.dumps(payload, ensure_ascii=True, separators=(',', ':'), sort_keys=True))
    print(payload['error'], file=sys.stderr)
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
