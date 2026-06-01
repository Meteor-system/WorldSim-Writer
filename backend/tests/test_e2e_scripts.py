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


def json_response(payload, status_code=200):
    return httpx.Response(status_code, json=payload)


def test_e2e_smoke_script_runs_api_flow_and_returns_json_summary(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test/')
    monkeypatch.delenv('E2E_REAL_LLM', raising=False)
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            json_response({'chapter_id': 20, 'draft_id': 30, 'draft_version': 1}),
            json_response({'version_conflict': False, 'character_changes': [], 'foreshadow_changes': []}),
            json_response({'ready': False, 'status': 'needs_review', 'blocking_reasons': [], 'warnings': ['mock warnings']}),
            json_response({'consistency_summary': {'status': 'clear'}, 'consistency_warnings': []}),
            json_response({'id': 20, 'status': 'approved', 'approved_version': 1}),
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


def test_e2e_smoke_script_fails_when_expected_event_is_missing(monkeypatch):
    monkeypatch.setenv('BASE_URL', 'https://worldsim.test')
    module = load_e2e_smoke_module()
    transport = SequencedTransport(
        [
            json_response({'status': 'ok', 'migration': {'up_to_date': True}}),
            json_response({'access_token': 'token', 'user': {'id': 1, 'email': 'e2e-smoke@example.com'}}),
            json_response({'id': 10, 'world_version': 1}),
            json_response({'chapter_id': 20, 'draft_id': 30, 'draft_version': 1}),
            json_response({'version_conflict': False}),
            json_response({'ready': True, 'status': 'ready', 'blocking_reasons': [], 'warnings': []}),
            json_response({'consistency_summary': {'status': 'clear'}, 'consistency_warnings': []}),
            json_response({'id': 20, 'status': 'approved', 'approved_version': 1}),
            json_response({'items': [{'event_type': 'world_version_increment'}], 'summary': {'event_type_counts': {'world_version_increment': 1}}}),
            json_response({'archive_format': 'zip', 'archive_encoding': 'base64', 'archive_base64': 'UEs=', 'files_are_inline': True, 'files': [{'path': 'World.md', 'content': '# World'}]}),
        ]
    )
    client = httpx.Client(transport=transport, base_url='https://worldsim.test')

    summary = module.run_smoke(client=client, email='e2e-smoke@example.com')

    assert summary['ok'] is False
    assert summary['checks']['events']['chapter_approved_seen'] is False
