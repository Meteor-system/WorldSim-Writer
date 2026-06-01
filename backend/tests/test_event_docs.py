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
    ]
    for term in required_terms:
        assert term in playbook
