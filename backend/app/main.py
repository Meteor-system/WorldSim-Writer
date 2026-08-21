import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from traceback import extract_tb
from urllib.parse import urlsplit
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.migrations import get_migration_status

_REQUEST_ID_HEADER = 'X-Request-ID'
_REQUEST_ID_PATTERN = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$')
_REQUEST_LOG_HANDLER = 'worldsim-structured-request'
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
request_logger = logging.getLogger('worldsim.request')


def _configure_request_logging(log_level: str) -> None:
    request_logger.setLevel(log_level)
    request_logger.propagate = False
    handler = next(
        (candidate for candidate in request_logger.handlers if candidate.get_name() == _REQUEST_LOG_HANDLER),
        None,
    )
    if handler is None:
        handler = logging.StreamHandler()
        handler.set_name(_REQUEST_LOG_HANDLER)
        handler.setFormatter(logging.Formatter('%(message)s'))
        request_logger.addHandler(handler)
    handler.setLevel(log_level)


def _request_id(candidate: str | None) -> str:
    if candidate and _REQUEST_ID_PATTERN.fullmatch(candidate):
        return candidate
    return uuid4().hex


def _route_template(request: Request) -> str:
    route = request.scope.get('route')
    path = getattr(route, 'path', None)
    return path if isinstance(path, str) else '<unmatched>'


def _exception_location(exc: Exception) -> dict[str, object]:
    frames = extract_tb(exc.__traceback__)
    for frame in reversed(frames):
        frame_path = Path(frame.filename).resolve()
        try:
            relative_path = frame_path.relative_to(_BACKEND_ROOT)
        except ValueError:
            continue
        return {
            'exception_file': relative_path.as_posix(),
            'exception_line': frame.lineno,
            'exception_function': frame.name,
        }
    if not frames:
        return {}
    frame = frames[-1]
    return {
        'exception_file': f'<external>/{Path(frame.filename).name}',
        'exception_line': frame.lineno,
        'exception_function': frame.name,
    }


def _request_log_level(route: str, status_code: int, exception_type: str | None) -> int:
    if exception_type or status_code >= 500:
        return logging.ERROR
    if status_code >= 400:
        return logging.WARNING
    if route in {'/live', '/ready'}:
        return logging.DEBUG
    return logging.INFO


def _log_request(
    *,
    request_id: str,
    method: str,
    route: str,
    status_code: int,
    duration_ms: float,
    exception_type: str | None = None,
    exception_location: dict[str, object] | None = None,
) -> None:
    level = _request_log_level(route, status_code, exception_type)
    payload: dict[str, object] = {
        'timestamp': datetime.now(UTC).isoformat(timespec='milliseconds').replace('+00:00', 'Z'),
        'level': logging.getLevelName(level).lower(),
        'event': 'request.failed' if exception_type else 'request.completed',
        'request_id': request_id,
        'method': method,
        'route': route,
        'status_code': status_code,
        'duration_ms': round(duration_ms, 3),
    }
    if exception_type:
        payload['exception_type'] = exception_type
        payload.update(exception_location or {})
    request_logger.log(level, json.dumps(payload, ensure_ascii=False, separators=(',', ':'), sort_keys=True))


def _public_migration_status() -> dict[str, object]:
    raw_status = get_migration_status()
    migration_status = raw_status.get('status')
    if migration_status not in {'up_to_date', 'behind'}:
        migration_status = 'unknown'
    public_status: dict[str, object] = {
        'current': raw_status.get('current'),
        'head': raw_status.get('head'),
        'up_to_date': raw_status.get('up_to_date') is True,
        'status': migration_status,
    }
    if migration_status == 'unknown':
        error = raw_status.get('error')
        public_status['error'] = (
            error
            if error in {'DATABASE_UNAVAILABLE', 'MIGRATION_REPOSITORY_UNAVAILABLE'}
            else 'MIGRATION_STATUS_UNAVAILABLE'
        )
    return public_status


def _cors_allow_origins(frontend_origin: str) -> list[str]:
    try:
        origin = urlsplit(frontend_origin)
        port = origin.port
    except ValueError:
        return [frontend_origin]

    loopback_aliases = {'localhost': '127.0.0.1', '127.0.0.1': 'localhost'}
    alias = loopback_aliases.get(origin.hostname)
    if (
        origin.scheme not in {'http', 'https'}
        or not origin.netloc
        or origin.username is not None
        or origin.password is not None
        or origin.path
        or origin.query
        or origin.fragment
        or alias is None
    ):
        return [frontend_origin]

    port_suffix = f':{port}' if port is not None else ''
    return list(dict.fromkeys([frontend_origin, f'{origin.scheme}://{alias}{port_suffix}']))


def create_app() -> FastAPI:
    settings = get_settings()
    _configure_request_logging(settings.log_level)
    app = FastAPI(title='WorldSim-Writer API')
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_allow_origins(settings.frontend_origin),
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
        expose_headers=[_REQUEST_ID_HEADER],
    )

    @app.middleware('http')
    async def observe_request(request: Request, call_next):
        request_id = _request_id(request.headers.get(_REQUEST_ID_HEADER))
        request.state.request_id = request_id
        started_at = perf_counter()
        status_code = 500
        exception_type = None
        exception_location = None
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers[_REQUEST_ID_HEADER] = request_id
            return response
        except Exception as exc:
            exception_type = type(exc).__name__
            exception_location = _exception_location(exc)
            raise
        finally:
            _log_request(
                request_id=request_id,
                method=request.method,
                route=_route_template(request),
                status_code=status_code,
                duration_ms=(perf_counter() - started_at) * 1000,
                exception_type=exception_type,
                exception_location=exception_location,
            )

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = getattr(request.state, 'request_id', uuid4().hex)
        safe_errors = [
            {
                'type': error.get('type'),
                'loc': list(error.get('loc', ())),
                'msg': error.get('msg'),
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={'detail': safe_errors, 'request_id': request_id},
            headers={_REQUEST_ID_HEADER: request_id},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception(request: Request, _exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, 'request_id', uuid4().hex)
        return JSONResponse(
            status_code=500,
            content={'detail': 'INTERNAL_SERVER_ERROR', 'request_id': request_id},
            headers={_REQUEST_ID_HEADER: request_id},
        )

    @app.get('/live')
    def liveness_check() -> dict[str, str]:
        return {'status': 'ok'}

    @app.get('/ready')
    def readiness_check() -> JSONResponse:
        migration = _public_migration_status()
        if migration['up_to_date'] is True:
            return JSONResponse(
                status_code=200,
                content={'status': 'ready', 'checks': {'database': 'ok', 'migration': migration}},
            )
        error = str(migration.get('error') or 'MIGRATION_NOT_UP_TO_DATE')
        database_status = {
            'DATABASE_UNAVAILABLE': 'unavailable',
            'MIGRATION_REPOSITORY_UNAVAILABLE': 'unknown',
            'MIGRATION_STATUS_UNAVAILABLE': 'unknown',
        }.get(error, 'ok')
        return JSONResponse(
            status_code=503,
            content={
                'status': 'not_ready',
                'checks': {'database': database_status, 'migration': migration},
                'error': error,
            },
        )

    @app.get('/health')
    def health_check() -> dict[str, object]:
        current_settings = get_settings()
        return {'status': 'ok', 'migration': _public_migration_status(), 'llm': {'mock': current_settings.llm_mock}}

    app.include_router(api_router)
    return app


app = create_app()
