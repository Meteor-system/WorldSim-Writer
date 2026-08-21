import json
import logging
from collections.abc import Callable, Mapping
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.llm_usage.models import LLMUsageAudit


AuditSessionFactory = Callable[[], Session]


usage_logger = logging.getLogger('worldsim.llm.usage')

_ERROR_CODES = frozenset(
    {
        'MODEL_TIMEOUT',
        'MODEL_AUTH_FAILED',
        'MODEL_RATE_LIMITED',
        'MODEL_REQUEST_FAILED',
        'MODEL_RESPONSE_INVALID',
    }
)
_PROVENANCE_FIELDS = frozenset(
    {
        'endpoint',
        'response_id',
        'provider_request_id',
        'schema_name',
        'schema_mode',
        'response_format',
        'finish_reason',
        'retry_reason',
    }
)


def _usage_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    return None


def extract_provider_usage(payload: Any) -> dict[str, int | None]:
    """Extract token counts from OpenAI-compatible Responses or Chat payloads."""
    usage: Any = payload.get('usage') if isinstance(payload, Mapping) else None
    if not isinstance(usage, Mapping):
        usage = {}
    input_tokens = _usage_int(usage.get('input_tokens'))
    if input_tokens is None:
        input_tokens = _usage_int(usage.get('prompt_tokens'))
    output_tokens = _usage_int(usage.get('output_tokens'))
    if output_tokens is None:
        output_tokens = _usage_int(usage.get('completion_tokens'))
    return {
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'total_tokens': _usage_int(usage.get('total_tokens')),
    }


def safe_error_code(exc: BaseException) -> str:
    """Classify errors without exposing provider or exception text."""
    for value in getattr(exc, 'args', ()):
        if isinstance(value, str) and value in _ERROR_CODES:
            return value

    if isinstance(exc, TimeoutError):
        return 'MODEL_TIMEOUT'

    response = getattr(exc, 'response', None)
    status_code = getattr(response, 'status_code', None)
    if not isinstance(status_code, int):
        status_code = getattr(exc, 'status_code', None)
    if status_code in {401, 403}:
        return 'MODEL_AUTH_FAILED'
    if status_code == 429:
        return 'MODEL_RATE_LIMITED'
    return 'MODEL_REQUEST_FAILED'


def _safe_provenance(provenance: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(provenance, Mapping):
        return {}
    safe: dict[str, Any] = {}
    for key in _PROVENANCE_FIELDS:
        value = provenance.get(key)
        if isinstance(value, (str, int, float, bool)) or value is None:
            if value is not None:
                safe[key] = value
    return safe


def _session_factory_from_db(db: Session | None) -> AuditSessionFactory | None:
    if db is None:
        return None
    try:
        bind = db.get_bind()
    except Exception:
        return None
    if bind is None:
        return None
    return sessionmaker(bind=bind, autoflush=False, expire_on_commit=False)


def audit_session_factory_from_db(db: Session | None) -> AuditSessionFactory | None:
    return _session_factory_from_db(db)


def record_llm_usage(
    db: Session | None = None,
    *,
    session_factory: AuditSessionFactory | None = None,
    operation: str,
    provider: str,
    api_mode: str,
    model: str,
    is_mock: bool,
    status: str,
    duration_ms: int,
    attempt_count: int = 1,
    schema_fallback_used: bool = False,
    world_id: int | None = None,
    chapter_id: int | None = None,
    draft_id: int | None = None,
    http_status: int | None = None,
    input_message_count: int = 0,
    input_chars: int = 0,
    output_chars: int = 0,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    total_tokens: int | None = None,
    error_code: str | None = None,
    request_id: str | None = None,
    provenance: Mapping[str, Any] | None = None,
) -> bool:
    """Persist audit telemetry in a short-lived transaction isolated from business state."""
    safe_provenance = _safe_provenance(provenance)
    audit_metadata = {
        'operation': operation,
        'provider': provider,
        'api_mode': api_mode,
        'model': model,
        'is_mock': bool(is_mock),
        'status': status,
        'duration_ms': max(0, duration_ms),
        'attempt_count': max(1, attempt_count),
        'schema_fallback_used': bool(schema_fallback_used),
        'http_status': http_status if isinstance(http_status, int) else None,
        'input_message_count': max(0, input_message_count),
        'input_chars': max(0, input_chars),
        'output_chars': max(0, output_chars),
        'input_tokens': _usage_int(input_tokens),
        'output_tokens': _usage_int(output_tokens),
        'total_tokens': _usage_int(total_tokens),
        'error_code': error_code if error_code in _ERROR_CODES else None,
        'request_id': request_id if isinstance(request_id, str) else None,
        'provenance': safe_provenance,
    }
    factory = session_factory or _session_factory_from_db(db)

    def log_failure() -> None:
        usage_logger.warning(
            json.dumps(
                {
                    'event': 'llm.usage_audit_failed',
                    'operation': operation,
                    'status': status,
                    'request_id': audit_metadata['request_id'],
                },
                ensure_ascii=False,
                separators=(',', ':'),
                sort_keys=True,
            )
        )

    if factory is None:
        log_failure()
        return False

    def add_audit_record(audit_db: Session, *, include_associations: bool) -> None:
        audit_db.add(
            LLMUsageAudit(
                world_id=world_id if include_associations else None,
                chapter_id=chapter_id if include_associations else None,
                draft_id=draft_id if include_associations else None,
                **audit_metadata,
            )
        )

    audit_db: Session | None = None
    try:
        audit_db = factory()
        add_audit_record(audit_db, include_associations=True)
        audit_db.commit()
    except IntegrityError:
        if audit_db is not None:
            try:
                audit_db.rollback()
            except Exception:
                pass
            try:
                audit_db.close()
            except Exception:
                pass
            audit_db = None
        if not any(value is not None for value in (world_id, chapter_id, draft_id)):
            log_failure()
            return False
        try:
            audit_db = factory()
            add_audit_record(audit_db, include_associations=False)
            audit_db.commit()
            usage_logger.warning(
                json.dumps(
                    {
                        'event': 'llm.usage_audit_association_fallback',
                        'operation': operation,
                        'status': status,
                        'request_id': audit_metadata['request_id'],
                    },
                    ensure_ascii=False,
                    separators=(',', ':'),
                    sort_keys=True,
                )
            )
        except Exception:
            if audit_db is not None:
                try:
                    audit_db.rollback()
                except Exception:
                    pass
            log_failure()
            return False
    except Exception:
        if audit_db is not None:
            try:
                audit_db.rollback()
            except Exception:
                pass
        log_failure()
        return False
    finally:
        if audit_db is not None:
            try:
                audit_db.close()
            except Exception:
                pass

    usage_logger.info(
        json.dumps(
            {
                'event': 'llm.usage_audit_recorded',
                'operation': operation,
                'provider': provider,
                'api_mode': api_mode,
                'model': model,
                'status': status,
                'is_mock': bool(is_mock),
            },
            ensure_ascii=False,
            separators=(',', ':'),
            sort_keys=True,
        )
    )
    return True
