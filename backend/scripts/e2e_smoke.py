#!/usr/bin/env python
import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import httpx

DEFAULT_BASE_URL = 'http://localhost:8000'
DEFAULT_PASSWORD = 'strongpass123'
DEFAULT_TIMEOUT_SECONDS = 60.0
MAX_RESPONSE_BODY_CHARS = 1000
BACKEND_DIR = Path(__file__).resolve().parents[1]
READINESS_STATUSES = {'ready', 'needs_review', 'blocked'}
CONSISTENCY_STATUSES = {'clear', 'needs_review', 'blocked'}
SECOND_CHAPTER_CANON = '第二章前设定：城主府外墙刻着三枚潮汐符印，只有湿信能显影。'
STALE_DRAFT_CANON = '第三章前设定：灵井只在子夜回声，旧草稿必须重新生成。'
SECOND_CHAPTER_GOAL = 'E2E smoke: chapter 2 follows the latest canon, previous summary, and open foreshadows.'
FRESH_SECOND_CHAPTER_GOAL = 'E2E smoke: regenerate chapter 2 after stale world-version rejection.'

_REDACTION_PATTERNS = [
    (re.compile(r'Authorization\s*:\s*Bearer\s+[^\s,;]+', re.IGNORECASE), 'Authorization: Bearer [REDACTED_SECRET]'),
    (re.compile(r'("authorization"\s*:\s*"Bearer\s+)[^"]+(")', re.IGNORECASE), r'\1[REDACTED_SECRET]\2'),
    (re.compile(r'("(?:api[_-]?key|llm_api_key|openai_api_key)"\s*:\s*")[^"]+(")', re.IGNORECASE), r'\1[REDACTED_SECRET]\2'),
    (re.compile(r'("password"\s*:\s*")[^"]+(")', re.IGNORECASE), r'\1[REDACTED_SECRET]\2'),
    (re.compile(r'("(?:llm_base_url|base_url)"\s*:\s*")https?://[^"]+(")', re.IGNORECASE), r'\1[REDACTED_URL]\2'),
    (re.compile(r'("(?:llm_model|model)"\s*:\s*")[^"]+(")', re.IGNORECASE), r'\1[REDACTED_MODEL]\2'),
    (re.compile(r'("messages"\s*:\s*)\[[\s\S]*', re.IGNORECASE), r'\1[REDACTED_MESSAGES]'),
    (re.compile(r'((?:api[_-]?key|llm_api_key|openai_api_key)\s*[=:]\s*)[^\s,;&}]+', re.IGNORECASE), r'\1[REDACTED_SECRET]'),
    (re.compile(r'((?:password)\s*[=:]\s*)[^\s,;&}]+', re.IGNORECASE), r'\1[REDACTED_SECRET]'),
    (re.compile(r'((?:llm_base_url|base_url)\s*[=:]\s*)https?://[^\s,;&}]+', re.IGNORECASE), r'\1[REDACTED_URL]'),
    (re.compile(r'https?://[^\s,;&}]+', re.IGNORECASE), '[REDACTED_URL]'),
    (re.compile(r'((?:llm_model|model)\s*[=:]\s*)[^\s,;&}]+', re.IGNORECASE), r'\1[REDACTED_MODEL]'),
    (re.compile(r'messages\s*[=:]\s*\[[\s\S]*', re.IGNORECASE), 'messages=[REDACTED_MESSAGES]'),
]


def _env_bool(name: str) -> bool:
    return os.getenv(name, '').strip().lower() in {'1', 'true', 'yes', 'on'}


def _base_url() -> str:
    return os.getenv('BASE_URL', DEFAULT_BASE_URL).rstrip('/')


def _continuous_chapters_enabled() -> bool:
    return _env_bool('E2E_CONTINUOUS_CHAPTERS')


def _timeout_seconds() -> float:
    raw_value = os.getenv('E2E_TIMEOUT_SECONDS', '').strip()
    if not raw_value:
        return DEFAULT_TIMEOUT_SECONDS
    try:
        timeout = float(raw_value)
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS
    if timeout <= 0:
        return DEFAULT_TIMEOUT_SECONDS
    return timeout


def _cleanup_command() -> str:
    return (
        f'cd {shlex.quote(str(BACKEND_DIR))} && '
        f'PYTHONIOENCODING=utf-8 {shlex.quote(sys.executable)} scripts/cleanup_e2e_data.py --confirm'
    )


def _runbook(mode: str, base_url: str) -> dict:
    if mode == 'real-llm':
        required_backend_env = ['LLM_MOCK=false', 'LLM_BASE_URL=<provider-url>', 'LLM_API_KEY=<secret>', 'LLM_MODEL=<model>']
        client_env = [f'BASE_URL={base_url}', 'E2E_REAL_LLM=1']
    else:
        required_backend_env = ['LLM_MOCK=true']
        client_env = [f'BASE_URL={base_url}', 'E2E_REAL_LLM unset or false']
    return {
        'required_backend_env': required_backend_env,
        'client_env': client_env,
        'optional_client_env': ['E2E_TIMEOUT_SECONDS=<seconds> for slow backends', 'E2E_CONTINUOUS_CHAPTERS=1 for two-chapter continuity smoke'],
        'cleanup': 'Run cleanup_command after smoke runs to remove e2e-* users and worlds.',
    }


def _next_action(summary: dict) -> str | None:
    error = summary.get('error')
    response_body = summary.get('response_body') or ''
    if error == 'BACKEND_LLM_MOCK_DISABLED':
        return 'Restart the backend with LLM_MOCK=true, then rerun mock smoke.'
    if error == 'BACKEND_LLM_MOCK_ENABLED':
        return 'Restart the backend with real LLM_* settings and LLM_MOCK=false, then rerun with E2E_REAL_LLM=1.'
    if error == 'MIGRATION_NOT_UP_TO_DATE':
        return 'Run alembic upgrade head from backend/, restart the backend, then rerun smoke.'
    if error == 'REQUEST_TIMEOUT':
        return 'Increase E2E_TIMEOUT_SECONDS for the smoke client or inspect backend/provider latency, then rerun smoke.'
    if 'MODEL_AUTH_FAILED' in response_body:
        return 'Check LLM_API_KEY permissions and provider access, restart the backend, then rerun real-LLM smoke.'
    if 'MODEL_RATE_LIMITED' in response_body:
        return 'Wait for provider quota or queue capacity, then rerun real-LLM smoke.'
    if summary.get('failed_step') == 'register':
        return 'Inspect register status_code/response_body; only explicit duplicate-email errors should fall back to login.'
    return None


def _finalize_summary(summary: dict) -> dict:
    action = _next_action(summary)
    if action:
        summary['next_action'] = action
    return summary


def _default_email() -> str:
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    return f'e2e-smoke-{stamp}-{uuid4().hex[:8]}@example.com'


def _redact_response_body(text: str) -> str:
    redacted = text
    for pattern, replacement in _REDACTION_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def _response_body_snippet(response: httpx.Response) -> str:
    return _redact_response_body(response.text)[:MAX_RESPONSE_BODY_CHARS]


def _json_response(response: httpx.Response) -> dict:
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError('Expected JSON object response')
    return payload


def _is_duplicate_email_register_response(response: httpx.Response) -> bool:
    if response.status_code not in {400, 409}:
        return False
    try:
        payload = response.json()
    except ValueError:
        return False
    if not isinstance(payload, dict):
        return False
    detail = payload.get('detail')
    return isinstance(detail, str) and (detail == 'EMAIL_ALREADY_REGISTERED' or 'already registered' in detail.lower())


def _mark_request_error(summary: dict, step: str, exc: httpx.RequestError) -> None:
    summary['failed_step'] = step
    summary['error'] = 'REQUEST_TIMEOUT' if isinstance(exc, httpx.TimeoutException) else str(exc)


def _step_json(summary: dict, step: str, request_call) -> dict:
    try:
        response = request_call()
        response.raise_for_status()
        try:
            payload = response.json()
        except ValueError:
            summary['failed_step'] = step
            summary['error'] = 'INVALID_JSON_RESPONSE'
            summary['status_code'] = response.status_code
            summary['response_body'] = _response_body_snippet(response)
            return {}
        if not isinstance(payload, dict):
            summary['failed_step'] = step
            summary['error'] = 'INVALID_JSON_RESPONSE_TYPE'
            summary['status_code'] = response.status_code
            summary['response_body'] = _response_body_snippet(response)
            return {}
        return payload
    except httpx.HTTPStatusError as exc:
        summary['failed_step'] = step
        summary['error'] = str(exc)
        summary['status_code'] = exc.response.status_code
        summary['response_body'] = _response_body_snippet(exc.response)
        return {}
    except httpx.RequestError as exc:
        _mark_request_error(summary, step, exc)
        return {}
    except Exception as exc:
        summary['failed_step'] = step
        summary['error'] = str(exc)
        return {}


def _has_failed(summary: dict) -> bool:
    return 'failed_step' in summary


def _require_fields(summary: dict, step: str, payload: dict, fields: list[str]) -> bool:
    missing = [field for field in fields if field not in payload]
    if not missing:
        return True
    summary['failed_step'] = step
    summary['error'] = 'MISSING_REQUIRED_FIELDS'
    summary['missing_fields'] = missing
    return False


def _require_paths(summary: dict, step: str, payload: dict, paths: list[str]) -> bool:
    missing = []
    for path in paths:
        current = payload
        for part in path.split('.'):
            if not isinstance(current, dict) or part not in current:
                missing.append(path)
                break
            current = current[part]
    if not missing:
        return True
    summary['failed_step'] = step
    summary['error'] = 'MISSING_REQUIRED_FIELDS'
    summary['missing_fields'] = missing
    return False


def _require_bool_paths(summary: dict, step: str, payload: dict, paths: list[str]) -> bool:
    invalid = []
    for path in paths:
        current = payload
        for part in path.split('.'):
            if not isinstance(current, dict) or part not in current:
                current = None
                break
            current = current[part]
        if not isinstance(current, bool):
            invalid.append(path)
    if not invalid:
        return True
    summary['failed_step'] = step
    summary['error'] = 'INVALID_FIELD_TYPES'
    summary['invalid_fields'] = invalid
    return False


def _require_list(summary: dict, step: str, payload: dict, field: str) -> bool:
    value = payload.get(field)
    if isinstance(value, list):
        return True
    summary['failed_step'] = step
    summary['error'] = 'INVALID_FIELD_TYPES'
    summary['invalid_fields'] = [field]
    return False


def _require_optional_dict(summary: dict, step: str, payload: dict, field: str) -> bool:
    if field not in payload or isinstance(payload.get(field), dict):
        return True
    summary['failed_step'] = step
    summary['error'] = 'INVALID_FIELD_TYPES'
    summary['invalid_fields'] = [field]
    return False


def _require_int_fields(summary: dict, step: str, payload: dict, fields: list[str]) -> bool:
    invalid = [field for field in fields if not isinstance(payload.get(field), int) or isinstance(payload.get(field), bool)]
    if not invalid:
        return True
    summary['failed_step'] = step
    summary['error'] = 'INVALID_FIELD_TYPES'
    summary['invalid_fields'] = invalid
    return False


def _require_bool_fields(summary: dict, step: str, payload: dict, fields: list[str]) -> bool:
    invalid = [field for field in fields if not isinstance(payload.get(field), bool)]
    if not invalid:
        return True
    summary['failed_step'] = step
    summary['error'] = 'INVALID_FIELD_TYPES'
    summary['invalid_fields'] = invalid
    return False


def _require_string_fields(summary: dict, step: str, payload: dict, fields: list[str]) -> bool:
    invalid = [field for field in fields if not isinstance(payload.get(field), str) or not payload.get(field)]
    if not invalid:
        return True
    summary['failed_step'] = step
    summary['error'] = 'INVALID_FIELD_TYPES'
    summary['invalid_fields'] = invalid
    return False


def _require_int_path(summary: dict, step: str, payload: dict, path: str) -> bool:
    current = payload
    for part in path.split('.'):
        if not isinstance(current, dict) or part not in current:
            summary['failed_step'] = step
            summary['error'] = 'MISSING_REQUIRED_FIELDS'
            summary['missing_fields'] = [path]
            return False
        current = current[part]
    if isinstance(current, int) and not isinstance(current, bool):
        return True
    summary['failed_step'] = step
    summary['error'] = 'INVALID_FIELD_TYPES'
    summary['invalid_fields'] = [path]
    return False


def _require_non_negative_int_path(summary: dict, step: str, payload: dict, path: str) -> bool:
    if not _require_int_path(summary, step, payload, path):
        return False
    current = payload
    for part in path.split('.'):
        current = current[part]
    if current >= 0:
        return True
    summary['failed_step'] = step
    summary['error'] = 'INVALID_FIELD_VALUES'
    summary['invalid_fields'] = [path]
    return False


def _require_string_path_in(summary: dict, step: str, payload: dict, path: str, allowed_values: set[str]) -> bool:
    current = payload
    for part in path.split('.'):
        if not isinstance(current, dict) or part not in current:
            summary['failed_step'] = step
            summary['error'] = 'MISSING_REQUIRED_FIELDS'
            summary['missing_fields'] = [path]
            return False
        current = current[part]
    if not isinstance(current, str) or not current:
        summary['failed_step'] = step
        summary['error'] = 'INVALID_FIELD_TYPES'
        summary['invalid_fields'] = [path]
        return False
    if current not in allowed_values:
        summary['failed_step'] = step
        summary['error'] = 'INVALID_FIELD_VALUES'
        summary['invalid_fields'] = [path]
        summary['allowed_values'] = {path: sorted(allowed_values)}
        return False
    return True


def _require_list_of_dicts(summary: dict, step: str, payload: dict, field: str) -> bool:
    value = payload.get(field)
    if isinstance(value, list) and all(isinstance(item, dict) for item in value):
        return True
    summary['failed_step'] = step
    summary['error'] = 'INVALID_FIELD_TYPES'
    summary['invalid_fields'] = [field]
    return False


def _register_or_login(client: httpx.Client, email: str, password: str, summary: dict) -> tuple[dict, str]:
    try:
        response = client.post('/auth/register', json={'email': email, 'password': password})
    except httpx.RequestError as exc:
        _mark_request_error(summary, 'register', exc)
        return {}, 'register'
    if _is_duplicate_email_register_response(response):
        return _step_json(summary, 'login', lambda: client.post('/auth/login', json={'email': email, 'password': password})), 'login'
    return _step_json(summary, 'register', lambda: response), 'register'


def _execution_context_from_prep(prep: dict, goal: str) -> dict:
    return {
        'source': 'next_chapter_prep',
        'source_world_version': prep['world_version'],
        'next_chapter_number': prep['next_chapter_number'],
        'goal': goal,
        'previous_chapter_summary': prep.get('previous_chapter_summary'),
        'recommended_pov': {
            'character_id': prep.get('recommended_pov_character_id'),
            'name': prep.get('recommended_pov_character_name'),
        },
        'source_signals': prep.get('source_signals') or [],
        'priority_characters': prep.get('priority_characters') or [],
        'priority_foreshadows': prep.get('priority_foreshadows') or [],
        'progression_hints': prep.get('progression_hints') or [],
        'continuity_warnings': prep.get('continuity_warnings') or [],
        'recent_events': [
            {
                'id': event.get('id'),
                'event_type': event.get('event_type'),
                'world_version_before': event.get('world_version_before'),
                'world_version_after': event.get('world_version_after'),
                'created_at': event.get('created_at'),
            }
            for event in prep.get('recent_events') or []
        ],
        'material_references': prep.get('material_references') or [],
    }


def run_smoke(client: httpx.Client | None = None, email: str | None = None, password: str | None = None) -> dict:
    owns_client = client is None
    base_url = _base_url()
    timeout_seconds = _timeout_seconds()
    if client is None:
        client = httpx.Client(base_url=base_url, timeout=timeout_seconds)
    else:
        base_url = str(client.base_url).rstrip('/')

    mode = 'real-llm' if _env_bool('E2E_REAL_LLM') else 'mock'
    email = email or os.getenv('E2E_EMAIL') or _default_email()
    password = password or os.getenv('E2E_PASSWORD') or DEFAULT_PASSWORD
    summary = {
        'ok': False,
        'mode': mode,
        'base_url': base_url,
        'email': email,
        'timeout_seconds': timeout_seconds,
        'requires_backend_llm_mock': mode == 'mock',
        'cleanup_command': _cleanup_command(),
        'runbook': _runbook(mode, base_url),
        'checks': {},
    }

    try:
        health = _step_json(summary, 'health', lambda: client.get('/health'))
        if _has_failed(summary):
            return _finalize_summary(summary)
        if not _require_paths(summary, 'health', health, ['status', 'migration.up_to_date', 'llm.mock']):
            return _finalize_summary(summary)
        if not _require_bool_paths(summary, 'health', health, ['migration.up_to_date', 'llm.mock']):
            return _finalize_summary(summary)
        backend_llm_mock = (health.get('llm') or {}).get('mock')
        summary['checks']['health'] = {
            'status': health.get('status'),
            'migration_up_to_date': (health.get('migration') or {}).get('up_to_date'),
            'llm_mock': backend_llm_mock,
        }
        if summary['checks']['health']['status'] != 'ok':
            summary['failed_step'] = 'health'
            summary['error'] = 'HEALTH_STATUS_NOT_OK'
            return _finalize_summary(summary)
        if summary['checks']['health']['migration_up_to_date'] is False:
            summary['failed_step'] = 'health'
            summary['error'] = 'MIGRATION_NOT_UP_TO_DATE'
            return _finalize_summary(summary)
        if mode == 'mock' and backend_llm_mock is False:
            summary['failed_step'] = 'health'
            summary['error'] = 'BACKEND_LLM_MOCK_DISABLED'
            return _finalize_summary(summary)
        if mode == 'real-llm' and backend_llm_mock is True:
            summary['failed_step'] = 'health'
            summary['error'] = 'BACKEND_LLM_MOCK_ENABLED'
            return _finalize_summary(summary)

        auth_payload, auth_step = _register_or_login(client, email, password, summary)
        if _has_failed(summary):
            return _finalize_summary(summary)
        if not _require_fields(summary, auth_step, auth_payload, ['access_token']):
            return _finalize_summary(summary)
        if not _require_string_fields(summary, auth_step, auth_payload, ['access_token']):
            return _finalize_summary(summary)
        if not _require_optional_dict(summary, auth_step, auth_payload, 'user'):
            return _finalize_summary(summary)
        token = auth_payload['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        summary['checks'][auth_step] = {'user_id': (auth_payload.get('user') or {}).get('id')}

        world = _step_json(summary, 'create_world', lambda: client.post('/worlds/from-template', headers=headers))
        if _has_failed(summary):
            return _finalize_summary(summary)
        if not _require_fields(summary, 'create_world', world, ['id', 'world_version']):
            return _finalize_summary(summary)
        if not _require_int_fields(summary, 'create_world', world, ['id', 'world_version']):
            return _finalize_summary(summary)
        world_id = world['id']
        initial_world_version = world.get('world_version')
        summary['world_id'] = world_id
        summary['checks']['create_world'] = {'world_version': initial_world_version}

        draft = _step_json(
            summary,
            'draft',
            lambda: client.post(
                f'/worlds/{world_id}/chapters/draft',
                json={'chapter_goal': 'E2E smoke: advance the sample world by one coherent chapter.'},
                headers=headers,
            ),
        )
        if _has_failed(summary):
            return _finalize_summary(summary)
        if not _require_fields(summary, 'draft', draft, ['chapter_id', 'draft_version']):
            return _finalize_summary(summary)
        if not _require_int_fields(summary, 'draft', draft, ['chapter_id', 'draft_version']):
            return _finalize_summary(summary)
        chapter_id = draft['chapter_id']
        draft_version = draft['draft_version']
        summary['chapter_id'] = chapter_id
        summary['draft_id'] = draft.get('draft_id')
        summary['checks']['draft'] = {'draft_version': draft_version}

        preview = _step_json(summary, 'approval_preview', lambda: client.get(f'/chapters/{chapter_id}/approval-preview', headers=headers))
        if _has_failed(summary):
            return _finalize_summary(summary)
        if not _require_fields(summary, 'approval_preview', preview, ['version_conflict']):
            return _finalize_summary(summary)
        if not _require_bool_fields(summary, 'approval_preview', preview, ['version_conflict']):
            return _finalize_summary(summary)
        if not _require_list_of_dicts(summary, 'approval_preview', preview, 'character_changes'):
            return _finalize_summary(summary)
        if not _require_list_of_dicts(summary, 'approval_preview', preview, 'foreshadow_changes'):
            return _finalize_summary(summary)
        preview_blocked = preview.get('version_conflict') is True
        character_change_count = len(preview.get('character_changes') or [])
        foreshadow_change_count = len(preview.get('foreshadow_changes') or [])
        proposed_change_count = character_change_count + foreshadow_change_count
        summary['checks']['approval_preview'] = {
            'version_conflict': preview.get('version_conflict'),
            'character_changes': character_change_count,
            'foreshadow_changes': foreshadow_change_count,
            'proposed_change_count': proposed_change_count,
            'blocked': preview_blocked,
        }
        if preview_blocked:
            summary['failed_step'] = 'approval_preview'
            summary['error'] = 'APPROVAL_PREVIEW_BLOCKED'
            return _finalize_summary(summary)
        if proposed_change_count == 0:
            summary['failed_step'] = 'approval_preview'
            summary['error'] = 'NO_PROPOSED_PROJECTION_CHANGES'
            return _finalize_summary(summary)

        readiness = _step_json(summary, 'approval_readiness', lambda: client.get(f'/chapters/{chapter_id}/approval-readiness', headers=headers))
        if _has_failed(summary):
            return _finalize_summary(summary)
        if not _require_fields(summary, 'approval_readiness', readiness, ['ready', 'status']):
            return _finalize_summary(summary)
        if not _require_bool_fields(summary, 'approval_readiness', readiness, ['ready']):
            return _finalize_summary(summary)
        if not _require_string_path_in(summary, 'approval_readiness', readiness, 'status', READINESS_STATUSES):
            return _finalize_summary(summary)
        if not _require_list(summary, 'approval_readiness', readiness, 'blocking_reasons'):
            return _finalize_summary(summary)
        if not _require_list(summary, 'approval_readiness', readiness, 'warnings'):
            return _finalize_summary(summary)
        readiness_blocking_reasons = readiness.get('blocking_reasons') or []
        readiness_blocked = readiness.get('status') == 'blocked' or bool(readiness_blocking_reasons)
        summary['checks']['approval_readiness'] = {
            'ready': readiness.get('ready'),
            'status': readiness.get('status'),
            'blocking_reasons': readiness_blocking_reasons,
            'warnings': readiness.get('warnings') or [],
            'blocked': readiness_blocked,
        }
        if readiness_blocked:
            summary['failed_step'] = 'approval_readiness'
            summary['error'] = 'APPROVAL_READINESS_BLOCKED'
            return _finalize_summary(summary)

        consistency = _step_json(
            summary,
            'approval_consistency',
            lambda: client.post(f'/chapters/{chapter_id}/approval-consistency', json={'draft_version': draft_version}, headers=headers),
        )
        if _has_failed(summary):
            return _finalize_summary(summary)
        if not _require_paths(summary, 'approval_consistency', consistency, ['consistency_summary.status']):
            return _finalize_summary(summary)
        if not _require_string_path_in(summary, 'approval_consistency', consistency, 'consistency_summary.status', CONSISTENCY_STATUSES):
            return _finalize_summary(summary)
        if not _require_non_negative_int_path(summary, 'approval_consistency', consistency, 'consistency_summary.blocking_count'):
            return _finalize_summary(summary)
        if not _require_fields(summary, 'approval_consistency', consistency, ['consistency_warnings']):
            return _finalize_summary(summary)
        if not _require_list_of_dicts(summary, 'approval_consistency', consistency, 'consistency_warnings'):
            return _finalize_summary(summary)
        consistency_summary = consistency.get('consistency_summary') or {}
        consistency_warnings = consistency.get('consistency_warnings') or []
        consistency_blocked = consistency_summary.get('status') == 'blocked' or (consistency_summary.get('blocking_count') or 0) > 0
        summary['checks']['approval_consistency'] = {
            **consistency_summary,
            'blocked': consistency_blocked,
            'warnings': consistency_warnings,
        }
        if consistency_blocked:
            summary['failed_step'] = 'approval_consistency'
            summary['error'] = 'APPROVAL_CONSISTENCY_BLOCKED'
            return _finalize_summary(summary)

        approve_payload = {'draft_version': draft_version}
        if _continuous_chapters_enabled():
            approve_payload['selected_foreshadow_change_indexes'] = []
        approved = _step_json(
            summary,
            'approve',
            lambda: client.post(
                f'/chapters/{chapter_id}/approve',
                json=approve_payload,
                headers=headers,
            ),
        )
        if _has_failed(summary):
            return _finalize_summary(summary)
        if not _require_fields(summary, 'approve', approved, ['status', 'approved_version']):
            return _finalize_summary(summary)
        if not _require_int_fields(summary, 'approve', approved, ['approved_version']):
            return _finalize_summary(summary)
        approved_version = approved.get('approved_version')
        expected_world_version_after = initial_world_version + 1 if isinstance(initial_world_version, int) else None
        summary['checks']['approve'] = {
            'status': approved.get('status'),
            'approved_version': approved_version,
            'expected_world_version_after': expected_world_version_after,
            'world_version_validation_source': 'overview',
        }
        if approved.get('status') != 'approved':
            summary['failed_step'] = 'approve'
            summary['error'] = 'APPROVAL_STATUS_NOT_APPROVED'
            return _finalize_summary(summary)

        overview = _step_json(summary, 'overview', lambda: client.get(f'/worlds/{world_id}/overview', headers=headers))
        if _has_failed(summary):
            return _finalize_summary(summary)
        if not _require_fields(summary, 'overview', overview, ['world_version', 'approved_chapter_count', 'characters', 'foreshadows']):
            return _finalize_summary(summary)
        if not _require_int_fields(summary, 'overview', overview, ['world_version', 'approved_chapter_count']):
            return _finalize_summary(summary)
        if not _require_list_of_dicts(summary, 'overview', overview, 'characters'):
            return _finalize_summary(summary)
        if not _require_list_of_dicts(summary, 'overview', overview, 'foreshadows'):
            return _finalize_summary(summary)
        overview_world_version = overview.get('world_version')
        approved_chapter_count = overview.get('approved_chapter_count')
        expected_approved_chapter_count = 1
        character_count = len(overview.get('characters') or [])
        foreshadow_count = len(overview.get('foreshadows') or [])
        overview_world_version_incremented = overview_world_version == expected_world_version_after
        overview_approved_chapter_count_incremented = approved_chapter_count >= expected_approved_chapter_count
        summary['checks']['overview'] = {
            'world_version': overview_world_version,
            'approved_chapter_count': approved_chapter_count,
            'expected_world_version': expected_world_version_after,
            'expected_approved_chapter_count': expected_approved_chapter_count,
            'world_version_incremented': overview_world_version_incremented,
            'world_version_matches_approval': overview_world_version_incremented,
            'approved_chapter_count_incremented': overview_approved_chapter_count_incremented,
            'character_count': character_count,
            'foreshadow_count': foreshadow_count,
        }
        if not overview_world_version_incremented:
            summary['failed_step'] = 'overview'
            summary['error'] = 'WORLD_VERSION_NOT_INCREMENTED'
            return _finalize_summary(summary)
        if not overview_approved_chapter_count_incremented:
            summary['failed_step'] = 'overview'
            summary['error'] = 'OVERVIEW_APPROVED_CHAPTER_MISSING'
            return _finalize_summary(summary)
        empty_projection_fields = []
        if character_count == 0:
            empty_projection_fields.append('characters')
        if foreshadow_count == 0:
            empty_projection_fields.append('foreshadows')
        if empty_projection_fields:
            summary['failed_step'] = 'overview'
            summary['error'] = 'OVERVIEW_PROJECTION_EMPTY'
            summary['invalid_fields'] = empty_projection_fields
            return _finalize_summary(summary)

        continuous_ok = True
        if _continuous_chapters_enabled():
            canon = _step_json(
                summary,
                'continuous_canon_update',
                lambda: client.put(
                    f'/worlds/{world_id}/canon',
                    json={'truth_canon': SECOND_CHAPTER_CANON, 'edit_reason': 'E2E smoke chapter 2 continuity setup'},
                    headers=headers,
                ),
            )
            if _has_failed(summary):
                return _finalize_summary(summary)
            if not _require_fields(summary, 'continuous_canon_update', canon, ['world_version']):
                return _finalize_summary(summary)
            if not _require_int_fields(summary, 'continuous_canon_update', canon, ['world_version']):
                return _finalize_summary(summary)
            canon_world_version = canon['world_version']
            expected_canon_world_version = overview_world_version + 1
            if canon_world_version != expected_canon_world_version:
                summary['failed_step'] = 'continuous_canon_update'
                summary['error'] = 'WORLD_VERSION_NOT_INCREMENTED'
                return _finalize_summary(summary)

            prep = _step_json(summary, 'next_chapter_prep', lambda: client.get(f'/worlds/{world_id}/next-chapter-prep', headers=headers))
            if _has_failed(summary):
                return _finalize_summary(summary)
            if not _require_fields(
                summary,
                'next_chapter_prep',
                prep,
                ['world_version', 'next_chapter_number', 'previous_chapter_summary'],
            ):
                return _finalize_summary(summary)
            if not _require_int_fields(summary, 'next_chapter_prep', prep, ['world_version', 'next_chapter_number']):
                return _finalize_summary(summary)
            for field in ['source_signals', 'priority_characters', 'priority_foreshadows', 'progression_hints', 'continuity_warnings', 'recent_events', 'material_references']:
                if not _require_list(summary, 'next_chapter_prep', prep, field):
                    return _finalize_summary(summary)
            if prep.get('world_version') != canon_world_version:
                summary['failed_step'] = 'next_chapter_prep'
                summary['error'] = 'WORLD_VERSION_NOT_INCREMENTED'
                return _finalize_summary(summary)
            if not prep.get('previous_chapter_summary'):
                summary['failed_step'] = 'next_chapter_prep'
                summary['error'] = 'PREVIOUS_CHAPTER_SUMMARY_MISSING'
                return _finalize_summary(summary)
            priority_foreshadow_count = len(prep.get('priority_foreshadows') or [])
            if priority_foreshadow_count == 0:
                summary['failed_step'] = 'next_chapter_prep'
                summary['error'] = 'PRIORITY_FORESHADOWS_MISSING'
                return _finalize_summary(summary)

            second_context = _execution_context_from_prep(prep, SECOND_CHAPTER_GOAL)
            second_draft = _step_json(
                summary,
                'second_draft',
                lambda: client.post(
                    f'/worlds/{world_id}/chapters/draft',
                    json={'chapter_goal': SECOND_CHAPTER_GOAL, 'execution_context': second_context},
                    headers=headers,
                ),
            )
            if _has_failed(summary):
                return _finalize_summary(summary)
            if not _require_fields(summary, 'second_draft', second_draft, ['chapter_id', 'draft_version', 'source_world_version', 'execution_context']):
                return _finalize_summary(summary)
            if not _require_int_fields(summary, 'second_draft', second_draft, ['chapter_id', 'draft_version', 'source_world_version']):
                return _finalize_summary(summary)
            if not _require_optional_dict(summary, 'second_draft', second_draft, 'execution_context'):
                return _finalize_summary(summary)
            second_execution_context = second_draft.get('execution_context') or {}
            if second_draft.get('source_world_version') != canon_world_version:
                summary['failed_step'] = 'second_draft'
                summary['error'] = 'WORLD_VERSION_MISMATCH'
                return _finalize_summary(summary)
            if second_execution_context.get('source_world_version') != canon_world_version or not second_execution_context.get('previous_chapter_summary'):
                summary['failed_step'] = 'second_draft'
                summary['error'] = 'EXECUTION_CONTEXT_NOT_CURRENT'
                return _finalize_summary(summary)
            if not second_execution_context.get('priority_foreshadows'):
                summary['failed_step'] = 'second_draft'
                summary['error'] = 'EXECUTION_CONTEXT_FORESHADOWS_MISSING'
                return _finalize_summary(summary)

            stale_canon = _step_json(
                summary,
                'stale_canon_update',
                lambda: client.put(
                    f'/worlds/{world_id}/canon',
                    json={'truth_canon': STALE_DRAFT_CANON, 'edit_reason': 'E2E smoke stale draft approval setup'},
                    headers=headers,
                ),
            )
            if _has_failed(summary):
                return _finalize_summary(summary)
            if not _require_fields(summary, 'stale_canon_update', stale_canon, ['world_version']):
                return _finalize_summary(summary)
            if not _require_int_fields(summary, 'stale_canon_update', stale_canon, ['world_version']):
                return _finalize_summary(summary)
            stale_world_version = stale_canon['world_version']

            try:
                stale_response = client.post(
                    f"/chapters/{second_draft['chapter_id']}/approve",
                    json={'draft_version': second_draft['draft_version']},
                    headers=headers,
                )
            except httpx.RequestError as exc:
                _mark_request_error(summary, 'stale_draft_approval', exc)
                return _finalize_summary(summary)
            stale_draft_rejected = stale_response.status_code == 409 and 'WORLD_VERSION_MISMATCH' in stale_response.text
            if not stale_draft_rejected:
                summary['failed_step'] = 'stale_draft_approval'
                summary['error'] = 'STALE_DRAFT_APPROVAL_NOT_REJECTED'
                summary['status_code'] = stale_response.status_code
                summary['response_body'] = _response_body_snippet(stale_response)
                return _finalize_summary(summary)

            fresh_prep = _step_json(summary, 'fresh_next_chapter_prep', lambda: client.get(f'/worlds/{world_id}/next-chapter-prep', headers=headers))
            if _has_failed(summary):
                return _finalize_summary(summary)
            if not _require_fields(
                summary,
                'fresh_next_chapter_prep',
                fresh_prep,
                ['world_version', 'next_chapter_number', 'previous_chapter_summary'],
            ):
                return _finalize_summary(summary)
            if not _require_int_fields(summary, 'fresh_next_chapter_prep', fresh_prep, ['world_version', 'next_chapter_number']):
                return _finalize_summary(summary)
            for field in ['source_signals', 'priority_characters', 'priority_foreshadows', 'progression_hints', 'continuity_warnings', 'recent_events', 'material_references']:
                if not _require_list(summary, 'fresh_next_chapter_prep', fresh_prep, field):
                    return _finalize_summary(summary)
            if fresh_prep.get('world_version') != stale_world_version:
                summary['failed_step'] = 'fresh_next_chapter_prep'
                summary['error'] = 'WORLD_VERSION_NOT_INCREMENTED'
                return _finalize_summary(summary)

            fresh_context = _execution_context_from_prep(fresh_prep, FRESH_SECOND_CHAPTER_GOAL)
            fresh_draft = _step_json(
                summary,
                'fresh_second_draft',
                lambda: client.post(
                    f'/worlds/{world_id}/chapters/draft',
                    json={'chapter_goal': FRESH_SECOND_CHAPTER_GOAL, 'execution_context': fresh_context},
                    headers=headers,
                ),
            )
            if _has_failed(summary):
                return _finalize_summary(summary)
            if not _require_fields(summary, 'fresh_second_draft', fresh_draft, ['chapter_id', 'draft_version', 'source_world_version', 'execution_context']):
                return _finalize_summary(summary)
            if not _require_int_fields(summary, 'fresh_second_draft', fresh_draft, ['chapter_id', 'draft_version', 'source_world_version']):
                return _finalize_summary(summary)
            if not _require_optional_dict(summary, 'fresh_second_draft', fresh_draft, 'execution_context'):
                return _finalize_summary(summary)
            fresh_chapter_id = fresh_draft['chapter_id']
            fresh_draft_version = fresh_draft['draft_version']
            fresh_draft_source_world_version = fresh_draft['source_world_version']
            fresh_execution_context = fresh_draft.get('execution_context') or {}
            if fresh_draft_source_world_version != stale_world_version:
                summary['failed_step'] = 'fresh_second_draft'
                summary['error'] = 'WORLD_VERSION_MISMATCH'
                return _finalize_summary(summary)
            if fresh_execution_context.get('source_world_version') != stale_world_version or not fresh_execution_context.get('previous_chapter_summary'):
                summary['failed_step'] = 'fresh_second_draft'
                summary['error'] = 'EXECUTION_CONTEXT_NOT_CURRENT'
                return _finalize_summary(summary)
            if not fresh_execution_context.get('priority_foreshadows'):
                summary['failed_step'] = 'fresh_second_draft'
                summary['error'] = 'EXECUTION_CONTEXT_FORESHADOWS_MISSING'
                return _finalize_summary(summary)

            second_preview = _step_json(summary, 'second_approval_preview', lambda: client.get(f'/chapters/{fresh_chapter_id}/approval-preview', headers=headers))
            if _has_failed(summary):
                return _finalize_summary(summary)
            if not _require_fields(summary, 'second_approval_preview', second_preview, ['version_conflict']):
                return _finalize_summary(summary)
            if not _require_bool_fields(summary, 'second_approval_preview', second_preview, ['version_conflict']):
                return _finalize_summary(summary)
            if not _require_list_of_dicts(summary, 'second_approval_preview', second_preview, 'character_changes'):
                return _finalize_summary(summary)
            if not _require_list_of_dicts(summary, 'second_approval_preview', second_preview, 'foreshadow_changes'):
                return _finalize_summary(summary)
            second_proposed_change_count = len(second_preview.get('character_changes') or []) + len(second_preview.get('foreshadow_changes') or [])
            if second_preview.get('version_conflict') is True:
                summary['failed_step'] = 'second_approval_preview'
                summary['error'] = 'APPROVAL_PREVIEW_BLOCKED'
                return _finalize_summary(summary)
            if second_proposed_change_count == 0:
                summary['failed_step'] = 'second_approval_preview'
                summary['error'] = 'NO_PROPOSED_PROJECTION_CHANGES'
                return _finalize_summary(summary)

            second_readiness = _step_json(summary, 'second_approval_readiness', lambda: client.get(f'/chapters/{fresh_chapter_id}/approval-readiness', headers=headers))
            if _has_failed(summary):
                return _finalize_summary(summary)
            if not _require_fields(summary, 'second_approval_readiness', second_readiness, ['ready', 'status']):
                return _finalize_summary(summary)
            if not _require_bool_fields(summary, 'second_approval_readiness', second_readiness, ['ready']):
                return _finalize_summary(summary)
            if not _require_string_path_in(summary, 'second_approval_readiness', second_readiness, 'status', READINESS_STATUSES):
                return _finalize_summary(summary)
            if not _require_list(summary, 'second_approval_readiness', second_readiness, 'blocking_reasons'):
                return _finalize_summary(summary)
            if not _require_list(summary, 'second_approval_readiness', second_readiness, 'warnings'):
                return _finalize_summary(summary)
            second_readiness_blocked = second_readiness.get('status') == 'blocked' or bool(second_readiness.get('blocking_reasons') or [])
            if second_readiness_blocked:
                summary['failed_step'] = 'second_approval_readiness'
                summary['error'] = 'APPROVAL_READINESS_BLOCKED'
                return _finalize_summary(summary)

            second_consistency = _step_json(
                summary,
                'second_approval_consistency',
                lambda: client.post(f'/chapters/{fresh_chapter_id}/approval-consistency', json={'draft_version': fresh_draft_version}, headers=headers),
            )
            if _has_failed(summary):
                return _finalize_summary(summary)
            if not _require_paths(summary, 'second_approval_consistency', second_consistency, ['consistency_summary.status']):
                return _finalize_summary(summary)
            if not _require_string_path_in(summary, 'second_approval_consistency', second_consistency, 'consistency_summary.status', CONSISTENCY_STATUSES):
                return _finalize_summary(summary)
            if not _require_non_negative_int_path(summary, 'second_approval_consistency', second_consistency, 'consistency_summary.blocking_count'):
                return _finalize_summary(summary)
            if not _require_fields(summary, 'second_approval_consistency', second_consistency, ['consistency_warnings']):
                return _finalize_summary(summary)
            if not _require_list_of_dicts(summary, 'second_approval_consistency', second_consistency, 'consistency_warnings'):
                return _finalize_summary(summary)
            second_consistency_summary = second_consistency.get('consistency_summary') or {}
            second_consistency_blocked = second_consistency_summary.get('status') == 'blocked' or (second_consistency_summary.get('blocking_count') or 0) > 0
            if second_consistency_blocked:
                summary['failed_step'] = 'second_approval_consistency'
                summary['error'] = 'APPROVAL_CONSISTENCY_BLOCKED'
                return _finalize_summary(summary)

            second_approved = _step_json(
                summary,
                'second_approve',
                lambda: client.post(f'/chapters/{fresh_chapter_id}/approve', json={'draft_version': fresh_draft_version}, headers=headers),
            )
            if _has_failed(summary):
                return _finalize_summary(summary)
            if not _require_fields(summary, 'second_approve', second_approved, ['status', 'approved_version']):
                return _finalize_summary(summary)
            if not _require_int_fields(summary, 'second_approve', second_approved, ['approved_version']):
                return _finalize_summary(summary)
            if second_approved.get('status') != 'approved':
                summary['failed_step'] = 'second_approve'
                summary['error'] = 'APPROVAL_STATUS_NOT_APPROVED'
                return _finalize_summary(summary)

            second_overview = _step_json(summary, 'second_overview', lambda: client.get(f'/worlds/{world_id}/overview', headers=headers))
            if _has_failed(summary):
                return _finalize_summary(summary)
            if not _require_fields(summary, 'second_overview', second_overview, ['world_version', 'approved_chapter_count', 'characters', 'foreshadows']):
                return _finalize_summary(summary)
            if not _require_int_fields(summary, 'second_overview', second_overview, ['world_version', 'approved_chapter_count']):
                return _finalize_summary(summary)
            if not _require_list_of_dicts(summary, 'second_overview', second_overview, 'characters'):
                return _finalize_summary(summary)
            if not _require_list_of_dicts(summary, 'second_overview', second_overview, 'foreshadows'):
                return _finalize_summary(summary)
            second_world_version_incremented = second_overview.get('world_version') == stale_world_version + 1
            second_chapter_count_incremented = second_overview.get('approved_chapter_count') >= 2
            if not second_world_version_incremented:
                summary['failed_step'] = 'second_overview'
                summary['error'] = 'WORLD_VERSION_NOT_INCREMENTED'
                return _finalize_summary(summary)
            if not second_chapter_count_incremented:
                summary['failed_step'] = 'second_overview'
                summary['error'] = 'OVERVIEW_APPROVED_CHAPTER_MISSING'
                return _finalize_summary(summary)

            summary['checks']['continuous_chapters'] = {
                'enabled': True,
                'canon_world_version': canon_world_version,
                'prep_world_version': prep.get('world_version'),
                'previous_chapter_summary_present': bool(prep.get('previous_chapter_summary')),
                'priority_foreshadow_count': priority_foreshadow_count,
                'stale_draft_rejected': stale_draft_rejected,
                'fresh_draft_source_world_version': fresh_draft_source_world_version,
                'second_chapter_approved': second_approved.get('status') == 'approved',
                'approved_chapter_count_incremented': second_chapter_count_incremented,
            }
            continuous_ok = stale_draft_rejected and second_world_version_incremented and second_chapter_count_incremented
        else:
            summary['checks']['continuous_chapters'] = {'enabled': False}

        events = _step_json(summary, 'events', lambda: client.get(f'/worlds/{world_id}/events', params={'limit': 100}, headers=headers))
        if _has_failed(summary):
            return _finalize_summary(summary)
        if not _require_fields(summary, 'events', events, ['items']):
            return _finalize_summary(summary)
        if not _require_list_of_dicts(summary, 'events', events, 'items'):
            return _finalize_summary(summary)
        if not _require_optional_dict(summary, 'events', events, 'summary'):
            return _finalize_summary(summary)
        event_types = [event.get('event_type') for event in events.get('items', [])]
        chapter_approved_seen = 'chapter_approved' in event_types or 'chapter_approved' in (events.get('summary') or {}).get('event_type_counts', {})
        summary['checks']['events'] = {
            'event_types': event_types,
            'chapter_approved_seen': chapter_approved_seen,
        }
        if not chapter_approved_seen:
            summary['failed_step'] = 'events'
            summary['error'] = 'CHAPTER_APPROVED_EVENT_MISSING'
            return _finalize_summary(summary)

        export = _step_json(summary, 'markdown_export', lambda: client.post(f'/worlds/{world_id}/export/markdown', headers=headers))
        if _has_failed(summary):
            return _finalize_summary(summary)
        if not _require_fields(summary, 'markdown_export', export, ['archive_format', 'archive_encoding', 'archive_base64', 'files_are_inline', 'files']):
            return _finalize_summary(summary)
        if not _require_string_fields(summary, 'markdown_export', export, ['archive_base64']):
            return _finalize_summary(summary)
        if not _require_list_of_dicts(summary, 'markdown_export', export, 'files'):
            return _finalize_summary(summary)
        files = export.get('files') or []
        has_world_md = any(file.get('path') == 'World.md' for file in files)
        summary['checks']['markdown_export'] = {
            'archive_format': export.get('archive_format'),
            'archive_encoding': export.get('archive_encoding'),
            'archive_base64_present': bool(export.get('archive_base64')),
            'files_are_inline': export.get('files_are_inline'),
            'file_count': len(files),
            'has_world_md': has_world_md,
        }
        invalid_export_fields = []
        if export.get('archive_format') != 'zip':
            invalid_export_fields.append('archive_format')
        if export.get('archive_encoding') != 'base64':
            invalid_export_fields.append('archive_encoding')
        if export.get('files_are_inline') is not True:
            invalid_export_fields.append('files_are_inline')
        if not export.get('archive_base64'):
            invalid_export_fields.append('archive_base64')
        if not has_world_md:
            invalid_export_fields.append('files.World.md')
        if invalid_export_fields:
            summary['failed_step'] = 'markdown_export'
            summary['error'] = 'MARKDOWN_EXPORT_INVALID_ARCHIVE'
            summary['invalid_fields'] = invalid_export_fields
            return _finalize_summary(summary)

        summary['ok'] = all(
            [
                health.get('status') == 'ok',
                not preview_blocked,
                proposed_change_count > 0,
                not readiness_blocked,
                not consistency_blocked,
                approved.get('status') == 'approved',
                overview_world_version_incremented,
                overview_approved_chapter_count_incremented,
                character_count > 0,
                foreshadow_count > 0,
                continuous_ok,
                chapter_approved_seen,
                export.get('archive_format') == 'zip',
                export.get('archive_encoding') == 'base64',
                export.get('files_are_inline') is True,
                bool(export.get('archive_base64')),
                has_world_md,
            ]
        )
        return _finalize_summary(summary)
    finally:
        if owns_client:
            client.close()


def main() -> int:
    try:
        summary = run_smoke()
    except Exception as exc:
        summary = {
            'ok': False,
            'mode': 'real-llm' if _env_bool('E2E_REAL_LLM') else 'mock',
            'base_url': _base_url(),
            'error': str(exc),
        }
    if 'runbook' not in summary:
        summary['runbook'] = _runbook(summary.get('mode', 'mock'), summary.get('base_url', _base_url()))
        summary['cleanup_command'] = _cleanup_command()
    summary = _finalize_summary(summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary.get('ok') else 1


if __name__ == '__main__':
    raise SystemExit(main())
