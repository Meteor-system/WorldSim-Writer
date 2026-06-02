from pathlib import Path

REPO_ROOT = Path('/opt/WorldSim-Writer')
DOC_PATHS = [
    REPO_ROOT / 'README.md',
    REPO_ROOT / 'CLAUDE.md',
    REPO_ROOT / 'WorldSim-Writer.md',
]


def test_event_type_docs_use_lower_snake_case_for_chapter_approval():
    combined = '\n'.join(path.read_text(encoding='utf-8') for path in DOC_PATHS)

    assert 'CHAPTER_APPROVED' not in combined
    assert 'chapter_approved' in combined


def test_env_example_documents_mock_llm_mode_for_e2e_smoke():
    env_example = (REPO_ROOT / 'backend' / '.env.example').read_text(encoding='utf-8')

    assert 'LLM_MOCK=false' in env_example


def test_beta_testing_playbook_documents_main_flow_smoke_and_reporting():
    playbook = (REPO_ROOT / 'BETA_TESTING.md').read_text(encoding='utf-8')

    required_terms = [
        'Mock smoke',
        'Real-LLM smoke',
        'Manual main-flow QA',
        'Archive/read-only spot checks',
        'Cleanup',
        'Bug report evidence',
        'failed_step',
        'status_code',
        'response_body',
        'MISSING_REQUIRED_FIELDS',
        'missing_fields',
        'MIGRATION_NOT_UP_TO_DATE',
        'alembic upgrade head',
        'world_version_incremented',
        'checks.approve.status',
        'approved_version',
        'llm_mock',
        'migration.up_to_date',
        'llm.mock',
        'checks.health.status',
        'HEALTH_STATUS_NOT_OK',
        'checks.register',
        'checks.login',
        'E2E_EMAIL',
        'BACKEND_LLM_MOCK_DISABLED',
        'BACKEND_LLM_MOCK_ENABLED',
        'checks.approval_preview.blocked',
        'checks.approval_preview.version_conflict',
        'approval preview version-conflict booleans',
        'checks.approval_preview.proposed_change_count',
        'checks.approval_readiness.blocked',
        'checks.approval_readiness.ready',
        'approval readiness ready booleans',
        'checks.approval_consistency.blocked',
        'checks.approval_consistency.status',
        'consistency_summary.status',
        'checks.approval_consistency.warnings',
        'approval consistency warning lists',
        'approval consistency blocker counts',
        'APPROVAL_PREVIEW_BLOCKED',
        'NO_PROPOSED_PROJECTION_CHANGES',
        'APPROVAL_READINESS_BLOCKED',
        'APPROVAL_CONSISTENCY_BLOCKED',
        'APPROVAL_STATUS_NOT_APPROVED',
        'WORLD_VERSION_NOT_INCREMENTED',
        'checks.overview.world_version_matches_approval',
        'checks.overview.approved_chapter_count_incremented',
        'OVERVIEW_WORLD_VERSION_NOT_UPDATED',
        'OVERVIEW_APPROVED_CHAPTER_MISSING',
        'OVERVIEW_PROJECTION_EMPTY',
        'checks.events.chapter_approved_seen',
        'CHAPTER_APPROVED_EVENT_MISSING',
        'MARKDOWN_EXPORT_INVALID_ARCHIVE',
        'files.World.md',
        'MODEL_AUTH_FAILED',
        'MODEL_RATE_LIMITED',
        'INVALID_FIELD_TYPES',
        'invalid_fields',
        'INVALID_JSON_RESPONSE',
        'INVALID_JSON_RESPONSE_TYPE',
        'non-object JSON',
        'redacted',
        'REDACTED_SECRET',
        'Authorization',
        'bearer',
        'E2E_TIMEOUT_SECONDS',
        'REQUEST_TIMEOUT',
        'JSON-shaped',
    ]
    for term in required_terms:
        assert term in playbook
