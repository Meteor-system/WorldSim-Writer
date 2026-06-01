import importlib.util
from pathlib import Path

import httpx


SCRIPT_PATH = Path('/opt/WorldSim-Writer/backend/scripts/e2e_smoke.py')


def load_e2e_smoke_module():
    spec = importlib.util.spec_from_file_location('e2e_smoke_script', SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SequencedTransport(httpx.BaseTransport):
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def handle_request(self, request):
        self.requests.append(request)
        assert self.responses, f'unexpected request: {request.method} {request.url}'
        return self.responses.pop(0)


class FailingTransport(httpx.BaseTransport):
    def __init__(self, message):
        self.message = message
        self.requests = []

    def handle_request(self, request):
        self.requests.append(request)
        raise httpx.ConnectError(self.message, request=request)


def json_response(payload, status_code=200):
    return httpx.Response(status_code, json=payload)


def test_e2e_smoke_script_runs_api_flow_and_returns_json_summary(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test/')
    monkeypatch.delenv('E2E_REAL_LLM', raising=False)
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            json_response({'chapter_id': 20, 'draft_id': 30, 'draft_version': 1}),
            json_response({'version_conflict': False, 'character_changes': [{'character_id': 1}], 'foreshadow_changes': []}),
            json_response({'ready': False, 'status': 'needs_review', 'blocking_reasons': [], 'warnings': ['mock warnings']}),
            json_response({'consistency_summary': {'status': 'clear'}, 'consistency_warnings': []}),
            json_response({'id': 20, 'status': 'approved', 'approved_version': 2}),
            json_response({'items': [{'event_type': 'chapter_approved'}], 'summary': {'event_type_counts': {'chapter_approved': 1}}}),
            json_response({'archive_format': 'zip', 'archive_encoding': 'base64', 'archive_base64': 'UEs=', 'files_are_inline': True, 'files': [{'path': 'World.md', 'content': '# World'}]}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is True
    assert summary['base_url'] == 'https://worldsim.test'
    assert summary['mode'] == 'mock'
    assert summary['world_id'] == 10
    assert summary['chapter_id'] == 20
    assert summary['checks']['health']['migration_up_to_date'] is True
    assert summary['checks']['health']['llm_mock'] is True
    assert summary['checks']['approval_preview']['proposed_change_count'] == 1
    assert summary['checks']['approve']['expected_world_version_after'] == 2
    assert summary['checks']['approve']['world_version_incremented'] is True
    assert summary['checks']['events']['chapter_approved_seen'] is True
    assert summary['checks']['markdown_export']['archive_format'] == 'zip'
    assert summary['checks']['markdown_export']['files_are_inline'] is True
    assert [request.url.path for request in transport.requests] == [
        '/health',
        '/auth/register',
        '/worlds/from-template',
        '/worlds/10/chapters/draft',
        '/chapters/20/approval-preview',
        '/chapters/20/approval-readiness',
        '/chapters/20/approval-consistency',
        '/chapters/20/approve',
        '/worlds/10/events',
        '/worlds/10/export/markdown',
    ]


def test_e2e_smoke_script_fails_when_approval_preview_has_version_conflict(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            json_response({'chapter_id': 20, 'draft_id': 30, 'draft_version': 1}),
            json_response({'version_conflict': True, 'character_changes': [], 'foreshadow_changes': []}),
            json_response({'ready': True, 'status': 'ready', 'blocking_reasons': [], 'warnings': []}),
            json_response({'consistency_summary': {'status': 'clear'}, 'consistency_warnings': []}),
            json_response({'id': 20, 'status': 'approved', 'approved_version': 2}),
            json_response({'items': [{'event_type': 'chapter_approved'}], 'summary': {'event_type_counts': {'chapter_approved': 1}}}),
            json_response({'archive_format': 'zip', 'archive_encoding': 'base64', 'archive_base64': 'UEs=', 'files_are_inline': True, 'files': [{'path': 'World.md', 'content': '# World'}]}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['checks']['approval_preview']['version_conflict'] is True
    assert summary['checks']['approval_preview']['blocked'] is True
    assert summary['failed_step'] == 'approval_preview'
    assert summary['error'] == 'APPROVAL_PREVIEW_BLOCKED'
    assert [request.url.path for request in transport.requests] == [
        '/health',
        '/auth/register',
        '/worlds/from-template',
        '/worlds/10/chapters/draft',
        '/chapters/20/approval-preview',
    ]


def test_e2e_smoke_script_fails_when_approval_preview_has_no_proposed_changes(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            json_response({'chapter_id': 20, 'draft_id': 30, 'draft_version': 1}),
            json_response({'version_conflict': False, 'character_changes': [], 'foreshadow_changes': []}),
            json_response({'ready': True, 'status': 'ready', 'blocking_reasons': [], 'warnings': []}),
            json_response({'consistency_summary': {'status': 'clear'}, 'consistency_warnings': []}),
            json_response({'id': 20, 'status': 'approved', 'approved_version': 2}),
            json_response({'items': [{'event_type': 'chapter_approved'}], 'summary': {'event_type_counts': {'chapter_approved': 1}}}),
            json_response({'archive_format': 'zip', 'archive_encoding': 'base64', 'archive_base64': 'UEs=', 'files_are_inline': True, 'files': [{'path': 'World.md', 'content': '# World'}]}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['checks']['approval_preview']['version_conflict'] is False
    assert summary['checks']['approval_preview']['proposed_change_count'] == 0
    assert summary['failed_step'] == 'approval_preview'
    assert summary['error'] == 'NO_PROPOSED_PROJECTION_CHANGES'
    assert [request.url.path for request in transport.requests] == [
        '/health',
        '/auth/register',
        '/worlds/from-template',
        '/worlds/10/chapters/draft',
        '/chapters/20/approval-preview',
    ]


def test_e2e_smoke_script_fails_when_expected_event_is_missing(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            json_response({'chapter_id': 20, 'draft_id': 30, 'draft_version': 1}),
            json_response({'version_conflict': False, 'character_changes': [{'character_id': 1}], 'foreshadow_changes': []}),
            json_response({'ready': True, 'status': 'ready', 'blocking_reasons': [], 'warnings': []}),
            json_response({'consistency_summary': {'status': 'clear'}, 'consistency_warnings': []}),
            json_response({'id': 20, 'status': 'approved', 'approved_version': 2}),
            json_response({'items': [{'event_type': 'world_version_increment'}], 'summary': {'event_type_counts': {'world_version_increment': 1}}}),
            json_response({'archive_format': 'zip', 'archive_encoding': 'base64', 'archive_base64': 'UEs=', 'files_are_inline': True, 'files': [{'path': 'World.md', 'content': '# World'}]}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['checks']['events']['chapter_approved_seen'] is False


def test_e2e_smoke_script_requires_event_items_for_event_check(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            json_response({'chapter_id': 20, 'draft_id': 30, 'draft_version': 1}),
            json_response({'version_conflict': False, 'character_changes': [{'character_id': 1}], 'foreshadow_changes': []}),
            json_response({'ready': True, 'status': 'ready', 'blocking_reasons': [], 'warnings': []}),
            json_response({'consistency_summary': {'status': 'clear'}, 'consistency_warnings': []}),
            json_response({'id': 20, 'status': 'approved', 'approved_version': 2}),
            json_response({'summary': {'event_type_counts': {'chapter_approved': 1}}}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['failed_step'] == 'events'
    assert summary['error'] == 'MISSING_REQUIRED_FIELDS'
    assert summary['missing_fields'] == ['items']
    assert [request.url.path for request in transport.requests] == [
        '/health',
        '/auth/register',
        '/worlds/from-template',
        '/worlds/10/chapters/draft',
        '/chapters/20/approval-preview',
        '/chapters/20/approval-readiness',
        '/chapters/20/approval-consistency',
        '/chapters/20/approve',
        '/worlds/10/events',
    ]


def test_e2e_smoke_script_requires_event_items_to_be_list_of_objects(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            json_response({'chapter_id': 20, 'draft_id': 30, 'draft_version': 1}),
            json_response({'version_conflict': False, 'character_changes': [{'character_id': 1}], 'foreshadow_changes': []}),
            json_response({'ready': True, 'status': 'ready', 'blocking_reasons': [], 'warnings': []}),
            json_response({'consistency_summary': {'status': 'clear'}, 'consistency_warnings': []}),
            json_response({'id': 20, 'status': 'approved', 'approved_version': 2}),
            json_response({'items': {'event_type': 'chapter_approved'}}),
            json_response({'archive_format': 'zip', 'archive_encoding': 'base64', 'archive_base64': 'UEs=', 'files_are_inline': True, 'files': [{'path': 'World.md', 'content': '# World'}]}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['failed_step'] == 'events'
    assert summary['error'] == 'INVALID_FIELD_TYPES'
    assert summary['invalid_fields'] == ['items']
    assert [request.url.path for request in transport.requests] == [
        '/health',
        '/auth/register',
        '/worlds/from-template',
        '/worlds/10/chapters/draft',
        '/chapters/20/approval-preview',
        '/chapters/20/approval-readiness',
        '/chapters/20/approval-consistency',
        '/chapters/20/approve',
        '/worlds/10/events',
    ]


def test_e2e_smoke_script_requires_markdown_export_archive_fields(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            json_response({'chapter_id': 20, 'draft_id': 30, 'draft_version': 1}),
            json_response({'version_conflict': False, 'character_changes': [{'character_id': 1}], 'foreshadow_changes': []}),
            json_response({'ready': True, 'status': 'ready', 'blocking_reasons': [], 'warnings': []}),
            json_response({'consistency_summary': {'status': 'clear'}, 'consistency_warnings': []}),
            json_response({'id': 20, 'status': 'approved', 'approved_version': 2}),
            json_response({'items': [{'event_type': 'chapter_approved'}], 'summary': {'event_type_counts': {'chapter_approved': 1}}}),
            json_response({'archive_format': 'zip', 'archive_encoding': 'base64', 'files_are_inline': True, 'files': [{'path': 'World.md', 'content': '# World'}]}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['failed_step'] == 'markdown_export'
    assert summary['error'] == 'MISSING_REQUIRED_FIELDS'
    assert summary['missing_fields'] == ['archive_base64']


def test_e2e_smoke_script_requires_markdown_export_files_to_be_list_of_objects(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            json_response({'chapter_id': 20, 'draft_id': 30, 'draft_version': 1}),
            json_response({'version_conflict': False, 'character_changes': [{'character_id': 1}], 'foreshadow_changes': []}),
            json_response({'ready': True, 'status': 'ready', 'blocking_reasons': [], 'warnings': []}),
            json_response({'consistency_summary': {'status': 'clear'}, 'consistency_warnings': []}),
            json_response({'id': 20, 'status': 'approved', 'approved_version': 2}),
            json_response({'items': [{'event_type': 'chapter_approved'}], 'summary': {'event_type_counts': {'chapter_approved': 1}}}),
            json_response({'archive_format': 'zip', 'archive_encoding': 'base64', 'archive_base64': 'UEs=', 'files_are_inline': True, 'files': 'World.md'}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['failed_step'] == 'markdown_export'
    assert summary['error'] == 'INVALID_FIELD_TYPES'
    assert summary['invalid_fields'] == ['files']


def test_e2e_smoke_script_fails_when_approval_does_not_increment_world_version(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            json_response({'chapter_id': 20, 'draft_id': 30, 'draft_version': 1}),
            json_response({'version_conflict': False, 'character_changes': [{'character_id': 1}], 'foreshadow_changes': []}),
            json_response({'ready': True, 'status': 'ready', 'blocking_reasons': [], 'warnings': []}),
            json_response({'consistency_summary': {'status': 'clear'}, 'consistency_warnings': []}),
            json_response({'id': 20, 'status': 'approved', 'approved_version': 1}),
            json_response({'items': [{'event_type': 'chapter_approved'}], 'summary': {'event_type_counts': {'chapter_approved': 1}}}),
            json_response({'archive_format': 'zip', 'archive_encoding': 'base64', 'archive_base64': 'UEs=', 'files_are_inline': True, 'files': [{'path': 'World.md', 'content': '# World'}]}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['checks']['approve']['approved_version'] == 1
    assert summary['checks']['approve']['expected_world_version_after'] == 2
    assert summary['checks']['approve']['world_version_incremented'] is False
    assert summary['failed_step'] == 'approve'
    assert summary['error'] == 'WORLD_VERSION_NOT_INCREMENTED'
    assert [request.url.path for request in transport.requests] == [
        '/health',
        '/auth/register',
        '/worlds/from-template',
        '/worlds/10/chapters/draft',
        '/chapters/20/approval-preview',
        '/chapters/20/approval-readiness',
        '/chapters/20/approval-consistency',
        '/chapters/20/approve',
    ]


def test_e2e_smoke_script_stops_when_approval_status_is_not_approved(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            json_response({'chapter_id': 20, 'draft_id': 30, 'draft_version': 1}),
            json_response({'version_conflict': False, 'character_changes': [{'character_id': 1}], 'foreshadow_changes': []}),
            json_response({'ready': True, 'status': 'ready', 'blocking_reasons': [], 'warnings': []}),
            json_response({'consistency_summary': {'status': 'clear'}, 'consistency_warnings': []}),
            json_response({'id': 20, 'status': 'rejected', 'approved_version': 2}),
            json_response({'items': [{'event_type': 'chapter_approved'}], 'summary': {'event_type_counts': {'chapter_approved': 1}}}),
            json_response({'archive_format': 'zip', 'archive_encoding': 'base64', 'archive_base64': 'UEs=', 'files_are_inline': True, 'files': [{'path': 'World.md', 'content': '# World'}]}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['checks']['approve']['status'] == 'rejected'
    assert summary['failed_step'] == 'approve'
    assert summary['error'] == 'APPROVAL_STATUS_NOT_APPROVED'
    assert [request.url.path for request in transport.requests] == [
        '/health',
        '/auth/register',
        '/worlds/from-template',
        '/worlds/10/chapters/draft',
        '/chapters/20/approval-preview',
        '/chapters/20/approval-readiness',
        '/chapters/20/approval-consistency',
        '/chapters/20/approve',
    ]



def test_e2e_smoke_script_requires_approval_status_after_approval(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            json_response({'chapter_id': 20, 'draft_id': 30, 'draft_version': 1}),
            json_response({'version_conflict': False, 'character_changes': [{'character_id': 1}], 'foreshadow_changes': []}),
            json_response({'ready': True, 'status': 'ready', 'blocking_reasons': [], 'warnings': []}),
            json_response({'consistency_summary': {'status': 'clear'}, 'consistency_warnings': []}),
            json_response({'id': 20, 'approved_version': 2}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['failed_step'] == 'approve'
    assert summary['error'] == 'MISSING_REQUIRED_FIELDS'
    assert summary['missing_fields'] == ['status']
    assert [request.url.path for request in transport.requests] == [
        '/health',
        '/auth/register',
        '/worlds/from-template',
        '/worlds/10/chapters/draft',
        '/chapters/20/approval-preview',
        '/chapters/20/approval-readiness',
        '/chapters/20/approval-consistency',
        '/chapters/20/approve',
    ]


def test_e2e_smoke_script_requires_approved_version_after_approval(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            json_response({'chapter_id': 20, 'draft_id': 30, 'draft_version': 1}),
            json_response({'version_conflict': False, 'character_changes': [{'character_id': 1}], 'foreshadow_changes': []}),
            json_response({'ready': True, 'status': 'ready', 'blocking_reasons': [], 'warnings': []}),
            json_response({'consistency_summary': {'status': 'clear'}, 'consistency_warnings': []}),
            json_response({'id': 20, 'status': 'approved'}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['failed_step'] == 'approve'
    assert summary['error'] == 'MISSING_REQUIRED_FIELDS'
    assert summary['missing_fields'] == ['approved_version']
    assert [request.url.path for request in transport.requests] == [
        '/health',
        '/auth/register',
        '/worlds/from-template',
        '/worlds/10/chapters/draft',
        '/chapters/20/approval-preview',
        '/chapters/20/approval-readiness',
        '/chapters/20/approval-consistency',
        '/chapters/20/approve',
    ]


def test_e2e_smoke_script_fails_when_approval_readiness_is_blocked(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            json_response({'chapter_id': 20, 'draft_id': 30, 'draft_version': 1}),
            json_response({'version_conflict': False, 'character_changes': [{'character_id': 1}], 'foreshadow_changes': []}),
            json_response({'ready': False, 'status': 'blocked', 'blocking_reasons': ['世界版本已变化，请重新生成草稿后再批准。'], 'warnings': []}),
            json_response({'consistency_summary': {'status': 'clear'}, 'consistency_warnings': []}),
            json_response({'id': 20, 'status': 'approved', 'approved_version': 2}),
            json_response({'items': [{'event_type': 'chapter_approved'}], 'summary': {'event_type_counts': {'chapter_approved': 1}}}),
            json_response({'archive_format': 'zip', 'archive_encoding': 'base64', 'archive_base64': 'UEs=', 'files_are_inline': True, 'files': [{'path': 'World.md', 'content': '# World'}]}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['checks']['approval_readiness']['status'] == 'blocked'
    assert summary['checks']['approval_readiness']['blocking_reasons'] == ['世界版本已变化，请重新生成草稿后再批准。']
    assert summary['checks']['approval_readiness']['blocked'] is True
    assert summary['failed_step'] == 'approval_readiness'
    assert summary['error'] == 'APPROVAL_READINESS_BLOCKED'
    assert [request.url.path for request in transport.requests] == [
        '/health',
        '/auth/register',
        '/worlds/from-template',
        '/worlds/10/chapters/draft',
        '/chapters/20/approval-preview',
        '/chapters/20/approval-readiness',
    ]


def test_e2e_smoke_script_requires_consistency_summary_status_before_approval(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            json_response({'chapter_id': 20, 'draft_id': 30, 'draft_version': 1}),
            json_response({'version_conflict': False, 'character_changes': [{'character_id': 1}], 'foreshadow_changes': []}),
            json_response({'ready': True, 'status': 'ready', 'blocking_reasons': [], 'warnings': []}),
            json_response({'consistency_summary': {}, 'consistency_warnings': []}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['failed_step'] == 'approval_consistency'
    assert summary['error'] == 'MISSING_REQUIRED_FIELDS'
    assert summary['missing_fields'] == ['consistency_summary.status']
    assert [request.url.path for request in transport.requests] == [
        '/health',
        '/auth/register',
        '/worlds/from-template',
        '/worlds/10/chapters/draft',
        '/chapters/20/approval-preview',
        '/chapters/20/approval-readiness',
        '/chapters/20/approval-consistency',
    ]


def test_e2e_smoke_script_fails_when_approval_consistency_is_blocked(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    consistency_warnings = [
        {
            'severity': 'blocking',
            'category': 'foreshadow_transition',
            'object_type': 'foreshadow',
            'object_id': 1,
            'change_index': 0,
            'message': 'Invalid transition',
        }
    ]
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            json_response({'chapter_id': 20, 'draft_id': 30, 'draft_version': 1}),
            json_response({'version_conflict': False, 'character_changes': [{'character_id': 1}], 'foreshadow_changes': []}),
            json_response({'ready': True, 'status': 'ready', 'blocking_reasons': [], 'warnings': []}),
            json_response({'consistency_summary': {'status': 'blocked', 'blocking_count': 1}, 'consistency_warnings': consistency_warnings}),
            json_response({'id': 20, 'status': 'approved', 'approved_version': 2}),
            json_response({'items': [{'event_type': 'chapter_approved'}], 'summary': {'event_type_counts': {'chapter_approved': 1}}}),
            json_response({'archive_format': 'zip', 'archive_encoding': 'base64', 'archive_base64': 'UEs=', 'files_are_inline': True, 'files': [{'path': 'World.md', 'content': '# World'}]}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['checks']['approval_consistency']['status'] == 'blocked'
    assert summary['checks']['approval_consistency']['blocking_count'] == 1
    assert summary['checks']['approval_consistency']['blocked'] is True
    assert summary['checks']['approval_consistency']['warnings'] == consistency_warnings
    assert summary['failed_step'] == 'approval_consistency'
    assert summary['error'] == 'APPROVAL_CONSISTENCY_BLOCKED'
    assert [request.url.path for request in transport.requests] == [
        '/health',
        '/auth/register',
        '/worlds/from-template',
        '/worlds/10/chapters/draft',
        '/chapters/20/approval-preview',
        '/chapters/20/approval-readiness',
        '/chapters/20/approval-consistency',
    ]


def test_e2e_smoke_script_requires_world_version_baseline_for_create_world(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['failed_step'] == 'create_world'
    assert summary['error'] == 'MISSING_REQUIRED_FIELDS'
    assert summary['missing_fields'] == ['world_version']
    assert summary['checks']['health']['status'] == 'ok'
    assert summary['checks']['register']['user_id'] == 1
    assert [request.url.path for request in transport.requests] == [
        '/health',
        '/auth/register',
        '/worlds/from-template',
    ]


def test_e2e_smoke_script_reports_missing_required_fields_for_success_response(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            json_response({'draft_id': 30, 'draft_version': 1}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['failed_step'] == 'draft'
    assert summary['error'] == 'MISSING_REQUIRED_FIELDS'
    assert summary['missing_fields'] == ['chapter_id']
    assert summary['checks']['health']['status'] == 'ok'
    assert summary['checks']['register']['user_id'] == 1
    assert summary['checks']['create_world']['world_version'] == 1
    assert [request.url.path for request in transport.requests] == [
        '/health',
        '/auth/register',
        '/worlds/from-template',
        '/worlds/10/chapters/draft',
    ]


def test_e2e_smoke_script_returns_step_context_for_http_failure(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            httpx.Response(502, text='MODEL_REQUEST_FAILED'),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['failed_step'] == 'draft'
    assert summary['status_code'] == 502
    assert summary['response_body'] == 'MODEL_REQUEST_FAILED'
    assert 'Authorization' not in summary['error']
    assert summary['checks']['health']['status'] == 'ok'
    assert summary['checks']['register']['user_id'] == 1
    assert summary['checks']['create_world']['world_version'] == 1


def test_e2e_smoke_script_redacts_sensitive_response_body_details(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    sensitive_body = (
        'MODEL_REQUEST_FAILED Authorization: Bearer secret-token '
        'api_key=sk-test-secret password=secretpass '
        'LLM_BASE_URL=https://provider.example/v1 LLM_MODEL=secret-model '
        "messages=[{'role':'user','content':'secret prompt'}]"
    )
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            httpx.Response(502, text=sensitive_body),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    response_body = summary['response_body']
    assert summary['ok'] is False
    assert summary['failed_step'] == 'draft'
    assert summary['status_code'] == 502
    assert 'secret-token' not in response_body
    assert 'sk-test-secret' not in response_body
    assert 'secretpass' not in response_body
    assert 'https://provider.example/v1' not in response_body
    assert 'secret-model' not in response_body
    assert 'secret prompt' not in response_body
    assert '[REDACTED_SECRET]' in response_body
    assert '[REDACTED_URL]' in response_body
    assert '[REDACTED_MODEL]' in response_body
    assert '[REDACTED_MESSAGES]' in response_body


def test_e2e_smoke_script_returns_step_context_for_request_error(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = FailingTransport('backend unavailable')
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['failed_step'] == 'health'
    assert 'backend unavailable' in summary['error']
    assert 'status_code' not in summary
    assert 'response_body' not in summary
    assert summary['checks'] == {}
    assert [request.url.path for request in transport.requests] == ['/health']


def test_e2e_smoke_script_reports_missing_access_token_for_login_fallback(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
            json_response({'detail': 'Email already registered'}, status_code=400),
            json_response({'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['failed_step'] == 'login'
    assert summary['error'] == 'MISSING_REQUIRED_FIELDS'
    assert summary['missing_fields'] == ['access_token']
    assert [request.url.path for request in transport.requests] == [
        '/health',
        '/auth/register',
        '/auth/login',
    ]


def test_e2e_smoke_script_requires_health_status_for_preflight(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['failed_step'] == 'health'
    assert summary['error'] == 'MISSING_REQUIRED_FIELDS'
    assert summary['missing_fields'] == ['status']
    assert [request.url.path for request in transport.requests] == ['/health']


def test_e2e_smoke_script_stops_when_health_status_is_not_ok(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'degraded', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['failed_step'] == 'health'
    assert summary['error'] == 'HEALTH_STATUS_NOT_OK'
    assert summary['checks']['health'] == {
        'status': 'degraded',
        'migration_up_to_date': True,
        'llm_mock': True,
    }
    assert [request.url.path for request in transport.requests] == ['/health']


def test_e2e_smoke_script_requires_health_llm_mode_for_preflight(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    monkeypatch.delenv('E2E_REAL_LLM', raising=False)
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {}}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['failed_step'] == 'health'
    assert summary['error'] == 'MISSING_REQUIRED_FIELDS'
    assert summary['missing_fields'] == ['llm.mock']
    assert [request.url.path for request in transport.requests] == ['/health']


def test_e2e_smoke_script_stops_when_mock_smoke_targets_real_llm_backend(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    monkeypatch.delenv('E2E_REAL_LLM', raising=False)
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': False}}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['failed_step'] == 'health'
    assert summary['error'] == 'BACKEND_LLM_MOCK_DISABLED'
    assert summary['checks']['health'] == {
        'status': 'ok',
        'migration_up_to_date': True,
        'llm_mock': False,
    }
    assert [request.url.path for request in transport.requests] == ['/health']


def test_e2e_smoke_script_stops_when_real_llm_smoke_targets_mock_backend(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    monkeypatch.setenv('E2E_REAL_LLM', '1')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}, 'llm': {'mock': True}}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['mode'] == 'real-llm'
    assert summary['failed_step'] == 'health'
    assert summary['error'] == 'BACKEND_LLM_MOCK_ENABLED'
    assert summary['checks']['health'] == {
        'status': 'ok',
        'migration_up_to_date': True,
        'llm_mock': True,
    }
    assert [request.url.path for request in transport.requests] == ['/health']


def test_e2e_smoke_script_stops_when_migration_is_not_up_to_date(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response(
                {
                    'status': 'ok',
                    'migration': {
                        'current': '0011_previous',
                        'head': '0012_add_tags',
                        'up_to_date': False,
                        'status': 'pending',
                    },
                    'llm': {'mock': True},
                }
            ),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['failed_step'] == 'health'
    assert summary['error'] == 'MIGRATION_NOT_UP_TO_DATE'
    assert summary['checks']['health'] == {
        'status': 'ok',
        'migration_up_to_date': False,
        'llm_mock': True,
    }
    assert [request.url.path for request in transport.requests] == ['/health']
