#!/usr/bin/env python
import json
import os
from datetime import datetime, timezone
from uuid import uuid4

import httpx

DEFAULT_BASE_URL = 'http://localhost:8000'
DEFAULT_PASSWORD = 'strongpass123'
MAX_RESPONSE_BODY_CHARS = 1000


def _env_bool(name: str) -> bool:
    return os.getenv(name, '').strip().lower() in {'1', 'true', 'yes', 'on'}


def _base_url() -> str:
    return os.getenv('BASE_URL', DEFAULT_BASE_URL).rstrip('/')


def _default_email() -> str:
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    return f'e2e-smoke-{stamp}-{uuid4().hex[:8]}@example.com'


def _response_body_snippet(response: httpx.Response) -> str:
    return response.text[:MAX_RESPONSE_BODY_CHARS]


def _json_response(response: httpx.Response) -> dict:
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError('Expected JSON object response')
    return payload


def _step_json(summary: dict, step: str, request_call) -> dict:
    try:
        return _json_response(request_call())
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
    if client is None:
        client = httpx.Client(base_url=base_url, timeout=60.0)
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
        consistency_summary = consistency.get('consistency_summary') or {}
        consistency_warnings = consistency.get('consistency_warnings')
        consistency_blocked = consistency_summary.get('status') == 'blocked' or (consistency_summary.get('blocking_count') or 0) > 0
        summary['checks']['approval_consistency'] = {
            **consistency_summary,
            'blocked': consistency_blocked,
            'warnings': consistency_warnings if isinstance(consistency_warnings, list) else [],
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
        event_types = [event.get('event_type') for event in events.get('items', [])]
        chapter_approved_seen = 'chapter_approved' in event_types or 'chapter_approved' in (events.get('summary') or {}).get('event_type_counts', {})
        summary['checks']['events'] = {
            'event_types': event_types,
            'chapter_approved_seen': chapter_approved_seen,
        }

        export = _step_json(summary, 'markdown_export', lambda: client.post(f'/worlds/{world_id}/export/markdown', headers=headers))
        if _has_failed(summary):
            return summary
        if not _require_fields(summary, 'markdown_export', export, ['archive_format', 'archive_encoding', 'archive_base64', 'files_are_inline', 'files']):
            return summary
        files = export.get('files') or []
        summary['checks']['markdown_export'] = {
            'archive_format': export.get('archive_format'),
            'archive_encoding': export.get('archive_encoding'),
            'archive_base64_present': bool(export.get('archive_base64')),
            'files_are_inline': export.get('files_are_inline'),
            'file_count': len(files),
            'has_world_md': any(file.get('path') == 'World.md' for file in files),
        }

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
                any(file.get('path') == 'World.md' for file in files),
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
