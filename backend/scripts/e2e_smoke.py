#!/usr/bin/env python
import json
import os
import re
from datetime import datetime, timezone
from uuid import uuid4

import httpx

DEFAULT_BASE_URL = 'http://localhost:8000'
DEFAULT_PASSWORD = 'strongpass123'
DEFAULT_TIMEOUT_SECONDS = 60.0
MAX_RESPONSE_BODY_CHARS = 1000

_REDACTION_PATTERNS = [
    (re.compile(r'Authorization\s*:\s*Bearer\s+[^\s,;]+', re.IGNORECASE), 'Authorization: Bearer [REDACTED_SECRET]'),
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
        summary['failed_step'] = step
        summary['error'] = str(exc)
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


def _require_list(summary: dict, step: str, payload: dict, field: str) -> bool:
    value = payload.get(field)
    if isinstance(value, list):
        return True
    summary['failed_step'] = step
    summary['error'] = 'INVALID_FIELD_TYPES'
    summary['invalid_fields'] = [field]
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
        summary['failed_step'] = 'register'
        summary['error'] = str(exc)
        return {}, 'register'
    if response.status_code == 400:
        return _step_json(summary, 'login', lambda: client.post('/auth/login', json={'email': email, 'password': password})), 'login'
    return _step_json(summary, 'register', lambda: response), 'register'


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
        'cleanup_command': "cd /opt/WorldSim-Writer/backend && PYTHONIOENCODING=utf-8 .venv/bin/python scripts/cleanup_e2e_data.py --confirm",
        'checks': {},
    }

    try:
        health = _step_json(summary, 'health', lambda: client.get('/health'))
        if _has_failed(summary):
            return summary
        if not _require_paths(summary, 'health', health, ['status', 'migration.up_to_date', 'llm.mock']):
            return summary
        backend_llm_mock = (health.get('llm') or {}).get('mock')
        summary['checks']['health'] = {
            'status': health.get('status'),
            'migration_up_to_date': (health.get('migration') or {}).get('up_to_date'),
            'llm_mock': backend_llm_mock,
        }
        if summary['checks']['health']['status'] != 'ok':
            summary['failed_step'] = 'health'
            summary['error'] = 'HEALTH_STATUS_NOT_OK'
            return summary
        if summary['checks']['health']['migration_up_to_date'] is False:
            summary['failed_step'] = 'health'
            summary['error'] = 'MIGRATION_NOT_UP_TO_DATE'
            return summary
        if mode == 'mock' and backend_llm_mock is False:
            summary['failed_step'] = 'health'
            summary['error'] = 'BACKEND_LLM_MOCK_DISABLED'
            return summary
        if mode == 'real-llm' and backend_llm_mock is True:
            summary['failed_step'] = 'health'
            summary['error'] = 'BACKEND_LLM_MOCK_ENABLED'
            return summary

        auth_payload, auth_step = _register_or_login(client, email, password, summary)
        if _has_failed(summary):
            return summary
        if not _require_fields(summary, auth_step, auth_payload, ['access_token']):
            return summary
        token = auth_payload['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        summary['checks'][auth_step] = {'user_id': (auth_payload.get('user') or {}).get('id')}

        world = _step_json(summary, 'create_world', lambda: client.post('/worlds/from-template', headers=headers))
        if _has_failed(summary):
            return summary
        if not _require_fields(summary, 'create_world', world, ['id', 'world_version']):
            return summary
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
            return summary
        if not _require_fields(summary, 'draft', draft, ['chapter_id', 'draft_version']):
            return summary
        chapter_id = draft['chapter_id']
        draft_version = draft['draft_version']
        summary['chapter_id'] = chapter_id
        summary['draft_id'] = draft.get('draft_id')
        summary['checks']['draft'] = {'draft_version': draft_version}

        preview = _step_json(summary, 'approval_preview', lambda: client.get(f'/chapters/{chapter_id}/approval-preview', headers=headers))
        if _has_failed(summary):
            return summary
        if not _require_list_of_dicts(summary, 'approval_preview', preview, 'character_changes'):
            return summary
        if not _require_list_of_dicts(summary, 'approval_preview', preview, 'foreshadow_changes'):
            return summary
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
            return summary
        if proposed_change_count == 0:
            summary['failed_step'] = 'approval_preview'
            summary['error'] = 'NO_PROPOSED_PROJECTION_CHANGES'
            return summary

        readiness = _step_json(summary, 'approval_readiness', lambda: client.get(f'/chapters/{chapter_id}/approval-readiness', headers=headers))
        if _has_failed(summary):
            return summary
        if not _require_fields(summary, 'approval_readiness', readiness, ['status']):
            return summary
        if not _require_list(summary, 'approval_readiness', readiness, 'blocking_reasons'):
            return summary
        if not _require_list(summary, 'approval_readiness', readiness, 'warnings'):
            return summary
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
            return summary

        consistency = _step_json(
            summary,
            'approval_consistency',
            lambda: client.post(f'/chapters/{chapter_id}/approval-consistency', json={'draft_version': draft_version}, headers=headers),
        )
        if _has_failed(summary):
            return summary
        if not _require_paths(summary, 'approval_consistency', consistency, ['consistency_summary.status']):
            return summary
        if not _require_int_path(summary, 'approval_consistency', consistency, 'consistency_summary.blocking_count'):
            return summary
        if not _require_fields(summary, 'approval_consistency', consistency, ['consistency_warnings']):
            return summary
        if not _require_list_of_dicts(summary, 'approval_consistency', consistency, 'consistency_warnings'):
            return summary
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
            return summary

        approved = _step_json(summary, 'approve', lambda: client.post(f'/chapters/{chapter_id}/approve', json={'draft_version': draft_version}, headers=headers))
        if _has_failed(summary):
            return summary
        if not _require_fields(summary, 'approve', approved, ['status', 'approved_version']):
            return summary
        approved_version = approved.get('approved_version')
        expected_world_version_after = initial_world_version + 1 if isinstance(initial_world_version, int) else None
        world_version_incremented = approved_version == expected_world_version_after
        summary['checks']['approve'] = {
            'status': approved.get('status'),
            'approved_version': approved_version,
            'expected_world_version_after': expected_world_version_after,
            'world_version_incremented': world_version_incremented,
        }
        if approved.get('status') != 'approved':
            summary['failed_step'] = 'approve'
            summary['error'] = 'APPROVAL_STATUS_NOT_APPROVED'
            return summary
        if not world_version_incremented:
            summary['failed_step'] = 'approve'
            summary['error'] = 'WORLD_VERSION_NOT_INCREMENTED'
            return summary

        events = _step_json(summary, 'events', lambda: client.get(f'/worlds/{world_id}/events', params={'limit': 100}, headers=headers))
        if _has_failed(summary):
            return summary
        if not _require_fields(summary, 'events', events, ['items']):
            return summary
        if not _require_list_of_dicts(summary, 'events', events, 'items'):
            return summary
        event_types = [event.get('event_type') for event in events.get('items', [])]
        chapter_approved_seen = 'chapter_approved' in event_types or 'chapter_approved' in (events.get('summary') or {}).get('event_type_counts', {})
        summary['checks']['events'] = {
            'event_types': event_types,
            'chapter_approved_seen': chapter_approved_seen,
        }
        if not chapter_approved_seen:
            summary['failed_step'] = 'events'
            summary['error'] = 'CHAPTER_APPROVED_EVENT_MISSING'
            return summary

        export = _step_json(summary, 'markdown_export', lambda: client.post(f'/worlds/{world_id}/export/markdown', headers=headers))
        if _has_failed(summary):
            return summary
        if not _require_fields(summary, 'markdown_export', export, ['archive_format', 'archive_encoding', 'archive_base64', 'files_are_inline', 'files']):
            return summary
        if not _require_list_of_dicts(summary, 'markdown_export', export, 'files'):
            return summary
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
            return summary

        summary['ok'] = all(
            [
                health.get('status') == 'ok',
                not preview_blocked,
                proposed_change_count > 0,
                not readiness_blocked,
                not consistency_blocked,
                approved.get('status') == 'approved',
                world_version_incremented,
                chapter_approved_seen,
                export.get('archive_format') == 'zip',
                export.get('archive_encoding') == 'base64',
                export.get('files_are_inline') is True,
                bool(export.get('archive_base64')),
                has_world_md,
            ]
        )
        return summary
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
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary.get('ok') else 1


if __name__ == '__main__':
    raise SystemExit(main())
